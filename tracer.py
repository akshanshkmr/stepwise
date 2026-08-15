"""Turn an UNINSTRUMENTED function into animation frames by watching its locals
line by line.

One tracer, two callers:
  - runner.js loads this file into Pyodide to animate the learner's own run
  - tools/record.py imports it to generate `steps` when authoring a problem
Keeping it in one file is the point: if the two drifted, a learner's run would
animate differently from the walkthrough it is being compared against.

ponytail: this infers intent from shape — the longest list of scalars is the
array, ints that index it are pointers, other scalars are the readout. It cannot
know algorithm-specific overlays like the bars view's water; an author who wants
those still calls Recorder.step by hand.
"""
import copy
import json
import sys
import traceback

MAX_FRAMES = 400
DEFAULT_BUDGET = 150_000


class Timeout(BaseException):
    """Not an Exception: a learner's broad `except Exception` must not eat it."""


def _scalar(v):
    return isinstance(v, (int, float, str)) and not isinstance(v, bool)


def as_cells(seq):
    return [c for c in seq] if isinstance(seq, str) else list(seq)


def _pick_array(local_vars, fallback):
    """The live array: the longest list of scalars in scope, else the argument.
    Choosing per frame means a solution that sorts a copy animates the copy."""
    best = None
    for v in local_vars.values():
        if isinstance(v, list) and v and all(_scalar(x) for x in v):
            if best is None or len(v) > len(best):
                best = v
    return list(best) if best is not None else list(fallback)


def frame_of(local_vars, fallback_array):
    array = _pick_array(local_vars, fallback_array)
    n = len(array)
    pointers, scalars = {}, {}
    for name, v in local_vars.items():
        if isinstance(v, list) or name.startswith("_"):
            continue
        if isinstance(v, bool):
            scalars[name] = v
        elif isinstance(v, int) and 0 <= v < n:
            pointers[name] = v
        elif _scalar(v):
            scalars[name] = v
    return {
        "array": array,
        "pointers": pointers,
        "vars": scalars,
        "highlight": sorted(set(pointers.values())),
        "caption": "",
    }


def caption_for(prev, cur):
    """Mechanical and honest: name what changed. It cannot say WHY, which is
    exactly why authored captions stay the teaching surface."""
    if prev is None:
        return "Your run starts here."
    moves = [f"{k}: {prev['pointers'][k]} to {v}"
             for k, v in cur["pointers"].items()
             if k in prev["pointers"] and prev["pointers"][k] != v]
    started = [f"{k} starts at {v}" for k, v in cur["pointers"].items()
               if k not in prev["pointers"]]
    changed = [f"{k} = {v}" for k, v in cur["vars"].items()
               if prev["vars"].get(k) != v]
    parts = moves + started + changed
    return "; ".join(parts) if parts else "The array changed."


def trace_call(fn, args, func_name, budget=DEFAULT_BUDGET):
    """Run fn(*args) under a line tracer. Returns
    {steps, result, error, truncated}. Never raises for a fault in fn.

    Arguments are deep-copied first: in-place solutions (Move Zeroes and every
    other two-pointer problem that rewrites its input) would otherwise mutate
    the caller's data and make a second trace of the same input disagree with
    the first."""
    args = copy.deepcopy(list(args))
    fallback = []
    for a in args:
        if isinstance(a, (list, str)):
            fallback = as_cells(a)
            break

    frames, left, prev_key = [], [budget], [None]

    def localtrace(frame, event, arg):
        if event != "line":
            return localtrace
        left[0] -= 1
        if left[0] < 0:
            raise Timeout()
        if len(frames) >= MAX_FRAMES:
            return localtrace
        try:
            f = frame_of(dict(frame.f_locals), fallback)
        except Exception:
            return localtrace
        key = json.dumps([f["array"], f["pointers"], f["vars"]],
                         sort_keys=True, default=str)
        if key != prev_key[0]:
            f["caption"] = caption_for(frames[-1] if frames else None, f)
            frames.append(f)
            prev_key[0] = key
        return localtrace

    def globaltrace(frame, event, arg):
        return localtrace if frame.f_code.co_name == func_name else None

    error = None
    previous = sys.gettrace()
    try:
        sys.settrace(globaltrace)
        result = fn(*args)
        sys.settrace(previous)
        try:
            result = json.loads(json.dumps(result))
        except TypeError:
            result = str(result)
    except Timeout:
        sys.settrace(previous)
        result, error = None, "timed out — check for a loop that never ends"
    except Exception:
        sys.settrace(previous)
        result, error = None, traceback.format_exc(limit=1).strip()

    return {"steps": frames, "result": result, "error": error,
            "truncated": len(frames) >= MAX_FRAMES}
