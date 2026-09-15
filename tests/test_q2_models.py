from tabito_itemgen.exam_models import Q2OrderingTask

from tests.full_exam_factory import q2


def test_q2_uses_7_through_12_and_real_ordering_schema():
    section = q2("EXAM-Q2")
    numbers = []
    ordering = []
    for task in section.tasks:
        if isinstance(task, Q2OrderingTask):
            ordering.append(task)
            numbers.extend(slot.answer_number for slot in task.answer_slots)
        else:
            numbers.append(task.answer_slot.answer_number)
    assert sorted(numbers) == list(range(7, 13))
    assert len(ordering) == 2
    assert all(len(task.token_pool) == 8 for task in ordering)
    assert all(len(task.correct_sequence) == 4 for task in ordering)
    assert section.tasks[1].selection_rule == "inappropriate"
