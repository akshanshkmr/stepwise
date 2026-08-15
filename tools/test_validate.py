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
    "steps": [
        {"array": [2, 7, 11, 15], "vars": {"l": 0, "r": 3}, "highlight": [0, 3], "caption": "start"},
        {"array": [2, 7, 11, 15], "vars": {"l": 0, "r": 2}, "highlight": [0, 2], "caption": "shrink"},
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


@pytest.mark.parametrize("bad", ["use `for i in range(n)`", "```python\nx=1\n```", "def two_sum(a, b):"])
def test_code_in_hint_reported(bad):
    p = copy.deepcopy(GOOD)
    p["hints"] = [bad]
    assert any("hint" in e for e in validate_problem(p))


def test_highlight_index_out_of_array_reported():
    p = copy.deepcopy(GOOD)
    p["steps"][0]["highlight"] = [99]
    assert any("highlight" in e for e in validate_problem(p))
