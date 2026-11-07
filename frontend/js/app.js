// App controller: upload flow, view switching, summary cards, notifications.
const $ = id => document.getElementById(id);
const state = { file: null, sessionId: null, filename: "", charts: [], report: null, busy: false };

const STEPS = ["Uploading dataset", "Cleaning data", "Extracting metadata", "Generating chart configurations", "Rendering charts"];

/* ---------- helpers ---------- */
function toast(msg, type = "info") {
  const t = document.createElement("div");
  t.className = "toast " + type; t.textContent = msg;
  $("toasts").appendChild(t);
  setTimeout(() => t.remove(), 4500);
}
const fmtSize = b => b < 1024 ? b + " B" : b < 1048576 ? (b / 1024).toFixed(1) + " KB" : (b / 1048576).toFixed(1) + " MB";
const fmtNum = n => typeof n === "number" ? n.toLocaleString() : "Not provided";

// Searches a backend object (any depth) for a numeric field whose key matches `re`.
// Objects of numbers (e.g. per-column counts) are summed. Returns undefined if nothing matches.
function deepFind(obj, re) {
  if (!obj || typeof obj !== "object") return undefined;
  for (const [k, v] of Object.entries(obj)) {
    if (re.test(k)) {
      if (typeof v === "number") return v;
      if (v && typeof v === "object" && !Array.isArray(v)) {
        const nums = Object.values(v);
        if (nums.length && nums.every(x => typeof x === "number")) return nums.reduce((a, b) => a + b, 0);
      }
    }
  }
  for (const v of Object.values(obj)) { const r = deepFind(v, re); if (r !== undefined) return r; }
}

/* ---------- views ---------- */
function showView(name) {
  ["dashboard", "analysis"].forEach(v => $(v).classList.toggle("hidden", v !== name));
  document.querySelectorAll(".tab[data-view]").forEach(t => t.classList.toggle("active", t.dataset.view === name));
  window.scrollTo({ top: 0 });
  if (name === "analysis" && !state.report && !state.busy) runAnalysis();
}
function enterApp() {
  $("landing").classList.add("hidden");
  $("appNav").classList.remove("hidden");
  $("fileBadge").textContent = state.filename; $("fileBadge").classList.remove("hidden");
  showView("dashboard");
}
async function resetAll(notify) {
  if (state.sessionId) Api.deleteSession(state.sessionId);
  Object.assign(state, { file: null, sessionId: null, filename: "", charts: [], report: null, busy: false });
  ["dashboard", "analysis", "appNav", "fileBadge", "fileInfo", "progress", "uploadError"].forEach(i => $(i).classList.add("hidden"));
  $("landing").classList.remove("hidden");
  $("fileInput").value = ""; $("analysisBody").innerHTML = ""; $("dlReport").disabled = true;
  window.scrollTo({ top: 0 });
  if (notify) toast(notify, "error");
}

/* ---------- file selection ---------- */
function setFile(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  const err = $("uploadError");
  err.classList.add("hidden");
  if (!CONFIG.ALLOWED_EXT.includes(ext)) return showUploadError("Unsupported file type. Choose a .csv, .xlsx or .xls file.");
  if (file.size > CONFIG.MAX_FILE_MB * 1048576) return showUploadError(`File is larger than ${CONFIG.MAX_FILE_MB} MB.`);
  if (file.size === 0) return showUploadError("The selected file is empty.");
  state.file = file;
  $("fileName").textContent = file.name; $("fileSize").textContent = fmtSize(file.size);
  $("fileInfo").classList.remove("hidden"); $("drop").classList.add("hidden");
}
function clearFile() {
  state.file = null; $("fileInput").value = "";
  $("fileInfo").classList.add("hidden"); $("drop").classList.remove("hidden"); $("progress").classList.add("hidden");
}
function showUploadError(msg) { const e = $("uploadError"); e.textContent = msg; e.classList.remove("hidden"); }

/* ---------- pipeline: upload -> clean -> metadata -> chart config -> visualize ---------- */
function setStep(i, status) {
  const items = $("stepList").children;
  [...items].forEach((li, k) => li.className = k < i ? "done" : k === i ? status : "");
  $("barFill").style.width = Math.round(((status === "done" ? i + 1 : i) / STEPS.length) * 100) + "%";
}

