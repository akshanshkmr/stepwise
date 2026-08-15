import { el, readout, pointers } from "./svg.js";

const W = 44, GAP = 8, LEFT = 20, TOP = 46, PLOT = 170;
const barX = (i) => LEFT + i * (W + GAP);

/** Columns at true height — for problems where the SHAPE matters: elevation
 *  maps, histograms, walls holding water.
 *
 *  Optional per-step data:
 *    water:  depth per column, drawn resting on top of that column
 *    region: {from, to, level} — a body of water spanning columns, drawn as one
 *            slab (Container With Most Water's rectangle between two walls) */
export function render(svg, step) {
  const { array, highlight, water, region } = step;
  const hl = new Set(highlight);

  const ceiling = Math.max(
    1,
    ...array,
    ...array.map((h, i) => h + (water?.[i] ?? 0)),
    region ? region.level : 0,
  );
  const unit = PLOT / ceiling;
  const base = TOP + PLOT;
  const yOf = (units) => base - units * unit;

  svg.setAttribute("viewBox",
    `0 0 ${Math.max(LEFT * 2 + array.length * (W + GAP), 480)} ${base + 78}`);

  readout(svg, step.vars, LEFT, 26);

  // The spanning slab sits behind the walls so the walls read as its container.
  if (region) {
    const from = Math.min(region.from, region.to);
    const to = Math.max(region.from, region.to);
    svg.appendChild(el("rect", {
      class: "region",
      x: barX(from) + W, y: yOf(region.level),
      width: Math.max(barX(to) - barX(from) - W, 0),
      height: region.level * unit,
    }));
  }

  array.forEach((h, i) => {
    const g = el("g", { class: "bar" + (hl.has(i) ? " hl" : "") });
    g.dataset.index = String(i);

    const depth = water?.[i] ?? 0;
    if (depth > 0) {
      g.appendChild(el("rect", {
        class: "water", x: barX(i), y: yOf(h + depth),
        width: W, height: depth * unit,
      }));
    }

    // A zero-height column still needs a visible footprint.
    g.appendChild(el("rect", {
      class: "column", x: barX(i), y: yOf(h), width: W,
      height: Math.max(h * unit, 2),
    }));

    g.appendChild(el("text", {
      class: "value", x: barX(i) + W / 2, y: yOf(h + depth) - 8,
      "text-anchor": "middle",
    }, String(h)));
    g.appendChild(el("text", {
      class: "idx", x: barX(i) + W / 2, y: base + 18, "text-anchor": "middle",
    }, String(i)));

    svg.appendChild(g);
  });

  svg.appendChild(el("line", {
    class: "baseline", x1: LEFT, y1: base,
    x2: LEFT + array.length * (W + GAP), y2: base,
  }));

  pointers(svg, step.pointers, (i) => barX(i) + W / 2, base + 42);
}
