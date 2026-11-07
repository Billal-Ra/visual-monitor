async function loadStatus() {
  const res = await fetch("status.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load status.json");
  return res.json();
}

function fmt(ts) {
  if (!ts) return "—";
  const d = new Date(ts);
  return d.toLocaleString();
}

function badgeClass(state) {
  if (state === "changed") return "changed";
  if (state === "error") return "error";
  return "ok";
}

function renderCard(item) {
  const state = item.state || "ok";
  const score = (item.score === null || item.score === undefined) ? "—" : item.score.toFixed(4);

  const shot = item.latest_screenshot ? `images/${item.latest_screenshot}` : null;
  const diff = item.latest_diff ? `images/${item.latest_diff}` : null;

  return `
  <div class="card" data-name="${(item.name || "").toLowerCase()}" data-state="${state}">
    <div class="row">
      <div class="name">${item.name}</div>
      <div class="badge ${badgeClass(state)}">${state.toUpperCase()}</div>
    </div>

    <div class="meta">
      <div><a href="${item.url}" target="_blank" rel="noopener">Open page</a></div>
      <div>Last checked: <b>${fmt(item.last_checked)}</b></div>
      <div>Last changed: <b>${fmt(item.last_changed)}</b></div>
      <div>Similarity score: <b>${score}</b> (threshold: ${item.threshold})</div>
      ${item.error ? `<div style="margin-top:8px;color:#fde68a;">Error: ${item.error}</div>` : ""}
    </div>

    <div class="thumbRow">
      ${shot ? `
      <div class="thumb">
        <img src="${shot}" alt="latest screenshot">
        <div class="small">Latest screenshot</div>
      </div>` : ""}
      ${diff ? `
      <div class="thumb">
        <img src="${diff}" alt="latest diff">
        <div class="small">Latest diff</div>
      </div>` : ""}
    </div>
  </div>
  `;
}

function applyFilters() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const f = document.getElementById("filter").value;

  document.querySelectorAll(".card").forEach(card => {
    const name = card.dataset.name || "";
    const state = card.dataset.state || "ok";
    const matchQ = !q || name.includes(q);
    const matchF = (f === "all") || (f === state);
    card.style.display = (matchQ && matchF) ? "" : "none";
  });
}

(async function init() {
  try {
    const data = await loadStatus();

    document.getElementById("lastUpdated").textContent =
      "Last updated: " + fmt(data.generated_at);

    const total = data.items.length;
    const changed = data.items.filter(x => x.state === "changed").length;
    const errors = data.items.filter(x => x.state === "error").length;
    document.getElementById("summary").textContent =
      `${total} pages • ${changed} changed • ${errors} errors`;

    const grid = document.getElementById("grid");
    grid.innerHTML = data.items.map(renderCard).join("");

    document.getElementById("search").addEventListener("input", applyFilters);
    document.getElementById("filter").addEventListener("change", applyFilters);
  } catch (e) {
    document.getElementById("summary").textContent = "Dashboard failed to load";
    console.error(e);
  }
})();
