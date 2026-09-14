from tabito_itemgen.scoring import score_responses, scoring_scheme


def _key() -> dict[int, int]:
    return {number: 1 for number in range(1, 51)}


def test_scoring_schemes_cover_exactly_200_points() -> None:
    for family in ("main_2026", "makeup_2026"):
        scheme = scoring_scheme(family)
        assert sum(group.points for group in scheme.groups) == 200
        numbers = sorted(number for group in scheme.groups for number in group.answer_numbers)
        assert numbers == list(range(1, 51))


def test_perfect_response_scores_200() -> None:
    author = _key()
    for family in ("main_2026", "makeup_2026"):
        result = score_responses(family, author, author)
        assert result.earned == 200


def test_q2_ordering_is_all_or_nothing_and_order_sensitive() -> None:
    author = _key()
    author[9] = 2
    author[10] = 4
    response = dict(author)
    response[9], response[10] = 4, 2

    result = score_responses("main_2026", author, response)
    group = next(group for group in result.groups if group.group_id == "Q2-9-10")
    assert group.possible == 4
    assert group.earned == 0


def test_main_q4_linked_star_group_is_order_insensitive_but_all_or_nothing() -> None:
    author = _key()
    author[23] = 2
    author[24] = 5
    response = dict(author)
    response[23], response[24] = 5, 2

    result = score_responses("main_2026", author, response)
    group = next(group for group in result.groups if group.group_id == "Q4-23-24")
    assert group.possible == 5
    assert group.earned == 5

    response[24] = 7
    result = score_responses("main_2026", author, response)
    group = next(group for group in result.groups if group.group_id == "Q4-23-24")
    assert group.earned == 0


def test_main_q4_each_five_group_awards_partial_credit_by_selected_choice() -> None:
    author = _key()
    author[21] = 4
    author[22] = 8
    response = dict(author)
    response[21] = 4
    response[22] = 7

    result = score_responses("main_2026", author, response)
    group = next(group for group in result.groups if group.group_id == "Q4-21-22")
    assert group.possible == 10
    assert group.earned == 5


def test_makeup_q5_family_has_distinct_grouping() -> None:
    scheme = scoring_scheme("makeup_2026")
    by_id = {group.group_id: group for group in scheme.groups}
    assert by_id["Q5-40-41"].points == 5
    assert by_id["Q5-40-41"].award_mode == "all_or_nothing"
    assert by_id["Q5-45-46"].points == 10
    assert by_id["Q5-45-46"].award_mode == "per_choice"
