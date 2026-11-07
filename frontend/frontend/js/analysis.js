// Turns whatever the backend returns (text or JSON) into readable sections. Nothing is invented.
const Analysis = {
  // Normalize any report shape to markdown-like text.
  toMarkdown(v, depth = 0) {
    if (v == null) return "";
    if (typeof v === "string") return v;
    if (typeof v !== "object") return String(v);
    if (Array.isArray(v)) return v.map(x => typeof x === "object" ? this.toMarkdown(x, depth + 1) : "- " + x).join("\n");
    return Object.entries(v).map(([k, val]) => {
      const head = "#".repeat(Math.min(depth + 1, 3)) + " " + k.replace(/[_-]+/g, " ").replace(/^\w/, c => c.toUpperCase());
      return `${head}\n${this.toMarkdown(val, depth + 1)}`;
    }).join("\n\n");
  },

  esc: s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])),
  inline(s) { return this.esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"); },

  render(el, report) {
    const lines = this.toMarkdown(report).split("\n");
    let html = "", list = false;
    const close = () => { if (list) { html += "</ul>"; list = false; } };
    for (let raw of lines) {
      const line = raw.trim();
      if (!line) { close(); continue; }
      let m;
      if ((m = line.match(/^#{1,6}\s+(.*)/)) || (m = line.match(/^\*\*(.+?)\*\*:?$/))) {
        close(); html += `<h3>${this.inline(m[1])}</h3>`;
      } else if ((m = line.match(/^[-*•]\s+(.*)/)) || (m = line.match(/^\d+[.)]\s+(.*)/))) {
        if (!list) { html += "<ul>"; list = true; }
        html += `<li>${this.inline(m[1])}</li>`;
      } else { close(); html += `<p>${this.inline(line)}</p>`; }
    }
    close();
    el.innerHTML = html || '<div class="empty">The backend returned an empty report.</div>';
  },

  toText(report) { return this.toMarkdown(report).replace(/\*\*/g, "").replace(/^#{1,6}\s+/gm, ""); },
};
