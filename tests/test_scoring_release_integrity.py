from tabito_itemgen.exam_production import exam_release_readiness

from tests.artifact_factory import write_clean_artifacts
from tests.full_exam_factory import build_exam


def test_scoring_scheme_change_invalidates_artifact_gate(tmp_path) -> None:
    manifest, _ = build_exam(tmp_path, "main_2026")
    write_clean_artifacts(tmp_path, manifest.exam_id)

    scoring = tmp_path / "output" / manifest.exam_id / "scoring_scheme.json"
    scoring.write_text('{"tampered": true}\n', encoding="utf-8")

    readiness = exam_release_readiness(tmp_path, manifest.exam_id)
    artifact_gate = next(gate for gate in readiness.gates if gate.name == "artifact preflight")
    assert not artifact_gate.passed
    assert "scoring_scheme.json changed after preflight" in artifact_gate.detail
