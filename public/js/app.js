const DEMO_USER = "demo";
const DEMO_PASS = "demo123";

let dashboardData = null;
let dailyChart = null;
let statusChart = null;
let scoreChart = null;

function isLoggedIn() {
  return sessionStorage.getItem("logged_in") === "true";
}

function setLoggedIn(username) {
  sessionStorage.setItem("logged_in", "true");
  sessionStorage.setItem("username", username);
}

function logout() {
  sessionStorage.removeItem("logged_in");
  sessionStorage.removeItem("username");
  location.reload();
}

function showApp() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");
  document.getElementById("sidebar-user").textContent =
    `👤 ${sessionStorage.getItem("username") || DEMO_USER}`;
}

function showPage(page) {
  document.querySelectorAll(".page").forEach((el) => el.classList.add("hidden"));
  document.getElementById(`page-${page}`).classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === page);
  });
}

async function fetchData() {
  const response = await fetch("/api/jobs");
  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }
  return response.json();
}

function renderStatusBanner(data) {
  const banner = document.getElementById("status-banner");
  banner.classList.remove("hidden", "warn", "info");
  if (!data.ok) {
    banner.classList.add("warn");
    banner.innerHTML = `<strong>Google Sheets not connected</strong> — ${data.message}`;
    return;
  }
  if ((data.stats?.total_jobs || 0) === 0) {
    banner.classList.add("info");
    banner.textContent = `${data.message}. Run the agent locally (python main.py) to add jobs.`;
    return;
  }
  banner.classList.add("info");
  banner.textContent = data.message;
}

function renderStats(data) {
  const stats = data.stats || {};
  document.getElementById("stat-total").textContent = stats.total_jobs || 0;
  document.getElementById("stat-drafts").textContent = stats.drafts || 0;
  document.getElementById("stat-match").textContent = `${stats.match_rate || 0}%`;
  document.getElementById("stat-avg").textContent = `${stats.avg_score || 0}/10`;
  document.getElementById("metric-jobs").textContent = stats.total_jobs || 0;
  document.getElementById("metric-drafts").textContent = stats.drafts || 0;
  document.getElementById("an-total").textContent = stats.total_jobs || 0;
  document.getElementById("an-drafts").textContent = stats.drafts || 0;
  document.getElementById("an-skipped").textContent = stats.skipped || 0;
}

function renderProfile(data) {
  const profile = data.profile || {};
  document.getElementById("profile-line").textContent =
    `${profile.title || ""} · ${profile.rate || ""}`;

  document.getElementById("achievements").innerHTML = (profile.experience_highlights || [])
    .map((item) => `<div class="achievement">${item}</div>`)
    .join("");

  document.getElementById("about-content").innerHTML = `
    <h3>What it does</h3>
    <p>This <strong>AI agent</strong> automates my Upwork freelance workflow end-to-end:</p>
    <ol>
      <li><strong>Gmail</strong> — reads Vollna job alerts</li>
      <li><strong>Parser</strong> — extracts job title, budget, description</li>
      <li><strong>Scorer</strong> — rates jobs 1–10 against my skills profile</li>
      <li><strong>Gemini AI</strong> — writes tailored proposals</li>
      <li><strong>Gmail drafts</strong> — saves proposals ready to review</li>
      <li><strong>Google Sheets</strong> — logs every job (this dashboard)</li>
      <li><strong>Slack</strong> — notifies when a draft is ready</li>
    </ol>
    <h3>Stack</h3>
    <p>Python · Gmail API · Google Gemini · Google Sheets · Slack · Vercel</p>
    <h3>Profile</h3>
    <p><strong>${profile.my_name || ""}</strong> — ${profile.bio || ""}</p>
    <h3>Skills</h3>
    <p>${(profile.skills || []).join(", ")}</p>
  `;
}

function renderRecent(data) {
  const wrap = document.getElementById("recent-table-wrap");
  const rows = data.recent || [];
  if (!data.ok) {
    wrap.innerHTML = `<p class="alert warn">Fix the Google Sheets connection above to load job data.</p>`;
    return;
  }
  if (!rows.length) {
    wrap.innerHTML = `<p class="alert info">No job rows in the sheet yet. Run the agent locally with <code>python main.py</code>.</p>`;
    return;
  }
  const head = "<tr><th>Date</th><th>Title</th><th>Budget</th><th>Score</th><th>Status</th></tr>";
  const body = rows
    .map(
      (row) =>
        `<tr><td>${row.date || ""}</td><td>${row.title || ""}</td><td>${row.budget || ""}</td><td>${row.score || 0}</td><td>${row.status || ""}</td></tr>`
    )
    .join("");
  wrap.innerHTML = `<table>${head}${body}</table>`;
}

