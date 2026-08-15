import { render } from "./visualizer.js";
import { ready, run, trace } from "./runner.js";

const PROBLEMS = ["valid-palindrome", "two-sum-ii", "container-with-most-water", "3sum", "trapping-rain-water", "move-zeroes"];

/** Index of the checkpoint that blocks advancing past `index`, or null. */
export function nextBlockingCheckpoint(checkpoints, answered, index) {
  for (let i = 0; i < checkpoints.length; i++) {
    if (checkpoints[i].afterStep === index && !answered.has(i)) return i;
  }
  return null;
}

if (document.getElementById("viz")) {

const $ = (id) => document.getElementById(id);
let problem = null, index = 0, answered = new Set(), hintsUsed = 0, code = "";
// Non-null while showing the learner's own traced run instead of the reference.
let mine = null;

const storageKey = () => `codeteach:${problem.id}`;

function save() {
  localStorage.setItem(storageKey(),
    JSON.stringify({ answered: [...answered], hintsUsed, code: $("editor").value }));
}

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(storageKey()) ?? "{}");
    answered = new Set(raw.answered ?? []);
    hintsUsed = raw.hintsUsed ?? 0;
    code = raw.code ?? "";
  } catch { answered = new Set(); hintsUsed = 0; code = ""; }
}

