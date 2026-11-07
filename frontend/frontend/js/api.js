// All backend communication lives here. UI code never calls fetch directly.
class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
  get isSessionExpired() { return this.status === 404 && /session/i.test(this.message); }
}

// Turn FastAPI error bodies ({detail: "..."} or validation arrays) into text.
function errText(body, fallback) {
  const d = body && body.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map(e => e.msg).join("; ");
  return fallback;
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(CONFIG.API_BASE + path, options);
  } catch {
    throw new ApiError(`Cannot reach the backend at ${CONFIG.API_BASE}. Make sure it is running.`, 0);
  }
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON body */ }
  if (!res.ok) throw new ApiError(errText(body, `Request failed (${res.status}).`), res.status);
  if (!body) throw new ApiError("The server returned an empty response.", res.status);
  return body;
}

const Api = {
  // XHR is used for upload so we can report real progress.
  upload(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      form.append("file", file);
      xhr.open("POST", CONFIG.API_BASE + "/api/upload");
      xhr.upload.onprogress = e => e.lengthComputable && onProgress(e.loaded / e.total);
      xhr.onerror = () => reject(new ApiError(`Cannot reach the backend at ${CONFIG.API_BASE}. Make sure it is running.`, 0));
      xhr.onload = () => {
        let body = null;
        try { body = JSON.parse(xhr.responseText); } catch {}
        if (xhr.status >= 200 && xhr.status < 300 && body) resolve(body);
        else reject(new ApiError(errText(body, `Upload failed (${xhr.status}).`), xhr.status));
      };
      xhr.send(form);
    });
  },
  clean: id => request(`/api/clean/${id}?drop_rows_with_missing=true`, { method: "POST" }),
  metadata: id => request(`/api/metadata/${id}`),
  generateCharts: id => request(`/api/generate-charts/${id}`, { method: "POST" }),
  visualize: id => request(`/api/visualize/${id}`, { method: "POST" }),
  analyze: id => request(`/api/analyze/${id}`, { method: "POST" }),
  deleteSession: id => request(`/api/session/${id}`, { method: "DELETE" }).catch(() => {}),
};
