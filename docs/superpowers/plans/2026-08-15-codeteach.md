# CodeTeach Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A static web app that teaches the Two Pointers pattern by animating the algorithm, halting to make the learner predict the next move, giving prose-only hints, and running the learner's own Python in the browser — never showing solution code.

**Architecture:** No backend, no build step, no framework. `index.html` loads three ES modules: `visualizer.js` (pure SVG renderer), `runner.js` (lazy Pyodide + test execution), `app.js` (all state). Content lives entirely in `problems/*.json`; adding a problem touches no JavaScript. `tools/record.py` generates the step traces at authoring time and is never served.

**Tech Stack:** Vanilla HTML/CSS/ES modules, SVG, Pyodide v0.26.4 from CDN, Python 3 + `pytest` for the authoring/validation tools only.

## Global Constraints

- No backend, no build step, no npm, no framework. Opening `index.html` via `file://` must work for everything except Run (Pyodide needs `http://`; a `python3 -m http.server` line goes in the README).
- No bundler means all browser code is ES modules loaded with `<script type="module">`.
- Solution code must never reach the browser. Reference solutions live only in `tools/record.py`.
- `hints` entries are prose: no code fences, no `def `, no `for `/`while `. Enforced by `tools/validate.py`.
- Pyodide version pinned to `0.26.4` at `https://cdn.jsdelivr.net/pyodide/v0.26.4/full/`.
- Problem JSON keys are exactly: `id`, `title`, `statement`, `examples`, `signature`, `func`, `steps`, `checkpoints`, `hints`, `tests`.
- Python tooling deps: `pytest` only. Everything else stdlib.
- Repo root is `/Users/akshanshkumar/Downloads/projects/codeteach`. All paths below are relative to it.

---

## File Structure

| File | Responsibility |
|---|---|
| `index.html` | Three-pane markup, module script tags, CDN link |
| `style.css` | Layout + theming |
| `visualizer.js` | `render(svgEl, step)` — pure function of a step object → SVG. No state. |
| `runner.js` | `loadPyodide()`, `run(source, func, tests)` → results array. No DOM. |
| `app.js` | Loads problem JSON, owns player index / checkpoint gate / hint count / localStorage, wires DOM |
| `problems/*.json` | All content. Five files. |
| `tools/record.py` | Reference solutions + `Recorder`; writes `steps` into problem JSON |
| `tools/validate.py` | The runnable check over every problem file |
| `tools/test_validate.py` | pytest for the validator's own logic |
| `README.md` | How to run, how to add a problem |

Task order builds bottom-up: content contract first (Task 1–2), then the two leaf modules that consume it (3–4), then the shell that wires them (5–6), then remaining content (7).

---

### Task 1: Problem schema + validator

**Files:**
- Create: `tools/validate.py`
- Create: `tools/test_validate.py`
- Create: `problems/two-sum-ii.json`
- Create: `requirements.txt`

**Interfaces:**
- Consumes: nothing.
- Produces: `validate_problem(problem: dict) -> list[str]` returning a list of human-readable error strings (empty = valid). `main()` walks `problems/*.json`, prints errors, exits 1 if any. The problem JSON schema every later task reads.

- [ ] **Step 1: Write the failing test**

Create `tools/test_validate.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 -m pytest tools/test_validate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate'`

- [ ] **Step 3: Write minimal implementation**

Create `tools/validate.py`:

```python
"""Validate every problems/*.json against the CodeTeach content contract."""
import json
import pathlib
import sys

REQUIRED = ["id", "title", "statement", "examples", "signature", "func",
            "steps", "checkpoints", "hints", "tests"]

# ponytail: substring scan, not a parser. Hints are short prose; if this ever
# false-positives, tighten the tokens rather than reaching for an AST.
CODE_TOKENS = ["```", "def ", "for ", "while ", "return ", "()"]


def validate_problem(p):
    errors = []
    for key in REQUIRED:
        if key not in p:
            errors.append(f"missing required key: {key}")
    if errors:
        return errors

    if not p["steps"]:
        errors.append("steps must not be empty")
    if not p["tests"]:
        errors.append("tests must not be empty")
    if not p["hints"]:
        errors.append("hints must not be empty")

    for i, step in enumerate(p["steps"]):
        for key in ("array", "vars", "highlight", "caption"):
            if key not in step:
                errors.append(f"steps[{i}] missing key: {key}")
                break
        else:
            n = len(step["array"])
            for h in step["highlight"]:
                if not isinstance(h, int) or not 0 <= h < n:
                    errors.append(f"steps[{i}] highlight index {h} outside array of length {n}")

    for i, cp in enumerate(p["checkpoints"]):
        for key in ("afterStep", "question", "options", "answer", "why"):
            if key not in cp:
                errors.append(f"checkpoints[{i}] missing key: {key}")
                break
        else:
            if not 0 <= cp["afterStep"] < len(p["steps"]):
                errors.append(f"checkpoints[{i}] afterStep {cp['afterStep']} outside steps range")
            if cp["answer"] not in cp["options"]:
                errors.append(f"checkpoints[{i}] answer {cp['answer']!r} not in options")

    for i, hint in enumerate(p["hints"]):
        for token in CODE_TOKENS:
            if token in hint:
                errors.append(f"hint[{i}] looks like code (contains {token!r}); hints must be prose")
                break

    for i, t in enumerate(p["tests"]):
        if "args" not in t or "expect" not in t:
            errors.append(f"tests[{i}] needs both args and expect")

    return errors


