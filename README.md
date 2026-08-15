# Stepwise

Learn the Two Pointers pattern by watching it work, predicting the next move, and
writing the code yourself. The app never shows you a solution.

## Run it

```bash
python3 serve.py
```

Open <http://localhost:8000>. The app requires an `http://` origin—it fetches problem
files at startup, so `file://` won't work. `serve.py` only serves the app's own files
(index.html, app.js, visualizer.js, runner.js, style.css, problems/) — it's a plain
`http.server` with everything else 404'd, not a security boundary, just answer-hiding
so the URL bar can't reach `dev/` or `tools/`.

## How it teaches

- The animation stops at checkpoints and asks what happens next. You cannot skip past.
- Hints escalate from a nudge to the invariant to the loop structure — always in prose, never code.
- You write the function; it runs in your browser against the real test cases.

## Add a problem

```bash
python3 tools/new_problem.py <id> --pattern "Stack" --difficulty Medium --view stack
```

`CLAUDE.md` is the full playbook — content rules, caption and checkpoint
guidance, and the traps. The short version:

1. In `tools/record.py`, add a plain `solve_<name>(...)` function and an `AUTO`
   entry giving it an example input.
2. Create `problems/<id>.json` with everything except `steps` (leave it `[]`):
   statement, examples, signature, func, pattern, order, view, hints, tests.
   `pattern` must be one of the categories in `patterns.json`; `order` places it
   within that pattern, easiest first.
3. `python3 tools/record.py` — the trace appears, with mechanical captions.
4. Read the generated frames and write real captions for the handful that sit at
   decisions, via `CAPTIONS[<id>][<frame index>]`. This is the teaching, and it
   is the one part no tool can do: the tracer sees `r -= 1`, not *why*.
5. Add 2–3 `CHECKPOINTS` entries at the moments where the naive guess is wrong.
6. `python3 tools/validate.py`. Nothing to register: `record.py` rebuilds
   `problems/index.json` and the sidebar picks the problem up on reload.

`move-zeroes` is the worked example of this path. The five older problems use
the hand-written `trace_<name>(rec)` route instead, which is still supported and
still the only way to emit view-specific overlays such as the bars view's
`water` and `region`.

### Curriculum

`patterns.json` holds the categories in teaching order. Each problem declares one
as its `pattern`, and `tools/record.py` generates `problems/index.json` — the
grouped list the sidebar renders. Categories with no problems yet are shown as
"soon" rather than hidden, so the shape of the curriculum is visible. Adding a
category is an edit to `patterns.json` and nowhere else.

### Views

A problem declares `"view": "cells"` or `"bars"`. Adding a new shape (grid,
tree, graph) means adding `views/<name>.js` and an entry in
`views/manifest.json` — the dispatcher, the app, the recorder and the validator
all read that manifest and need no edit.

## Predict before you write

The editor stays closed until you have answered a problem's checkpoints. This is
the product's claim taken seriously: it used to be possible to ignore the
walkthrough entirely and go straight to the code, which made the anti-memorization
mechanic opt-in. It is an experiment — set `GATE_EDITOR` to `false` in `app.js`
to turn it off in one line. Solved problems stay open.

## Progress

Solving a problem (every test passing once) ticks it in the sidebar and advances
its pattern's count and the bar at the bottom. Progress, revealed hints, answered
checkpoints, your code, and which sections you collapsed all live in
`localStorage` — there are no accounts and nothing leaves the browser.

## Checks

```bash
python3 -m pytest tools/ -v && python3 tools/validate.py
```

`node dev/test-node.mjs` runs the browser-free logic — the two gates, the storage
migration, and the highlighter's escaping. CI runs that plus the Python suites and
checks that regenerating the traces is a no-op.

Browser checks need the dev harnesses, which `serve.py` deliberately hides. Run the
plain, everything-exposed server instead — dev-only, since it also serves the
reference solutions in `dev/` and `tools/`:

```bash
python3 -m http.server 8000
```

Then open `/dev/test-visualizer.html` and `/dev/test-runner.html`; every line must say PASS.
(The `dev/` harnesses hold reference solutions — they are not part of the app.)
