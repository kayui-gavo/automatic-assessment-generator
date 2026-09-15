from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Iterable

ANSWER_COLUMNS = {
    "participant_id",
    "exam_id",
    "exam_fingerprint",
    "answer_number",
    "section",
    "selected_option",
    "omitted",
    "ambiguity_flag",
    "note",
}
SECTION_COLUMNS = {
    "participant_id",
    "exam_id",
    "exam_fingerprint",
    "section",
    "elapsed_seconds",
    "completed",
    "perceived_difficulty_1_5",
    "note",
}
SECTIONS = {"Q1", "Q2", "Q3", "Q4", "Q5"}
EXPECTED_ANSWERS = set(range(1, 51))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing CSV header")
        return [dict(row) for row in reader]


def _require_columns(path: Path, rows: list[dict[str, str]], required: set[str]) -> None:
    if rows:
        available = set(rows[0])
    else:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            available = set(reader.fieldnames or [])
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"{path}: missing columns: {', '.join(missing)}")


def _binary(value: str, field: str, row_no: int) -> int:
    if value not in {"0", "1"}:
        raise ValueError(f"row {row_no}: {field} must be 0 or 1")
    return int(value)


def _int(value: str, field: str, row_no: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {row_no}: {field} must be an integer") from exc


def _identity(rows: Iterable[dict[str, str]]) -> tuple[str, str]:
    identities = {(row["exam_id"].strip(), row["exam_fingerprint"].strip()) for row in rows}
    if not identities:
        raise ValueError("pilot data is empty")
    if len(identities) != 1:
        raise ValueError("pilot data mixes multiple exam_id / exam_fingerprint values")
    exam_id, fingerprint = next(iter(identities))
    if not exam_id or not fingerprint:
        raise ValueError("exam_id and exam_fingerprint must be non-empty")
    return exam_id, fingerprint


def _section_for_answer(answer_number: int) -> str:
    if answer_number <= 6:
        return "Q1"
    if answer_number <= 12:
        return "Q2"
    if answer_number <= 20:
        return "Q3"
    if answer_number <= 36:
        return "Q4"
    return "Q5"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, label: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label}: {path}") from exc


def _load_released_answer_key(
    release_record_path: Path,
    *,
    exam_id: str,
    exam_fingerprint: str,
) -> dict[int, int]:
    release = _read_json(release_record_path, "release record")
    if not isinstance(release, dict):
        raise ValueError("release.json must be an object")
    if release.get("exam_id") != exam_id:
        raise ValueError("release record exam_id does not match student pilot data")
    if release.get("exam_fingerprint") != exam_fingerprint:
        raise ValueError("release record fingerprint does not match student pilot data")

    gates = release.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("release record has no gate evidence")
    if any(not isinstance(row, dict) or row.get("passed") is not True for row in gates):
        raise ValueError("release record contains an incomplete or failed release gate")

    artifact_dir = release_record_path.parent / "artifacts"
    artifact_manifest_path = artifact_dir / "artifact_manifest.json"
    expected_manifest_sha = release.get("artifact_manifest_sha256")
    if not isinstance(expected_manifest_sha, str) or not expected_manifest_sha:
        raise ValueError("release record does not bind artifact_manifest.json")
    if not artifact_manifest_path.exists():
        raise ValueError("approved artifact_manifest.json is missing")
    if _sha256_file(artifact_manifest_path) != expected_manifest_sha:
        raise ValueError("artifact_manifest.json hash does not match release record")

    manifest = _read_json(artifact_manifest_path, "artifact manifest")
    if not isinstance(manifest, dict):
        raise ValueError("artifact_manifest.json must be an object")
    if manifest.get("exam_id") != exam_id:
        raise ValueError("artifact manifest exam_id does not match student pilot data")
    if manifest.get("exam_fingerprint") != exam_fingerprint:
        raise ValueError("artifact manifest fingerprint does not match student pilot data")

    checks = manifest.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("artifact manifest has no PDF checks")
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("artifact manifest contains a malformed PDF check")
        name = check.get("name")
        expected_pdf_sha = check.get("pdf_sha256")
        if not isinstance(name, str) or not name:
            raise ValueError("artifact manifest PDF check has no name")
        if not isinstance(expected_pdf_sha, str) or not expected_pdf_sha:
            raise ValueError(f"artifact manifest does not bind {name}.pdf")
        pdf_path = artifact_dir / f"{name}.pdf"
        if not pdf_path.exists() or _sha256_file(pdf_path) != expected_pdf_sha:
            raise ValueError(f"approved artifact {name}.pdf failed integrity verification")

    extra_files = manifest.get("extra_files")
    if not isinstance(extra_files, dict):
        raise ValueError("artifact manifest has no valid extra_files map")
    expected_answer_sha = extra_files.get("answer_key.json")
    if not isinstance(expected_answer_sha, str) or not expected_answer_sha:
        raise ValueError("artifact manifest does not bind answer_key.json")

    answer_key_path = artifact_dir / "answer_key.json"
    if not answer_key_path.exists():
        raise ValueError("approved answer_key.json is missing")
    if _sha256_file(answer_key_path) != expected_answer_sha:
        raise ValueError("answer_key.json hash does not match artifact manifest")

    raw_key = _read_json(answer_key_path, "answer key")
    if not isinstance(raw_key, dict):
        raise ValueError("answer_key.json must be an object")

    parsed: dict[int, int] = {}
    for raw_number, raw_option in raw_key.items():
        try:
            number = int(raw_number)
            option = int(raw_option)
        except (TypeError, ValueError) as exc:
            raise ValueError("answer_key.json contains a non-integer answer mapping") from exc
        if not 1 <= number <= 50 or not 1 <= option <= 10:
            raise ValueError("answer_key.json contains an out-of-range answer mapping")
        parsed[number] = option
    if set(parsed) != EXPECTED_ANSWERS:
        missing = sorted(EXPECTED_ANSWERS - set(parsed))
        extra = sorted(set(parsed) - EXPECTED_ANSWERS)
        raise ValueError(
            f"answer_key.json must contain answer numbers 1..50 exactly; missing={missing}, extra={extra}"
        )
    return parsed


