import { render } from "./visualizer.js";
import { ready, run } from "./runner.js";

const PROBLEMS = ["two-sum-ii"];

/** Index of the checkpoint that blocks advancing past `index`, or null. */
export function nextBlockingCheckpoint(checkpoints, answered, index) {
  for (let i = 0; i < checkpoints.length; i++) {
    if (checkpoints[i].afterStep === index && !answered.has(i)) return i;
  }
  return null;
}

if (document.getElementById("viz")) {

const $ = (id) => document.getElementById(id);
let problem = null, index = 0, answered = new Set(), hintsUsed = 0;

const storageKey = () => `codeteach:${problem.id}`;

function save() {
  localStorage.setItem(storageKey(),
    JSON.stringify({ answered: [...answered], hintsUsed }));
}

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(storageKey()) ?? "{}");
    answered = new Set(raw.answered ?? []);
    hintsUsed = raw.hintsUsed ?? 0;
  } catch { answered = new Set(); hintsUsed = 0; }
}

async function loadProblem(id) {
  problem = await (await fetch(`problems/${id}.json`)).json();
  index = 0;
  load();
  $("title").textContent = problem.title;
  $("statement").innerHTML = problem.statement
    .split("\n\n").map(p => `<p>${inline(p)}</p>`).join("");
  $("examples").innerHTML = problem.examples
    .map(e => `<div>Input: ${e.input}<br>Output: ${e.output}</div>`).join("");
  $("editor").value = `${problem.signature}\n    `;
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
  render($("viz"), problem.steps[index]);
  $("step-count").textContent = `${index + 1} / ${problem.steps.length}`;
  $("scrub").value = String(index);

  const blocked = nextBlockingCheckpoint(problem.checkpoints, answered, index);
  const atEnd = index >= problem.steps.length - 1;
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
  const target = Math.max(0, Math.min(problem.steps.length - 1, i));
  // Never step past an unanswered gate.
  for (let k = index; k < target; k++) {
    if (nextBlockingCheckpoint(problem.checkpoints, answered, k) !== null) {
      index = k; draw(); return;
    }
  }
  index = target;
  draw();
}

$("next").onclick = () => go(index + 1);
$("prev").onclick = () => go(index - 1);
$("first").onclick = () => go(0);
$("last").onclick = () => go(problem.steps.length - 1);
$("scrub").oninput = (e) => go(Number(e.target.value));
$("hint-btn").onclick = () => { hintsUsed++; save(); renderHints(); };

$("run").onclick = async () => {
  const btn = $("run");
  btn.disabled = true;
  $("results").textContent = "Starting Python…";
  try {
    await ready((msg) => { $("results").textContent = msg; });
    const results = await run($("editor").value, problem.func, problem.tests);
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
    $("results").textContent = `${err.message} — check your connection and press Run again.`;
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
