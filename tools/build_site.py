#!/usr/bin/env python3
"""Assemble the deployable site into _site/.

GitHub Pages serves whatever you hand it, so this must hand it the app and
nothing else — tools/ holds every reference solution and dev/ holds two more.

The rule is not restated here: it is imported from serve.py, so the local
server and the deployed site cannot disagree about what counts as the app.
That mattering is not hypothetical — three features shipped broken because a
file was missing from that list.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import serve  # noqa: E402  — the single source of truth for "what is the app"

OUT = ROOT / "_site"

# Anything matching these must never reach the site, whatever the rules say.
FORBIDDEN_DIRS = {"tools", "dev", "docs", ".github", ".git"}


def app_files():
    """Every path serve.py would serve, as (source, relative destination)."""
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts[0] in FORBIDDEN_DIRS or rel.parts[0].startswith("."):
            continue
        # serve.py speaks in URL paths.
        if serve.AppOnlyHandler._allowed(None, "/" + rel.as_posix()):
            yield path, rel


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    copied = []
    for src, rel in app_files():
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(rel.as_posix())

    # Pages runs Jekyll by default, which would drop files it does not like.
    (OUT / ".nojekyll").write_text("")

    if "index.html" not in copied:
        print("refusing to deploy: no index.html in the built site", file=sys.stderr)
        return 1

    leaked = [p for p in copied
              if p.startswith(("tools/", "dev/", "docs/"))]
    if leaked:
        print(f"refusing to deploy: solution files leaked: {leaked}", file=sys.stderr)
        return 1

    print(f"built _site/ with {len(copied)} files")
    for p in copied:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