def main():
    root = pathlib.Path(__file__).resolve().parent.parent
    files = sorted((root / "problems").glob("*.json"))
    if not files:
        print("no problem files found")
        return 1
    failed = False
    for path in files:
        try:
            problem = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"{path.name}: invalid JSON: {exc}")
            failed = True
            continue
        errors = validate_problem(problem)
        for error in errors:
            print(f"{path.name}: {error}")
        failed = failed or bool(errors)
        if not errors:
            print(f"{path.name}: ok ({len(problem['steps'])} steps, "
                  f"{len(problem['checkpoints'])} checkpoints)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

Create `requirements.txt`:

```
pytest
```

Create `problems/two-sum-ii.json` — `steps` is a placeholder single frame here and gets regenerated by Task 2:

```json
{
  "id": "two-sum-ii",
  "title": "Two Sum II — Input Array Is Sorted",
  "statement": "Given a **1-indexed** array of integers `numbers` that is already sorted in non-decreasing order, find two numbers that add up to `target`.\n\nReturn the two indices as a list `[index1, index2]` where `1 <= index1 < index2 <= numbers.length`. There is exactly one solution, and you may not use the same element twice.\n\nSolve it using only constant extra space.",
  "examples": [
    { "input": "numbers = [2,7,11,15], target = 9", "output": "[1,2]" },
    { "input": "numbers = [2,3,4], target = 6", "output": "[1,3]" }
  ],
  "signature": "def two_sum(numbers, target):",
  "func": "two_sum",
  "steps": [
    { "array": [2, 7, 11, 15], "vars": { "l": 0, "r": 3 }, "highlight": [0, 3], "caption": "placeholder — regenerated by tools/record.py" }
  ],
  "checkpoints": [],
  "hints": [
    "The array is sorted. What does that tell you about a pair whose sum is already too large?",
    "If the widest pair sums above the target, no pair using that largest element can work — every partner for it is at least as big as the one you just tried.",
    "Keep one index at each end. Compare the current sum to the target and move exactly one index inward each round: the one whose move pushes the sum in the direction you need."
  ],
  "tests": [
    { "args": [[2, 7, 11, 15], 9], "expect": [1, 2] },
    { "args": [[2, 3, 4], 6], "expect": [1, 3] },
    { "args": [[-1, 0], -1], "expect": [1, 2] },
    { "args": [[1, 2, 3, 4, 4, 9, 56, 90], 8], "expect": [4, 5] }
  ]
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 -m pytest tools/test_validate.py -v && python3 tools/validate.py`
Expected: all pytest tests PASS; validate.py prints `two-sum-ii.json: ok (1 steps, 0 checkpoints)` and exits 0.

- [ ] **Step 5: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add tools/validate.py tools/test_validate.py problems/two-sum-ii.json requirements.txt
git commit -m "feat: problem schema validator and first problem file"
```

---

### Task 2: Step recorder (authoring tool)

**Files:**
- Create: `tools/record.py`
- Create: `tools/test_record.py`
- Modify: `problems/two-sum-ii.json` (its `steps` and `checkpoints` are regenerated)

**Interfaces:**
- Consumes: the problem JSON schema and `validate_problem` from Task 1.
- Produces: `Recorder` with `.step(array, vars, caption, highlight)` and `.steps` (list of dicts matching the `steps` schema). A `SOLUTIONS` dict mapping problem id → a function `(recorder) -> None` that traces the example input. `main()` rewrites each problem's `steps` in place, preserving every other key.

This file contains the only copies of the reference solutions in the repo. It is a developer tool — it is never loaded by the browser and must not be referenced from `index.html`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_record.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 -m pytest tools/test_record.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'record'`

- [ ] **Step 3: Write minimal implementation**

Create `tools/record.py`:

```python
"""Authoring tool: run reference solutions with a recorder to produce animation
step traces. NEVER served to the browser — this is the only place solution code
lives in this repo."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Recorder:
    def __init__(self):
        self.steps = []

    def step(self, array, vars, caption, highlight):
        self.steps.append({
            "array": list(array),
            "vars": dict(vars),
            "highlight": list(highlight),
            "caption": caption,
        })


def trace_two_sum_ii(rec):
    numbers, target = [2, 7, 11, 15], 9
    l, r = 0, len(numbers) - 1
    rec.step(numbers, {"l": l, "r": r, "target": target},
             f"Start wide: l at {numbers[l]}, r at {numbers[r]}.", [l, r])
    while l < r:
        total = numbers[l] + numbers[r]
        rec.step(numbers, {"l": l, "r": r, "sum": total, "target": target},
                 f"{numbers[l]} + {numbers[r]} = {total}, target is {target}.", [l, r])
        if total == target:
            rec.step(numbers, {"l": l, "r": r, "sum": total, "target": target},
                     f"Match. Answer is [{l + 1}, {r + 1}] in 1-indexed terms.", [l, r])
            return
        if total > target:
            r -= 1
            rec.step(numbers, {"l": l, "r": r, "target": target},
                     "Sum was too big, so move r inward to a smaller number.", [l, r])
        else:
            l += 1
            rec.step(numbers, {"l": l, "r": r, "target": target},
                     "Sum was too small, so move l inward to a bigger number.", [l, r])


SOLUTIONS = {
    "two-sum-ii": trace_two_sum_ii,
}

# Checkpoints are authored by hand against the recorded trace, keyed by problem id.
# afterStep indexes into the generated steps.
CHECKPOINTS = {
    "two-sum-ii": [
        {"afterStep": 1, "question": "The sum is 17 and the target is 9. Which pointer should move?",
         "options": ["l, rightward", "r, leftward"], "answer": "r, leftward",
         "why": "The sum is too big, so you need a smaller number. Moving l rightward only makes the sum larger; moving r leftward is the only way down."},
        {"afterStep": 3, "question": "Now the sum is 13, still above 9. What happens next?",
         "options": ["l, rightward", "r, leftward"], "answer": "r, leftward",
         "why": "Same reasoning as before — that is the whole invariant. Too big means shrink from the right."},
    ],
}


def main():
    for pid, trace_fn in SOLUTIONS.items():
        path = ROOT / "problems" / f"{pid}.json"
        problem = json.loads(path.read_text())
        rec = Recorder()
        trace_fn(rec)
        problem["steps"] = rec.steps
        problem["checkpoints"] = CHECKPOINTS.get(pid, [])
        path.write_text(json.dumps(problem, indent=2) + "\n")
        print(f"{path.name}: wrote {len(rec.steps)} steps, "
              f"{len(problem['checkpoints'])} checkpoints")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Regenerate, validate, and run the tests**

Run:
```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 tools/record.py && python3 tools/validate.py && python3 -m pytest tools/ -v
```
Expected: `record.py` reports the step count; `validate.py` prints `ok` and exits 0; every pytest test passes.

- [ ] **Step 5: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add tools/record.py tools/test_record.py problems/two-sum-ii.json
git commit -m "feat: step recorder generating animation traces from reference solutions"
```

---

### Task 3: Visualizer

**Files:**
- Create: `visualizer.js`
- Create: `test-visualizer.html`

**Interfaces:**
- Consumes: a `step` object from a problem's `steps` array.
- Produces: `export function render(svg, step)` — clears `svg` and draws the array boxes, highlight styling, pointer labels from `step.vars`, and returns nothing. Pure: same step in, same SVG out, no module-level state. `app.js` (Task 5) is its only caller.

Design: a horizontal row of boxes. Boxes whose index appears in `step.highlight` get the `hl` class. Any entry in `step.vars` whose value is an integer within array range is drawn as a labelled arrow under that box (so `l`, `r`, `i`, `j` all work with no extra config); non-index vars like `sum` and `target` are drawn as a readout line above the row. This is the whole reason a single renderer covers the pattern.

- [ ] **Step 1: Write the failing test**

There is no test runner in this project by design. The check is a browser harness that asserts against the real DOM. Create `test-visualizer.html`:

```html
<!doctype html>
<meta charset="utf-8">
<title>visualizer self-check</title>
<svg id="s" viewBox="0 0 800 220"></svg>
<pre id="out"></pre>
<script type="module">
import { render } from "./visualizer.js";

const svg = document.getElementById("s");
const results = [];
const check = (name, fn) => {
  try { fn(); results.push("PASS " + name); }
  catch (e) { results.push("FAIL " + name + " — " + e.message); }
};
const assert = (cond, msg) => { if (!cond) throw new Error(msg); };

const step = {
  array: [2, 7, 11, 15],
  vars: { l: 0, r: 3, sum: 17, target: 9 },
  highlight: [0, 3],
  caption: "sum is 17",
};

check("draws one box per element", () => {
  render(svg, step);
  assert(svg.querySelectorAll(".cell").length === 4, "expected 4 cells");
});

check("highlights only the highlighted indices", () => {
  render(svg, step);
  const hl = [...svg.querySelectorAll(".cell.hl")].map(e => Number(e.dataset.index));
  assert(JSON.stringify(hl) === "[0,3]", "got " + JSON.stringify(hl));
});

check("draws a pointer for each index-valued var", () => {
  render(svg, step);
  const names = [...svg.querySelectorAll(".pointer")].map(e => e.dataset.name).sort();
  assert(JSON.stringify(names) === '["l","r"]', "got " + JSON.stringify(names));
});

check("non-index vars go to the readout, not the pointers", () => {
  render(svg, step);
  const readout = svg.querySelector(".readout").textContent;
  assert(readout.includes("sum = 17"), "readout missing sum: " + readout);
  assert(readout.includes("target = 9"), "readout missing target: " + readout);
});

check("re-render clears the previous frame", () => {
  render(svg, step);
  render(svg, { array: [1, 2], vars: { l: 0 }, highlight: [], caption: "x" });
  assert(svg.querySelectorAll(".cell").length === 2, "stale cells left behind");
  assert(svg.querySelectorAll(".pointer").length === 1, "stale pointers left behind");
});

check("two pointers on the same index both render", () => {
  render(svg, { array: [1, 2, 3], vars: { l: 1, r: 1 }, highlight: [1], caption: "meet" });
  assert(svg.querySelectorAll(".pointer").length === 2, "expected 2 pointers");
});

document.getElementById("out").textContent = results.join("\n");
</script>
```

- [ ] **Step 2: Run it to verify it fails**

Run:
```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 -m http.server 8000
```
Open `http://localhost:8000/test-visualizer.html`.
Expected: the page is blank / the console shows a 404 for `visualizer.js`.

- [ ] **Step 3: Write minimal implementation**

Create `visualizer.js`:

```javascript
const NS = "http://www.w3.org/2000/svg";
const BOX = 72, GAP = 14, TOP = 70, LEFT = 20;

function el(tag, attrs, text) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

const cellX = (i) => LEFT + i * (BOX + GAP);

export function render(svg, step) {
  svg.replaceChildren();
  const { array, vars, highlight, caption } = step;
  const hl = new Set(highlight);

  const width = LEFT * 2 + array.length * (BOX + GAP);
  svg.setAttribute("viewBox", `0 0 ${Math.max(width, 480)} 260`);

  // Non-index vars, shown as a readout above the row.
  const isIndex = (v) => Number.isInteger(v) && v >= 0 && v < array.length;
  const readout = Object.entries(vars)
    .filter(([, v]) => !isIndex(v))
    .map(([k, v]) => `${k} = ${v}`)
    .join("   ");
  const readoutNode = el("text", { class: "readout", x: LEFT, y: 34 }, readout);
  svg.appendChild(readoutNode);

  array.forEach((value, i) => {
    const g = el("g", { class: "cell" + (hl.has(i) ? " hl" : "") });
    g.dataset.index = String(i);
    g.appendChild(el("rect", { x: cellX(i), y: TOP, width: BOX, height: BOX, rx: 8 }));
    g.appendChild(el("text", {
      class: "value", x: cellX(i) + BOX / 2, y: TOP + BOX / 2,
      "text-anchor": "middle", "dominant-baseline": "central",
    }, String(value)));
    g.appendChild(el("text", {
      class: "idx", x: cellX(i) + BOX / 2, y: TOP - 12, "text-anchor": "middle",
    }, String(i)));
    svg.appendChild(g);
  });

  // Pointers, stacked so two on the same index stay readable.
  const perIndex = new Map();
  Object.entries(vars).filter(([, v]) => isIndex(v)).forEach(([name, i]) => {
    const row = perIndex.get(i) ?? 0;
    perIndex.set(i, row + 1);
    const y = TOP + BOX + 26 + row * 26;
    const g = el("g", { class: "pointer" });
    g.dataset.name = name;
    g.appendChild(el("text", {
      x: cellX(i) + BOX / 2, y, "text-anchor": "middle",
    }, `▲ ${name}`));
    svg.appendChild(g);
  });

  svg.appendChild(el("text", {
    class: "caption", x: LEFT, y: 244,
  }, caption ?? ""));
}
```

- [ ] **Step 4: Run it to verify it passes**

Reload `http://localhost:8000/test-visualizer.html`.
Expected: the `<pre>` shows six lines, all starting with `PASS`, and the SVG above shows four boxes with `l` and `r` arrows.

- [ ] **Step 5: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add visualizer.js test-visualizer.html
git commit -m "feat: SVG array visualizer"
```

---

### Task 4: Python runner

**Files:**
- Create: `runner.js`
- Create: `test-runner.html`

**Interfaces:**
- Consumes: `problem.func` (function name string) and `problem.tests` (`[{args, expect}]`).
- Produces:
  - `export async function ready(onProgress)` — idempotent lazy Pyodide load; resolves once ready, rejects with a readable Error if the CDN fails.
  - `export async function run(source, func, tests)` → `Promise<Result[]>` where `Result = {args, expect, actual, pass, error}`. `error` is a string or `null`. Never throws for learner mistakes — a bad submission comes back as failing results.
- `app.js` (Task 5) is the only caller. This module touches no DOM.

Timeout: Pyodide runs synchronously on the main thread, so a learner's infinite loop cannot be interrupted from JS. Instead, a Python-side counter raises after 5 million interpreter steps via `sys.settrace`-free `sys.setrecursionlimit`-independent means — concretely, `run` injects a bounded-iteration guard using `sys.settrace` with a line-count budget, and reports `error: "timed out — check for a loop that never ends"`.

- [ ] **Step 1: Write the failing test**

Create `test-runner.html`:

```html
<!doctype html>
<meta charset="utf-8">
<title>runner self-check</title>
<pre id="out">loading pyodide…</pre>
<script type="module">
import { ready, run } from "./runner.js";

const results = [];
const check = async (name, fn) => {
  try { await fn(); results.push("PASS " + name); }
  catch (e) { results.push("FAIL " + name + " — " + e.message); }
  document.getElementById("out").textContent = results.join("\n");
};
const assert = (cond, msg) => { if (!cond) throw new Error(msg); };

const TESTS = [
  { args: [[2, 7, 11, 15], 9], expect: [1, 2] },
  { args: [[2, 3, 4], 6], expect: [1, 3] },
];

const CORRECT = `
def two_sum(numbers, target):
    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            return [l + 1, r + 1]
        if s > target:
            r -= 1
        else:
            l += 1
`;

await ready((msg) => { document.getElementById("out").textContent = msg; });

await check("correct solution passes every case", async () => {
  const res = await run(CORRECT, "two_sum", TESTS);
  assert(res.length === 2, "expected 2 results");
  assert(res.every(r => r.pass), JSON.stringify(res));
});

await check("wrong answer is reported, not thrown", async () => {
  const res = await run("def two_sum(numbers, target):\n    return [0, 0]\n", "two_sum", TESTS);
  assert(res.every(r => !r.pass), "should have failed");
  assert(JSON.stringify(res[0].actual) === "[0,0]", "actual not captured");
  assert(res[0].error === null, "should not be an error, just wrong");
});

await check("exception in learner code becomes an error result", async () => {
  const res = await run("def two_sum(numbers, target):\n    return 1 / 0\n", "two_sum", TESTS);
  assert(!res[0].pass, "should not pass");
  assert(res[0].error && res[0].error.includes("ZeroDivisionError"), "got " + res[0].error);
});

await check("missing function name gives a clear message", async () => {
  const res = await run("x = 1\n", "two_sum", TESTS);
  assert(res[0].error && res[0].error.includes("two_sum"), "got " + res[0].error);
});

await check("syntax error gives a clear message", async () => {
  const res = await run("def two_sum(:\n", "two_sum", TESTS);
  assert(res[0].error && res[0].error.includes("SyntaxError"), "got " + res[0].error);
});

await check("infinite loop times out instead of hanging", async () => {
  const res = await run("def two_sum(numbers, target):\n    while True:\n        pass\n", "two_sum", TESTS);
  assert(res[0].error && res[0].error.includes("timed out"), "got " + res[0].error);
});

await check("state does not leak between runs", async () => {
  await run("def two_sum(numbers, target):\n    return [1, 2]\n", "two_sum", TESTS);
  const res = await run("y = 2\n", "two_sum", TESTS);
  assert(res[0].error && res[0].error.includes("two_sum"), "stale function survived: " + res[0].error);
});
</script>
```

- [ ] **Step 2: Run it to verify it fails**

Run `python3 -m http.server 8000` from the repo root, open `http://localhost:8000/test-runner.html`.
Expected: blank/404 for `runner.js` in the console.

- [ ] **Step 3: Write minimal implementation**

Create `runner.js`:

```javascript
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
```

Note for the implementer: `_Timeout` must not be caught by the learner's own bare `except:` in a way that hides it — if a submission swallows it, the budget simply runs out again on the next line and re-raises. That behaviour is acceptable; do not add machinery for it.

- [ ] **Step 4: Run it to verify it passes**

Reload `http://localhost:8000/test-runner.html` (allow ~20s for the first Pyodide download).
Expected: seven lines, all `PASS`.

- [ ] **Step 5: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add runner.js test-runner.html
git commit -m "feat: browser Python runner with timeout and error reporting"
```

---

### Task 5: App shell — three panes, player, checkpoint gate

**Files:**
- Create: `index.html`
- Create: `style.css`
- Create: `app.js`

**Interfaces:**
- Consumes: `render` from `visualizer.js` (Task 3), `ready`/`run` from `runner.js` (Task 4), the problem JSON schema (Task 1).
- Produces: the running app. No exports — `app.js` is the entry point.

State owned by `app.js`: `problem` (loaded JSON), `index` (current step), `answered` (Set of checkpoint indices already answered correctly), `hintsUsed` (int). `hintsUsed` and `answered` persist to `localStorage` under key `codeteach:<problem.id>`.

**The checkpoint gate is the core mechanic and must behave exactly as follows:** a checkpoint with `afterStep: k` blocks any advance past step `k` until it is in `answered`. While blocked, the ▶ and ⏭ buttons and the scrubber are disabled, and the question with its options renders in place of the caption. Selecting the correct option adds it to `answered`, shows `why` as confirmation, and re-enables the controls. Selecting a wrong option shows `why` and leaves it blocked. ◀ and ⏮ are never disabled — going back is always allowed.

- [ ] **Step 1: Write the failing test — extend the browser harness**

Append to the end of `test-visualizer.html`'s script (this is where the gate logic gets its check, since `app.js` exports the gate helper for exactly this reason):

```javascript
import { nextBlockingCheckpoint } from "./app.js";

check("no checkpoint means no block", () => {
  assert(nextBlockingCheckpoint([], new Set(), 0) === null, "should not block");
});

check("checkpoint at current step blocks when unanswered", () => {
  const cps = [{ afterStep: 1 }, { afterStep: 3 }];
  assert(nextBlockingCheckpoint(cps, new Set(), 1) === 0, "should block on cp 0");
});

check("answered checkpoint does not block", () => {
  const cps = [{ afterStep: 1 }];
  assert(nextBlockingCheckpoint(cps, new Set([0]), 1) === null, "answered should pass");
});

check("checkpoint for a later step does not block yet", () => {
  const cps = [{ afterStep: 3 }];
  assert(nextBlockingCheckpoint(cps, new Set(), 1) === null, "too early to block");
});
```

- [ ] **Step 2: Run it to verify it fails**

Reload `http://localhost:8000/test-visualizer.html`.
Expected: console error — cannot resolve `./app.js`.

- [ ] **Step 3: Write the implementation**

Create `index.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CodeTeach — Two Pointers</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>CodeTeach</h1>
  <select id="picker" aria-label="Choose a problem"></select>
</header>

<main>
  <section class="pane" id="problem-pane">
    <h2 id="title"></h2>
    <div id="statement"></div>
    <h3>Examples</h3>
    <div id="examples"></div>
    <h3>Hints</h3>
    <div id="hints"></div>
    <button id="hint-btn">Reveal a hint</button>
    <p id="hint-count" class="muted"></p>
  </section>

  <section class="pane" id="viz-pane">
    <svg id="viz" viewBox="0 0 800 260" role="img" aria-label="Algorithm animation"></svg>
    <div id="checkpoint" hidden>
      <p id="cp-question"></p>
      <div id="cp-options"></div>
      <p id="cp-feedback" role="status"></p>
    </div>
    <div class="controls">
      <button id="first" aria-label="First step">⏮</button>
      <button id="prev" aria-label="Previous step">◀</button>
      <button id="next" aria-label="Next step">▶</button>
      <button id="last" aria-label="Last step">⏭</button>
      <input id="scrub" type="range" min="0" value="0" aria-label="Step">
      <span id="step-count" class="muted"></span>
    </div>
  </section>

  <section class="pane" id="code-pane">
    <label for="editor">Your solution</label>
    <textarea id="editor" spellcheck="false"></textarea>
    <button id="run">Run tests</button>
    <div id="results"></div>
  </section>
</main>

<script type="module" src="app.js"></script>
</body>
</html>
```

Create `style.css`:

```css
:root {
  --bg: #12141a; --pane: #1a1d26; --ink: #e8eaf0; --muted: #8b91a3;
  --accent: #6ea8fe; --hl: #f0b429; --ok: #4ade80; --bad: #f87171;
  --line: #2a2e3a;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, sans-serif;
}
header {
  display: flex; align-items: center; gap: 1rem;
  padding: .75rem 1.25rem; border-bottom: 1px solid var(--line);
}
h1 { font-size: 1.05rem; margin: 0; letter-spacing: .02em; }
select, button, textarea { font: inherit; }
select {
  background: var(--pane); color: var(--ink);
  border: 1px solid var(--line); border-radius: 6px; padding: .35rem .5rem;
}
main {
  display: grid; grid-template-columns: minmax(280px, 1fr) 1.6fr minmax(320px, 1fr);
  gap: 1px; background: var(--line); height: calc(100vh - 53px);
}
.pane { background: var(--pane); padding: 1.1rem; overflow-y: auto; }
h2 { font-size: 1.1rem; margin: 0 0 .6rem; }
h3 { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em;
     color: var(--muted); margin: 1.4rem 0 .5rem; }
.muted { color: var(--muted); font-size: .85rem; }
code, pre, textarea, #examples { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
#examples div { background: #0f1116; border-radius: 6px; padding: .5rem .7rem;
                margin-bottom: .5rem; font-size: .85rem; }
#hints p { border-left: 2px solid var(--accent); padding-left: .7rem; margin: .6rem 0; }
button {
  background: var(--accent); color: #0b0d12; border: 0; border-radius: 6px;
  padding: .45rem .8rem; cursor: pointer; font-weight: 600;
}
button:disabled { background: var(--line); color: var(--muted); cursor: not-allowed; }
button.ghost { background: transparent; color: var(--ink); border: 1px solid var(--line); }

#viz { width: 100%; height: auto; }
.cell rect { fill: #0f1116; stroke: var(--line); stroke-width: 2; }
.cell.hl rect { stroke: var(--hl); stroke-width: 3; fill: #241d0d; }
.cell .value { fill: var(--ink); font-size: 22px; font-weight: 600; }
.cell .idx { fill: var(--muted); font-size: 12px; }
.pointer text { fill: var(--accent); font-size: 15px; font-weight: 600; }
.readout { fill: var(--muted); font-size: 15px; }
.caption { fill: var(--ink); font-size: 16px; }

.controls { display: flex; align-items: center; gap: .5rem; margin-top: 1rem; }
#scrub { flex: 1; }
#checkpoint {
  margin-top: 1rem; padding: 1rem; border: 1px solid var(--hl); border-radius: 8px;
  background: #201a0c;
}
#cp-options { display: flex; gap: .5rem; flex-wrap: wrap; margin: .7rem 0; }
#cp-feedback:empty { display: none; }

#editor {
  width: 100%; height: 300px; background: #0f1116; color: var(--ink);
  border: 1px solid var(--line); border-radius: 6px; padding: .7rem;
  font-size: 13.5px; resize: vertical;
}
#run { margin-top: .6rem; }
.result { border-left: 3px solid var(--line); padding: .5rem .7rem; margin-top: .6rem;
          font-size: .82rem; background: #0f1116; }
.result.pass { border-color: var(--ok); }
.result.fail { border-color: var(--bad); }
.result pre { margin: .3rem 0 0; white-space: pre-wrap; color: var(--muted); }
```

Create `app.js`:

```javascript
import { render } from "./visualizer.js";
import { ready, run } from "./runner.js";

const PROBLEMS = ["two-sum-ii"];

/** Index of the checkpoint that blocks advancing past `index`, or null. */
export function nextBlockingCheckpoint(checkpoints, answered, index) {
  for (let i = 0; i < checkpoints.length; i++) {
    if (checkpoints[i].afterStep === index && !answered.has(i)) return i;
  }
  return null;
}

const $ = (id) => document.getElementById(id);
let problem = null, index = 0, answered = new Set(), hintsUsed = 0;

const storageKey = () => `codeteach:${problem.id}`;

function save() {
  localStorage.setItem(storageKey(),
    JSON.stringify({ answered: [...answered], hintsUsed }));
}

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(storageKey()) ?? "{}");
    answered = new Set(raw.answered ?? []);
    hintsUsed = raw.hintsUsed ?? 0;
  } catch { answered = new Set(); hintsUsed = 0; }
}

async function loadProblem(id) {
  problem = await (await fetch(`problems/${id}.json`)).json();
  index = 0;
  load();
  $("title").textContent = problem.title;
  $("statement").innerHTML = problem.statement
    .split("\n\n").map(p => `<p>${inline(p)}</p>`).join("");
  $("examples").innerHTML = problem.examples
    .map(e => `<div>Input: ${e.input}<br>Output: ${e.output}</div>`).join("");
  $("editor").value = `${problem.signature}\n    `;
  $("scrub").max = String(problem.steps.length - 1);
  $("results").replaceChildren();
  renderHints();
  draw();
}

// ponytail: bold + inline code only. Problem statements are ours, not user input.
const inline = (s) => s
  .replace(/&/g, "&amp;").replace(/</g, "&lt;")
  .replace(/`([^`]+)`/g, "<code>$1</code>")
  .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

function renderHints() {
  $("hints").innerHTML = problem.hints.slice(0, hintsUsed)
    .map(h => `<p>${inline(h)}</p>`).join("");
  $("hint-count").textContent = `${hintsUsed} of ${problem.hints.length} hints used`;
  $("hint-btn").disabled = hintsUsed >= problem.hints.length;
}

function draw() {
  render($("viz"), problem.steps[index]);
  $("step-count").textContent = `${index + 1} / ${problem.steps.length}`;
  $("scrub").value = String(index);

  const blocked = nextBlockingCheckpoint(problem.checkpoints, answered, index);
  const atEnd = index >= problem.steps.length - 1;
  $("next").disabled = blocked !== null || atEnd;
  $("last").disabled = blocked !== null || atEnd;
  $("scrub").disabled = blocked !== null;
  $("prev").disabled = index === 0;
  $("first").disabled = index === 0;

  if (blocked === null) { $("checkpoint").hidden = true; return; }
  const cp = problem.checkpoints[blocked];
  $("checkpoint").hidden = false;
  $("cp-question").textContent = cp.question;
  $("cp-feedback").textContent = "";
  $("cp-options").replaceChildren(...cp.options.map(opt => {
    const b = document.createElement("button");
    b.className = "ghost";
    b.textContent = opt;
    b.onclick = () => {
      if (opt === cp.answer) {
        answered.add(blocked);
        save();
        draw();
        $("checkpoint").hidden = false;
        $("cp-question").textContent = "Right.";
        $("cp-options").replaceChildren();
        $("cp-feedback").textContent = cp.why;
      } else {
        $("cp-feedback").textContent = `Not quite. ${cp.why}`;
      }
    };
    return b;
  }));
}

function go(i) {
  const target = Math.max(0, Math.min(problem.steps.length - 1, i));
  // Never step past an unanswered gate.
  for (let k = index; k < target; k++) {
    if (nextBlockingCheckpoint(problem.checkpoints, answered, k) !== null) {
      index = k; draw(); return;
    }
  }
  index = target;
  draw();
}

$("next").onclick = () => go(index + 1);
$("prev").onclick = () => go(index - 1);
$("first").onclick = () => go(0);
$("last").onclick = () => go(problem.steps.length - 1);
$("scrub").oninput = (e) => go(Number(e.target.value));
$("hint-btn").onclick = () => { hintsUsed++; save(); renderHints(); };

$("run").onclick = async () => {
  const btn = $("run");
  btn.disabled = true;
  $("results").textContent = "Starting Python…";
  try {
    await ready((msg) => { $("results").textContent = msg; });
    const results = await run($("editor").value, problem.func, problem.tests);
    $("results").replaceChildren(...results.map(r => {
      const div = document.createElement("div");
      div.className = "result " + (r.pass ? "pass" : "fail");
      const head = r.pass ? "PASS" : "FAIL";
      div.innerHTML = `<strong>${head}</strong> ${escapeHtml(JSON.stringify(r.args))}`;
      const pre = document.createElement("pre");
      pre.textContent = r.error
        ? r.error
        : `expected ${JSON.stringify(r.expect)}\ngot      ${JSON.stringify(r.actual)}`;
      if (!r.pass) div.appendChild(pre);
      return div;
    }));
  } catch (err) {
    $("results").textContent = `${err.message} — check your connection and press Run again.`;
  } finally {
    btn.disabled = false;
  }
};

const escapeHtml = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

$("picker").replaceChildren(...PROBLEMS.map(id => {
  const o = document.createElement("option");
  o.value = id; o.textContent = id;
  return o;
}));
$("picker").onchange = (e) => loadProblem(e.target.value);

loadProblem(PROBLEMS[0]);
```

Note: `app.js` runs its wiring at import time, so `test-visualizer.html` importing it will also try to load a problem. That is fine — the harness page has no matching DOM ids, so `$()` returns null and the wiring throws after the exported function is already available. If that noise is distracting, the implementer may move the wiring into a `if (document.getElementById("viz")) { … }` guard. Do not restructure further.

- [ ] **Step 4: Run and verify**

Reload `http://localhost:8000/test-visualizer.html` — all ten checks `PASS`.
Then open `http://localhost:8000/index.html` and confirm by hand:
1. The problem text, four boxes, and `l`/`r` arrows render.
2. Pressing ▶ reaches step 2 and stops; the question appears; ▶, ⏭ and the scrubber are disabled.
3. Clicking the wrong option shows the explanation and stays blocked.
4. Clicking the right option unblocks; ▶ works again.
5. ◀ still works while blocked.
6. Reloading the page keeps the checkpoint answered and the hint count.
7. "Reveal a hint" adds one hint and updates the count; it disables at 3 of 3.
8. Pasting a correct two-pointer solution and pressing Run shows four green PASS rows.

- [ ] **Step 5: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add index.html style.css app.js test-visualizer.html
git commit -m "feat: app shell with animation player, checkpoint gate, hints and test runner"
```

---

### Task 6: README

**Files:**
- Create: `README.md`
- Create: `.gitignore`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing code-facing.

- [ ] **Step 1: Write `README.md`**

```markdown
# CodeTeach

Learn the Two Pointers pattern by watching it work, predicting the next move, and
writing the code yourself. The app never shows you a solution.

## Run it

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>. A `file://` open works too, except "Run tests" —
Pyodide needs an `http://` origin.

## How it teaches

- The animation stops at checkpoints and asks what happens next. You cannot skip past.
- Hints escalate from a nudge to the invariant to the loop structure — always in prose, never code.
- You write the function; it runs in your browser against the real test cases.

## Add a problem

1. Add a `trace_<name>(rec)` function and a `CHECKPOINTS` entry in `tools/record.py`.
2. Create `problems/<id>.json` with everything except `steps` and `checkpoints`.
3. `python3 tools/record.py` to generate the trace.
4. `python3 tools/validate.py` to check it.
5. Add the id to `PROBLEMS` in `app.js`.

## Checks

```bash
python3 -m pytest tools/ -v && python3 tools/validate.py
```

Browser checks: open `/test-visualizer.html` and `/test-runner.html`; every line must say PASS.
```

- [ ] **Step 2: Write `.gitignore`**

```
__pycache__/
.pytest_cache/
.DS_Store
```

- [ ] **Step 3: Verify the README's own commands run**

Run: `cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 -m pytest tools/ -v && python3 tools/validate.py`
Expected: all pass, exit 0.

- [ ] **Step 4: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add README.md .gitignore
git commit -m "docs: README and gitignore"
```

---

### Task 7: Remaining four Two Pointers problems

**Files:**
- Create: `problems/valid-palindrome.json`, `problems/3sum.json`, `problems/container-with-most-water.json`, `problems/trapping-rain-water.json`
- Modify: `tools/record.py` (four `trace_*` functions, four `CHECKPOINTS` entries, four `SOLUTIONS` entries)
- Modify: `app.js:5` (the `PROBLEMS` array)

**Interfaces:**
- Consumes: `Recorder`, `SOLUTIONS`, `CHECKPOINTS` from Task 2; the schema from Task 1.
- Produces: four more problem files. No new interfaces.

This task adds content only. If it needs a JavaScript change beyond the `PROBLEMS` array, the visualizer's design is wrong — stop and say so rather than special-casing.

- [ ] **Step 1: Write the four problem JSON files**

Each follows `problems/two-sum-ii.json` exactly: every key present, `steps` set to a single placeholder frame (regenerated in Step 3), `checkpoints` empty. Author `statement`, `examples`, `signature`, `func`, `hints` (3 rungs, prose only) and `tests` (4+ cases including an edge case) per problem:

| id | func | signature | edge case to include in tests |
|---|---|---|---|
| `valid-palindrome` | `is_palindrome` | `def is_palindrome(s):` | `""` → `true`; `"0P"` → `false` |
| `container-with-most-water` | `max_area` | `def max_area(height):` | two-element input |
| `3sum` | `three_sum` | `def three_sum(nums):` | all zeros `[0,0,0,0]` → `[[0,0,0]]`; no-solution input → `[]` |
| `trapping-rain-water` | `trap` | `def trap(height):` | strictly increasing input → `0` |

For `3sum`, `expect` is a list of triples; the runner compares with `==`, so the reference solution's output order must match what you write in `expect`. Sort both: return triples sorted ascending, and the outer list sorted.

- [ ] **Step 2: Add the traces and checkpoints to `tools/record.py`**

For each problem add a `trace_<name>(rec)` that runs the real algorithm on the first example, calling `rec.step(...)` at every pointer move with a caption naming *why* the pointer moved (the caption carries the teaching — "sum was too big, so shrink from the right", not "r -= 1"). Register it in `SOLUTIONS` and add 2–3 `CHECKPOINTS` entries per problem placed at moments where the decision is genuinely non-obvious.

Checkpoint placement rule: the first move of a problem is never a good checkpoint (nothing has been learned yet), and neither is a repeat of a decision already gated in the same problem — vary what you ask. Good targets: the first time an invariant pays off, and any point where the naive guess is wrong (e.g. in Container With Most Water, "move the *taller* wall" is the tempting wrong answer — gate exactly there).

- [ ] **Step 3: Regenerate and validate**

Run:
```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach && python3 tools/record.py && python3 tools/validate.py && python3 -m pytest tools/ -v
```
Expected: five files regenerated and reported `ok`; `test_every_solution_produces_a_valid_trace` and `test_regenerated_problem_files_are_valid` now cover all five; exit 0.

- [ ] **Step 4: Register them in the app**

Modify `app.js:5`:

```javascript
const PROBLEMS = ["valid-palindrome", "two-sum-ii", "container-with-most-water", "3sum", "trapping-rain-water"];
```

- [ ] **Step 5: Verify each in the browser**

With `python3 -m http.server 8000` running, open `http://localhost:8000` and for each of the five entries in the picker: step through to the end, answer each checkpoint (wrong option first, then right), and paste a correct solution to confirm every test passes. Any problem whose animation is unreadable needs its trace captions or step granularity fixed in `record.py`, not a visualizer change.

- [ ] **Step 6: Commit**

```bash
cd /Users/akshanshkumar/Downloads/projects/codeteach
git add problems/ tools/record.py app.js
git commit -m "feat: remaining four Two Pointers problems"
```
