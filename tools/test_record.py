import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from record import AUTO, CAPTIONS, SOLUTIONS, Recorder, auto_trace
from validate import validate_problem

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_recorder_captures_frames():
    rec = Recorder()
    rec.step([1, 2, 3], {"l": 0}, "first", highlight=[0], vars={"sum": 4})
    rec.step([1, 2, 3], {"l": 1}, "second", highlight=[1])
    assert len(rec.steps) == 2
    assert rec.steps[0] == {"array": [1, 2, 3], "pointers": {"l": 0}, "vars": {"sum": 4},
                            "highlight": [0], "caption": "first"}
    assert rec.steps[1]["vars"] == {}


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
            assert all(0 <= v < n for v in step["pointers"].values()), f"{pid} step {i} bad pointer"


def test_every_hand_written_step_carries_the_scalars_its_captions_discuss():
    """Hand-written traces show a readout: pointers alone are not the story.
    Auto-traced problems are exempt — a solution whose only state is two
    indices has nothing to put there, and inventing one would be a lie."""
    for pid, trace_fn in SOLUTIONS.items():
        rec = Recorder()
        trace_fn(rec)
        for i, step in enumerate(rec.steps):
            assert step["vars"], f"{pid} step {i} has an empty readout"


def test_auto_traced_solutions_produce_valid_frames():
    for pid, (fn, args) in AUTO.items():
        steps = auto_trace(fn, args)
        assert steps, f"{pid} produced no frames"
        for i, step in enumerate(steps):
            n = len(step["array"])
            assert step["caption"], f"{pid} frame {i} has an empty caption"
            assert all(0 <= v < n for v in step["pointers"].values()), \
                f"{pid} frame {i} has a pointer outside the array"


def test_caption_overrides_point_at_real_frames():
    """An override index past the end of the trace would silently teach nothing."""
    for pid, overrides in CAPTIONS.items():
        fn, args = AUTO[pid]
        count = len(auto_trace(fn, args))
        for i in overrides:
            assert 0 <= i < count, f"{pid} caption {i} is outside its {count} frames"


def test_regenerated_problem_files_are_valid():
    for pid in list(SOLUTIONS) + list(AUTO):
        path = ROOT / "problems" / f"{pid}.json"
        assert path.exists(), f"missing {path}"
        assert validate_problem(json.loads(path.read_text())) == []
