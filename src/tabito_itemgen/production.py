from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from .io import dump_json, load_json
from .models import HumanQA, Item, Review
from .validate import check_bank_similarity, compare_review, validate_item_file

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
SIMILARITY_APPROVAL_LIMIT = 0.35


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ReleaseReadiness:
    item_id: str
    fingerprint: str
    gates: tuple[Gate, ...]

    @property
    def ready(self) -> bool:
        return all(gate.passed for gate in self.gates)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_chat_json(text: str) -> dict:
    """Parse a manual-ChatGPT JSON response without accepting arbitrary prose.

    Generation prompts require JSON-only output, but ChatGPT may still wrap the
    response in one Markdown code fence. Accept that wrapper and reject surrounding
    commentary so accidental prose never enters the item bank.
    """

    stripped = text.strip()
    match = _CODE_FENCE_RE.fullmatch(stripped)
    if match:
        stripped = match.group(1).strip()
    data = json.loads(stripped)
    if not isinstance(data, dict):
        raise ValueError("response JSON must be one object")
    return data


def item_fingerprint(item: Item) -> str:
    """Return a stable fingerprint of the substantive candidate content.

    Workflow state is intentionally excluded so moving the exact same content from
    draft to approved does not invalidate the audit trail. Every other item field is
    included: changing a prompt, option, answer, material, rationale, source note, or
    blueprint-facing metadata invalidates previous review/QA evidence.
    """

    payload = item.model_dump(exclude={"workflow"})
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def import_item_response(
    root: Path,
    text: str,
    *,
    expected_item_id: str | None = None,
    expected_surface_family: str | None = None,
) -> tuple[Item, Path, Path, list[str], list[str]]:
    data = parse_chat_json(text)
    item = Item.model_validate(data)

    if expected_item_id and item.item_id != expected_item_id:
        raise ValueError(
            f"generated item_id {item.item_id!r} does not match request {expected_item_id!r}"
        )
    if expected_surface_family and item.surface_family != expected_surface_family:
        raise ValueError(
            "generated surface_family "
            f"{item.surface_family!r} does not match request {expected_surface_family!r}"
        )

    # Generated responses always enter the local bank as drafts, regardless of what
    # the model returned in workflow.state.
    canonical = item.model_copy(deep=True)
    canonical.workflow.state = "draft"

    responses = root / "workspace" / "responses"
    response_path = responses / f"{canonical.item_id}.response.json"
    dump_json(response_path, data)

    draft_path = root / "item_bank" / "draft" / f"{canonical.item_id}.json"
    dump_json(draft_path, canonical.model_dump())
    _, errors, warnings = validate_item_file(draft_path)
    return canonical, response_path, draft_path, errors, warnings


def review_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "reviews" / f"{item_id}.review.json"


def review_meta_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "reviews" / f"{item_id}.review.meta.json"


def human_qa_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "human_qa" / f"{item_id}.human_qa.json"


def human_qa_meta_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "human_qa" / f"{item_id}.human_qa.meta.json"


def release_record_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "releases" / f"{item_id}.release.json"


def _candidate_for_item_id(root: Path, item_id: str) -> Item | None:
    for path in (
        root / "item_bank" / "draft" / f"{item_id}.json",
        root / "item_bank" / "approved" / f"{item_id}.json",
    ):
        if path.exists():
            try:
                return Item.model_validate(load_json(path))
            except (ValidationError, ValueError, json.JSONDecodeError):
                return None
    return None


def import_review_response(
    root: Path,
    text: str,
    *,
    item: Item | None = None,
) -> tuple[Review, Path]:
    data = parse_chat_json(text)
    review = Review.model_validate(data)
    candidate = item or _candidate_for_item_id(root, review.item_id)
    if candidate is None:
        raise ValueError(
            "cannot bind review to candidate content; import/save the item draft first"
        )
    if candidate.item_id != review.item_id:
        raise ValueError("review item_id does not match candidate item")

    path = review_path(root, review.item_id)
    dump_json(path, review.model_dump())
    dump_json(
        review_meta_path(root, review.item_id),
        {
            "item_id": review.item_id,
            "item_fingerprint": item_fingerprint(candidate),
            "saved_at": _utc_now(),
        },
    )
    return review, path


def save_human_qa(root: Path, qa: HumanQA, *, item: Item | None = None) -> Path:
    candidate = item or _candidate_for_item_id(root, qa.item_id)
    if candidate is None:
        raise ValueError(
            "cannot bind human QA to candidate content; import/save the item draft first"
        )
    if candidate.item_id != qa.item_id:
        raise ValueError("human QA item_id does not match candidate item")

    path = human_qa_path(root, qa.item_id)
    dump_json(path, qa.model_dump())
    dump_json(
        human_qa_meta_path(root, qa.item_id),
        {
            "item_id": qa.item_id,
            "item_fingerprint": item_fingerprint(candidate),
            "saved_at": _utc_now(),
        },
    )
    return path


def load_review_if_present(root: Path, item_id: str) -> Review | None:
    path = review_path(root, item_id)
    if not path.exists():
        return None
    try:
        return Review.model_validate(load_json(path))
    except (ValidationError, ValueError, json.JSONDecodeError):
        return None


def load_human_qa_if_present(root: Path, item_id: str) -> HumanQA | None:
    path = human_qa_path(root, item_id)
    if not path.exists():
        return None
    try:
        return HumanQA.model_validate(load_json(path))
    except (ValidationError, ValueError, json.JSONDecodeError):
        return None


