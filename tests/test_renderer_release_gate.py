from tabito_itemgen.artifact_preflight import ArtifactManifest
from tabito_itemgen.exam_production import exam_release_readiness
from tabito_itemgen.io import dump_json, load_json

from tests.artifact_factory import write_clean_artifacts
from tests.full_exam_factory import build_exam


def test_stale_renderer_artifact_is_rejected_by_release_gate(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    artifact_path = write_clean_artifacts(tmp_path, manifest.exam_id)
    raw = load_json(artifact_path)
    stale = "renderer-sha256:" + "0" * 64
    raw["renderer_revision"] = stale
    dump_json(artifact_path, raw)

    # Historical evidence remains parseable and preserves the exact renderer
    # provenance that produced it. Freshness is a release-gate concern.
    historical = ArtifactManifest.model_validate(load_json(artifact_path))
    assert historical.renderer_revision == stale
    assert historical.source_renderer_revision is None

    readiness = exam_release_readiness(tmp_path, manifest.exam_id)
    artifact_gate = next(
        gate for gate in readiness.gates if gate.name == "artifact preflight"
    )
    assert not artifact_gate.passed
    assert "stale for the current renderer" in artifact_gate.detail
