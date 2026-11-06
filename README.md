<div align="center">

<h1>📊 AI Data Analyst Pro</h1>

<p><b>Turn raw data into meaningful insights.</b></p>

<p>
Upload a CSV or Excel file, get it cleaned automatically, explore AI-generated charts,<br>
and read a written business report, all in one dashboard.
</p>

<p>
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JS-4f46e5?style=for-the-badge&logo=javascript&logoColor=white" alt="Vanilla JS">
  <img src="https://img.shields.io/badge/Charts-Groq-f55036?style=for-the-badge" alt="Groq">
  <img src="https://img.shields.io/badge/Analysis-Gemini-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/Version-2.0.0-0f1b3d?style=for-the-badge" alt="Version">
</p>

<p>
  <a href="#-features">Features</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-reference">API</a> •
  <a href="#-project-structure">Structure</a> •
  <a href="#-limitations--roadmap">Roadmap</a>
</p>

</div>

<!--
  Add a screenshot after your first run:
  <p align="center"><img src="docs/dashboard.png" alt="Dashboard" width="900"></p>
-->

---

## ✨ Features

<table>
  <tr>
    <td width="33%" valign="top">
      <h3>📁 Easy upload</h3>
      Drag and drop <code>.csv</code>, <code>.xlsx</code> or <code>.xls</code> files with a live progress indicator.
    </td>
    <td width="33%" valign="top">
      <h3>🧹 Automatic cleaning</h3>
      Missing values and duplicates are handled for you, and a cleaning report is kept with the session.
    </td>
    <td width="33%" valign="top">
      <h3>🔎 Dataset profiling</h3>
      Column types and statistics are extracted and used to guide the AI.
    </td>
  </tr>
  <tr>
    <td valign="top">
      <h3>📈 AI chart generation</h3>
      Groq picks suitable charts for your data: bar, line, pie, scatter, histogram and box plot.
    </td>
    <td valign="top">
      <h3>🧠 AI business report</h3>
      Gemini reads the dashboard and writes a report. Download it as a TXT file.
    </td>
    <td valign="top">
      <h3>⬇️ Exports</h3>
      Download each chart as a PNG, or the whole dashboard as a single PNG.
    </td>
  </tr>
</table>

---

## 🔄 How It Works

<table>
  <tr>
    <td align="center" width="20%"><b>1. Upload</b><br><code>POST /api/upload</code></td>
    <td align="center" width="20%"><b>2. Clean</b><br><code>POST /api/clean/{id}</code></td>
    <td align="center" width="20%"><b>3. Profile</b><br><code>GET /api/metadata/{id}</code></td>
    <td align="center" width="20%"><b>4. Plan charts</b><br><code>POST /api/generate-charts/{id}</code></td>
    <td align="center" width="20%"><b>5. Render</b><br><code>POST /api/visualize/{id}</code></td>
  </tr>
</table>

After the charts are ready, opening the **AI Analysis** tab calls `POST /api/analyze/{id}`, which sends the dashboard image and metadata to Gemini.

Each upload creates a temporary **session**. Sessions expire, and the frontend sends you back to the upload page if that happens.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A Groq API key (chart planning)
- A Google Gemini API key (analysis)

### 1. Start the backend

```bash
# install your project dependencies, then:
python main.py
```

The API runs at **http://127.0.0.1:8000** and its interactive docs are at **http://127.0.0.1:8000/docs**.

> Configure your Groq and Gemini keys in the backend only. The frontend never holds API keys.

### 2. Start the frontend

```bash
cd frontend
python -m http.server 5500
```

Open **http://127.0.0.1:5500** in your browser.

> The backend already allows cross-origin requests, so no extra setup is needed. The page loads Plotly, Lucide and Google Fonts from CDNs, so you need an internet connection.

### 3. Change the backend URL

Edit `frontend/js/config.js`:

```js
window.CONFIG = {
  API_BASE: "http://127.0.0.1:8000",
  MAX_FILE_MB: 50,
  ALLOWED_EXT: ["csv", "xlsx", "xls"],
};
```

---

## 🔌 API Reference

<table>
  <thead>
    <tr><th>Method</th><th>Endpoint</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td><code>POST</code></td><td><code>/api/upload</code></td><td>Upload a file and create a session</td></tr>
    <tr><td><code>GET</code></td><td><code>/api/session/{id}</code></td><td>Check a session (name, rows, columns)</td></tr>
    <tr><td><code>DELETE</code></td><td><code>/api/session/{id}</code></td><td>Delete a session</td></tr>
    <tr><td><code>POST</code></td><td><code>/api/clean/{id}</code></td><td>Clean the dataset and return a report</td></tr>
    <tr><td><code>GET</code></td><td><code>/api/metadata/{id}</code></td><td>Extract dataset metadata</td></tr>
    <tr><td><code>POST</code></td><td><code>/api/generate-charts/{id}</code></td><td>Ask Groq for chart configurations</td></tr>
    <tr><td><code>POST</code></td><td><code>/api/visualize/{id}</code></td><td>Render charts as base64 PNG images</td></tr>
    <tr><td><code>POST</code></td><td><code>/api/analyze/{id}</code></td><td>Ask Gemini for the analysis report</td></tr>
    <tr><td><code>GET</code></td><td><code>/health</code></td><td>Health check</td></tr>
  </tbody>
</table>

---

## 🗂 Project Structure

```text
.
├── main.py                 # FastAPI app entry point
├── app/
│   ├── routes/             # upload, cleaning, metadata, charts, visualization, analytics
│   ├── services/           # data loading/cleaning, metadata, chart and AI logic
│   └── utils/              # file validation, session manager
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/
        ├── config.js       # backend URL and limits
        ├── api.js          # all backend calls and error handling
        ├── charts.js       # chart rendering and PNG exports
        ├── analysis.js     # AI report formatting
        └── app.js          # upload flow, navigation, dashboard
```

---

## 🛠 Tech Stack

<table>
  <tr>
    <td><b>Backend</b></td>
    <td>Python, FastAPI, Pandas, Groq, Google Gemini</td>
  </tr>
  <tr>
    <td><b>Frontend</b></td>
    <td>HTML5, CSS3, vanilla JavaScript, Plotly.js, Lucide Icons, Google Fonts (Manrope)</td>
  </tr>
</table>

---

## ⚠️ Limitations & Roadmap

<details>
<summary><b>Why aren't the charts more interactive?</b></summary>
<br>
The backend returns charts as PNG images, so zoom, pan and hover tooltips are not possible yet.
The frontend already renders a chart interactively with Plotly when it receives a <code>plotly</code> field
(<code>{ data, layout }</code>) for it.
</details>

<details>
<summary><b>Why is there no date range slider?</b></summary>
<br>
No endpoint filters data by date, and static images cannot be filtered in the browser.
The slider needs structured chart data or a date-range parameter on <code>/api/visualize</code>.
</details>

**Planned improvements**

- [ ] Return Plotly figure JSON from `/api/visualize` for fully interactive charts
- [ ] Date range filtering once chart data is available
- [ ] Reorder the exception handlers in `analytics.py` so Gemini-specific errors are caught first
- [ ] PDF export for the AI report

---

## 🔒 Privacy

- Uploaded data lives in a temporary in-memory session and can be deleted at any time.
- The frontend stores nothing in `localStorage` and holds no API keys.

---

<div align="center">
  <sub>Built with FastAPI, Groq, Gemini and Plotly.</sub>
</div>
