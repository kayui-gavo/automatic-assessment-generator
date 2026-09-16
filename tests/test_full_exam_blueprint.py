from tabito_itemgen.exam_models import ExamManifest, SECTION_SPECS, SectionRef


def test_full_exam_blueprint_is_200_points_80_minutes_50_answers():
    refs = [
        SectionRef(
            section=section,
            section_id=f"EXAM-{section}",
            expected_score=score,
            answer_start=start,
            answer_end=end,
        )
        for section, (score, start, end) in SECTION_SPECS.items()
    ]
    exam = ExamManifest(
        exam_id="EXAM",
        exam_family="main_2026",
        title_ja="Test",
        sections=refs,
    )
    assert exam.total_score == 200
    assert exam.duration_minutes == 80
    assert exam.answer_range == (1, 50)
    assert sum(ref.expected_score for ref in exam.sections) == 200
    assert [(ref.answer_start, ref.answer_end) for ref in exam.sections] == [
        (1, 6), (7, 12), (13, 20), (21, 36), (37, 50)
    ]
