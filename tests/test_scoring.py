import pytest

from tabito_itemgen.scoring import SCORING_VERSION, score_responses, scoring_scheme


def _key() -> dict[int, int]:
    return {number: 1 for number in range(1, 51)}


def _valid_key_for(family: str) -> dict[int, int]:
    """Build a synthetic author key that respects unordered-group uniqueness."""

    key = _key()
    scheme = scoring_scheme(family)
    for group in scheme.groups:
        if group.comparison_mode == "set" and len(group.answer_numbers) > 1:
            for index, number in enumerate(group.answer_numbers, start=1):
                key[number] = index
    return key


def _group(result, group_id: str):
    return next(group for group in result.groups if group.group_id == group_id)


def test_scoring_schemes_cover_exactly_200_points_and_official_section_totals() -> None:
    expected_sections = {"Q1": 24, "Q2": 16, "Q3": 40, "Q4": 60, "Q5": 60}
    for family in ("main_2026", "makeup_2026"):
        scheme = scoring_scheme(family)
        assert scheme.scoring_version == SCORING_VERSION
        assert sum(group.points for group in scheme.groups) == 200
        numbers = sorted(number for group in scheme.groups for number in group.answer_numbers)
        assert numbers == list(range(1, 51))
        actual_sections = {
            section: sum(group.points for group in scheme.groups if group.section == section)
            for section in expected_sections
        }
        assert actual_sections == expected_sections


def test_perfect_response_scores_200() -> None:
    for family in ("main_2026", "makeup_2026"):
        author = _valid_key_for(family)
        result = score_responses(family, author, author)
        assert result.scoring_version == SCORING_VERSION
        assert result.earned == 200
        assert result.possible == 200


def test_q2_ordering_is_all_or_nothing_and_order_sensitive() -> None:
    author = _valid_key_for("main_2026")
    author[9] = 2
    author[10] = 4
    response = dict(author)
    response[9], response[10] = 4, 2

    result = score_responses("main_2026", author, response)
    group = _group(result, "Q2-9-10")
    assert group.possible == 4
    assert group.earned == 0


def test_main_starred_nonhyphen_pair_is_order_sensitive() -> None:
    author = _valid_key_for("main_2026")
    author[23] = 2
    author[24] = 5
    response = dict(author)
    response[23], response[24] = 5, 2

    result = score_responses("main_2026", author, response)
    group = _group(result, "Q4-23-24")
    assert group.possible == 5
    assert group.earned == 0

    response[23], response[24] = 2, 5
    result = score_responses("main_2026", author, response)
    assert _group(result, "Q4-23-24").earned == 5


@pytest.mark.parametrize(
    ("group_id", "numbers"),
    [
        ("Q4-31-32", (31, 32)),
        ("Q4-35-36", (35, 36)),
        ("Q5-38-39", (38, 39)),
    ],
)
def test_main_other_starred_nonhyphen_pairs_are_order_sensitive(group_id, numbers) -> None:
    author = _valid_key_for("main_2026")
    first, second = numbers
    author[first], author[second] = 2, 5
    response = dict(author)
    response[first], response[second] = 5, 2

    result = score_responses("main_2026", author, response)
    assert _group(result, group_id).earned == 0


def test_main_hyphenated_star_group_ignores_order_but_requires_both() -> None:
    author = _valid_key_for("main_2026")
    author[27], author[28] = 3, 4
    response = dict(author)
    response[27], response[28] = 4, 3

    result = score_responses("main_2026", author, response)
    assert _group(result, "Q4-27-28").earned == 5

    response[28] = 7
    result = score_responses("main_2026", author, response)
    assert _group(result, "Q4-27-28").earned == 0


def test_main_each_five_hyphen_group_awards_partial_credit_by_selected_choice() -> None:
    author = _valid_key_for("main_2026")
    author[21], author[22] = 4, 8
    response = dict(author)
    response[21] = 4
    response[22] = 7

    result = score_responses("main_2026", author, response)
    group = _group(result, "Q4-21-22")
    assert group.possible == 10
    assert group.earned == 5


def test_makeup_q5_family_has_distinct_grouping_and_order_semantics() -> None:
    scheme = scoring_scheme("makeup_2026")
    by_id = {group.group_id: group for group in scheme.groups}
    assert by_id["Q5-40-41"].points == 5
    assert by_id["Q5-40-41"].award_mode == "all_or_nothing"
    assert by_id["Q5-40-41"].comparison_mode == "set"
    assert by_id["Q5-45-46"].points == 10
    assert by_id["Q5-45-46"].award_mode == "per_choice"
    assert by_id["Q5-47-48"].award_mode == "all_or_nothing"
    assert by_id["Q5-47-48"].comparison_mode == "ordered"


def test_makeup_q5_47_48_swapped_answers_receive_no_points() -> None:
    author = _valid_key_for("makeup_2026")
    author[47], author[48] = 1, 3
    response = dict(author)
    response[47], response[48] = 3, 1

    result = score_responses("makeup_2026", author, response)
    assert _group(result, "Q5-47-48").earned == 0


def test_scoring_rejects_incomplete_author_key() -> None:
    author = _valid_key_for("main_2026")
    author.pop(50)
    with pytest.raises(ValueError, match="author key must contain answer numbers 1..50 exactly"):
        score_responses("main_2026", author, {})


def test_scoring_rejects_duplicate_author_choices_in_unordered_group() -> None:
    author = _valid_key_for("main_2026")
    author[21] = 4
    author[22] = 4
    with pytest.raises(ValueError, match="duplicate choices in set group Q4-21-22"):
        score_responses("main_2026", author, {})