function renderProposals(data) {
  const container = document.getElementById("proposals-content");
  const drafts = data.drafts || [];
  if (!drafts.length) {
    container.innerHTML = `<p class="alert info">No proposals yet.</p>`;
    return;
  }
  container.innerHTML = `<p class="alert info">${drafts.length} proposal(s) drafted by the AI agent</p>`;
  drafts.forEach((draft) => {
    const card = document.createElement("details");
    card.className = "proposal-card";
    card.innerHTML = `
      <summary>${draft.title || "Job"} — ${draft.budget || ""}</summary>
      <div class="proposal-body">
        <p><strong>Score:</strong> ${draft.score || 0}/10</p>
        ${draft.url ? `<p><a href="${draft.url}" target="_blank" rel="noopener">Open job link</a></p>` : ""}
        <textarea readonly>${draft.proposal || ""}</textarea>
        <p class="caption">Also saved in Gmail → Drafts</p>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderStatusList(data) {
  const container = document.getElementById("status-list");
  const counts = data.status_counts || {};
  const total = data.stats?.total_jobs || 0;
  container.innerHTML = Object.entries(counts)
    .map(([status, count]) => {
      const pct = total ? Math.round((count / total) * 100) : 0;
      return `<div><strong>${status}:</strong> ${count} (${pct}%)</div>`;
    })
    .join("");
}

function renderCharts(data) {
  const dailyCtx = document.getElementById("daily-chart");
  const statusCtx = document.getElementById("status-chart");
  const scoreCtx = document.getElementById("score-chart");

  if (dailyChart) dailyChart.destroy();
  if (statusChart) statusChart.destroy();
  if (scoreChart) scoreChart.destroy();

  dailyChart = new Chart(dailyCtx, {
    type: "bar",
    data: {
      labels: (data.daily || []).map((item) => item.day),
      datasets: [{
        label: "Jobs",
        data: (data.daily || []).map((item) => item.jobs),
        backgroundColor: "#FF6B00",
      }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });

  const statusEntries = Object.entries(data.status_counts || {});
  statusChart = new Chart(statusCtx, {
    type: "doughnut",
    data: {
      labels: statusEntries.map(([name]) => name),
      datasets: [{
        data: statusEntries.map(([, count]) => count),
        backgroundColor: ["#22c55e", "#f59e0b", "#3b82f6", "#94a3b8"],
      }],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });

  const scores = data.scores || [];
  const bins = Array(10).fill(0);
  scores.forEach((score) => {
    const bucket = Math.max(0, Math.min(9, Math.floor(Number(score)) - 1));
    if (Number(score) >= 1 && Number(score) <= 10) bins[bucket] += 1;
  });
  scoreChart = new Chart(scoreCtx, {
    type: "bar",
    data: {
      labels: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
      datasets: [{ label: "Jobs", data: bins, backgroundColor: "#FF6B00" }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

function renderDashboard(data) {
  dashboardData = data;
  renderStatusBanner(data);
  renderProfile(data);
  renderStats(data);
  renderRecent(data);
  renderProposals(data);
  renderStatusList(data);
  renderCharts(data);
}

async function loadDashboard() {
  try {
    const data = await fetchData();
    renderDashboard(data);
  } catch (error) {
    const banner = document.getElementById("status-banner");
    banner.classList.remove("hidden");
    banner.classList.add("warn");
    banner.textContent = `Could not load dashboard data: ${error.message}`;
  }
}

document.getElementById("login-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const error = document.getElementById("login-error");
  if (username === DEMO_USER && password === DEMO_PASS) {
    error.classList.add("hidden");
    setLoggedIn(username);
    showApp();
    loadDashboard();
    return;
  }
  error.textContent = "Wrong username or password";
  error.classList.remove("hidden");
});

document.querySelectorAll(".nav-btn").forEach((btn) => {
  btn.addEventListener("click", () => showPage(btn.dataset.page));
});

document.getElementById("refresh-btn").addEventListener("click", loadDashboard);
document.getElementById("logout-btn").addEventListener("click", logout);

if (isLoggedIn()) {
  showApp();
  loadDashboard();
}
