const NS = "http://www.w3.org/2000/svg";
const BOX = 72, GAP = 14, TOP = 70, LEFT = 20;

function el(tag, attrs, text) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

const cellX = (i) => LEFT + i * (BOX + GAP);

export function render(svg, step) {
  svg.replaceChildren();
  const { array, vars, highlight, caption } = step;
  const hl = new Set(highlight);

  const width = LEFT * 2 + array.length * (BOX + GAP);
  svg.setAttribute("viewBox", `0 0 ${Math.max(width, 480)} 260`);

  // Non-index vars, shown as a readout above the row.
  const isIndex = (v) => Number.isInteger(v) && v >= 0 && v < array.length;
  const readout = Object.entries(vars)
    .filter(([, v]) => !isIndex(v))
    .map(([k, v]) => `${k} = ${v}`)
    .join("   ");
  const readoutNode = el("text", { class: "readout", x: LEFT, y: 34 }, readout);
  svg.appendChild(readoutNode);

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

  // Pointers, stacked so two on the same index stay readable.
  const perIndex = new Map();
  Object.entries(vars).filter(([, v]) => isIndex(v)).forEach(([name, i]) => {
    const row = perIndex.get(i) ?? 0;
    perIndex.set(i, row + 1);
    const y = TOP + BOX + 26 + row * 26;
    const g = el("g", { class: "pointer" });
    g.dataset.name = name;
    g.appendChild(el("text", {
      x: cellX(i) + BOX / 2, y, "text-anchor": "middle",
    }, `▲ ${name}`));
    svg.appendChild(g);
  });

  svg.appendChild(el("text", {
    class: "caption", x: LEFT, y: 244,
  }, caption ?? ""));
}
