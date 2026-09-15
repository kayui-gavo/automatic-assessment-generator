import csv
import hashlib
import json

import pytest

from tabito_itemgen.pilot_analysis import analyze_pilot, validate_answer_rows

ANSWER_FIELDS = [
    "participant_id",
    "exam_id",
    "exam_fingerprint",
    "answer_number",
    "section",
    "selected_option",
    "omitted",
    "ambiguity_flag",
    "note",
]
SECTION_FIELDS = [
    "participant_id",
    "exam_id",
    "exam_fingerprint",
    "section",
    "elapsed_seconds",
    "completed",
    "perceived_difficulty_1_5",
    "note",
]


def _section_for(answer_number: int) -> str:
    if answer_number <= 6:
        return "Q1"
    if answer_number <= 12:
        return "Q2"
    if answer_number <= 20:
        return "Q3"
    if answer_number <= 36:
        return "Q4"
    return "Q5"


def _answer_rows():
    rows = []
    for participant in ("P001", "P002"):
        for answer_number in range(1, 51):
            selected = "1"
            omitted = "0"
            ambiguity = "0"
            if participant == "P002" and answer_number == 1:
                selected = "2"
            if participant == "P002" and answer_number == 2:
                ambiguity = "1"
            if participant == "P002" and answer_number == 50:
                selected = ""
                omitted = "1"
            rows.append(
                {
                    "participant_id": participant,
                    "exam_id": "EXAM-001",
                    "exam_fingerprint": "fingerprint-001",
                    "answer_number": str(answer_number),
                    "section": _section_for(answer_number),
                    "selected_option": selected,
                    "omitted": omitted,
                    "ambiguity_flag": ambiguity,
                    "note": "",
                }
            )
    return rows


def _section_rows():
    rows = []
    elapsed = {
        "P001": {"Q1": 300, "Q2": 360, "Q3": 720, "Q4": 1260, "Q5": 1800},
        "P002": {"Q1": 420, "Q2": 420, "Q3": 780, "Q4": 1320, "Q5": 1680},
    }
    for participant, timings in elapsed.items():
        for section, seconds in timings.items():
            rows.append(
                {
                    "participant_id": participant,
                    "exam_id": "EXAM-001",
                    "exam_fingerprint": "fingerprint-001",
                    "section": section,
                    "elapsed_seconds": str(seconds),
                    "completed": "1",
                    "perceived_difficulty_1_5": "3",
                    "note": "",
                }
            )
    return rows


def _write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_bound_artifacts(tmp_path):
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    answer_key = artifact_dir / "answer_key.json"
    answer_key.write_text(
        json.dumps({str(number): 1 for number in range(1, 51)}, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(answer_key.read_bytes()).hexdigest()
    manifest = artifact_dir / "artifact_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "exam_id": "EXAM-001",
                "exam_fingerprint": "fingerprint-001",
                "extra_files": {"answer_key.json": digest},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest, answer_key


def test_pilot_analysis_emits_item_participant_section_and_exam_summaries(tmp_path):
    answers = tmp_path / "answers.csv"
    sections = tmp_path / "sections.csv"
    out_dir = tmp_path / "analysis"
    artifact_manifest, _ = _write_bound_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())

    summary = analyze_pilot(answers, sections, artifact_manifest, out_dir)

    assert summary == {
        "exam_id": "EXAM-001",
        "exam_fingerprint": "fingerprint-001",
        "participants": 2,
        "median_correct_answers": 49.0,
        "max_correct_answers": 50,
        "min_correct_answers": 48,
    }

    with (out_dir / "item_summary.csv").open(encoding="utf-8", newline="") as handle:
        items = list(csv.DictReader(handle))
    assert len(items) == 50
    assert items[0]["answer_number"] == "1"
    assert items[0]["correct_option"] == "1"
    assert items[0]["correct_rate"] == "0.5"
    assert items[0]["option_1_count"] == "1"
    assert items[0]["option_2_count"] == "1"
    assert items[-1]["omission_rate"] == "0.5"

    with (out_dir / "section_summary.csv").open(encoding="utf-8", newline="") as handle:
        section_summary = list(csv.DictReader(handle))
    q1 = next(row for row in section_summary if row["section"] == "Q1")
    assert q1["median_elapsed_seconds"] == "360.0"
    assert q1["completion_rate"] == "1.0"

    saved = json.loads((out_dir / "pilot_summary.json").read_text(encoding="utf-8"))
    assert saved == summary


def test_answer_validation_rejects_missing_answer_rows():
    rows = _answer_rows()
    rows.pop()
    with pytest.raises(ValueError, match="expected answer rows 1..50"):
        validate_answer_rows(rows)


def test_pilot_analysis_rejects_tampered_answer_key(tmp_path):
    answers = tmp_path / "answers.csv"
    sections = tmp_path / "sections.csv"
    artifact_manifest, answer_key = _write_bound_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())
    answer_key.write_text('{"1": 2}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="hash does not match artifact manifest"):
        analyze_pilot(answers, sections, artifact_manifest, tmp_path / "analysis")
