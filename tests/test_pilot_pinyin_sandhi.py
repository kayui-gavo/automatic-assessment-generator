from pathlib import Path

from tabito_itemgen.section_io import load_section

ROOT = Path(__file__).resolve().parents[1]
Q3 = ROOT / "pilots" / "exam_001" / "q3_v5.json"


def test_pilot_q3_applies_bu_sandhi_only_before_fourth_tone():
    section = load_section(Q3)
    tasks = {task.task_id: task for task in section.tasks}

    # 不但 / 不够: the following syllable is fourth tone, so 不 surfaces as bú.
    assert "búdàn" in tasks["Q3-A2"].options[0]
    assert "búgòu" in tasks["Q3-B2"].source_text

    # 不能: néng is second tone, so 不 remains fourth tone. Guard against an
    # over-broad replacement that turns every 不 into bú.
    assert "bùnéng" in tasks["Q3-A3"].options[2]
    assert "bùnéng" in tasks["Q3-B2"].source_text
    assert "búnéng" not in tasks["Q3-B2"].source_text
