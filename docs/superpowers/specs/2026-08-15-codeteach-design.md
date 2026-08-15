# CodeTeach — Design

Date: 2026-08-15

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

Static site. No backend, no build step, no framework. Opening `index.html`
from disk or any static host runs the app.

```
index.html        layout + pane markup
style.css
app.js            state machine: load problem, drive player, gate checkpoints, reveal hints
visualizer.js     SVG array renderer: boxes, pointer arrows, highlights, caption
runner.js         lazy Pyodide load, execute learner code against tests
problems/*.json   one file per problem — the entire content contract
tools/record.py   authoring-time step recorder (not shipped to the browser)
tools/validate.py the one runnable check
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
    { "array": [2,7,11,15], "vars": {"l":0,"r":3,"sum":17},
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

## Authoring flow

`tools/record.py` holds the reference solutions and a tiny recorder helper.
Running it executes each solution against its example input, capturing a step
each time the recorder is called, and writes `steps` into the problem JSON.
The reference solutions live only in this file and are never served.

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
`steps` non-empty; every `checkpoints[].afterStep` within `steps` range; every
`answer` present in its `options`; `tests` non-empty; no fenced code or `def ` in
any hint. Run it after any content edit.

## V1 content

Two Pointers, five problems: Valid Palindrome, Two Sum II, 3Sum,
Container With Most Water, Trapping Rain Water.

## Open scaling question (deferred)

Patterns needing a tree, grid, or graph visualizer require a second renderer
behind the same `render(step)` interface. Deliberately out of scope until the
array pattern is validated.
