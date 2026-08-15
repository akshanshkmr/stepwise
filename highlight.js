/* Minimal Python highlighter for the editor overlay.
   ponytail: one regex pass, no parser, no dependency. It colours the things a
   learner looks at — strings, comments, keywords, numbers, def names — and is
   deliberately wrong about nothing else, because a wrong highlight is worse
   than none. Reach for CodeMirror only if this stops being enough. */

const KEYWORD = new Set([
  "and", "as", "assert", "async", "await", "break", "class", "continue", "def",
  "del", "elif", "else", "except", "finally", "for", "from", "global", "if",
  "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
  "return", "try", "while", "with", "yield",
]);

const CONSTANT = new Set(["True", "False", "None", "self"]);

const BUILTIN = new Set([
  "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float", "int",
  "isinstance", "len", "list", "map", "max", "min", "print", "range",
  "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip",
]);

// Order matters: comments and strings win over everything inside them.
const TOKEN = new RegExp([
  /(?<comment>#[^\n]*)/.source,
  /(?<string>"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/.source,
  /(?<number>\b\d+(?:\.\d+)?\b)/.source,
  /(?<word>\b[A-Za-z_]\w*\b)/.source,
].join("|"), "g");

const esc = (s) => s
  .replace(/&/g, "&amp;")
  .replace(/</g, "&lt;")
  .replace(/>/g, "&gt;");

/** Returns HTML for `src`. Every character of the input is escaped, so the
 *  learner's own code can never inject markup into the page. */
export function pythonToHtml(src) {
  let out = "";
  let last = 0;
  let prevWord = "";   // the word before this one, so `def foo` can colour foo
  let m;
  TOKEN.lastIndex = 0;

  while ((m = TOKEN.exec(src)) !== null) {
    out += esc(src.slice(last, m.index));
    const g = m.groups;
    const text = esc(m[0]);

    if (g.comment) {
      out += `<span class="tok-comment">${text}</span>`;
    } else if (g.string) {
      out += `<span class="tok-string">${text}</span>`;
    } else if (g.number) {
      out += `<span class="tok-number">${text}</span>`;
    } else if (KEYWORD.has(m[0])) {
      out += `<span class="tok-keyword">${text}</span>`;
    } else if (CONSTANT.has(m[0])) {
      out += `<span class="tok-constant">${text}</span>`;
    } else if (prevWord === "def" || prevWord === "class") {
      out += `<span class="tok-name">${text}</span>`;
    } else if (BUILTIN.has(m[0])) {
      out += `<span class="tok-builtin">${text}</span>`;
    } else {
      out += text;
    }

    if (g.word) prevWord = m[0];
    last = m.index + m[0].length;
  }

  out += esc(src.slice(last));
  // A trailing newline needs a character after it or the last line collapses
  // and the overlay drifts out of step with the textarea.
  return out + "\n";
}
