#!/usr/bin/env python3
"""Scaffold a problem file with every required key present.

    python3 tools/new_problem.py two-sum --pattern "Arrays & Hashing" \\
        --difficulty Easy --view cells

Writes problems/<id>.json with placeholders, then tells you what to fill in.
It deliberately does NOT write steps: those come from tools/record.py, either
auto-traced from a plain solution or from a hand-written trace function.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PATTERNS = json.loads((ROOT / "patterns.json").read_text())["order"]
VIEWS = [k for k in json.loads((ROOT / "views" / "manifest.json").read_text())
         if not k.startswith("_")]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


def next_order(pattern):
    """Problems sort by `order` within a pattern, easiest first."""
    used = []
    for path in (ROOT / "problems").glob("*.json"):
        if path.name == "index.json":
            continue
        p = json.loads(path.read_text())
        if p.get("pattern") == pattern:
            used.append(p.get("order", 0))
    return max(used, default=0) + 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", help="kebab-case id, e.g. valid-parentheses")
    ap.add_argument("--pattern", required=True, choices=PATTERNS, metavar="PATTERN",
                    help="one of: " + "; ".join(PATTERNS))
    ap.add_argument("--difficulty", required=True, choices=DIFFICULTIES)
    ap.add_argument("--view", default="cells", choices=VIEWS,
                    help="cells for values, bars for shape, stack for kept state")
    ap.add_argument("--func", help="function name (default: id with underscores)")
    ap.add_argument("--title", help="display title (default: derived from id)")
    args = ap.parse_args()

    path = ROOT / "problems" / f"{args.id}.json"
    if path.exists():
        print(f"{path.relative_to(ROOT)} already exists", file=sys.stderr)
        return 1

    func = args.func or args.id.replace("-", "_")
    title = args.title or args.id.replace("-", " ").title()

    problem = {
        "id": args.id,
        "title": title,
        "statement": "TODO: the problem, in your own words. Blank line between "
                     "paragraphs. Use `backticks` for identifiers and **bold** "
                     "for the constraint people miss.",
        "examples": [{"input": "TODO", "output": "TODO"}],
        "signature": f"def {func}(TODO):",
        "func": func,
        "pattern": args.pattern,
        "difficulty": args.difficulty,
        "order": next_order(args.pattern),
        "view": args.view,
        "steps": [],
        "checkpoints": [],
        "hints": [
            "TODO rung 1 — a question that points at the idea without naming it.",
            "TODO rung 2 — the invariant, in words. Why the naive move is wrong.",
            "TODO rung 3 — the loop structure in prose. Still no code.",
        ],
        "tests": [
            {"args": ["TODO"], "expect": "TODO"},
        ],
    }
    path.write_text(json.dumps(problem, indent=2) + "\n")

    print(f"wrote {path.relative_to(ROOT)}\n")
    print("Next:")
    print(f"  1. Fill in statement, examples, signature and tests (4+ cases, "
          f"including the edge case people get wrong).")
    print(f"  2. Write the three hints. The validator rejects anything "
          f"code-shaped — see CLAUDE.md.")
    print(f"  3. Add the solution to tools/record.py:")
    print(f"       auto-traced: a plain solve_{func}(...) plus an AUTO entry")
    print(f"       hand-written: trace_{func}(rec) plus a SOLUTIONS entry "
          f"(needed for view overlays)")
    print(f"  4. python3 tools/record.py     # generates steps")
    print(f"  5. Read the frames, write CAPTIONS for the decision points, "
          f"add 2-3 CHECKPOINTS.")
    print(f"  6. python3 tools/validate.py && python3 -m pytest tools/ -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
