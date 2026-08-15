# CodeTeach

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

1. Add a `trace_<name>(rec)` function and a `CHECKPOINTS` entry in `tools/record.py`.
2. Create `problems/<id>.json` with everything except `steps` and `checkpoints`.
3. `python3 tools/record.py` to generate the trace.
4. `python3 tools/validate.py` to check it.
5. Add the id to `PROBLEMS` in `app.js`.

## Checks

```bash
python3 -m pytest tools/ -v && python3 tools/validate.py
```

Browser checks need the dev harnesses, which `serve.py` deliberately hides. Run the
plain, everything-exposed server instead — dev-only, since it also serves the
reference solutions in `dev/` and `tools/`:

```bash
python3 -m http.server 8000
```

Then open `/dev/test-visualizer.html` and `/dev/test-runner.html`; every line must say PASS.
(The `dev/` harnesses hold reference solutions — they are not part of the app.)
