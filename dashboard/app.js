// Interactive Frontend Controller for Resilient Multi-Agent Energy Management System

let powerChartInstance = null;
let voltageChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();

  document.getElementById("btn-run-sim").addEventListener("click", handleRunSimulation);
  document.getElementById("btn-send-chat").addEventListener("click", handleSendChat);
  document.getElementById("chat-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSendChat();
  });
});

async function initDashboard() {
  await loadAgentStatus();
  await loadBenchmarkMatrix();
  await loadTrajectoryData("resilient_false_data");
}

async function loadAgentStatus(runId = "resilient_false_data") {
  try {
    const res = await fetch(`/api/agents/status?run_id=${runId}`);
    const data = await res.json();
    renderAgentTrustCards(data.agents);
  } catch (e) {
    console.warn("Could not load agent status, using fallback", e);
  }
}

function renderAgentTrustCards(agents) {
  const container = document.getElementById("agent-trust-container");
  container.innerHTML = "";

  for (const [id, info] of Object.entries(agents)) {
    const trust = info.trust !== undefined ? info.trust : 1.0;
    const isQuarantined = trust < 0.40;

    let barColor = "var(--accent-emerald)";
    if (trust < 0.40) barColor = "var(--accent-rose)";
    else if (trust < 0.75) barColor = "var(--accent-amber)";

    const row = document.createElement("div");
    row.className = "agent-row";
    row.innerHTML = `
      <div class="agent-info">
        <h4>${id} ${isQuarantined ? '<span style="color:var(--accent-rose); font-size:0.75rem;">[QUARANTINED]</span>' : ''}</h4>
        <p>${info.role} • Bus ${info.bus || 'Global'}</p>
      </div>
      <div class="trust-gauge">
        <div class="trust-bar-bg">
          <div class="trust-bar-fill" style="width: ${Math.round(trust * 100)}%; background: ${barColor};"></div>
        </div>
        <div class="trust-val" style="color: ${barColor}">${trust.toFixed(2)}</div>
      </div>
    `;
    container.appendChild(row);

    // If solar is quarantined, highlight Bus 18 in red on SVG
    if (id === "solar_agent" && isQuarantined) {
      const node = document.getElementById("bus-18-node");
      if (node) node.setAttribute("fill", "var(--accent-rose)");
    }
  }
}

async function loadBenchmarkMatrix(scenario = "false_data") {
  try {
    const res = await fetch(`/api/metrics/benchmark-matrix?attack_scenario=${scenario}`);
    const data = await res.json();
    renderBenchmarkTable(data);
  } catch (e) {
    console.warn("Could not load benchmark table", e);
  }
}

