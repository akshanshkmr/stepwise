"""Validate every problems/*.json against the CodeTeach content contract."""
import json
import pathlib
import sys

REQUIRED = ["id", "title", "statement", "examples", "signature", "func",
            "view", "steps", "checkpoints", "hints", "tests"]

# The view contract is data, shared with visualizer.js. Adding a view means
# adding views/<name>.js and a manifest entry — this validator needs no edit.
MANIFEST = json.loads((pathlib.Path(__file__).resolve().parent.parent
                       / "views" / "manifest.json").read_text())
VIEWS = {k: v for k, v in MANIFEST.items() if not k.startswith("_")}

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
    if not p["checkpoints"]:
        errors.append("checkpoints must not be empty")

    view = p["view"]
    if view not in VIEWS:
        errors.append(f"unknown view {view!r}; known views: {', '.join(sorted(VIEWS))}")
        return errors
    required_keys = ("vars", "highlight", "caption", *VIEWS[view]["requires"])
    allowed_extra = set(VIEWS[view]["optional"])

    for i, step in enumerate(p["steps"]):
        for key in required_keys:
            if key not in step:
                errors.append(f"steps[{i}] missing key {key!r} required by view {view!r}")
                break
        else:
            n = len(step["array"])
            unknown = set(step) - set(required_keys) - allowed_extra
            if unknown:
                errors.append(
                    f"steps[{i}] has key(s) {sorted(unknown)} that view {view!r} does not "
                    f"declare; add them to views/manifest.json or drop them")
            if "water" in step and len(step["water"]) != n:
                errors.append(
                    f"steps[{i}] water has {len(step['water'])} entries "
                    f"but the array has {n}")
            region = step.get("region")
            if region is not None:
                for edge in ("from", "to"):
                    if not 0 <= region.get(edge, -1) < n:
                        errors.append(
                            f"steps[{i}] region {edge}={region.get(edge)} is not an index "
                            f"into an array of length {n}")
            for h in step["highlight"]:
                if not isinstance(h, int) or not 0 <= h < n:
                    errors.append(f"steps[{i}] highlight index {h} outside array of length {n}")
            for name, v in step["pointers"].items():
                if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v < n:
                    errors.append(f"steps[{i}] pointer {name!r}={v} is not an index into an array of length {n}")

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
