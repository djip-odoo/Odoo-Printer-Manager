// UI helpers
function setText(id, txt) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerText = typeof txt === "string" ? txt : JSON.stringify(txt, null, 2);
}

function setInputValue(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val || "";
}

function disable(id, yes = true) {
  const el = document.getElementById(id);
  if (el) el.disabled = !!yes;
}

function showToast(msg) {
  const out = document.getElementById("serviceOutput");
  if (out) out.innerText = `${new Date().toLocaleTimeString()} — ${msg}\n` + out.innerText;
}

// Fetch device IP
async function fetchIp() {
  try {
    setInputValue("deviceIp", "Fetching IP");
    const out = await window.serviceApi.getIp();
    const ip = (out || "").trim().split("\n")[0] || "";
    setInputValue("deviceIp", ip);
    renderManualPrinters(ip);
    return ip;
  } catch (e) {
    setText("serviceOutput", `Failed to get IP: ${e}`);
    return "";
  }
}

// Build base URL
function buildBaseUrl() {
  const ip = document.getElementById("deviceIp").value.trim();
  const host = ip;
  if (!host) throw new Error("No device IP found");
  return `http://${host}`;
}

// Build printer URLs and display
function displayPrinterUrls(list = []) {
  const outputEl = document.getElementById("printerOutput");
  const baseHost = document.getElementById("deviceIp").value.trim();
  if (!baseHost) {
    outputEl.innerText = "No IP/override set to build printer URLs";
    return;
  }

  if (!list.length) {
    outputEl.innerText = "No printers found";
    return;
  }

  const urls = list.map(p => {
    const vendorId = p.vendor_id || p.vendorID || "";
    const productId = p.product_id || p.productID || "";
    return `${baseHost}/vid/${vendorId}/pid/${productId}`;
  });

  renderPrinters(urls)
  outputEl.innerText = "All printers listed";
}

// Fetch printer list
async function fetchPrinterList() {
  try {
    const base = buildBaseUrl();
    const url = `${base}/printer-list`;
    setText("printerOutput", "Fetching printer list...");
    disable("btnRefreshPrinters", true);

    const res = await fetch(url, { method: "GET" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    if (!data || data.status !== "success") throw new Error("Bad response from server");

    const list = data.message || [];
    displayPrinterUrls(list);

  } catch (err) {
    setText("printerOutput", "Error fetching printers, may service is down");
  } finally {
    disable("btnRefreshPrinters", false);
  }
}

// Service control wrappers
async function runAddService() {
  setText("serviceOutput", "Adding service...");
  disable("btnAddService", true);
  try {
    const out = await window.serviceApi.addService();
    setText("serviceOutput", out);
    showToast("Add service finished");
  } catch (e) {
    setText("serviceOutput", "Add failed: " + e);
  } finally {
    disable("btnAddService", false);
  }
}

async function runDeleteService() {
  setText("serviceOutput", "Deleting service...");
  disable("btnDeleteService", true);
  try {
    const out = await window.serviceApi.deleteService();
    setText("serviceOutput", out);
    showToast("Delete service finished");
  } catch (e) {
    setText("serviceOutput", "Delete failed: " + e);
  } finally {
    disable("btnDeleteService", false);
  }
}

async function runRestartService() {
  setText("serviceOutput", "Restarting service...");
  disable("btnRestartService", true);
  try {
    const out = await window.serviceApi.restartService();
    setText("serviceOutput", out);
    showToast("Restart service finished");
  } catch (e) {
    setText("serviceOutput", "Restart failed: " + e);
  } finally {
    disable("btnRestartService", false);
  }
}

// Check service status
async function checkServiceStatus() {
  setText("serviceOutput", "Checking service status...");

  try {
    const baseHost = document.getElementById("deviceIp").value.trim();
    if (!baseHost) {
      setText("serviceOutput", "No device IP set.");
      return;
    }

    const url = `http://${baseHost}`;
    const res = await fetch(url, { method: "GET" });

    if (res.status === 200) {
      setText("serviceOutput", `Service is running at ${url}`);
    } else {
      setText("serviceOutput", `Service returned HTTP ${res.status}`);
    }
  } catch (e) {
    setText("serviceOutput", `Failed to reach service, may service is down: ${e}`);
  }
}


// Wire buttons & auto-run
window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btnFetchIp").addEventListener("click", fetchIp);
  document.getElementById("btnRefreshPrinters").addEventListener("click", fetchPrinterList);
  document.getElementById("btnAddService").addEventListener("click", runAddService);
  document.getElementById("btnDeleteService").addEventListener("click", runDeleteService);
  document.getElementById("btnRestartService").addEventListener("click", runRestartService);

  // Auto-run: try fetch IP, then printer list
  (async () => {
    try { await fetchIp(); } catch { }
    try { await fetchPrinterList(); } catch { }
    try {
      await checkServiceStatus();  // <-- Check service automatically
    } catch {

    }
  })();
});