def _saved_fingerprint(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        value = load_json(path).get("item_fingerprint")
        return value if isinstance(value, str) and value else None
    except (ValueError, json.JSONDecodeError, OSError):
        return None


def review_binding_status(root: Path, item: Item) -> tuple[bool, str]:
    saved = _saved_fingerprint(review_meta_path(root, item.item_id))
    current = item_fingerprint(item)
    if saved is None:
        return False, "review is missing content fingerprint; run blind review again"
    if saved != current:
        return False, "candidate changed after blind review; run blind review again"
    return True, "review is bound to current candidate"


def human_qa_binding_status(root: Path, item: Item) -> tuple[bool, str]:
    saved = _saved_fingerprint(human_qa_meta_path(root, item.item_id))
    current = item_fingerprint(item)
    if saved is None:
        return False, "human QA is missing content fingerprint; review current version again"
    if saved != current:
        return False, "candidate changed after human QA; repeat human QA"
    return True, "human QA is bound to current candidate"


def human_qa_errors(item: Item, qa: HumanQA) -> list[str]:
    errors: list[str] = []
    if qa.item_id != item.item_id:
        errors.append("human QA item_id does not match item")
    if qa.disposition != "approve":
        errors.append(f"human QA disposition is {qa.disposition}, not approve")
    failed = [name for name, passed in qa.checks.model_dump().items() if not passed]
    if failed:
        errors.append("human QA required checks failed: " + ", ".join(failed))
    if qa.high_severity_ambiguity_after_blind:
        errors.append("human QA found high-severity ambiguity after blind review")
    return errors


def release_readiness(
    root: Path,
    item_path: Path,
    review: Review | None = None,
    human_qa: HumanQA | None = None,
) -> ReleaseReadiness:
    item, validation_errors, _ = validate_item_file(item_path)
    if item is None:
        item_id = item_path.stem
        return ReleaseReadiness(
            item_id=item_id,
            fingerprint="",
            gates=(Gate("deterministic validation", False, "; ".join(validation_errors)),),
        )

    fingerprint = item_fingerprint(item)
    review = review or load_review_if_present(root, item.item_id)
    human_qa = human_qa or load_human_qa_if_present(root, item.item_id)

    gates: list[Gate] = [
        Gate(
            "deterministic validation",
            not validation_errors,
            "pass" if not validation_errors else "; ".join(validation_errors),
        )
    ]

    if review is None:
        gates.append(Gate("blind review", False, "review JSON not saved"))
    else:
        binding_ok, binding_detail = review_binding_status(root, item)
        review_errors, _ = compare_review(item, review)
        passed = binding_ok and not review_errors
        detail_parts = [binding_detail]
        if review_errors:
            detail_parts.append("; ".join(review_errors))
        gates.append(Gate("blind review", passed, " | ".join(detail_parts)))

    if human_qa is None:
        gates.append(Gate("human QA", False, "human QA record not saved"))
    else:
        binding_ok, binding_detail = human_qa_binding_status(root, item)
        qa_errors = human_qa_errors(item, human_qa)
        passed = binding_ok and not qa_errors
        detail_parts = [binding_detail]
        if qa_errors:
            detail_parts.append("; ".join(qa_errors))
        gates.append(Gate("human QA", passed, " | ".join(detail_parts)))

    matches = check_bank_similarity(item, root / "item_bank" / "approved")
    best = matches[0] if matches else None
    similarity_ok = best is None or best[1] < SIMILARITY_APPROVAL_LIMIT
    gates.append(
        Gate(
            "approved-bank similarity",
            similarity_ok,
            "no notable match"
            if best is None
            else f"highest={best[1]:.3f} vs {best[0]} (limit {SIMILARITY_APPROVAL_LIMIT:.2f})",
        )
    )
    return ReleaseReadiness(
        item_id=item.item_id,
        fingerprint=fingerprint,
        gates=tuple(gates),
    )


def approve_item(root: Path, item_path: Path) -> tuple[Path, ReleaseReadiness]:
    readiness = release_readiness(root, item_path)
    if not readiness.ready:
        failed = [f"{gate.name}: {gate.detail}" for gate in readiness.gates if not gate.passed]
        raise ValueError("release gates failed: " + " | ".join(failed))

    item = Item.model_validate(load_json(item_path))
    target = root / "item_bank" / "approved" / f"{item.item_id}.json"
    if target.exists():
        existing = Item.model_validate(load_json(target))
        if item_fingerprint(existing) != readiness.fingerprint:
            raise ValueError(
                "approved item_id already exists with different content; create a new item_id/version"
            )
        return target, readiness

    approved = item.model_copy(deep=True)
    approved.workflow.state = "approved"
    dump_json(target, approved.model_dump())

    record = {
        "item_id": item.item_id,
        "item_fingerprint": readiness.fingerprint,
        "approved_at": _utc_now(),
        "approved_path": str(target.relative_to(root)),
        "review_path": str(review_path(root, item.item_id).relative_to(root)),
        "human_qa_path": str(human_qa_path(root, item.item_id).relative_to(root)),
        "blueprint_version": item.workflow.blueprint_version,
        "surface_family": item.surface_family,
        "gates": [
            {"name": gate.name, "passed": gate.passed, "detail": gate.detail}
            for gate in readiness.gates
        ],
    }
    dump_json(release_record_path(root, item.item_id), record)
    return target, readiness
