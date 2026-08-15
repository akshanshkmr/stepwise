import { el, readout, pointers } from "./svg.js";

const BOX = 52, GAP = 8, LEFT = 20, ROW = 56;
const SBOX = 52, SGAP = 6, SBASE = 250;   // the stack sits below the input row
const cellX = (i) => LEFT + i * (BOX + GAP);

/** Input on a row, the stack growing upward beneath it — for problems where
 *  the answer depends on what you kept, not just where you are looking.
 *
 *  step.stack is the stack bottom-first; the last entry is the top and is the
 *  only one most decisions actually consult, so it is the one marked. */
export function render(svg, step) {
  const { array, highlight, stack = [] } = step;
  const hl = new Set(highlight);

  const width = Math.max(LEFT * 2 + array.length * (BOX + GAP), 480);
  svg.setAttribute("viewBox", `0 0 ${width} 300`);

  readout(svg, step.vars, LEFT, 26);

  array.forEach((value, i) => {
    const g = el("g", { class: "cell" + (hl.has(i) ? " hl" : "") });
    g.dataset.index = String(i);
    g.appendChild(el("rect", { x: cellX(i), y: ROW, width: BOX, height: BOX, rx: 8 }));
    g.appendChild(el("text", {
      class: "value", x: cellX(i) + BOX / 2, y: ROW + BOX / 2,
      "text-anchor": "middle", "dominant-baseline": "central",
    }, String(value)));
    g.appendChild(el("text", {
      class: "idx", x: cellX(i) + BOX / 2, y: ROW - 10, "text-anchor": "middle",
    }, String(i)));
    svg.appendChild(g);
  });

  pointers(svg, step.pointers, (i) => cellX(i) + BOX / 2, ROW + BOX + 22);

  // The stack itself, bottom entry at the bottom.
  svg.appendChild(el("text", {
    class: "stack-label", x: LEFT, y: SBASE + 18,
  }, stack.length ? "stack" : "stack (empty)"));

  stack.forEach((value, i) => {
    const top = i === stack.length - 1;
    const g = el("g", { class: "stack-item" + (top ? " top" : "") });
    g.dataset.depth = String(i);
    const y = SBASE - (i + 1) * (SBOX + SGAP) + SBOX - 6;
    g.appendChild(el("rect", {
      x: LEFT + 62, y, width: SBOX, height: SBOX, rx: 8,
    }));
    g.appendChild(el("text", {
      x: LEFT + 62 + SBOX / 2, y: y + SBOX / 2,
      "text-anchor": "middle", "dominant-baseline": "central",
    }, String(value)));
    if (top) {
      g.appendChild(el("text", {
        class: "stack-top", x: LEFT + 62 + SBOX + 12, y: y + SBOX / 2,
        "dominant-baseline": "central",
      }, "top"));
    }
    svg.appendChild(g);
  });
}
