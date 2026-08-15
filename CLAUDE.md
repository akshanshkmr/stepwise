# Stepwise — working in this repo

A static app that teaches algorithm patterns by animating them, stopping to make
the learner predict the next move, and giving prose hints. **It never shows
solution code.** That constraint is the product, not a preference.

## Ground rules

- **No dependencies, no build step, no framework.** Plain ES modules and Python
  stdlib. `pytest` is the only dependency, and only for the tools.
- **No external requests at runtime.** Pyodide from its pinned CDN is the sole
  exception. Do not add a font CDN, a highlighter library, or an icon pack —
  each of those has already been considered and rejected.
- **Solutions live in `tools/record.py` and `dev/` only.** `serve.py` serves the
  app and nothing else. Three separate features shipped broken because a new
  file was not reachable — if something 404s in the browser, check `serve.py`
  before debugging anything else.
- **Adding a problem must not require JavaScript.** If it does, the design is
  wrong; say so rather than working around it.

## Adding a problem

```bash
python3 tools/new_problem.py <id> --pattern "Stack" --difficulty Medium --view stack
```

That writes `problems/<id>.json` with every required key. Then:

**1. Fill in the content.** Statement in your own words, 2–3 examples, and
**4+ tests including the edge case people actually get wrong** (empty input, a
two-element array, all-duplicates, no-solution). Tests are compared with `==`
after a JSON round-trip, so a returned tuple matches a list expectation — but
ordering still matters. If a problem admits several valid orderings, say which
one you require in the statement.

**2. Write three hints that escalate.** Nudge → the invariant → the loop
structure in words. Never code.

The validator rejects code-shaped hints. It matches *shapes*, not words, so
"keep taking the most recent day for as long as today is warmer" is fine while
`for i in range(n)` is not. Rejected shapes: code fences, `def name(`,
`for x in`, `while x <`, `return [`, `x += y`, `nums[i]`, `f()`. If it rejects
prose that is genuinely prose, tighten the pattern in `tools/validate.py` —
don't reword good writing into worse writing.

**3. Add the solution to `tools/record.py`.** Two routes:

*Auto-traced (default).* Write a plain, uninstrumented `solve_<name>(...)` and
register it in `AUTO` with an example input. `tracer.py` derives frames from its
locals: the longest list of scalars is the array, ints indexing it are pointers,
other scalars become the readout.

*Hand-written (required for view overlays).* Write `trace_<name>(rec)` calling
`rec.step(array, pointers, caption, highlight, vars=..., **extra)` and register
it in `SOLUTIONS`. You need this when the view takes data the tracer cannot
infer — `water`/`region` for `bars`, `stack` for `stack` — or when the input and
a working list would confuse the "longest list" heuristic, which is exactly the
case for every stack problem.

**4. `python3 tools/record.py`**, then **read the generated frames**.

**5. Write the captions that matter.** The tracer's captions are mechanical
("`r: 3 to 2`"). Override the decision points via `CAPTIONS[<id>][<frame index>]`.
A caption must say **why** a move happened, never restate the code:

> ✅ "The sum is too big, so only shrinking from the right can help."
> ❌ "r decreases by 1."

Auto-traced frames put the blandest caption on the most important moment — a
swap shows as "The array changed." Those are the ones to rewrite first.

**6. Add 2–3 checkpoints.** These are the product. Rules learned the hard way:

- Never on the first move — nothing has been learned yet.
- Never the same decision twice in one problem.
- Put them where **the naive guess is wrong**. Container With Most Water gates
  exactly at "move the taller wall", because that is the tempting error.
- Distractors must be *plausible and comparable in length*. An obviously silly
  short option lets someone pass on prose style alone, which defeats the point.
  Three options beat two where a real second misconception exists.
- `afterStep` must land on a frame whose state matches the question's wording.
  If the question says "the sum is 17", the frame must show 17.

**7. Check it.**

```bash
python3 tools/record.py && python3 tools/validate.py && python3 -m pytest tools/ -q
node dev/test-node.mjs
```

Nothing to register anywhere: `record.py` rebuilds `problems/index.json` and the
sidebar picks the problem up on reload.

**8. Drive it in a browser.** Step to the end, answer each checkpoint wrong once
then right, and paste a correct solution to confirm the tests pass. An animation
that reads badly is fixed in the trace's captions or step granularity — never in
the visualizer.

## Views

A problem declares `"view"`. Adding a shape means one file in `views/` plus an
entry in `views/manifest.json`; the dispatcher, app, recorder and validator all
read that manifest and need no edit.

| view | for | extra step keys |
|---|---|---|
| `cells` | arrays and strings where the **values** matter | — |
| `bars` | histograms and elevation maps where the **shape** matters | `water`, `region` |
| `stack` | problems where the answer depends on **what you kept** | `stack` |

Still unbuilt: `grid`, `tree`, `graph`, `linked`. Before committing to a pattern
that needs one, build one throwaway problem first — the step schema is proven for
rows and a stack, and is **unproven** for a DP table or a recursion tree.

## Difficulty and curriculum

`difficulty` is `Easy`/`Medium`/`Hard`. `pattern` must be one of the categories
in `patterns.json`, and `order` places the problem within it, easiest first.
Patterns with no problems collapse into a single "N more patterns" line.

## The prediction gate

The editor stays locked until the learner answers a problem's checkpoints. This
is the product's central claim, made unavoidable — it used to be skippable, which
made the whole mechanic opt-in. It sits behind `GATE_EDITOR` in `app.js` so the
experiment can be ended in one line. Solved problems stay unlocked.

## Testing

- `pytest tools/` — content contract and the authoring tools.
- `node dev/test-node.mjs` — browser-free logic: both gates, storage migration,
  highlighter escaping. Runs in CI.
- `dev/test-visualizer.html`, `dev/test-runner.html` — need a browser and a human.
  Serve them with plain `python3 -m http.server` (they hold reference solutions,
  so `serve.py` hides them).

Add a check for anything non-trivial. When a bug is found, the fix is not done
until something would fail if it came back.

## Things that have bitten before

- A display rule beating `[hidden]`, showing a panel that should be closed.
- `.ghost`'s muted colour making checkpoint options look disabled.
- The global `code {}` chip styling leaking onto the editor's highlight overlay.
- A new file missing from `serve.py`, so the browser silently ran a cached copy.
- Setting `open` on `<details>` during construction fires `toggle`, which
  persisted a collapse the reader never asked for.
- The tracer not deep-copying arguments, so in-place solutions disagreed with
  themselves on a second run.
