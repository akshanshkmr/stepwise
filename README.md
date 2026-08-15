# Stepwise

**Learn algorithms by predicting them, not by reading solutions.**

Stepwise animates an algorithm frame by frame, stops at the moments where the
obvious guess is wrong, and makes you commit to an answer before it will go on.
Then you write the code yourself and run it against real tests.

It never shows you a solution.

```bash
git clone https://github.com/akshanshkmr/stepwise.git
cd stepwise
python3 serve.py
```

Open <http://localhost:8000>. No install, no build, no account, no server.

---

## Why

Most practice tools optimise for throughput: read the editorial, memorise the
shape, move on. That produces people who can recite two-pointer code and stall
the moment a problem is phrased differently.

Stepwise is built on the opposite bet — that the useful moment is the one just
before you know the answer. So the animation halts and asks:

> The sum is 17 and the target is 9. Which pointer should move?
>
> - `l, rightward`
> - `r, leftward`

Answer wrong and it tells you why, and stays put. **The editor stays locked
until you have answered.** If you never make a prediction, you never get to
type — that is the whole product, and it is deliberately not skippable.

## What you get per problem

- **An animation built from a real run** of the algorithm, not a hand-drawn
  approximation. Every frame is recorded state.
- **Checkpoints** at the decisions where the naive guess fails.
- **Three hints that escalate** — a nudge, then the invariant, then the loop
  structure in words. Never code. The build rejects a hint that looks like code.
- **Your own run, visualised.** Write a solution, press *Visualize my run*, and
  your code is traced and animated in the same view, so you can watch where
  yours diverges. Nothing is injected into your code; a `sys.settrace` hook
  reads its locals.
- **Real tests in the browser** via Pyodide. Wrong answers, exceptions, syntax
  errors and infinite loops all come back as results, never as a hung tab.

## Watch a bug happen

Give Two Sum II an inverted comparison and trace it:

```
l starts at 0; r starts at 3
s = 17
l: 0 to 1
s = 22
l: 1 to 2
s = 26
```

The sum runs *away* from the target 9. You see the bug instead of being told
about it.

## Content

8 problems across 3 patterns, following the NeetCode structure:

| Pattern | Problems |
| --- | --- |
| Arrays & Hashing | Move Zeroes |
| Two Pointers | Valid Palindrome · Two Sum II · 3Sum · Container With Most Water · Trapping Rain Water |
| Stack | Valid Parentheses · Daily Temperatures |

Each carries a difficulty, and the sidebar tracks what you have solved.

## Views

Problems are drawn by the view their data deserves, declared in one line of JSON:

| view | for | example |
| --- | --- | --- |
| `cells` | arrays and strings where the **values** matter | Two Sum II |
| `bars` | histograms and elevation maps where the **shape** matters | Trapping Rain Water — real columns with water pooling in the dips |
| `stack` | problems where the answer depends on **what you kept** | Valid Parentheses |

Adding a shape is one file in `views/` plus a manifest entry. The dispatcher,
the app, the recorder and the validator all read that manifest and need no edit.

## How it is built

No dependencies, no build step, no framework, no backend. Plain ES modules and
the Python standard library. Everything is static; `serve.py` exists only to
serve the app and *not* the reference solutions.

```
index.html  app.js  visualizer.js  runner.js  highlight.js  style.css
views/          one renderer per shape of data, plus manifest.json
problems/       one JSON file per problem — the entire content contract
tracer.py       turns an uninstrumented function into animation frames
tools/          authoring: record.py, validate.py, new_problem.py
dev/            self-check harnesses (these hold reference solutions)
```

The interesting piece is `tracer.py`. It runs an ordinary, uninstrumented
function under `sys.settrace` and derives animation frames from its locals — the
longest list of scalars is the array, integers indexing it are pointers, other
scalars are the readout. **One tracer, two callers:** the browser uses it to
animate your run, and the authoring tools use it to generate a problem's
walkthrough. Two copies would drift, and your run would animate differently from
the walkthrough it is compared against.

Progress, hints, answered checkpoints and your code live in `localStorage`.
Nothing leaves the browser.

## Adding a problem

```bash
python3 tools/new_problem.py two-sum --pattern "Arrays & Hashing" --difficulty Easy --view cells
```

Then write the content, add a plain solution to `tools/record.py`, run
`python3 tools/record.py` to generate the frames, and rewrite the captions at
the decision points. [`CLAUDE.md`](CLAUDE.md) is the full playbook, including the
rules for captions and checkpoints and the traps this repo has already hit.

The generated captions are mechanical (`r: 3 to 2`). Rewriting the handful that
sit at decisions is the real work, and it is the part no tool can do:

> ✅ "The sum is too big, so only shrinking from the right can help."
>
> ❌ "r decreases by 1."

Nothing needs registering — `record.py` rebuilds the index and the sidebar picks
the problem up on reload.

## Checks

```bash
python3 -m pytest tools/ -q     # content contract and authoring tools
python3 tools/validate.py       # every problem file
node dev/test-node.mjs          # gates, storage migration, highlighter escaping
```

CI runs those plus a check that regenerating the traces is a no-op, which
catches a committed animation drifting from the solution that produced it.

Two harnesses need a browser: `dev/test-visualizer.html` and
`dev/test-runner.html`. They contain reference solutions, so `serve.py` hides
them; serve them with plain `python3 -m http.server` when you want to run them.

## Honest limitations

- **The step schema is proven for rows and a stack.** It is *unproven* for a DP
  table or a recursion tree. Those patterns need a new view and probably a
  schema change — worth one throwaway problem before committing to them.
- **The auto-tracer cannot infer view overlays.** It does not know about the
  water in Trapping Rain Water or the stack in Valid Parentheses, so those
  problems are hand-traced, and *your* traced run renders without them.
- **Your run is not diffed against the reference.** You can watch both; nothing
  yet points at the first frame where they part.
- **Auto-generated captions are honest but dull.** The tracer sees `r -= 1`, not
  why.
- **`serve.py` is answer-hiding, not a security boundary.** It stops a curious
  learner browsing to the solutions; it does nothing against anyone who has the
  repo.
- **The prediction gate is an experiment.** Set `GATE_EDITOR = false` in
  `app.js` to turn it off in one line.

## Licence

MIT.
