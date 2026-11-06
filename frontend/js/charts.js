// Chart rendering. The backend currently returns PNG data URLs ({image}).
// If a chart later carries structured Plotly data ({plotly:{data,layout}}), it is rendered interactively.
const Charts = {
  render(container, charts) {
    container.innerHTML = "";
    if (!charts.length) {
      container.innerHTML = '<div class="empty card">The backend returned no charts for this dataset.</div>';
      return;
    }
    charts.forEach((c, i) => container.appendChild(this.card(c, i)));
    if (window.lucide) lucide.createIcons();
  },

  card(c, i) {
    const el = document.createElement("figure");
    el.className = "card chart";
    el.style.margin = 0;
    const title = c.title || `Chart ${i + 1}`;
    const fig = c.plotly || null;
    el.innerHTML = `<div class="head"><b></b><span class="row">
      <button class="btn icon" data-a="png" title="Download PNG"><i data-lucide="download"></i></button>
      <button class="btn icon" data-a="full" title="Full screen"><i data-lucide="maximize-2"></i></button></span></div>`;
    el.querySelector("b").textContent = title + (c.chart_type ? ` (${c.chart_type})` : "");

    let plot = null;
    if (fig && window.Plotly) {
      plot = document.createElement("div");
      plot.className = "plot";
      el.appendChild(plot);
      Plotly.newPlot(plot, fig.data, { autosize: true, ...(fig.layout || {}) }, { responsive: true, displaylogo: false });
    } else if (c.image) {
      const img = document.createElement("img");
      img.src = c.image; img.alt = title;
      el.appendChild(img);
    } else {
      el.insertAdjacentHTML("beforeend", '<p class="muted">No image or chart data was returned for this chart.</p>');
    }

    el.querySelector('[data-a="png"]').onclick = () =>
      plot ? Plotly.downloadImage(plot, { format: "png", filename: slug(title) }) : saveHref(c.image, slug(title) + ".png");
    el.querySelector('[data-a="full"]').onclick = () => {
      if (document.fullscreenElement) document.exitFullscreen();
      else el.requestFullscreen?.().then(() => plot && Plotly.Plots.resize(plot));
    };
    return el;
  },

  // Composes all chart images into one PNG (the backend has no endpoint that returns its dashboard image).
  async downloadDashboard(charts, name) {
    const imgs = await Promise.all(charts.filter(c => c.image).map(c => new Promise((ok, no) => {
      const im = new Image(); im.onload = () => ok(im); im.onerror = no; im.src = c.image;
    })));
    if (!imgs.length) throw new Error("No chart images are available to export.");
    const cols = 2, cellW = 900, pad = 24;
    const heights = imgs.map(im => im.height * cellW / im.width);
    const rows = Math.ceil(imgs.length / cols);
    const rowH = Array.from({ length: rows }, (_, r) => Math.max(...heights.slice(r * cols, r * cols + cols)));
    const cv = document.createElement("canvas");
    cv.width = cols * cellW + (cols + 1) * pad;
    cv.height = rowH.reduce((a, b) => a + b + pad, pad);
    const ctx = cv.getContext("2d");
    ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, cv.width, cv.height);
    let y = pad;
    for (let r = 0; r < rows; r++) {
      imgs.slice(r * cols, r * cols + cols).forEach((im, k) =>
        ctx.drawImage(im, pad + k * (cellW + pad), y, cellW, im.height * cellW / im.width));
      y += rowH[r] + pad;
    }
    saveHref(cv.toDataURL("image/png"), slug(name || "dashboard") + "-dashboard.png");
  },
};

function slug(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "chart"; }
function saveHref(href, filename) {
  const a = document.createElement("a");
  a.href = href; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
}
