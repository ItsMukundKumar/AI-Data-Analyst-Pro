// Dashboard charts. Each chart is a card the user can zoom, hide, reorder and export.
// Backend charts may carry {plotly:{data,layout}} (interactive) and/or {image} (PNG fallback).
const Charts = {
  items: [], container: null, type: "all", drag: null,

  render(container, charts) {
    this.container = container; this.type = "all";
    this.items = charts.map((c, i) => { const it = { c, hidden: false }; this.build(it, i); return it; });
    const types = [...new Set(charts.map(c => c.chart_type).filter(Boolean))];
    $("typeFilter").innerHTML = '<option value="all">All charts</option>' + types.map(t => `<option>${t}</option>`).join("");
    $("typeFilter").value = "all";
    if (!charts.length) container.innerHTML = '<div class="empty card">The backend returned no charts for this dataset.</div>';
    else this.layout();
  },

  bindTools() {
    $("typeFilter").onchange = e => { this.type = e.target.value; this.layout(); };
    $("colBtns").onclick = e => {
      const n = e.target.dataset.n; if (!n) return;
      this.container.className = "grid cols" + n;
      [...$("colBtns").children].forEach(b => b.classList.toggle("on", b === e.target));
      this.layout();
    };
    $("showAll").onclick = () => { this.items.forEach(it => it.hidden = false); this.layout(); };
    $("resetZoom").onclick = () => this.items.forEach(it => {
      if (it.plot && it.c.chart_type !== "pie") try { Plotly.relayout(it.plot, { "xaxis.autorange": true, "yaxis.autorange": true }); } catch {}
    });
  },

  shown: it => !it.hidden && (Charts.type === "all" || it.c.chart_type === Charts.type),

  // Re-attach cards in current order, honoring filter and hidden state.
  layout() {
    this.container.innerHTML = "";
    this.items.forEach(it => { it.el.classList.toggle("hidden", !this.shown(it)); this.container.appendChild(it.el); });
    const n = this.items.filter(it => it.hidden).length;
    $("showAll").classList.toggle("hidden", !n);
    $("showAll").textContent = `Show ${n} hidden chart${n > 1 ? "s" : ""}`;
    requestAnimationFrame(() => this.items.forEach(it => it.plot && this.shown(it) && Plotly.Plots.resize(it.plot)));
    if (window.lucide) lucide.createIcons();
  },

  build(it, i) {
    const c = it.c, title = c.title || `Chart ${i + 1}`;
    const el = it.el = document.createElement("figure");
    el.className = "card chart"; el.style.margin = 0;
    el.innerHTML = `<div class="head"><span class="row"><i data-lucide="grip-vertical" class="grip" title="Drag to reorder"></i><b></b></span>
      <span class="row"><button class="btn icon" data-a="png" title="Download PNG"><i data-lucide="download"></i></button>
      <button class="btn icon" data-a="full" title="Full screen"><i data-lucide="maximize-2"></i></button>
      <button class="btn icon" data-a="hide" title="Hide chart"><i data-lucide="eye-off"></i></button></span></div>`;
    el.querySelector("b").textContent = title + (c.chart_type ? ` (${c.chart_type})` : "");

    const fig = c.plotly;
    if (fig && fig.data && window.Plotly) {
      const plot = it.plot = document.createElement("div");
      plot.className = "plot"; el.appendChild(plot);
      const layout = { autosize: true, dragmode: "zoom", ...(fig.layout || {}) };
      // Date slider only when the returned x values are real dates.
      if (c.chart_type !== "pie" && this.hasDates(fig)) layout.xaxis = { ...(layout.xaxis || {}), rangeslider: { visible: true } };
      Plotly.newPlot(plot, fig.data, layout, { responsive: true, displaylogo: false, scrollZoom: true,
        modeBarButtonsToRemove: ["lasso2d", "select2d"] });
    } else if (c.image) {
      el.insertAdjacentHTML("beforeend", `<img alt="">`);
      const img = el.querySelector("img"); img.src = c.image; img.alt = title;
    } else el.insertAdjacentHTML("beforeend", '<p class="muted">No image or chart data was returned.</p>');

    el.querySelector('[data-a="png"]').onclick = () => it.plot
      ? Plotly.downloadImage(it.plot, { format: "png", filename: slug(title) }) : saveHref(c.image, slug(title) + ".png");
    el.querySelector('[data-a="full"]').onclick = () =>
      document.fullscreenElement ? document.exitFullscreen() : el.requestFullscreen?.().then(() => it.plot && Plotly.Plots.resize(it.plot));
    el.querySelector('[data-a="hide"]').onclick = () => { it.hidden = true; this.layout(); };

    // Drag and drop reordering (mouse; grab the handle).
    el.querySelector(".grip").onmousedown = () => el.draggable = true;
    el.ondragstart = e => { this.drag = it; e.dataTransfer.effectAllowed = "move"; el.classList.add("dragging"); };
    el.ondragend = () => { el.draggable = false; el.classList.remove("dragging"); };
    el.ondragover = e => e.preventDefault();
    el.ondrop = e => {
      e.preventDefault();
      const a = this.items.indexOf(this.drag), b = this.items.indexOf(it);
      if (a < 0 || a === b) return;
      this.items.splice(b, 0, this.items.splice(a, 1)[0]); this.layout();
    };
  },

  hasDates(fig) {
    const x = fig.data[0] && fig.data[0].x;
    return Array.isArray(x) && x.length > 1 && x.slice(0, 5).every(v => typeof v === "string" && /^\d{4}-\d{2}-\d{2}/.test(v));
  },

  // Composes the visible charts, in on-screen order, into one PNG.
  async downloadDashboard(name) {
    const vis = this.items.filter(it => this.shown(it));
    const srcs = await Promise.all(vis.map(it =>
      it.plot ? Plotly.toImage(it.plot, { format: "png", width: 900, height: 560 }) : it.c.image));
    const imgs = await Promise.all(srcs.filter(Boolean).map(s => new Promise((ok, no) => {
      const im = new Image(); im.onload = () => ok(im); im.onerror = no; im.src = s;
    })));
    if (!imgs.length) throw new Error("No visible charts to export.");
    const cols = 2, cellW = 900, pad = 24;
    const hs = imgs.map(im => im.height * cellW / im.width), rows = Math.ceil(imgs.length / cols);
    const rowH = Array.from({ length: rows }, (_, r) => Math.max(...hs.slice(r * cols, r * cols + cols)));
    const cv = document.createElement("canvas");
    cv.width = cols * cellW + (cols + 1) * pad; cv.height = rowH.reduce((a, b) => a + b + pad, pad);
    const ctx = cv.getContext("2d"); ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, cv.width, cv.height);
    let y = pad;
    for (let r = 0; r < rows; r++) {
      imgs.slice(r * cols, r * cols + cols).forEach((im, k) => ctx.drawImage(im, pad + k * (cellW + pad), y, cellW, im.height * cellW / im.width));
      y += rowH[r] + pad;
    }
    saveHref(cv.toDataURL("image/png"), slug(name || "dashboard") + "-dashboard.png");
  },
};

function slug(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "chart"; }
function saveHref(href, filename) {
  const a = document.createElement("a"); a.href = href; a.download = filename;
  document.body.appendChild(a); a.click(); a.remove();
}
