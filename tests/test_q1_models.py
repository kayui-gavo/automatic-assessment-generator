from tests.full_exam_factory import q1


def test_q1_uses_answers_1_through_6_and_native_task_types():
    section = q1("EXAM-Q1")
    numbers = sorted(task.answer_slot.answer_number for task in section.tasks)
    assert numbers == list(range(1, 7))
    assert [task.subsection for task in section.tasks] == ["A", "B", "C", "C", "D", "D"]
    assert section.tasks[0].target == "initial"
    assert section.tasks[1].target == "final"