async function runPipeline() {
  if (!state.file || state.busy) return;
  state.busy = true;
  $("uploadError").classList.add("hidden");
  $("progress").classList.remove("hidden");
  $("analyzeBtn").disabled = $("resetFile").disabled = true;
  $("stepList").innerHTML = STEPS.map(s => `<li>${s}</li>`).join("");
  let step = 0;
  try {
    setStep(0, "run");
    const up = await Api.upload(state.file, f => { $("barFill").style.width = (f * 100 / STEPS.length) + "%"; });
    state.sessionId = up.session_id; state.filename = up.filename || state.file.name;
    if (!state.sessionId) throw new Error("The backend did not return a session id.");

    setStep(step = 1, "run");
    const cleaned = await Api.clean(state.sessionId);
    setStep(step = 2, "run");
    const meta = await Api.metadata(state.sessionId);
    setStep(step = 3, "run");
    await Api.generateCharts(state.sessionId);
    setStep(step = 4, "run");
    const vis = await Api.visualize(state.sessionId);
    state.charts = Array.isArray(vis.charts) ? vis.charts : [];

    setStep(4, "done");
    renderSummary(up, cleaned.cleaning_report, meta.metadata);
    Charts.render($("charts"), state.charts);
    enterApp();
    toast("Dataset processed successfully.", "success");
  } catch (e) {
    setStep(step, "fail");
    if (e.isSessionExpired) return resetAll("Your session expired. Please upload the dataset again.");
    showUploadError(e.message || "Something went wrong.");
  } finally {
    state.busy = false; $("analyzeBtn").disabled = $("resetFile").disabled = false;
  }
}

/* ---------- dashboard ---------- */
function renderSummary(up, report, meta) {
  const ds = up.dataset || {};
  const rows = deepFind(meta, /^(total_)?rows$|row_count|num_rows/i) ?? ds.total_rows;
  const cols = deepFind(meta, /^(total_)?columns$|column_count|num_columns/i) ?? ds.total_columns;
  const missing = deepFind(meta, /missing|null/i) ?? deepFind(report, /missing|null/i);
  const dupes = deepFind(meta, /duplicate/i) ?? deepFind(report, /duplicate/i);
  const cards = [["Total rows", rows], ["Total columns", cols], ["Missing values", missing], ["Duplicate rows", dupes]];
  $("summary").innerHTML = cards.map(([l, v]) =>
    `<div class="card stat"><b>${fmtNum(v)}</b><span>${l}</span></div>`).join("");
}

/* ---------- AI analysis ---------- */
async function runAnalysis() {
  if (!state.sessionId) return;
  state.busy = true; state.report = null;
  $("dlReport").disabled = $("regen").disabled = true;
  $("analysisBody").innerHTML = '<div class="loading">Generating AI analysis. This can take up to a minute.</div>';
  try {
    const res = await Api.analyze(state.sessionId);
    if (res.analysis_report == null) throw new Error("The backend response did not include an analysis report.");
    state.report = res.analysis_report;
    Analysis.render($("analysisBody"), state.report);
    $("dlReport").disabled = false;
  } catch (e) {
    if (e.isSessionExpired) return resetAll("Your session expired. Please upload the dataset again.");
    $("analysisBody").innerHTML = '<div class="alert"></div>';
    $("analysisBody").firstChild.textContent = e.message;
    toast("Analysis failed.", "error");
  } finally { state.busy = false; $("regen").disabled = false; }
}

/* ---------- wiring ---------- */
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();
  Charts.bindTools();
  const drop = $("drop");
  $("startBtn").onclick = () => $("uploadSection").scrollIntoView({ behavior: "smooth" });
  $("brand").onclick = e => { e.preventDefault(); if (!state.sessionId) window.scrollTo({ top: 0, behavior: "smooth" }); };
  $("browseBtn").onclick = e => { e.stopPropagation(); $("fileInput").click(); };
  drop.onclick = () => $("fileInput").click();
  drop.onkeydown = e => (e.key === "Enter" || e.key === " ") && $("fileInput").click();
  $("fileInput").onchange = e => e.target.files[0] && setFile(e.target.files[0]);
  ["dragenter", "dragover"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", e => e.dataTransfer.files[0] && setFile(e.dataTransfer.files[0]));
  $("resetFile").onclick = clearFile;
  $("analyzeBtn").onclick = runPipeline;
  document.querySelectorAll(".tab[data-view]").forEach(t => t.onclick = () => showView(t.dataset.view));
  $("newDataset").onclick = () => resetAll();
  $("regen").onclick = runAnalysis;
  $("dlDashboard").onclick = () => Charts.downloadDashboard(state.filename)
    .then(() => toast("Dashboard PNG downloaded.", "success")).catch(e => toast(e.message, "error"));
  $("dlReport").onclick = () => {
    const blob = new Blob([`AI Analysis Report: ${state.filename}\n\n${Analysis.toText(state.report)}`], { type: "text/plain" });
    saveHref(URL.createObjectURL(blob), slug(state.filename) + "-analysis.txt");
  };
});