def validate_answer_rows(rows: list[dict[str, str]]) -> tuple[str, str]:
    exam_id, fingerprint = _identity(rows)
    seen: set[tuple[str, int]] = set()
    participant_answers: dict[str, set[int]] = defaultdict(set)
    for row_no, row in enumerate(rows, start=2):
        participant = row["participant_id"].strip()
        if not participant:
            raise ValueError(f"row {row_no}: participant_id must be non-empty")
        answer_number = _int(row["answer_number"], "answer_number", row_no)
        if not 1 <= answer_number <= 50:
            raise ValueError(f"row {row_no}: answer_number must be in 1..50")
        section = row["section"].strip()
        expected_section = _section_for_answer(answer_number)
        if section != expected_section:
            raise ValueError(
                f"row {row_no}: answer {answer_number} must belong to {expected_section}"
            )
        key = (participant, answer_number)
        if key in seen:
            raise ValueError(f"row {row_no}: duplicate participant/answer_number {key}")
        seen.add(key)
        participant_answers[participant].add(answer_number)

        omitted = _binary(row["omitted"], "omitted", row_no)
        _binary(row["ambiguity_flag"], "ambiguity_flag", row_no)
        selected = row["selected_option"].strip()
        if omitted:
            if selected:
                raise ValueError(f"row {row_no}: omitted=1 requires blank selected_option")
        else:
            selected_option = _int(selected, "selected_option", row_no)
            if not 1 <= selected_option <= 10:
                raise ValueError(f"row {row_no}: selected_option must be in 1..10")

    for participant, answers in participant_answers.items():
        if answers != EXPECTED_ANSWERS:
            missing = sorted(EXPECTED_ANSWERS - answers)
            raise ValueError(
                f"participant {participant}: expected answer rows 1..50; missing {missing}"
            )
    return exam_id, fingerprint


def validate_section_rows(rows: list[dict[str, str]]) -> tuple[str, str]:
    exam_id, fingerprint = _identity(rows)
    seen: set[tuple[str, str]] = set()
    participant_sections: dict[str, set[str]] = defaultdict(set)
    for row_no, row in enumerate(rows, start=2):
        participant = row["participant_id"].strip()
        if not participant:
            raise ValueError(f"row {row_no}: participant_id must be non-empty")
        section = row["section"].strip()
        if section not in {*SECTIONS, "TOTAL"}:
            raise ValueError(f"row {row_no}: section must be Q1..Q5 or TOTAL")
        key = (participant, section)
        if key in seen:
            raise ValueError(f"row {row_no}: duplicate participant/section {key}")
        seen.add(key)
        participant_sections[participant].add(section)
        elapsed = _int(row["elapsed_seconds"], "elapsed_seconds", row_no)
        if elapsed < 0:
            raise ValueError(f"row {row_no}: elapsed_seconds must be non-negative")
        _binary(row["completed"], "completed", row_no)
        difficulty = row["perceived_difficulty_1_5"].strip()
        if difficulty:
            value = _int(difficulty, "perceived_difficulty_1_5", row_no)
            if not 1 <= value <= 5:
                raise ValueError(
                    f"row {row_no}: perceived_difficulty_1_5 must be blank or 1..5"
                )

    for participant, sections in participant_sections.items():
        missing = sorted(SECTIONS - sections)
        if missing:
            raise ValueError(
                f"participant {participant}: section timing rows missing {missing}"
            )
    return exam_id, fingerprint


def _row_is_correct(row: dict[str, str], answer_key: dict[int, int]) -> bool:
    selected = row["selected_option"].strip()
    if not selected:
        return False
    return int(selected) == answer_key[int(row["answer_number"])]


