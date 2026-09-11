from __future__ import annotations

import json
import re
from dataclasses import dataclass
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
    gates: tuple[Gate, ...]

    @property
    def ready(self) -> bool:
        return all(gate.passed for gate in self.gates)


def parse_chat_json(text: str) -> dict:
    """Parse a manual-ChatGPT JSON response without accepting arbitrary prose.

    The generation prompts require JSON-only output, but ChatGPT may still wrap the
    response in a single Markdown code fence. We accept that one harmless wrapper and
    reject surrounding commentary so accidental prose never enters the item bank.
    """

    stripped = text.strip()
    match = _CODE_FENCE_RE.fullmatch(stripped)
    if match:
        stripped = match.group(1).strip()
    data = json.loads(stripped)
    if not isinstance(data, dict):
        raise ValueError("response JSON must be one object")
    return data


def import_item_response(root: Path, text: str) -> tuple[Item, Path, Path, list[str], list[str]]:
    data = parse_chat_json(text)
    item = Item.model_validate(data)

    responses = root / "workspace" / "responses"
    response_path = responses / f"{item.item_id}.response.json"
    dump_json(response_path, data)

    draft_path = root / "item_bank" / "draft" / f"{item.item_id}.json"
    dump_json(draft_path, data)
    _, errors, warnings = validate_item_file(draft_path)
    return item, response_path, draft_path, errors, warnings


def import_review_response(root: Path, text: str) -> tuple[Review, Path]:
    data = parse_chat_json(text)
    review = Review.model_validate(data)
    path = root / "workspace" / "reviews" / f"{review.item_id}.review.json"
    dump_json(path, review.model_dump())
    return review, path


def human_qa_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "human_qa" / f"{item_id}.human_qa.json"


def review_path(root: Path, item_id: str) -> Path:
    return root / "workspace" / "reviews" / f"{item_id}.review.json"


def save_human_qa(root: Path, qa: HumanQA) -> Path:
    path = human_qa_path(root, qa.item_id)
    dump_json(path, qa.model_dump())
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
            gates=(Gate("deterministic validation", False, "; ".join(validation_errors)),),
        )

    review = review or load_review_if_present(root, item.item_id)
    human_qa = human_qa or load_human_qa_if_present(root, item.item_id)

    gates: list[Gate] = []
    gates.append(
        Gate(
            "deterministic validation",
            not validation_errors,
            "pass" if not validation_errors else "; ".join(validation_errors),
        )
    )

    if review is None:
        gates.append(Gate("blind review", False, "review JSON not saved"))
    else:
        review_errors, _ = compare_review(item, review)
        gates.append(
            Gate(
                "blind review",
                not review_errors,
                "pass" if not review_errors else "; ".join(review_errors),
            )
        )

    if human_qa is None:
        gates.append(Gate("human QA", False, "human QA record not saved"))
    else:
        qa_errors = human_qa_errors(item, human_qa)
        gates.append(
            Gate(
                "human QA",
                not qa_errors,
                "pass" if not qa_errors else "; ".join(qa_errors),
            )
        )

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
    return ReleaseReadiness(item_id=item.item_id, gates=tuple(gates))


def approve_item(root: Path, item_path: Path) -> tuple[Path, ReleaseReadiness]:
    readiness = release_readiness(root, item_path)
    if not readiness.ready:
        failed = [f"{gate.name}: {gate.detail}" for gate in readiness.gates if not gate.passed]
        raise ValueError("release gates failed: " + " | ".join(failed))

    item = Item.model_validate(load_json(item_path))
    approved = item.model_copy(deep=True)
    approved.workflow.state = "approved"
    target = root / "item_bank" / "approved" / f"{approved.item_id}.json"
    dump_json(target, approved.model_dump())
    return target, readiness
