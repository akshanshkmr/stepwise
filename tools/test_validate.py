import copy
import pytest
from validate import validate_problem

GOOD = {
    "id": "two-sum-ii",
    "title": "Two Sum II",
    "statement": "Find two numbers that add to target.",
    "examples": [{"input": "numbers = [2,7,11,15], target = 9", "output": "[1,2]"}],
    "signature": "def two_sum(numbers, target):",
    "func": "two_sum",
    "pattern": "Two Pointers",
    "difficulty": "Medium",
    "order": 1,
    "view": "cells",
    "steps": [
        {"array": [2, 7, 11, 15], "pointers": {"l": 0, "r": 3}, "vars": {"sum": 17},
         "highlight": [0, 3], "caption": "start"},
        {"array": [2, 7, 11, 15], "pointers": {"l": 0, "r": 2}, "vars": {"sum": 13},
         "highlight": [0, 2], "caption": "shrink"},
    ],
    "checkpoints": [
        {"afterStep": 0, "question": "Which pointer moves?", "options": ["left", "right"],
         "answer": "right", "why": "The sum is too large."}
    ],
    "hints": ["What does sortedness rule out?", "A pair to the right of r is always worse."],
    "tests": [{"args": [[2, 7, 11, 15], 9], "expect": [1, 2]}],
}


def test_valid_problem_has_no_errors():
    assert validate_problem(copy.deepcopy(GOOD)) == []


def test_missing_key_reported():
    p = copy.deepcopy(GOOD)
    del p["hints"]
    assert any("hints" in e for e in validate_problem(p))


def test_checkpoint_out_of_range_reported():
    p = copy.deepcopy(GOOD)
    p["checkpoints"][0]["afterStep"] = 9
    assert any("afterStep" in e for e in validate_problem(p))


def test_answer_not_in_options_reported():
    p = copy.deepcopy(GOOD)
    p["checkpoints"][0]["answer"] = "middle"
    assert any("answer" in e for e in validate_problem(p))


def test_empty_steps_reported():
    p = copy.deepcopy(GOOD)
    p["steps"] = []
    assert any("steps" in e for e in validate_problem(p))


def test_empty_tests_reported():
    p = copy.deepcopy(GOOD)
    p["tests"] = []
    assert any("tests" in e for e in validate_problem(p))


@pytest.mark.parametrize("bad", [
    "use `for i in range(n)`",
    "```python\nx=1\n```",
    "def two_sum(a, b):",
    "compare numbers[l] with the target",
    "return [l + 1, r + 1] once they match",
    "set r -= 1 to shrink the window",
])
def test_code_in_hint_reported(bad):
    p = copy.deepcopy(GOOD)
    p["hints"] = [bad]
    assert any("hint" in e for e in validate_problem(p))


def test_highlight_index_out_of_array_reported():
    p = copy.deepcopy(GOOD)
    p["steps"][0]["highlight"] = [99]
    assert any("highlight" in e for e in validate_problem(p))


def test_missing_pointers_key_reported():
    p = copy.deepcopy(GOOD)
    del p["steps"][0]["pointers"]
    assert any("pointers" in e for e in validate_problem(p))


@pytest.mark.parametrize("bad", [9, -1, "0", True])
def test_pointer_outside_array_reported(bad):
    p = copy.deepcopy(GOOD)
    p["steps"][0]["pointers"]["l"] = bad
    assert any("pointer" in e for e in validate_problem(p))


def test_empty_checkpoints_reported():
    p = copy.deepcopy(GOOD)
    p["checkpoints"] = []
    assert any("checkpoints" in e for e in validate_problem(p))


# --- view registry -------------------------------------------------------

def test_unknown_view_reported():
    p = copy.deepcopy(GOOD)
    p["view"] = "hologram"
    assert any("unknown view" in e for e in validate_problem(p))


def test_bars_view_accepts_water_and_region():
    p = copy.deepcopy(GOOD)
    p["view"] = "bars"
    for step in p["steps"]:
        step["water"] = [0] * len(step["array"])
        step["region"] = {"from": 0, "to": 3, "level": 2}
    assert validate_problem(p) == []


def test_cells_view_rejects_water_it_does_not_declare():
    p = copy.deepcopy(GOOD)
    p["steps"][0]["water"] = [0, 0, 0, 0]
    assert any("does not" in e for e in validate_problem(p))


def test_water_length_must_match_array():
    p = copy.deepcopy(GOOD)
    p["view"] = "bars"
    p["steps"][0]["water"] = [0, 0]
    assert any("water has 2 entries" in e for e in validate_problem(p))


def test_region_edge_outside_array_reported():
    p = copy.deepcopy(GOOD)
    p["view"] = "bars"
    p["steps"][0]["region"] = {"from": 0, "to": 99, "level": 1}
    assert any("region to=99" in e for e in validate_problem(p))


def test_unknown_pattern_reported():
    p = copy.deepcopy(GOOD)
    p["pattern"] = "Vibes"
    assert any("unknown pattern" in e for e in validate_problem(p))


@pytest.mark.parametrize("fine", [
    "Keep taking the most recent waiting day for as long as today is warmer.",
    "Every partner for it is at least as big as the one you just tried.",
    "Return the two indices, not the values.",
    "Move exactly one marker inward each round while the markers have not met.",
])
def test_prose_that_merely_uses_code_words_is_allowed(fine):
    p = copy.deepcopy(GOOD)
    p["hints"] = [fine]
    assert validate_problem(p) == [], f"rejected legitimate prose: {fine}"


def test_unknown_difficulty_reported():
    p = copy.deepcopy(GOOD)
    p["difficulty"] = "Spicy"
    assert any("difficulty" in e for e in validate_problem(p))
