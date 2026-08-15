"""Authoring tool: run reference solutions with a recorder to produce animation
step traces. NEVER served to the browser — this is the only place solution code
lives in this repo."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Recorder:
    def __init__(self):
        self.steps = []

    def step(self, array, vars, caption, highlight):
        self.steps.append({
            "array": list(array),
            "vars": dict(vars),
            "highlight": list(highlight),
            "caption": caption,
        })


def trace_two_sum_ii(rec):
    numbers, target = [2, 7, 11, 15], 9
    l, r = 0, len(numbers) - 1
    rec.step(numbers, {"l": l, "r": r, "target": target},
             f"Start wide: l at {numbers[l]}, r at {numbers[r]}.", [l, r])
    while l < r:
        total = numbers[l] + numbers[r]
        rec.step(numbers, {"l": l, "r": r, "sum": total, "target": target},
                 f"{numbers[l]} + {numbers[r]} = {total}, target is {target}.", [l, r])
        if total == target:
            rec.step(numbers, {"l": l, "r": r, "sum": total, "target": target},
                     f"Match. Answer is [{l + 1}, {r + 1}] in 1-indexed terms.", [l, r])
            return
        if total > target:
            r -= 1
            rec.step(numbers, {"l": l, "r": r, "target": target},
                     "Sum was too big, so move r inward to a smaller number.", [l, r])
        else:
            l += 1
            rec.step(numbers, {"l": l, "r": r, "target": target},
                     "Sum was too small, so move l inward to a bigger number.", [l, r])


SOLUTIONS = {
    "two-sum-ii": trace_two_sum_ii,
}

# Checkpoints are authored by hand against the recorded trace, keyed by problem id.
# afterStep indexes into the generated steps.
CHECKPOINTS = {
    "two-sum-ii": [
        {"afterStep": 1, "question": "The sum is 17 and the target is 9. Which pointer should move?",
         "options": ["l, rightward", "r, leftward"], "answer": "r, leftward",
         "why": "The sum is too big, so you need a smaller number. Moving l rightward only makes the sum larger; moving r leftward is the only way down."},
        {"afterStep": 3, "question": "Now the sum is 13, still above 9. What happens next?",
         "options": ["l, rightward", "r, leftward"], "answer": "r, leftward",
         "why": "Same reasoning as before — that is the whole invariant. Too big means shrink from the right."},
    ],
}


def main():
    for pid, trace_fn in SOLUTIONS.items():
        path = ROOT / "problems" / f"{pid}.json"
        problem = json.loads(path.read_text())
        rec = Recorder()
        trace_fn(rec)
        problem["steps"] = rec.steps
        problem["checkpoints"] = CHECKPOINTS.get(pid, [])
        path.write_text(json.dumps(problem, indent=2) + "\n")
        print(f"{path.name}: wrote {len(rec.steps)} steps, "
              f"{len(problem['checkpoints'])} checkpoints")
    return 0


if __name__ == "__main__":
    sys.exit(main())
