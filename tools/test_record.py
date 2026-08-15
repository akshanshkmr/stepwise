import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from record import SOLUTIONS, Recorder
from validate import validate_problem

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_recorder_captures_frames():
    rec = Recorder()
    rec.step([1, 2, 3], {"l": 0}, "first", highlight=[0])
    rec.step([1, 2, 3], {"l": 1}, "second", highlight=[1])
    assert len(rec.steps) == 2
    assert rec.steps[0] == {"array": [1, 2, 3], "vars": {"l": 0},
                            "highlight": [0], "caption": "first"}


def test_recorder_copies_array_so_later_mutation_does_not_leak():
    arr = [1, 2, 3]
    rec = Recorder()
    rec.step(arr, {"l": 0}, "before", highlight=[0])
    arr[0] = 99
    assert rec.steps[0]["array"] == [1, 2, 3]


def test_every_solution_produces_a_valid_trace():
    for pid, trace_fn in SOLUTIONS.items():
        rec = Recorder()
        trace_fn(rec)
        assert rec.steps, f"{pid} recorded no steps"
        for i, step in enumerate(rec.steps):
            n = len(step["array"])
            assert all(0 <= h < n for h in step["highlight"]), f"{pid} step {i} bad highlight"
            assert step["caption"], f"{pid} step {i} has empty caption"


def test_regenerated_problem_files_are_valid():
    for pid in SOLUTIONS:
        path = ROOT / "problems" / f"{pid}.json"
        assert path.exists(), f"missing {path}"
        assert validate_problem(json.loads(path.read_text())) == []