function renderBenchmarkTable(rows) {
  const tbody = document.getElementById("bench-tbody");
  tbody.innerHTML = "";

  if (!rows || rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;">Execute scenario to populate table</td></tr>`;
    return;
  }

  rows.forEach(r => {
    const tr = document.createElement("tr");
    const isResilient = r.Controller.toLowerCase().includes("resilient");
    tr.style.background = isResilient ? "rgba(16, 185, 129, 0.08)" : "transparent";

    tr.innerHTML = `
      <td style="font-weight:600; color:${isResilient ? 'var(--accent-emerald)' : 'var(--text-main)'}">${r.Controller}</td>
      <td>€${r.Normal_Cost_EUR.toFixed(2)}</td>
      <td>€${r.Attack_Cost_EUR.toFixed(2)}</td>
      <td>${r.Attack_Violations_h} hrs</td>
      <td style="color:${r.Performance_Degradation > 0.1 ? 'var(--accent-rose)' : 'var(--accent-emerald)'}">
        ${(r.Performance_Degradation * 100).toFixed(2)}%
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadTrajectoryData(runId) {
  try {
    const res = await fetch(`/api/metrics/trajectory?run_id=${runId}&max_points=72`);
    const points = await res.json();
    if (points && points.length > 0) {
      updateKpis(points[points.length - 1]);
      renderCharts(points);
    }
  } catch (e) {
    console.error("Failed to load trajectory points", e);
  }
}

function updateKpis(latest) {
  if (!latest) return;
  document.getElementById("kpi-vmin").innerText = `${latest.v_min_pu.toFixed(4)} p.u.`;
  document.getElementById("kpi-soc").innerText = `${(latest.soc * 100).toFixed(1)}%`;
  document.getElementById("kpi-solar").innerText = `${latest.solar_mw.toFixed(2)} MW`;
  document.getElementById("kpi-ev").innerText = `${latest.ev_p_mw.toFixed(2)} MW`;
}

function renderCharts(points) {
  const labels = points.map(p => `T+${p.step}h`);
  const prices = points.map(p => p.price);
  const solars = points.map(p => p.solar_mw);
  const bess = points.map(p => p.battery_p_mw);
  const vmins = points.map(p => p.v_min_pu);

  // Power & Price Chart
  const ctxPower = document.getElementById("chart-power").getContext("2d");
  if (powerChartInstance) powerChartInstance.destroy();

  powerChartInstance = new Chart(ctxPower, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Wholesale Price (€/MWh)",
          data: prices,
          borderColor: "#3b82f6",
          borderWidth: 1.8,
          yAxisID: "y1",
          pointRadius: 0
        },
        {
          label: "Solar PV (MW)",
          data: solars,
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          fill: true,
          borderWidth: 1.5,
          yAxisID: "y",
          pointRadius: 0
        },
        {
          label: "BESS Power (MW)",
          data: bess,
          borderColor: "#8b5cf6",
          borderWidth: 1.5,
          yAxisID: "y",
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          title: { display: true, text: "Power (MW)", color: "#94a3b8" },
          grid: { color: "rgba(255,255,255,0.05)" }
        },
        y1: {
          position: "right",
          title: { display: true, text: "Price (€/MWh)", color: "#3b82f6" },
          grid: { drawOnChartArea: false }
        },
        x: { grid: { display: false } }
      }
    }
  });

  // Voltage Chart
  const ctxV = document.getElementById("chart-voltage").getContext("2d");
  if (voltageChartInstance) voltageChartInstance.destroy();

  voltageChartInstance = new Chart(ctxV, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Minimum Feeder Voltage (p.u.)",
          data: vmins,
          borderColor: "#10b981",
          borderWidth: 2,
          pointRadius: 0
        },
        {
          label: "ANSI Undervoltage Limit (0.95 p.u.)",
          data: labels.map(() => 0.95),
          borderColor: "rgba(244, 63, 94, 0.6)",
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0.88,
          max: 1.05,
          title: { display: true, text: "Voltage (p.u.)", color: "#94a3b8" },
          grid: { color: "rgba(255,255,255,0.05)" }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

async function handleRunSimulation() {
  const btn = document.getElementById("btn-run-sim");
  btn.disabled = true;
  btn.innerHTML = `<span class="badge-pulse"></span> Simulating...`;

  const controller = document.getElementById("select-controller").value;
  const attack = document.getElementById("select-attack").value;
  const steps = parseInt(document.getElementById("input-steps").value) || 72;

  try {
    const res = await fetch("/api/simulation/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        controller: controller,
        attack_scenario: attack,
        episode_length: steps,
        start_idx: 1000
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      const runId = `${controller}_${attack}`;
      document.getElementById("kpi-cost").innerText = `€${data.summary.total_operating_cost_eur.toLocaleString()}`;
      await loadAgentStatus(runId);
      await loadTrajectoryData(runId);
      await loadBenchmarkMatrix(attack === "none" ? "false_data" : attack);
    }
  } catch (e) {
    alert("Simulation execution error: " + e);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      Execute Scenario
    `;
  }
}

async function handleSendChat() {
  const input = document.getElementById("chat-input");
  const query = input.value.trim();
  if (!query) return;

  const chatBox = document.getElementById("chat-box");

  // Append user bubble
  const userBubble = document.createElement("div");
  userBubble.className = "chat-bubble bubble-user";
  userBubble.innerText = query;
  chatBox.appendChild(userBubble);
  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  // Append thinking bubble
  const thinkingBubble = document.createElement("div");
  thinkingBubble.className = "chat-bubble bubble-copilot";
  thinkingBubble.innerHTML = `<em>Consulting RAG knowledge base & AC power flow telemetry...</em>`;
  chatBox.appendChild(thinkingBubble);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const res = await fetch("/api/copilot/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, run_id: "resilient_false_data" })
    });
    const data = await res.json();

    let formatted = `<strong>Copilot:</strong>\n${data.response.replace(/\n/g, '<br>')}`;
    if (data.rag_context_snippets && data.rag_context_snippets.length > 0) {
      formatted += `<div style="margin-top:8px; font-size:0.75rem; color:var(--text-dim); border-top:1px solid var(--border-subtle); padding-top:6px;"><strong>Citations:</strong><br>${data.rag_context_snippets.slice(0, 2).join('<br>')}</div>`;
    }
    thinkingBubble.innerHTML = formatted;
  } catch (e) {
    thinkingBubble.innerText = "Error querying Copilot: " + e;
  }
  chatBox.scrollTop = chatBox.scrollHeight;
}
