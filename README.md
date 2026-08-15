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
