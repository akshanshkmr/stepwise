"""Validate every problems/*.json against the CodeTeach content contract."""
import json
import pathlib
import sys

REQUIRED = ["id", "title", "statement", "examples", "signature", "func",
            "steps", "checkpoints", "hints", "tests"]

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

    for i, step in enumerate(p["steps"]):
        for key in ("array", "pointers", "vars", "highlight", "caption"):
            if key not in step:
                errors.append(f"steps[{i}] missing key: {key}")
                break
        else:
            n = len(step["array"])
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