async function loadProblem(id) {
  try {
    const res = await fetch(`problems/${id}.json`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    problem = await res.json();
  } catch (err) {
    $("caption").textContent =
      `Could not load the problem "${id}" (${err.message}). Serve this app over http:// and reload the page.`;
    return;
  }
  index = 0;
  mine = null;
  load();
  $("title").textContent = problem.title;
  $("statement").innerHTML = problem.statement
    .split("\n\n").map(p => `<p>${inline(p)}</p>`).join("");
  $("examples").innerHTML = problem.examples
    .map(e => `<div>Input: ${e.input}<br>Output: ${e.output}</div>`).join("");
  $("editor").value = code || `${problem.signature}\n${INDENT}`;
  drawGutter();
  $("scrub").max = String(problem.steps.length - 1);
  $("results").replaceChildren();
  renderHints();
  draw();
}

// ponytail: bold + inline code only. Problem statements are ours, not user input.
const inline = (s) => s
  .replace(/&/g, "&amp;").replace(/</g, "&lt;")
  .replace(/`([^`]+)`/g, "<code>$1</code>")
  .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

function renderHints() {
  $("hints").innerHTML = problem.hints.slice(0, hintsUsed)
    .map(h => `<p>${inline(h)}</p>`).join("");
  $("hint-count").textContent = `${hintsUsed} of ${problem.hints.length} hints used`;
  $("hint-btn").disabled = hintsUsed >= problem.hints.length;
}

function draw() {
  // `mine` holds the learner's own traced run. The reference walkthrough in
  // problem.steps is never overwritten — switching back is just dropping it.
  const steps = mine ?? problem.steps;
  const checkpoints = mine ? [] : problem.checkpoints;

  render($("viz"), steps[index], problem.view);
  $("caption").textContent = steps[index].caption ?? "";
  $("step-count").textContent = `${index + 1} / ${steps.length}`;
  $("scrub").max = String(steps.length - 1);
  $("scrub").value = String(index);
  $("mine-bar").hidden = !mine;

  const blocked = nextBlockingCheckpoint(checkpoints, answered, index);
  const atEnd = index >= steps.length - 1;
  $("next").disabled = blocked !== null || atEnd;
  $("last").disabled = blocked !== null || atEnd;
  $("scrub").disabled = blocked !== null;
  $("prev").disabled = index === 0;
  $("first").disabled = index === 0;

  if (blocked === null) { $("checkpoint").hidden = true; return; }
  const cp = problem.checkpoints[blocked];
  $("checkpoint").hidden = false;
  $("cp-question").textContent = cp.question;
  $("cp-feedback").textContent = "";
  $("cp-options").replaceChildren(...cp.options.map(opt => {
    const b = document.createElement("button");
    b.className = "ghost";
    b.textContent = opt;
    b.onclick = () => {
      if (opt === cp.answer) {
        answered.add(blocked);
        save();
        draw();
        $("checkpoint").hidden = false;
        $("cp-question").textContent = "Right.";
        $("cp-options").replaceChildren();
        $("cp-feedback").textContent = cp.why;
      } else {
        $("cp-feedback").textContent = `Not quite. ${cp.why}`;
      }
    };
    return b;
  }));
}

function go(i) {
  const steps = mine ?? problem.steps;
  const checkpoints = mine ? [] : problem.checkpoints;
  const target = Math.max(0, Math.min(steps.length - 1, i));
  // Never step past an unanswered gate.
  for (let k = index; k < target; k++) {
    if (nextBlockingCheckpoint(checkpoints, answered, k) !== null) {
      index = k; draw(); return;
    }
  }
  index = target;
  draw();
}

function showMine(steps) {
  mine = steps;
  index = 0;
  draw();
}

$("next").onclick = () => go(index + 1);
$("prev").onclick = () => go(index - 1);
$("first").onclick = () => go(0);
$("last").onclick = () => go((mine ?? problem.steps).length - 1);
$("scrub").oninput = (e) => go(Number(e.target.value));
$("hint-btn").onclick = () => { hintsUsed++; save(); renderHints(); };
$("editor").oninput = () => { save(); drawGutter(); };
$("editor").onscroll = () => { $("gutter").scrollTop = $("editor").scrollTop; };

function drawGutter() {
  const lines = $("editor").value.split("\n").length;
  $("gutter").textContent = Array.from({ length: lines }, (_, i) => i + 1).join("\n");
}

// ponytail: Tab and auto-indent only — the two things a plain textarea gets
// wrong for Python. No syntax highlighting: that needs a real editor library,
// and this stays a zero-dependency static page. Swap in CodeMirror if you
// ever want colour, not before.
const INDENT = "    ";

$("editor").onkeydown = (e) => {
  const ed = e.target;
  const { selectionStart: a, selectionEnd: b, value: v } = ed;

  const replace = (text, caret) => {
    ed.setRangeText(text, a, b, "end");
    if (caret !== undefined) ed.selectionStart = ed.selectionEnd = caret;
    ed.dispatchEvent(new Event("input"));
  };

  if (e.key === "Tab") {
    e.preventDefault();
    if (e.shiftKey) {
      // Dedent the current line by up to one indent level.
      const lineStart = v.lastIndexOf("\n", a - 1) + 1;
      const lead = v.slice(lineStart, lineStart + INDENT.length);
      const cut = lead.startsWith(INDENT) ? INDENT.length : lead.search(/[^ ]|$/);
      if (cut) {
        ed.setRangeText("", lineStart, lineStart + cut, "preserve");
        ed.dispatchEvent(new Event("input"));
      }
      return;
    }
    replace(INDENT);
    return;
  }

  if (e.key === "Enter") {
    e.preventDefault();
    const lineStart = v.lastIndexOf("\n", a - 1) + 1;
    const line = v.slice(lineStart, a);
    let indent = line.match(/^ */)[0];
    if (line.trimEnd().endsWith(":")) indent += INDENT;
    replace("\n" + indent);
  }
};

$("mine-back").onclick = () => { mine = null; index = 0; draw(); };

$("viz-mine").onclick = async () => {
  const btn = $("viz-mine");
  const ran = problem;              // a trace belongs to the problem it came from
  const src = $("editor").value;
  const stale = () => problem !== ran;
  const args = ran.tests[0].args;   // the first case is the one the examples show
  btn.disabled = true;
  $("results").textContent = "Tracing your code…";
  try {
    await ready((msg) => { if (!stale()) $("results").textContent = msg; });
    const out = await trace(src, ran.func, args);
    if (stale()) return;

    if (!out.steps.length) {
      $("results").textContent = out.error
        ? `Could not trace your code: ${out.error}`
        : `Your ${ran.func} ran without any state to watch — no loop variables changed.`;
      return;
    }
    showMine(out.steps);

    const notes = [`Traced your run on ${JSON.stringify(args)} — ${out.steps.length} frames.`];
    if (out.error) notes.push(`It stopped early: ${out.error}`);
    else notes.push(`It returned ${JSON.stringify(out.result)}.`);
    if (out.truncated) notes.push("Only the first 400 frames were captured.");
    $("results").textContent = notes.join(" ");
  } catch (err) {
    if (!stale()) $("results").textContent = `${err.message} — press the button again.`;
  } finally {
    btn.disabled = false;
  }
};

$("run").onclick = async () => {
  const btn = $("run");
  const ran = problem; // results belong to this problem only
  const src = $("editor").value;
  const stale = () => problem !== ran;
  btn.disabled = true;
  $("results").textContent = "Starting Python…";
  try {
    await ready((msg) => { if (!stale()) $("results").textContent = msg; });
    const results = await run(src, ran.func, ran.tests);
    if (stale()) return;
    $("results").replaceChildren(...results.map(r => {
      const div = document.createElement("div");
      div.className = "result " + (r.pass ? "pass" : "fail");
      const head = r.pass ? "PASS" : "FAIL";
      div.innerHTML = `<strong>${head}</strong> ${escapeHtml(JSON.stringify(r.args))}`;
      const pre = document.createElement("pre");
      pre.textContent = r.error
        ? r.error
        : `expected ${JSON.stringify(r.expect)}\ngot      ${JSON.stringify(r.actual)}`;
      if (!r.pass) div.appendChild(pre);
      return div;
    }));
  } catch (err) {
    if (!stale()) $("results").textContent = `${err.message} — check your connection and press Run again.`;
  } finally {
    btn.disabled = false;
  }
};

const escapeHtml = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

$("picker").replaceChildren(...PROBLEMS.map(id => {
  const o = document.createElement("option");
  o.value = id; o.textContent = id;
  return o;
}));
$("picker").onchange = (e) => loadProblem(e.target.value);

loadProblem(PROBLEMS[0]);

}
