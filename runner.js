const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const LINE_BUDGET = 2_000_000;
// Tracing does real work per line, so the same budget would take minutes
// and freeze the tab. A correct solution needs a few thousand lines at most.
const TRACE_BUDGET = 150_000;

let pyodidePromise = null;

export function ready(onProgress) {
  if (pyodidePromise) return pyodidePromise;
  pyodidePromise = (async () => {
    onProgress?.("Downloading Python (about 10 MB, first time only)…");
    const { loadPyodide } = await import(`${PYODIDE_URL}pyodide.mjs`);
    const py = await loadPyodide({ indexURL: PYODIDE_URL });
    py.runPython(HARNESS);
    onProgress?.("Python ready.");
    return py;
  })().catch((err) => {
    pyodidePromise = null; // let the user retry
    throw new Error(`Could not load Python: ${err.message}`);
  });
  return pyodidePromise;
}

// ponytail: a line-count trace budget, not real preemption. Pyodide runs on the
// main thread so nothing can interrupt it; if this ever needs to be responsive
// during execution, move the whole runner into a web worker.
const HARNESS = `
import json, sys, traceback

class _Timeout(BaseException):
    pass


# --- automatic tracer ----------------------------------------------------
# Turns an UNINSTRUMENTED function into animation frames by watching its
# locals line by line. The learner writes ordinary Python; nothing is
# injected into their code.
#
# ponytail: this infers intent from shape — the longest list of scalars is
# the array, ints that index it are pointers, other scalars are the readout.
# It cannot know algorithm-specific overlays like the bars view's water.
# Frames come out mechanical on purpose: the recorder's hand-written captions
# stay the teaching surface, this one just shows what your code did.

_MAX_FRAMES = 400


def _scalar(v):
    return isinstance(v, (int, float, str, bool)) and not isinstance(v, bool)


def _as_cells(seq):
    return [c for c in seq] if isinstance(seq, str) else list(seq)


def _pick_array(local_vars, fallback):
    """The live array: the longest list of scalars in scope, else the argument.
    Picking it per frame means a solution that sorts a copy animates the copy."""
    best = None
    for v in local_vars.values():
        if isinstance(v, list) and v and all(_scalar(x) for x in v):
            if best is None or len(v) > len(best):
                best = v
    return list(best) if best is not None else fallback


def _frame_of(local_vars, fallback_array):
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


def _caption(prev, cur):
    """Mechanical, honest: name what actually changed between two frames."""
    if prev is None:
        return "Your run starts here."
    moves = [f"{k}: {prev['pointers'][k]} to {v}"
             for k, v in cur["pointers"].items()
             if k in prev["pointers"] and prev["pointers"][k] != v]
    new_ptr = [f"{k} starts at {v}" for k, v in cur["pointers"].items()
               if k not in prev["pointers"]]
    changed = [f"{k} = {v}" for k, v in cur["vars"].items()
               if prev["vars"].get(k) != v]
    parts = moves + new_ptr + changed
    return "; ".join(parts) if parts else "The array changed."


def _trace_run(source, func_name, args_json):
    args = json.loads(args_json)
    ns = {}
    try:
        exec(source, ns)
    except Exception:
        return json.dumps({"error": traceback.format_exc(limit=0).strip(), "steps": []})
    fn = ns.get(func_name)
    if not callable(fn):
        return json.dumps({
            "error": f"No function named {func_name} was defined.", "steps": []})

    fallback = []
    for a in args:
        if isinstance(a, (list, str)):
            fallback = _as_cells(a)
            break

    frames, budget, prev_key = [], [${TRACE_BUDGET}], [None]

    def localtrace(frame, event, arg):
        if event != "line":
            return localtrace
        budget[0] -= 1
        if budget[0] < 0:
            raise _Timeout()
        if len(frames) >= _MAX_FRAMES:
            return localtrace
        try:
            f = _frame_of(dict(frame.f_locals), fallback)
        except Exception:
            return localtrace
        key = json.dumps([f["array"], f["pointers"], f["vars"]], sort_keys=True,
                         default=str)
        if key != prev_key[0]:
            f["caption"] = _caption(frames[-1] if frames else None, f)
            frames.append(f)
            prev_key[0] = key
        return localtrace

    def globaltrace(frame, event, arg):
        return localtrace if frame.f_code.co_name == func_name else None

    error = None
    try:
        sys.settrace(globaltrace)
        result = fn(*[_copy(a) for a in args])
        sys.settrace(None)
        try:
            result = json.loads(json.dumps(result))
        except TypeError:
            result = str(result)
    except _Timeout:
        sys.settrace(None)
        result, error = None, "timed out — check for a loop that never ends"
    except Exception:
        sys.settrace(None)
        result, error = None, traceback.format_exc(limit=1).strip()

    truncated = len(frames) >= _MAX_FRAMES
    return json.dumps({"steps": frames, "result": result, "error": error,
                       "truncated": truncated})

def _run_tests(source, func_name, tests_json):
    tests = json.loads(tests_json)
    ns = {}
    try:
        exec(source, ns)
    except Exception:
        msg = traceback.format_exc(limit=0).strip()
        return json.dumps([{"args": t["args"], "expect": t["expect"], "actual": None,
                            "pass": False, "error": msg} for t in tests])
    fn = ns.get(func_name)
    if not callable(fn):
        msg = f"No function named {func_name} was defined. Your solution must define {func_name}."
        return json.dumps([{"args": t["args"], "expect": t["expect"], "actual": None,
                            "pass": False, "error": msg} for t in tests])

    results = []
    for t in tests:
        budget = [${LINE_BUDGET}]

        def _trace(frame, event, arg, budget=budget):
            if event == "line":
                budget[0] -= 1
                if budget[0] < 0:
                    raise _Timeout()
            return _trace

        try:
            sys.settrace(_trace)
            actual = fn(*[_copy(a) for a in t["args"]])
            sys.settrace(None)
            try:
                # Round-trip so a tuple compares equal to the list in "expect".
                actual = json.loads(json.dumps(actual))
            except TypeError as e:
                results.append({"args": t["args"], "expect": t["expect"], "actual": None,
                                "pass": False, "error": f"TypeError: {e}"})
                continue
            ok = actual == t["expect"]
            results.append({"args": t["args"], "expect": t["expect"],
                            "actual": actual, "pass": ok, "error": None})
        except _Timeout:
            sys.settrace(None)
            results.append({"args": t["args"], "expect": t["expect"], "actual": None,
                            "pass": False,
                            "error": "timed out — check for a loop that never ends"})
        except Exception:
            sys.settrace(None)
            results.append({"args": t["args"], "expect": t["expect"], "actual": None,
                            "pass": False, "error": traceback.format_exc(limit=1).strip()})
    return json.dumps(results)

def _copy(value):
    if isinstance(value, list):
        return [_copy(v) for v in value]
    if isinstance(value, dict):
        return {k: _copy(v) for k, v in value.items()}
    return value
`;

export async function run(source, func, tests) {
  const py = await ready();
  const runTests = py.globals.get("_run_tests");
  try {
    const raw = runTests(source, func, JSON.stringify(tests));
    return JSON.parse(raw);
  } finally {
    runTests.destroy();
  }
}

/** Runs the learner's own function on one input and returns animation frames
 *  captured from its locals: {steps, result, error, truncated}.
 *  Never throws for a learner mistake — errors come back in `error`, and any
 *  frames captured before the failure are still returned so a crash can be
 *  watched up to the moment it happened. */
export async function trace(source, func, args) {
  const py = await ready();
  const traceRun = py.globals.get("_trace_run");
  try {
    const raw = traceRun(source, func, JSON.stringify(args));
    return JSON.parse(raw);
  } finally {
    traceRun.destroy();
  }
}
