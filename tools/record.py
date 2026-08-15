"""Authoring tool: run reference solutions with a recorder to produce animation
step traces. NEVER served to the browser — this is the only place solution code
lives in this repo."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import tracer  # noqa: E402  — same tracer the browser uses on the learner's run


def auto_trace(fn, args, func_name=None):
    """Generate steps from an ordinary solution, no rec.step calls needed.

    The captions come out mechanical ("r: 3 to 2"). That is the deal: this gets
    a problem animating in minutes, and an author then rewrites the handful of
    captions that sit at decision points, where the WHY is the teaching. Use
    CAPTIONS below to override them by frame index.
    """
    out = tracer.trace_call(fn, args, func_name or fn.__name__)
    if out["error"]:
        raise RuntimeError(f"{fn.__name__} failed while tracing: {out['error']}")
    if not out["steps"]:
        raise RuntimeError(f"{fn.__name__} produced no frames — nothing changed to watch")
    return out["steps"]


class Recorder:
    def __init__(self):
        self.steps = []

    def step(self, array, pointers, caption, highlight, vars=None, **extra):
        """pointers: name -> index into array (drawn as arrows).
        vars: name -> any scalar the caption talks about (drawn as a readout).
        extra: view-specific keys, e.g. the bars view's `water` and `region`.
        Whatever a view declares in views/manifest.json is passed straight
        through, so a new view needs no change to this recorder."""
        step = {
            "array": list(array),
            "pointers": dict(pointers),
            "vars": dict(vars or {}),
            "highlight": list(highlight),
            "caption": caption,
        }
        step.update(extra)
        self.steps.append(step)


def trace_two_sum_ii(rec):
    numbers, target = [2, 7, 11, 15], 9
    l, r = 0, len(numbers) - 1
    rec.step(numbers, {"l": l, "r": r},
             f"Start wide: l at {numbers[l]}, r at {numbers[r]}.", [l, r],
             vars={"target": target})
    while l < r:
        total = numbers[l] + numbers[r]
        rec.step(numbers, {"l": l, "r": r},
                 f"{numbers[l]} + {numbers[r]} = {total}, target is {target}.", [l, r],
                 vars={"sum": total, "target": target})
        if total == target:
            rec.step(numbers, {"l": l, "r": r},
                     f"Match. Answer is [{l + 1}, {r + 1}] in 1-indexed terms.", [l, r],
                     vars={"sum": total, "target": target})
            return
        if total > target:
            r -= 1
            rec.step(numbers, {"l": l, "r": r},
                     "Sum was too big, so move r inward to a smaller number.", [l, r],
                     vars={"target": target})
        else:
            l += 1
            rec.step(numbers, {"l": l, "r": r},
                     "Sum was too small, so move l inward to a bigger number.", [l, r],
                     vars={"target": target})


def _walk_palindrome(rec, s, opening):
    arr = list(s)
    l, r = 0, len(arr) - 1
    rec.step(arr, {"l": l, "r": r}, opening, [l, r], vars={"verdict": "unknown"})
    while l < r:
        if not arr[l].isalnum():
            l += 1
            rec.step(arr, {"l": l, "r": r},
                     "That character isn't a letter or digit, so skip it and slide l right.", [l, r],
                     vars={"verdict": "unknown"})
            continue
        if not arr[r].isalnum():
            r -= 1
            rec.step(arr, {"l": l, "r": r},
                     "That character isn't a letter or digit, so skip it and slide r left.", [l, r],
                     vars={"verdict": "unknown"})
            continue
        if arr[l].lower() != arr[r].lower():
            rec.step(arr, {"l": l, "r": r},
                     f"'{arr[l]}' and '{arr[r]}' disagree, so this can't be a palindrome.", [l, r],
                     vars={"verdict": "false"})
            return
        l += 1
        r -= 1
        rec.step(arr, {"l": l, "r": r}, "Those matched, so move both markers inward.", [l, r],
                 vars={"verdict": "unknown"})
    rec.step(arr, {"l": l, "r": r},
             "Markers crossed without ever disagreeing, so it is a palindrome.", [l, r],
             vars={"verdict": "true"})


def trace_valid_palindrome(rec):
    # Two runs: one that fails on a mismatch, one that survives the crossing.
    _walk_palindrome(rec, "race a car", "Start with one marker at each end.")
    _walk_palindrome(rec, "ab_a",
                     "New string, same method: markers at each end of \"ab_a\".")


def trace_container_with_most_water(rec):
    height = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    l, r = 0, len(height) - 1
    best = 0
    rec.step(height, {"l": l, "r": r}, "Start as wide as possible: one wall at each end.",
             [l, r], vars={"best": best},
                 region={"from": l, "to": r, "level": min(height[l], height[r])})
    while l < r:
        area = min(height[l], height[r]) * (r - l)
        best = max(best, area)
        rec.step(height, {"l": l, "r": r},
                 f"Width {r - l} times the shorter wall ({min(height[l], height[r])}) = {area}. Best so far: {best}.",
                 [l, r], vars={"area": area, "best": best},
                 region={"from": l, "to": r, "level": min(height[l], height[r])})
        if height[l] < height[r]:
            l += 1
            rec.step(height, {"l": l, "r": r},
                     "The left wall was shorter, so it was the one capping the water — move it inward looking for something taller.",
                     [l, r], vars={"best": best},
                 region={"from": l, "to": r, "level": min(height[l], height[r])})
        elif height[l] > height[r]:
            r -= 1
            rec.step(height, {"l": l, "r": r},
                     "The right wall was shorter, so it was the one capping the water — move it inward looking for something taller.",
                     [l, r], vars={"best": best},
                 region={"from": l, "to": r, "level": min(height[l], height[r])})
        else:
            l += 1
            rec.step(height, {"l": l, "r": r},
                     "The walls are tied, so either side is equally responsible for the cap — move the left one inward.",
                     [l, r], vars={"best": best},
                 region={"from": l, "to": r, "level": min(height[l], height[r])})
    rec.step(height, {"l": l, "r": r}, f"Markers met. Best area found was {best}.",
             [l, r], vars={"best": best},
                 region={"from": l, "to": r, "level": min(height[l], height[r])})


def trace_three_sum(rec):
    nums = sorted([-1, 0, 1, 2, -1, -4])
    n = len(nums)
    found = 0
    i = 0
    while i < n - 2:
        if nums[i] > 0:
            rec.step(nums, {"i": i},
                     "This fixed number is positive; the array is sorted, so every remaining sum can only be larger. Stop.",
                     [i], vars={"found": found})
            break
        if i > 0 and nums[i] == nums[i - 1]:
            rec.step(nums, {"i": i},
                     "This fixed number repeats the previous one — skip it so we don't rediscover the same triples.",
                     [i], vars={"found": found})
            i += 1
            continue
        l, r = i + 1, n - 1
        rec.step(nums, {"i": i, "l": l, "r": r}, "Fix this number, then scan the rest with l and r.",
                 [i, l, r], vars={"found": found})
        while l < r:
            total = nums[i] + nums[l] + nums[r]
            if total == 0:
                found += 1
                rec.step(nums, {"i": i, "l": l, "r": r},
                         "These three sum to zero — record the triple, then move both markers inward to keep looking.",
                         [i, l, r], vars={"total": total, "found": found})
                l += 1
                r -= 1
                while l < r and nums[l] == nums[l - 1]:
                    l += 1
                while l < r and nums[r] == nums[r + 1]:
                    r -= 1
                if l < r:
                    rec.step(nums, {"i": i, "l": l, "r": r}, "Markers moved inward past the match.",
                             [i, l, r], vars={"total": nums[i] + nums[l] + nums[r], "found": found})
            elif total < 0:
                l += 1
                rec.step(nums, {"i": i, "l": l, "r": r},
                         "The total is negative, so shrink from the left to reach for a bigger number.",
                         [i, l, r], vars={"total": total, "found": found})
            else:
                r -= 1
                rec.step(nums, {"i": i, "l": l, "r": r},
                         "The total is positive, so shrink from the right to reach for a smaller number.",
                         [i, l, r], vars={"total": total, "found": found})
        i += 1
    last = min(i, n - 1)
    rec.step(nums, {"i": last}, f"Done scanning. Found {found} triple(s).", [last],
             vars={"found": found})


def trace_trapping_rain_water(rec):
    height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    l, r = 0, len(height) - 1
    left_max = right_max = water = 0
    depths = [0] * len(height)
    rec.step(height, {"l": l, "r": r},
             "One marker at each end; track the tallest wall seen so far from each side.", [l, r],
             vars={"left_max": left_max, "right_max": right_max, "water": water},
             water=list(depths))

    def scalars():
        return {"left_max": left_max, "right_max": right_max, "water": water}

    while l < r:
        if height[l] < height[r]:
            if height[l] >= left_max:
                same = height[l] == left_max
                left_max = height[l]
                rec.step(height, {"l": l, "r": r},
                         f"height[l]={height[l]} "
                         + ("matches the tallest-from-the-left wall so far"
                            if same else "is a new tallest-from-the-left wall")
                         + f" ({left_max}); nothing traps here.",
                         [l, r], vars=scalars(), water=list(depths))
            else:
                gained = left_max - height[l]
                water += gained
                depths[l] = gained
                rec.step(height, {"l": l, "r": r},
                         f"height[l]={height[l]} is shorter than the tallest left wall so far ({left_max}); "
                         f"{gained} unit(s) of water sit here (running total {water}).", [l, r],
                         vars=scalars(), water=list(depths))
            l += 1
            rec.step(height, {"l": l, "r": r},
                     "The left side had the shorter running wall, so it was the one deciding the water level — move it inward.",
                     [l, r], vars=scalars(), water=list(depths))
        else:
            if height[r] >= right_max:
                same = height[r] == right_max
                right_max = height[r]
                rec.step(height, {"l": l, "r": r},
                         f"height[r]={height[r]} "
                         + ("matches the tallest-from-the-right wall so far"
                            if same else "is a new tallest-from-the-right wall")
                         + f" ({right_max}); nothing traps here.",
                         [l, r], vars=scalars(), water=list(depths))
            else:
                gained = right_max - height[r]
                water += gained
                depths[r] = gained
                rec.step(height, {"l": l, "r": r},
                         f"height[r]={height[r]} is shorter than the tallest right wall so far ({right_max}); "
                         f"{gained} unit(s) of water sit here (running total {water}).", [l, r],
                         vars=scalars(), water=list(depths))
            r -= 1
            rec.step(height, {"l": l, "r": r},
                     "The right side had the shorter running wall, so it was the one deciding the water level — move it inward.",
                     [l, r], vars=scalars(), water=list(depths))
    rec.step(height, {"l": l, "r": r}, f"Markers met. Total trapped water: {water}.", [l, r],
             vars=scalars(), water=list(depths))


# --- auto-traced problems -------------------------------------------------
# No rec.step calls: an ordinary solution, traced automatically. This is the
# path a new problem should take.

def solve_move_zeroes(nums):
    slot = 0
    for scan in range(len(nums)):
        if nums[scan] != 0:
            nums[slot], nums[scan] = nums[scan], nums[slot]
            slot += 1
    return nums


AUTO = {
    "move-zeroes": (solve_move_zeroes, [[0, 1, 0, 3, 12]]),
}

# Only the frames where the WHY matters. Everything else keeps the tracer's
# mechanical caption, which is accurate if bland.
CAPTIONS = {
    "move-zeroes": {
        0: "Both markers will start at the front — this pair moves at different speeds rather than from opposite ends.",
        1: "slot starts at 0: the first position that still needs filling.",
        2: "scan starts at 0 too, and it is the one that will visit every element.",
        3: "nums[0] was a zero, so nothing was placed. scan moves on alone and slot stays waiting.",
        4: "nums[scan] is 1, a non-zero, so it swaps into the slot — and the zero that was there gets pushed out to where scan is.",
        5: "Only now does slot advance: position 0 is settled, so the next non-zero belongs at 1.",
        7: "Another zero at index 2, so scan passes over it and slot holds its place again.",
        8: "3 is non-zero, so it swaps down into the waiting slot.",
        11: "12 swaps into the last waiting slot, and the zeros have been pushed to the back without ever being moved deliberately.",
        12: "Every element has been scanned. Everything left of slot is settled, and the zeros fell to the end on their own.",
    },
}

# Checkpoints are authored by hand against the recorded trace, keyed by problem
# id. afterStep indexes into the generated steps.

SOLUTIONS = {
    "two-sum-ii": trace_two_sum_ii,
    "valid-palindrome": trace_valid_palindrome,
    "container-with-most-water": trace_container_with_most_water,
    "3sum": trace_three_sum,
    "trapping-rain-water": trace_trapping_rain_water,
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
    "valid-palindrome": [
        {"afterStep": 3, "question": "r now points at a space. What should happen?",
         "options": ["Compare it directly against the character at l", "Skip it — slide r left and check again"],
         "answer": "Skip it — slide r left and check again",
         "why": "Only letters and digits count toward the comparison. A space carries no information either way, so it's simply skipped."},
        {"afterStep": 4, "question": "l points at 'e' and r points at 'a'. What does that tell you about the answer?",
         "options": ["Nothing yet — keep sliding r left until it finds a character that matches 'e'",
                     "Nothing yet — the markers must actually cross before any verdict is possible",
                     "It is settled: a mirrored pair disagrees, so the answer is false"],
         "answer": "It is settled: a mirrored pair disagrees, so the answer is false",
         "why": "Every mirrored pair has to agree. Searching onward for a matching character would be solving a different problem, and waiting for the markers to cross cannot un-do a disagreement, so you can stop the moment one appears."},
    ],
    "container-with-most-water": [
        {"afterStep": 3, "question": "height[l]=8 and height[r]=7. Which wall should move?",
         "options": ["l, the taller wall (8)", "r, the shorter wall (7)"],
         "answer": "r, the shorter wall (7)",
         "why": "The shorter wall is what caps the water. Moving the taller wall only shrinks the width while the cap stays the same or gets worse; moving the shorter wall is the only move that could find something taller."},
        {"afterStep": 7, "question": "The walls are tied (8 and 8). Which pointer(s) could move without losing correctness?",
         "options": ["Only r may move", "Either l or r works"],
         "answer": "Either l or r works",
         "why": "When both walls are equally tall, either one is equally responsible for the cap, so moving either marker inward keeps the search correct."},
    ],
    "3sum": [
        {"afterStep": 4, "question": "The total is still negative and l has caught up to r. What happens next?",
         "options": ["Move r one more step left so the two markers can swap sides and finish the stretch",
                     "Move l one more step right, since the total is negative and needs a bigger number",
                     "Stop this pass — no room is left between the markers — and move to the next fixed number"],
         "answer": "Stop this pass — no room is left between the markers — and move to the next fixed number",
         "why": "The markers have to bracket a pair. Once they meet there is nothing between them, so neither moving l nor moving r can produce a new pair for this fixed number; the sweep moves on."},
        {"afterStep": 6, "question": "The total is exactly zero. What should happen to the markers?",
         "options": ["Move only l inward, since the triple is already recorded and r still bounds the stretch",
                     "Move both markers inward, past any repeats, and keep sweeping this fixed number",
                     "Leave the markers and advance the fixed number, since a hit ends this stretch"],
         "answer": "Move both markers inward, past any repeats, and keep sweeping this fixed number",
         "why": "With the sum already at zero, moving only one marker can only overshoot in one direction, and this fixed number may still bracket other pairs — so move both inward and continue rather than abandoning the stretch."},
        {"afterStep": 8, "question": "The next fixed number, nums[2], equals nums[1] (both -1). What should happen when the sweep reaches it?",
         "options": ["Process it normally — it might find a new triple", "Skip it — any triple it starts would duplicate one already found"],
         "answer": "Skip it — any triple it starts would duplicate one already found",
         "why": "Fixing the same value twice in a row explores the same territory nums[1] already covered, producing duplicate triples."},
    ],
    "trapping-rain-water": [
        {"afterStep": 6, "question": "height[l]=0, and the tallest left wall seen so far is 1. What happens here?",
         "options": ["Nothing traps — height[l] becomes the new left_max", "Water traps here, up to the left_max"],
         "answer": "Water traps here, up to the left_max",
         "why": "This bar is shorter than the tallest wall already seen on the left, so water sits on top of it up to that wall's height."},
        {"afterStep": 10, "question": "height[l]=2 and height[r]=1. Which side gets processed next?",
         "options": ["l, the taller side", "r, the shorter side"],
         "answer": "r, the shorter side",
         "why": "The side with the lower current bar is the one whose water level is already decided — the far side is guaranteed at least as tall, so it can't be the limiting wall."},
    ],
    "move-zeroes": [
        {"afterStep": 3,
         "question": "scan just passed a zero and slot did not move. Why not?",
         "options": [
             "slot only advances once something has actually been placed there",
             "slot advances every time scan does, just one step behind",
             "slot is waiting for scan to reach the end of the array"],
         "answer": "slot only advances once something has actually been placed there",
         "why": "slot marks the first unfilled position. If it advanced past a zero, that zero would be treated as settled and would never reach the back."},
        {"afterStep": 4,
         "question": "A non-zero was just swapped into slot. What happens to slot now?",
         "options": [
             "it advances, because that position is now settled",
             "it stays, because the swap may need to be repeated",
             "it jumps to wherever scan is"],
         "answer": "it advances, because that position is now settled",
         "why": "The slot has been filled with the correct next value, so the boundary of the settled region moves forward by exactly one."},
    ],
}


def main():
    for pid in list(SOLUTIONS) + list(AUTO):
        trace_fn = SOLUTIONS.get(pid)
        path = ROOT / "problems" / f"{pid}.json"
        problem = json.loads(path.read_text())

        if pid in AUTO:
            # Auto-traced: an ordinary solution plus caption overrides.
            fn, args = AUTO[pid]
            steps = auto_trace(fn, args)
            for i, text in CAPTIONS.get(pid, {}).items():
                if not 0 <= i < len(steps):
                    raise IndexError(
                        f"{pid}: caption override {i} is outside the {len(steps)} "
                        f"frames the tracer produced")
                steps[i]["caption"] = text
            written, kind = steps, f"auto ({len(CAPTIONS.get(pid, {}))} captions written)"
        else:
            rec = Recorder()
            trace_fn(rec)
            written, kind = rec.steps, "hand"

        problem["steps"] = written
        problem["checkpoints"] = CHECKPOINTS.get(pid, [])
        path.write_text(json.dumps(problem, indent=2) + "\n")
        print(f"{path.name}: wrote {len(written)} steps, "
              f"{len(problem['checkpoints'])} checkpoints [{kind}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
