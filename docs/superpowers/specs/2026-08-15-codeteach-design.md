# CodeTeach — Design

Date: 2026-08-15

> Renamed to **Stepwise** on 2026-08-16. This document keeps the original
> name as the record of what was designed; the code, README and CLAUDE.md use
> the new one.

## Purpose

A coding-practice app that teaches the *core idea* of an algorithm instead of its
solution text. It states the problem, animates how the solution works, interrupts
the animation to make the learner predict the next move, and gives escalating
prose hints. It never displays solution code.

Content: the NeetCode 150 problem set. V1 covers one pattern — Two Pointers —
end to end, to prove the loop before scaling.

## Non-goals (v1)

Accounts, server-side progress, spaced repetition, discussion, multiple
visualizer types, more than one pattern. `localStorage` is the only persistence.

## Architecture

Static site. No backend, no build step, no framework. It must be served over
`http://` — problems are fetched at load, so `file://` does not work at all.

```
index.html        layout + pane markup
style.css
app.js            state machine: load problem, drive player, gate checkpoints, reveal hints
visualizer.js     SVG array renderer: boxes, pointer arrows, highlights, readout
runner.js         lazy Pyodide load, execute learner code against tests
problems/*.json   one file per problem — the entire content contract
tools/record.py   authoring-time step recorder (not shipped to the browser)
tools/validate.py the one runnable check
dev/*.html        browser self-check harnesses (hold reference solutions; not served as part of the app)
```

Each unit has one job and a narrow interface: `visualizer.render(step)`,
`runner.run(source, signature, tests) -> results[]`, `app.js` owns all state.
Adding a problem touches no JavaScript.

## Data contract

A problem is one JSON file:

```json
{
  "id": "two-sum-ii",
  "title": "Two Sum II — Input Array Is Sorted",
  "statement": "markdown string",
  "examples": [{ "input": "...", "output": "..." }],
  "signature": "def two_sum(numbers, target):",
  "steps": [
    { "array": [2,7,11,15], "pointers": {"l":0,"r":3}, "vars": {"sum":17,"target":9},
      "highlight": [0,3], "caption": "sum is 17, larger than the target 9" }
  ],
  "checkpoints": [
    { "afterStep": 3, "question": "Which pointer moves next?",
      "options": ["left", "right"], "answer": "right",
      "why": "The sum is too large. Moving left only raises it, so only r can help." }
  ],
  "hints": [
    "What does the array being sorted let you rule out?",
    "If the current pair sums too high, every pair to the right of r is worse.",
    "Keep two indices at the ends and move exactly one inward each iteration, based on the comparison."
  ],
  "tests": [ { "args": [[2,7,11,15], 9], "expect": [1,2] } ]
}
```

Rules:
- `hints` are prose. No code fences, no identifiers-as-answer. Validated.
- `steps` is a literal recorded trace, not a program. The solution never ships.
- `checkpoints[].afterStep` indexes into `steps`.
- A step names its pointers explicitly: `pointers` are indices into `array` and
  render as arrows; `vars` are the scalars the caption talks about and render as
  the readout. The renderer never guesses which is which.
- The caption is rendered as HTML below the SVG by `app.js`, so it wraps.

## Authoring flow

Two routes, both driven by `tools/record.py`, which holds every reference
solution and is never served.

**Auto-traced (default).** `tracer.py` runs an ordinary, uninstrumented solution
under `sys.settrace` and derives frames from its locals: the longest list of
scalars is the array, ints indexing it are pointers, other scalars are the
readout. Captions come out mechanical ("r: 3 to 2"); the author overrides the
handful that sit at decisions, where the WHY is the teaching. This is the path a
new problem takes.

**Hand-written.** A `trace_<name>(rec)` function calling `rec.step(...)`. Still
required for view-specific overlays the tracer cannot infer, such as the bars
view's `water` and `region`, and used by the five original problems.

`tracer.py` is shared: the browser loads the same file to animate the learner's
own run, so a learner's trace and the walkthrough it is compared against are
produced by identical code.

## The learner loop

1. Read the problem (left pane).
2. Step through the animation (center pane) with `⏮ ◀ ▶ ⏭` and a scrubber.
3. At a checkpoint the player **halts**. The caption is replaced by the question
   and its options; the forward controls and the scrubber are disabled until the
   learner answers. A wrong answer shows `why` and stays put; the learner may
   then continue. This gate is the anti-memorization mechanism — it is not
   skippable.
4. Hints are revealed one rung at a time on request, with the count shown
   ("2 of 3 used"), persisted per problem in `localStorage`.
5. Write the function in the editor (right pane) and Run.

## Running code

Pyodide loads on the first Run, not on page load, with a visible loading state.
`runner.js` defines the learner's source in the Pyodide namespace, then calls
the function once per test case, comparing to `expect` with a deep equality
check. Results render per case: pass/fail, the input, expected, actual.
Uncaught exceptions are shown verbatim with their traceback. A test that runs
longer than 5 seconds is reported as a timeout rather than hanging the page.

Failure modes handled: Pyodide fails to load (message + retry), learner code
raises (traceback shown), function name missing (explicit "define `two_sum`"
message), infinite loop (timeout).

## Testing

`tools/validate.py` asserts, for every `problems/*.json`: required keys present;
`steps`, `tests`, `hints` and `checkpoints` non-empty; every `pointers` value a
valid index into that step's `array`; every `checkpoints[].afterStep` within `steps` range; every
`answer` present in its `options`; no fenced code or `def ` in
any hint. Run it after any content edit.

## Visualizing the learner's own run

"Visualize my run" traces the learner's function on the first test input and
animates it in the same view, with checkpoints off and the reference walkthrough
untouched behind it. Crashes and timeouts still return the frames captured
before they happened, so a bug can be watched up to the moment it bites.

Known limits: captions are mechanical, and the tracer cannot infer `water` or
`region`, so a learner's Trapping Rain Water run renders as bare columns.
Divergence between the learner's run and the reference is not yet flagged.

## V1 content

Two Pointers, six problems: Valid Palindrome, Two Sum II, 3Sum, Container With
Most Water, Trapping Rain Water, Move Zeroes.

## Views

`visualizer.js` dispatches over `views/*.js` by the problem's `view` key.
`cells` (values matter) and `bars` (shape matters, with water and region
overlays) exist. `grid`, `tree`, `graph` and `linked` slot in behind the same
`render(svg, step)` interface plus a `views/manifest.json` entry, which the
validator reads. Not built until a pattern needs one.
