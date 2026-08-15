<h1 align="center">Stepwise</h1>

<p align="center">
  <strong>Stop memorising algorithms. Start predicting them.</strong><br>
  <a href="https://akshanshkmr.github.io/stepwise/">Try it now →</a>
</p>

---

You know the feeling. You read the solution, it makes perfect sense, you nod
along — and a week later, faced with a slightly different problem, you have
nothing.

That is because reading a solution feels like learning and isn't. Stepwise is
built to stop you doing it.

## How it works

**1. Watch the algorithm run.** Not a diagram of it — a real recorded run,
frame by frame. Trapping Rain Water shows actual walls with water pooling in the
dips. Valid Parentheses shows the stack growing and shrinking as brackets match.

**2. It stops and asks you.** At the moments where the obvious guess is wrong,
the animation halts:

> **The sum is 17 and the target is 9. Which pointer should move?**
> - l, rightward
> - r, leftward

Guess wrong and it explains why, and stays exactly where it is. **You cannot
skip ahead, and you cannot open the editor until you have answered.** That is
the entire point: the useful moment is the one just before you know.

**3. Get hints that make you think.** Three of them, escalating — a nudge, then
the idea that makes it work, then the shape of the loop in plain English. Never
code. You are told what to think about, not what to type.

**4. Write it yourself and run it.** Real Python, real test cases, in your
browser. Nothing to install.

**5. Watch your own code run.** Stuck on why yours fails? Press **Visualize my
run** and your solution is animated in the same picture. A classic:

```
l starts at 0; r starts at 3
s = 17
l: 0 to 1
s = 22      ← moving away from the target
l: 1 to 2
s = 26
```

You see the bug instead of being told about it.

## What's inside

| Pattern | Problems |
| --- | --- |
| **Arrays & Hashing** | Move Zeroes `Easy` |
| **Two Pointers** | Valid Palindrome `Easy` · Two Sum II `Medium` · 3Sum `Medium` · Container With Most Water `Medium` · Trapping Rain Water `Hard` |
| **Stack** | Valid Parentheses `Easy` · Daily Temperatures `Medium` |

Organised by pattern, following the NeetCode structure. The sidebar tracks what
you have solved. More patterns are coming — sliding window, binary search, trees,
graphs, dynamic programming.

## Things worth knowing

**Nothing is stored anywhere but your browser.** No account, no sign-up, no
tracking, no server. Your progress, your code, and your hints live in
`localStorage` and never leave your machine. Clearing your browser data clears
your progress.

**Python only, for now.**

**The first run takes a moment.** Python runs inside the browser, so the first
time you press *Run tests* it downloads about 10 MB. After that it is instant.

**It will not show you the answer.** Not in a hint, not in the animation, not
anywhere. If you want a solution to copy, this is the wrong tool — and that is
deliberate.

## Run it on your own machine

```bash
git clone https://github.com/akshanshkmr/stepwise.git
cd stepwise
python3 serve.py
```

Then open <http://localhost:8000>. No install, no build step, no dependencies.

## Contributing

Problems are plain JSON files, and adding one needs no JavaScript. The full
authoring guide — how to write hints that teach, where to place the prediction
checkpoints, and how the animations get generated — is in
[CLAUDE.md](CLAUDE.md).

```bash
python3 tools/new_problem.py two-sum --pattern "Arrays & Hashing" --difficulty Easy --view cells
```

If a hint would be more useful, a caption clearer, or a checkpoint better
placed, that is the most valuable kind of contribution here. The captions are
the teaching.

## Licence

MIT.