def analyze_answers(
    rows: list[dict[str, str]],
    answer_key: dict[int, int],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_item: dict[int, list[dict[str, str]]] = defaultdict(list)
    by_participant: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_item[int(row["answer_number"])].append(row)
        by_participant[row["participant_id"].strip()].append(row)

    item_summary: list[dict[str, object]] = []
    for answer_number in sorted(by_item):
        item_rows = by_item[answer_number]
        n = len(item_rows)
        correct = sum(_row_is_correct(row, answer_key) for row in item_rows)
        omitted = sum(int(row["omitted"]) for row in item_rows)
        ambiguity = sum(int(row["ambiguity_flag"]) for row in item_rows)
        options = Counter(
            int(row["selected_option"])
            for row in item_rows
            if row["selected_option"].strip()
        )
        first = item_rows[0]
        summary: dict[str, object] = {
            "answer_number": answer_number,
            "section": first["section"].strip(),
            "correct_option": answer_key[answer_number],
            "n": n,
            "attempted": n - omitted,
            "correct": correct,
            "correct_rate": round(correct / n, 4),
            "omission_rate": round(omitted / n, 4),
            "ambiguity_reports": ambiguity,
        }
        for option in range(1, 11):
            summary[f"option_{option}_count"] = options.get(option, 0)
        item_summary.append(summary)

    participant_summary: list[dict[str, object]] = []
    for participant in sorted(by_participant):
        participant_rows = by_participant[participant]
        participant_summary.append(
            {
                "participant_id": participant,
                "answered_rows": len(participant_rows),
                "correct": sum(_row_is_correct(row, answer_key) for row in participant_rows),
                "omitted": sum(int(row["omitted"]) for row in participant_rows),
                "ambiguity_reports": sum(
                    int(row["ambiguity_flag"]) for row in participant_rows
                ),
            }
        )
    return item_summary, participant_summary


def analyze_sections(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["section"].strip()].append(row)

    order = ["Q1", "Q2", "Q3", "Q4", "Q5", "TOTAL"]
    summary: list[dict[str, object]] = []
    for section in order:
        section_rows = grouped.get(section)
        if not section_rows:
            continue
        elapsed = [int(row["elapsed_seconds"]) for row in section_rows]
        completed = [int(row["completed"]) for row in section_rows]
        difficulties = [
            int(row["perceived_difficulty_1_5"])
            for row in section_rows
            if row["perceived_difficulty_1_5"].strip()
        ]
        summary.append(
            {
                "section": section,
                "n": len(section_rows),
                "median_elapsed_seconds": float(median(elapsed)),
                "completion_rate": round(sum(completed) / len(completed), 4),
                "median_perceived_difficulty": (
                    float(median(difficulties)) if difficulties else ""
                ),
            }
        )
    return summary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty summary: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze_pilot(
    answer_csv: Path,
    section_csv: Path,
    release_record_path: Path,
    out_dir: Path,
) -> dict[str, object]:
    answer_rows = _read_csv(answer_csv)
    section_rows = _read_csv(section_csv)
    _require_columns(answer_csv, answer_rows, ANSWER_COLUMNS)
    _require_columns(section_csv, section_rows, SECTION_COLUMNS)
    answer_identity = validate_answer_rows(answer_rows)
    section_identity = validate_section_rows(section_rows)
    if answer_identity != section_identity:
        raise ValueError("answer and section files refer to different exam versions")

    exam_id, fingerprint = answer_identity
    answer_key = _load_released_answer_key(
        release_record_path,
        exam_id=exam_id,
        exam_fingerprint=fingerprint,
    )
    item_summary, participant_summary = analyze_answers(answer_rows, answer_key)
    section_summary = analyze_sections(section_rows)

    answer_participants = {row["participant_id"].strip() for row in answer_rows}
    section_participants = {row["participant_id"].strip() for row in section_rows}
    if answer_participants != section_participants:
        raise ValueError("answer and section files contain different participant sets")

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "item_summary.csv", item_summary)
    _write_csv(out_dir / "participant_summary.csv", participant_summary)
    _write_csv(out_dir / "section_summary.csv", section_summary)

    correct_counts = [int(row["correct"]) for row in participant_summary]
    summary = {
        "exam_id": exam_id,
        "exam_fingerprint": fingerprint,
        "participants": len(participant_summary),
        "median_correct_answers": float(median(correct_counts)),
        "max_correct_answers": max(correct_counts),
        "min_correct_answers": min(correct_counts),
    }
    (out_dir / "pilot_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze TABITO timed student-pilot CSV files")
    parser.add_argument("answers", type=Path, help="student_trial_answers.csv")
    parser.add_argument("sections", type=Path, help="student_trial_sections.csv")
    parser.add_argument(
        "--release-record",
        type=Path,
        required=True,
        help="approved exam release.json used to verify artifacts and answer_key.json",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("pilot_analysis"),
        help="directory for summary CSV/JSON files",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = analyze_pilot(
        args.answers,
        args.sections,
        args.release_record,
        args.out_dir,
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
