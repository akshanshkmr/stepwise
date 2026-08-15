const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/";
const LINE_BUDGET = 2_000_000;

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

class _Timeout(Exception):
    pass

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
  const raw = runTests(source, func, JSON.stringify(tests));
  runTests.destroy();
  return JSON.parse(raw);
}
