import { el, readout, pointers } from "./svg.js";

const BOX = 72, GAP = 14, TOP = 70, LEFT = 20;
const cellX = (i) => LEFT + i * (BOX + GAP);

/** One labelled box per element — for problems where the VALUES matter. */
export function render(svg, step) {
  const { array, highlight } = step;
  const hl = new Set(highlight);

  svg.setAttribute("viewBox",
    `0 0 ${Math.max(LEFT * 2 + array.length * (BOX + GAP), 480)} 220`);

  readout(svg, step.vars, LEFT, 34);

  array.forEach((value, i) => {
    const g = el("g", { class: "cell" + (hl.has(i) ? " hl" : "") });
    g.dataset.index = String(i);
    g.appendChild(el("rect", { x: cellX(i), y: TOP, width: BOX, height: BOX, rx: 8 }));
    g.appendChild(el("text", {
      class: "value", x: cellX(i) + BOX / 2, y: TOP + BOX / 2,
      "text-anchor": "middle", "dominant-baseline": "central",
    }, String(value)));
    g.appendChild(el("text", {
      class: "idx", x: cellX(i) + BOX / 2, y: TOP - 12, "text-anchor": "middle",
    }, String(i)));
    svg.appendChild(g);
  });

  pointers(svg, step.pointers, (i) => cellX(i) + BOX / 2, TOP + BOX + 26);
}
