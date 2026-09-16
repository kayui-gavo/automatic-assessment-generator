import csv
import hashlib
import json

import pytest

from tabito_itemgen.pilot_analysis import analyze_pilot, validate_answer_rows
from tabito_itemgen.scoring import scoring_scheme

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


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _author_key() -> dict[int, int]:
    key = {number: 1 for number in range(1, 51)}
    for group in scoring_scheme("main_2026").groups:
        if group.comparison_mode == "set" and len(group.answer_numbers) > 1:
            for index, number in enumerate(group.answer_numbers, start=1):
                key[number] = index
    return key


def _answer_rows():
    key = _author_key()
    rows = []
    for participant in ("P001", "P002"):
        for answer_number in range(1, 51):
            selected = str(key[answer_number])
            omitted = "0"
            ambiguity = "0"
            if participant == "P002" and answer_number == 1:
                selected = "2" if key[answer_number] != 2 else "3"
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


def _write_released_artifacts(tmp_path):
    approved = tmp_path / "approved" / "EXAM-001"
    artifact_dir = approved / "artifacts"
    artifact_dir.mkdir(parents=True)

    (approved / "exam.json").write_text(
        json.dumps(
            {
                "exam_id": "EXAM-001",
                "exam_family": "main_2026",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    checks = []
    for name in ("student", "teacher", "answer_sheet"):
        pdf = artifact_dir / f"{name}.pdf"
        pdf.write_bytes(f"%PDF-1.4\n{name}\n".encode())
        checks.append({"name": name, "pdf_sha256": _sha256(pdf)})

    answer_key = artifact_dir / "answer_key.json"
    answer_key.write_text(
        json.dumps({str(number): option for number, option in _author_key().items()}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    scoring = artifact_dir / "scoring_scheme.json"
    scoring.write_text(
        json.dumps(
            scoring_scheme("main_2026").model_dump(mode="json"),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = artifact_dir / "artifact_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "exam_id": "EXAM-001",
                "exam_fingerprint": "fingerprint-001",
                "checks": checks,
                "extra_files": {
                    "answer_key.json": _sha256(answer_key),
                    "scoring_scheme.json": _sha256(scoring),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    release = approved / "release.json"
    release.write_text(
        json.dumps(
            {
                "exam_id": "EXAM-001",
                "exam_fingerprint": "fingerprint-001",
                "artifact_manifest_sha256": _sha256(manifest),
                "gates": [{"name": "release", "passed": True, "detail": "pass"}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return release, answer_key, scoring, artifact_dir / "student.pdf"


def test_pilot_analysis_emits_item_participant_section_and_exam_summaries(tmp_path):
    answers = tmp_path / "answers.csv"
    sections = tmp_path / "sections.csv"
    out_dir = tmp_path / "analysis"
    release_record, _, _, _ = _write_released_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())

    summary = analyze_pilot(answers, sections, release_record, out_dir)

    assert summary == {
        "exam_id": "EXAM-001",
        "exam_fingerprint": "fingerprint-001",
        "exam_family": "main_2026",
        "scoring_version": "R8-2026-scoring-v1",
        "participants": 2,
        "median_correct_answers": 49.0,
        "max_correct_answers": 50,
        "min_correct_answers": 48,
        "median_score_200": 195.5,
        "max_score_200": 200,
        "min_score_200": 191,
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

    with (out_dir / "participant_summary.csv").open(encoding="utf-8", newline="") as handle:
        participants = list(csv.DictReader(handle))
    assert participants[0]["correct"] == "50"
    assert participants[0]["score_200"] == "200"
    assert participants[1]["correct"] == "48"
    assert participants[1]["score_200"] == "191"

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
    release_record, answer_key, _, _ = _write_released_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())
    answer_key.write_text('{"1": 2}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="hash does not match artifact manifest"):
        analyze_pilot(answers, sections, release_record, tmp_path / "analysis")


def test_pilot_analysis_rejects_tampered_scoring_scheme(tmp_path):
    answers = tmp_path / "answers.csv"
    sections = tmp_path / "sections.csv"
    release_record, _, scoring, _ = _write_released_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())
    scoring.write_text('{"family": "makeup_2026"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="scoring_scheme.json hash does not match"):
        analyze_pilot(answers, sections, release_record, tmp_path / "analysis")


def test_pilot_analysis_rejects_wrong_family_scoring_scheme_even_when_rehashed(tmp_path):
    answers = tmp_path / "answers.csv"
    sections = tmp_path / "sections.csv"
    release_record, _, scoring, _ = _write_released_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())

    scoring.write_text(
        json.dumps(scoring_scheme("makeup_2026").model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    artifact_manifest = release_record.parent / "artifacts" / "artifact_manifest.json"
    manifest = json.loads(artifact_manifest.read_text(encoding="utf-8"))
    manifest["extra_files"]["scoring_scheme.json"] = _sha256(scoring)
    artifact_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    release = json.loads(release_record.read_text(encoding="utf-8"))
    release["artifact_manifest_sha256"] = _sha256(artifact_manifest)
    release_record.write_text(json.dumps(release, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="scoring family does not match approved exam family"):
        analyze_pilot(answers, sections, release_record, tmp_path / "analysis")


def test_pilot_analysis_rejects_tampered_student_pdf(tmp_path):
    answers = tmp_path / "answers.csv"
    sections = tmp_path / "sections.csv"
    release_record, _, _, student_pdf = _write_released_artifacts(tmp_path)
    _write_csv(answers, ANSWER_FIELDS, _answer_rows())
    _write_csv(sections, SECTION_FIELDS, _section_rows())
    student_pdf.write_bytes(b"%PDF-1.4\ntampered\n")

    with pytest.raises(ValueError, match="student.pdf failed integrity verification"):
        analyze_pilot(answers, sections, release_record, tmp_path / "analysis")