// Example JS to render printer URLs with copy button
const printerListEl = document.getElementById('printerList');

function renderPrinters(printers = [], demo = false) {
  printerListEl.innerHTML = '';
  if (printers.length === 0) {
    printerListEl.innerHTML = '<p class="empty">No printers found.</p>';
    return;
  }

  printers.forEach(url => {
    const printerEl = document.createElement('div');
    printerEl.className = 'printer-item';

    const urlEl = document.createElement('span');
    urlEl.className = 'printer-url';
    urlEl.textContent = demo ? "Demo url:" + url : url;

    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn btn-copy';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(url);
      copyBtn.textContent = 'Copied!';
      setTimeout(() => copyBtn.textContent = 'Copy', 1500);
    };

    printerEl.appendChild(urlEl);
    printerEl.appendChild(copyBtn);
    printerListEl.appendChild(printerEl);
  });
}

renderPrinters(['192.168.1.101:8000/vid/1234/pid/3456'], true);
const manualIpInput = document.getElementById('manualIp');
const manualUrlOutput = document.getElementById('manualUrlOutput');
const btnGenerateUrl = document.getElementById('btnGenerateUrl');

const LOCAL_STORAGE_KEY = 'manualPrinters';

// Load saved printers from localStorage
function loadManualPrinters() {
  const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
  return saved ? JSON.parse(saved) : [];
}

// Save printers to localStorage
function saveManualPrinters(list) {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(list));
}
// Render manual printers
function renderManualPrinters(newIp) {
  const printers = loadManualPrinters();
  manualUrlOutput.innerHTML = '';

  if (!printers.length) {
    manualUrlOutput.innerHTML = '<p class="empty">No IP printers saved.</p>';
    return;
  }

  const ipPrefix = document.getElementById("deviceIp").value.trim() || newIp || '';

  printers.forEach((printer, index) => {
    const printerEl = document.createElement('div');
    printerEl.className = 'printer-item';
    printerEl.style.display = 'flex';
    printerEl.style.alignItems = 'center';
    printerEl.style.justifyContent = 'space-between';
    printerEl.style.gap = '10px';

    // URL
    const urlEl = document.createElement('span');
    urlEl.className = 'printer-url';
    urlEl.textContent = ipPrefix + printer.url;
    urlEl.style.flex = '1';
    urlEl.style.overflowWrap = 'anywhere';

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'btn btn-copy';
    copyBtn.textContent = 'Copy';
    copyBtn.onclick = () => {
      navigator.clipboard.writeText(ipPrefix + printer.url);
      copyBtn.textContent = 'Copied!';
      setTimeout(() => copyBtn.textContent = 'Copy', 1500);
    };

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn btn-red';
    deleteBtn.textContent = 'Delete';
    deleteBtn.onclick = () => {
      const list = loadManualPrinters();
      list.splice(index, 1);
      saveManualPrinters(list);
      renderManualPrinters();
    };

    printerEl.appendChild(urlEl);
    printerEl.appendChild(deleteBtn);
    printerEl.appendChild(copyBtn);
    manualUrlOutput.appendChild(printerEl);
  });
}

// Add manual printer
btnGenerateUrl.onclick = () => {
  const ip = manualIpInput.value.trim();
  if (!ip) {
    manualUrlOutput.innerHTML = '<p class="empty">Please enter an IP.</p>';
    return;
  }

  const url = `/ip/${ip}`;

  const printers = loadManualPrinters();
  printers.push({ url });
  saveManualPrinters(printers);

  manualIpInput.value = '';
  renderManualPrinters();
};

