from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .io import load_json
from .models import Item, Review
from .production import import_review_response, item_fingerprint, parse_chat_json


def _find_candidate(root: Path, item_id: str) -> Item | None:
    for path in (
        root / "item_bank" / "draft" / f"{item_id}.json",
        root / "item_bank" / "approved" / f"{item_id}.json",
    ):
        if not path.exists():
            continue
        try:
            return Item.model_validate(load_json(path))
        except (ValidationError, ValueError, json.JSONDecodeError):
            return None
    return None


def import_bound_review_response(
    root: Path,
    text: str,
    *,
    item: Item | None = None,
) -> tuple[Review, Path]:
    """Import a reviewer response only if it names the exact candidate version.

    The blind-review prompt gives the reviewer one opaque SHA-256 fingerprint and
    requires it to be echoed unchanged. Re-pasting a review produced for an older
    draft therefore cannot create fresh release evidence for a modified candidate.
    """

    data = parse_chat_json(text)
    review = Review.model_validate(data)
    candidate = item or _find_candidate(root, review.item_id)
    if candidate is None:
        raise ValueError(
            "cannot bind review to candidate content; import/save the item draft first"
        )
    if candidate.item_id != review.item_id:
        raise ValueError("review item_id does not match candidate item")

    expected = item_fingerprint(candidate)
    observed = data.get("candidate_fingerprint")
    if observed != expected:
        if not observed:
            raise ValueError(
                "review is missing candidate_fingerprint; generate a fresh blind-review prompt"
            )
        raise ValueError(
            "review candidate_fingerprint does not match the current item; "
            "generate a fresh blind-review prompt for this version"
        )

    return import_review_response(root, text, item=candidate)
