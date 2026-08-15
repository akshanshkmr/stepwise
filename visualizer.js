import { el } from "./views/svg.js";
import { render as cells } from "./views/cells.js";
import { render as bars } from "./views/bars.js";

// The view registry. A new shape of problem (grid, tree, graph, linked list)
// is a new file here plus an entry in views/manifest.json — no change to this
// dispatcher, to app.js, or to the validator.
const VIEWS = { cells, bars };

export const viewNames = () => Object.keys(VIEWS);

/** Draws one step in the named view. Defaults to `cells` so a problem without
 *  an explicit view still renders.
 *  The caption is NOT drawn here: app.js renders it as HTML so it wraps. */
export function render(svg, step, view = "cells") {
  const draw = VIEWS[view];
  svg.replaceChildren();
  if (!draw) {
    svg.appendChild(el("text", { class: "readout", x: 20, y: 40 },
      `Unknown view "${view}" — add views/${view}.js and a manifest entry.`));
    return;
  }
  draw(svg, step);
}
