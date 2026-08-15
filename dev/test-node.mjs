/* Logic checks that need no browser, so CI can run them.
 *
 * The DOM-dependent checks still live in the two harness pages — rendering is
 * genuinely a browser concern. What runs here is everything that is pure: the
 * checkpoint gate, the editor gate, the storage migration, and the highlighter's
 * escaping, which is the one place learner input reaches innerHTML.
 *
 * Run: node dev/test-node.mjs
 */
import assert from "node:assert/strict";
import { test } from "node:test";

import { pythonToHtml } from "../highlight.js";
import { GATE_EDITOR, migrate, nextBlockingCheckpoint, predictionsOwed } from "../app.js";

test("checkpoint gate blocks only on an unanswered checkpoint at this step", () => {
  const cps = [{ afterStep: 1 }, { afterStep: 3 }];
  assert.equal(nextBlockingCheckpoint(cps, new Set(), 1), 0);
  assert.equal(nextBlockingCheckpoint(cps, new Set([0]), 1), null);
  assert.equal(nextBlockingCheckpoint(cps, new Set(), 0), null);
  assert.equal(nextBlockingCheckpoint([], new Set(), 0), null);
});

test("the editor stays shut until every prediction is made", () => {
  assert.equal(GATE_EDITOR, true, "the experiment is meant to be on by default");
  const cps = [{}, {}];
  assert.equal(predictionsOwed(cps, new Set(), false), 2);
  assert.equal(predictionsOwed(cps, new Set([0]), false), 1);
  assert.equal(predictionsOwed(cps, new Set([0, 1]), false), 0);
});

test("a solved problem never re-locks", () => {
  assert.equal(predictionsOwed([{}, {}], new Set(), true), 0);
});

test("a problem with no checkpoints cannot lock anyone out", () => {
  assert.equal(predictionsOwed([], new Set(), false), 0);
});

test("migration stamps v1 records and preserves their progress", () => {
  const out = migrate({ answered: [0], hintsUsed: 2, code: "x", solved: true });
  assert.equal(out.v, 2);
  assert.deepEqual(out.answered, [0]);
  assert.equal(out.hintsUsed, 2);
  assert.equal(out.solved, true);
});

test("migration discards records from a newer build rather than guessing", () => {
  assert.equal(migrate({ v: 99, answered: [0] }), null);
});

test("migration passes an empty record through untouched", () => {
  assert.deepEqual(migrate({}), {});
});

test("migration rejects junk", () => {
  assert.equal(migrate(null), null);
  assert.equal(migrate("nope"), null);
});

test("the highlighter escapes markup before it reaches innerHTML", () => {
  const html = pythonToHtml('x = "<img src=x onerror=alert(1)>"');
  assert.ok(!html.includes("<img"), html);
  assert.ok(html.includes("&lt;img"), html);
});

test("the highlighter preserves the source exactly", () => {
  const src = 'def f(x):\n    return x  # done\n';
  const stripped = pythonToHtml(src)
    .replace(/<[^>]+>/g, "")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  assert.equal(stripped, src + "\n");
});

test("keywords inside strings and comments are not coloured", () => {
  const html = pythonToHtml('x = "return None"  # def foo');
  assert.ok(!html.includes('tok-keyword">return'), html);
  assert.ok(!html.includes('tok-keyword">def'), html);
});
