from tests.full_exam_factory import q5


def _groups(section):
    return {
        task.question_no: sorted(slot.answer_number for slot in task.answer_slots)
        for task in section.tasks
    }


def test_q5_main_uses_14_slots_and_11_questions():
    section = q5("EXAM-Q5", "main_2026")
    assert len(section.tasks) == 11
    assert sorted(number for group in _groups(section).values() for number in group) == list(range(37, 51))
    assert _groups(section)[10] == [47, 48]
    assert _groups(section)[11] == [49, 50]


def test_q5_makeup_uses_14_slots_and_10_questions():
    section = q5("EXAM-Q5", "makeup_2026")
    assert len(section.tasks) == 10
    assert _groups(section)[4] == [40, 41]
    assert _groups(section)[8] == [45, 46]
    assert _groups(section)[9] == [47, 48]
    assert _groups(section)[10] == [49, 50]
