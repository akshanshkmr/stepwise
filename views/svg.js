export const NS = "http://www.w3.org/2000/svg";

export function el(tag, attrs, text) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

/** Every view puts its scalars on the same readout line, so they read the same
 *  way whichever view is on screen. */
export function readout(svg, vars, x, y) {
  const text = Object.entries(vars ?? {}).map(([k, v]) => `${k} = ${v}`).join("   ");
  svg.appendChild(el("text", { class: "readout", x, y }, text));
}

/** Pointer arrows, stacked when two share an index so neither is hidden. */
export function pointers(svg, map, xOf, y, rowHeight = 26) {
  const perIndex = new Map();
  Object.entries(map ?? {}).forEach(([name, i]) => {
    const row = perIndex.get(i) ?? 0;
    perIndex.set(i, row + 1);
    const g = el("g", { class: "pointer" });
    g.dataset.name = name;
    g.appendChild(el("text", {
      x: xOf(i), y: y + row * rowHeight, "text-anchor": "middle",
    }, `▲ ${name}`));
    svg.appendChild(g);
  });
}
