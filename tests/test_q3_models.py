from tests.full_exam_factory import q3


def test_q3_uses_13_through_20_with_bidirectional_translation():
    section = q3("EXAM-Q3")
    ordered = sorted(section.tasks, key=lambda task: task.answer_slot.answer_number)
    assert [task.answer_slot.answer_number for task in ordered] == list(range(13, 21))
    assert all(task.direction == "ja_to_zh" for task in ordered[:4])
    assert all(task.direction == "zh_to_ja" for task in ordered[4:])
    assert all(task.distractor_error_types for task in ordered)
