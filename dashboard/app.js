/* Local API data only. No fabricated analytics or HTML interpolation of event data. */
"use strict";
const $ = (id) => document.getElementById(id);
const charts = {};
let refreshing = null;
let runningDemo = false;

async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(),
    options.method ? 60000 : 12000,
  );
  try {
    const response = await fetch(`${API_URL}/${path}`, {
      ...options,
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(
        data.error || `API returned HTTP ${response.status}`,
      );
      error.status = response.status;
      throw error;
    }
    return data;
  } finally {
    clearTimeout(timer);
  }
}

function icon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("class", "icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `/assets/vendor/lucide.svg#${name}`);
  svg.append(use);
  return svg;
}

function setStatus(id, text, state) {
  $(id).textContent = text;
  $(id).className = `status-${state}`;
}

async function refreshHealth() {
  try {
    const health = await api("health");
    setStatus("status-api", "Online", "good");
    setStatus(
      "status-engine",
      health.detection_engine === "ready" ? "Ready" : "Unavailable",
      health.detection_engine === "ready" ? "good" : "bad",
    );
    setStatus(
      "status-model",
      health.model.ready ? "Loaded" : "Not loaded",
      health.model.ready ? "good" : "warn",
    );
    setStatus(
      "status-demo",
      health.demo_model.ready ? "Available · synthetic only" : "Not enabled",
      "warn",
    );
    setStatus(
      "status-risk",
      health.risk_engine === "ready" ? "Ready" : "Unavailable",
      health.risk_engine === "ready" ? "good" : "bad",
    );
    const full = health.operating_mode === "FULL_MODEL_MODE";
    setStatus(
      "status-mode",
      full ? "FULL MODEL MODE" : "DEMO MODE",
      full ? "good" : "warn",
    );
    $("mode-title").textContent = full ? "Model ready" : "Rules-only demo mode";
    $("mode-message").textContent = full
      ? "Ready. Choose an example below or submit flow data. This page never monitors your network automatically."
      : "The model is unavailable, but the examples still work using security rules only.";
    setStatus(
      "status-database",
      health.storage === "ready" ? "Connected" : "Error",
      health.storage === "ready" ? "good" : "bad",
    );
    $("model-note").textContent = health.model.ready
      ? "The selected model checks examples and submitted flow data. Model confidence is not a guarantee that an attack occurred."
      : `Model unavailable: ${health.model.error}. Examples use rules only; model predictions are not available.`;
  } catch (error) {
    setStatus(
      "status-api",
      error.status ? "Online · API error" : "Offline",
      "bad",
    );
    for (const id of [
      "status-engine",
      "status-model",
      "status-demo",
      "status-database",
      "status-risk",
      "status-mode",
    ])
      setStatus(id, "Unavailable", "bad");
    $("model-note").textContent = error.message;
    $("mode-title").textContent = "Connection unavailable";
    $("mode-message").textContent = "API readiness could not be verified.";
  }
}

function dateText(timestamp) {
  if (!timestamp) return "Unavailable";
  const date = new Date(
    timestamp.includes("T") ? timestamp : timestamp.replace(" ", "T") + "Z",
  );
  return Number.isNaN(date.getTime())
    ? timestamp
    : date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
}

function showChart(id, type, labels, datasets, options = {}) {
  const hasData = datasets.some((set) => set.data.some((value) => value > 0));
  $(id + "-empty").hidden = hasData;
  $(id + "-chart").hidden = !hasData;
  if (!window.Chart) {
    $(id + "-chart").hidden = true;
    $(id + "-empty").hidden = false;
    $(id + "-empty").textContent =
      "Chart library unavailable. Counts remain available below.";
    return;
  }
  const settings = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: {
        display: type === "doughnut",
        position: "bottom",
        labels: {
          color: "#a4afb9",
          boxWidth: 9,
          padding: 16,
          font: { size: 10 },
        },
      },
    },
    ...options,
  };
  if (charts[id]) {
    charts[id].data = { labels, datasets };
    charts[id].options = settings;
    charts[id].update("none");
  } else {
    charts[id] = new Chart($(id + "-chart"), {
      type,
      data: { labels, datasets },
      options: settings,
    });
  }
}

function renderMetrics(data) {
  $("kpi-total").textContent = data.total_alerts.toLocaleString();
  $("kpi-high").textContent = (data.by_severity.High || 0).toLocaleString();
  $("kpi-medium").textContent = (data.by_severity.Medium || 0).toLocaleString();
  $("kpi-low").textContent = (data.by_severity.Low || 0).toLocaleString();
  $("kpi-active").textContent = data.active_alerts.toLocaleString();
  $("kpi-scope").textContent =
    `${data.demo_alerts} demo · ${data.observed_alerts} submitted / legacy`;
  const axis = {
    grid: { color: "#dce5df" },
    ticks: { color: "#64736a", font: { size: 10 }, precision: 0 },
    beginAtZero: true,
  };
  const times = data.timeline.map((point) => point.hour.slice(11, 16));
  showChart(
    "timeline",
    "line",
    times,
    [
      {
        label: "Alerts",
        data: data.timeline.map((point) => point.count),
        borderColor: "#18764f",
        backgroundColor: "#18764f18",
        fill: true,
        tension: 0.25,
        pointRadius: 3,
        yAxisID: "y",
      },
      {
        label: "Average risk",
        data: data.timeline.map((point) => point.average_risk),
        borderColor: "#28699e",
        borderDash: [4, 4],
        pointRadius: 2,
        yAxisID: "risk",
      },
    ],
    {
      scales: {
        x: {
          ...axis,
          grid: { display: false },
          ticks: { ...axis.ticks, maxTicksLimit: 8 },
        },
        y: {
          ...axis,
          title: { display: true, text: "Alerts", color: "#64736a" },
        },
        risk: {
          ...axis,
          position: "right",
          max: 1000,
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Average risk", color: "#64736a" },
        },
      },
      plugins: {
        legend: {
          display: true,
          labels: { color: "#64736a", boxWidth: 10, font: { size: 10 } },
        },
      },
    },
  );
  $("timeline-summary").textContent =
    data.timeline
      .map(
        (point) =>
          `${point.hour}: ${point.count} alerts, mean risk ${point.average_risk ?? "unavailable"}`,
      )
      .join("; ") || "No alerts in last 24 hours";
  const severity = [
    "Low",
    "Medium",
    "High",
    ...Object.keys(data.by_severity).filter(
      (name) => !["Low", "Medium", "High"].includes(name),
    ),
  ];
  showChart(
    "severity",
    "doughnut",
    severity,
    [
      {
        data: severity.map((name) => data.by_severity[name] || 0),
        backgroundColor: ["#18764f", "#d69a27", "#c34850", "#a4afb9"],
        borderWidth: 0,
      },
    ],
    { cutout: "76%" },
  );
  $("severity-summary").textContent = severity
    .map((name) => `${name}: ${data.by_severity[name] || 0}`)
    .join(" · ");
  const categories = Object.keys(data.by_category);
  showChart(
    "category",
    "bar",
    categories.map(categoryLabel),
    [
      {
        label: "Saved alerts",
        data: Object.values(data.by_category),
        backgroundColor: "#18764f",
        borderRadius: 3,
        maxBarThickness: 30,
      },
    ],
    {
      indexAxis: "y",
      scales: { x: axis, y: { ...axis, grid: { display: false } } },
    },
  );
  $("category-summary").textContent =
    categories.map((name) => `${name}: ${data.by_category[name]}`).join("; ") ||
    "No stored categories";
  const sourceNames = Object.keys(data.by_source);
  showChart(
    "source",
    "bar",
    sourceNames.map(sourceLabel),
    [
      {
        label: "Saved alerts",
        data: Object.values(data.by_source),
        backgroundColor: ["#28699e", "#18764f", "#d69a27", "#a4afb9"],
        borderRadius: 4,
        maxBarThickness: 38,
      },
    ],
    { scales: { x: { ...axis, grid: { display: false } }, y: axis } },
  );
  $("source-summary").textContent =
    sourceNames
      .map((name) => `${name.toUpperCase()}: ${data.by_source[name]}`)
      .join(" · ") || "No stored detections";
}

function renderAlerts(alerts) {
  const body = $("alerts-body");
  body.replaceChildren();
  $("shown-count").textContent = alerts.length;
  const filtered = ["severity", "category", "source"].some(
    (name) => $("filter-" + name).value,
  );
  $("empty-state").hidden = alerts.length > 0;
  $("empty-state").querySelector("h3").textContent = filtered
    ? "No alerts match these filters"
    : "No alerts detected yet";
  for (const alert of alerts) {
    const row = body.insertRow();
    const time = row.insertCell();
    time.className = "table-time";
    time.textContent = dateText(alert.timestamp);
    const category = row.insertCell();
    const title = document.createElement("div");
    title.className = "alert-category";
    title.textContent = categoryLabel(alert.category || alert.title);
    category.append(title);
    const provenance = document.createElement("span");
    provenance.className = alert.is_demo ? "demo-record" : "alert-meta";
    provenance.textContent = alert.is_demo
      ? "Demo example"
      : alert.model_kind === "offline_rules"
        ? "Saved capture · rules only"
        : "Submitted data";
    category.append(provenance);
    const severity = row.insertCell();
    const badge = document.createElement("span");
    badge.className =
      "badge " +
      (["Low", "Medium", "High"].includes(alert.severity)
        ? `severity-${alert.severity.toLowerCase()}`
        : "");
    badge.textContent = alert.severity
      ? `${alert.severity} attention`
      : "Unknown";
    severity.append(badge);
    const score = document.createElement("span");
    score.className = "risk-value";
    score.textContent = `${alert.risk_score ?? "—"} / 1000 risk score`;
    severity.append(score);
    const action = row.insertCell();
    const button = document.createElement("button");
    button.className = "button subtle";
    button.textContent = "View details";
    button.setAttribute(
      "aria-label",
      `View details for ${categoryLabel(alert.category || alert.title)}`,
    );
    button.addEventListener("click", () => showDetails(alert.id));
    action.append(button);
  }
}

function categoryLabel(category) {
  return (
    {
      PORT_SCAN: "Port scan",
      BRUTE_FORCE: "Login guessing",
      DOS: "Traffic flood",
      OTHER_ATTACK: "Other suspicious activity",
      BENIGN: "Normal traffic",
    }[category] || category
  );
}

function sourceLabel(source) {
  return (
    {
      ml: "Model",
      rule: "Security rule",
      both: "Model + rule",
      offline_rules: "Offline rules",
    }[source] ||
    source ||
    "Unknown"
  );
}

function refreshDashboard() {
  if (refreshing) return refreshing;
  const scope = $("scope").value;
  const query = new URLSearchParams({ mode: scope, limit: "50" });
  for (const name of ["severity", "category", "source"])
    if ($("filter-" + name).value) query.set(name, $("filter-" + name).value);
  refreshing = (async () => {
    try {
      const [metrics, alerts] = await Promise.all([
        api(`metrics?mode=${scope}`),
        api(`alerts?${query}`),
      ]);
      renderMetrics(metrics);
      renderAlerts(alerts);
      $("api-error").hidden = true;
      $("updated").textContent =
        `Updated ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
    } catch (error) {
      $("api-error").hidden = false;
      $("api-error").textContent =
        `Alert data unavailable: ${error.message}. Any displayed values are from the last successful refresh.`;
      $("updated").textContent = "Refresh failed · data may be stale";
    }
    await refreshHealth();
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

async function refreshAfterChange() {
  if (refreshing) await refreshing;
  await refreshDashboard();
}

function detailPair(list, label, value) {
  const group = document.createElement("div"),
    term = document.createElement("dt"),
    description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value ?? "Unavailable";
  group.append(term, description);
  list.append(group);
}

async function showDetails(id) {
  const dialog = $("alert-dialog"),
    content = $("detail-content");
  content.textContent = "Loading stored alert evidence…";
  if (!dialog.open) dialog.showModal();
  try {
    const alert = await api(`alerts/${id}`);
    $("detail-title").textContent =
      `Alert #${alert.id} · ${alert.category || alert.title}`;
    content.replaceChildren();
    const provenance = document.createElement("p");
    provenance.className = "notice";
    provenance.textContent = alert.is_demo
      ? "DEMO EXAMPLE · Simulated data, not an observation from your network."
      : alert.model_kind === "offline_rules"
        ? "SAVED CAPTURE · Packet-header rules only; no model prediction was applied."
        : "SUBMITTED DATA · Available evidence is shown below.";
    content.append(provenance);
    const list = document.createElement("dl");
    list.className = "detail-list";
    const values = {
      "Model label": alert.label ?? "Not used",
      "Alert type": categoryLabel(alert.category || alert.title),
      "Model confidence":
        alert.confidence == null
          ? "Not used"
          : `${(alert.confidence * 100).toFixed(1)}% model confidence`,
      "Risk score": `${alert.risk_score} / 1000`,
      "Attention level": alert.severity,
      "Found by": sourceLabel(alert.detection_source || alert.source),
      Time: dateText(alert.timestamp),
      Status: alert.status,
      "Data source": alert.model_kind,
      "Source IP": alert.source_ip,
      "Destination IP": alert.destination_ip,
      Example: alert.scenario,
    };
    Object.entries(values).forEach(([key, value]) =>
      detailPair(list, key, value),
    );
    content.append(list);
    const heading = document.createElement("h3");
    heading.textContent = "Rule evidence";
    content.append(heading);
    for (const match of alert.rule_matches) {
      const rule = document.createElement("p");
      rule.className = "evidence-rule";
      rule.textContent = `${match.rule}: ${match.message}`;
      content.append(rule);
    }
    if (!alert.rule_matches.length) {
      const p = document.createElement("p");
      p.textContent = "No deterministic rule matches recorded.";
      content.append(p);
    }
    if (alert.evidence.risk_factors) {
      const factors = alert.evidence.risk_factors;
      const p = document.createElement("p");
      p.className = "evidence-rule";
      p.textContent = `Risk: ${factors.likelihood} likelihood × ${factors.impact} impact × ${factors.exposure} exposure = ${alert.risk_score}`;
      content.append(p);
    }
    const details = document.createElement("details"),
      summary = document.createElement("summary"),
      pre = document.createElement("pre");
    summary.textContent = "Input and rule evidence";
    pre.textContent = Object.keys(alert.evidence).length
      ? JSON.stringify(alert.evidence, null, 2)
      : "Evidence was not retained for this legacy record.";
    details.append(summary, pre);
    content.append(details);
  } catch (error) {
    content.textContent = `Evidence unavailable: ${error.message}`;
  }
}

async function runScenario(name) {
  if (runningDemo) return;
  runningDemo = true;
  const buttons = document.querySelectorAll("[data-scenario], #reset-demo");
  buttons.forEach((button) => {
    button.disabled = true;
  });
  $("demo-result").className = "demo-result";
  $("demo-result").textContent = "Checking this example…";
  try {
    const result = await api("demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: name }),
    });
    $("demo-result").className = "demo-result success";
    const outcome = result.alert_generated
      ? `${categoryLabel(result.category)} · ${result.severity} attention · risk score ${result.risk_score} out of 1000. Found by ${sourceLabel(result.detection_source).toLowerCase()}. Alert #${result.alert_id} saved.`
      : `${categoryLabel(result.category)} · no alert was created.`;
    $("demo-result").textContent =
      `Demo example complete. ${outcome} ${result.confidence == null ? "Model not used; security rules only." : "The model was used with security rules."}`;
    if (result.alert_id) {
      const button = document.createElement("button");
      button.textContent = "View evidence";
      button.addEventListener("click", () => showDetails(result.alert_id));
      $("demo-result").append(button);
    }
    await refreshAfterChange();
  } catch (error) {
    $("demo-result").className = "demo-result error";
    $("demo-result").textContent = `Demo failed: ${error.message}`;
  } finally {
    runningDemo = false;
    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

document
  .querySelectorAll("[data-scenario]")
  .forEach((button) =>
    button.addEventListener("click", () =>
      runScenario(button.dataset.scenario),
    ),
  );
$("reset-demo").addEventListener("click", async () => {
  if (
    !window.confirm(
      "Delete only Demo / Simulated alerts? Submitted and legacy records will be preserved.",
    )
  )
    return;
  $("reset-demo").disabled = true;
  try {
    const result = await api("demo/alerts", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    });
    $("demo-result").className = "demo-result";
    $("demo-result").textContent =
      `Cleared ${result.deleted} demo alerts. Submitted and legacy records preserved.`;
    await refreshAfterChange();
  } catch (error) {
    $("demo-result").className = "demo-result error";
    $("demo-result").textContent = `Reset failed: ${error.message}`;
  } finally {
    $("reset-demo").disabled = false;
  }
});
$("refresh").addEventListener("click", refreshAfterChange);
for (const id of [
  "scope",
  "filter-severity",
  "filter-category",
  "filter-source",
])
  $(id).addEventListener("change", refreshAfterChange);
$("close-dialog").addEventListener("click", () => $("alert-dialog").close());
document.querySelectorAll(".main-nav a").forEach((link) =>
  link.addEventListener("click", () => {
    const section = document.querySelector(link.hash);
    if (section instanceof HTMLDetailsElement) section.open = true;
  }),
);
$("analytics-details").addEventListener("toggle", () => {
  if ($("analytics-details").open)
    requestAnimationFrame(() =>
      Object.values(charts).forEach((chart) => chart.resize()),
    );
});
refreshDashboard();
setInterval(refreshDashboard, 5000);

async function loadCaptures() {
  try {
    const data = await api("captures");
    $("capture-file").replaceChildren();
    for (const file of data.captures) {
      const option = document.createElement("option");
      option.value = file.filename;
      option.textContent = file.filename;
      $("capture-file").append(option);
    }
    if (!data.captures.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No lab captures found";
      $("capture-file").append(option);
    }
  } catch (error) {
    $("capture-result").textContent =
      `Capture catalogue unavailable: ${error.message}`;
  }
}
$("process-capture").addEventListener("click", async () => {
  $("process-capture").disabled = true;
  $("capture-result").textContent =
    "Reading stored packet headers → aggregated rule counters → risk → storage…";
  try {
    const result = await api("captures/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ capture: $("capture-file").value }),
    });
    $("capture-result").textContent =
      `Offline / Rules only · ${result.analysis.capture} · ${result.analysis.packets} packets read · ${result.alerts_generated} alert(s) stored. No benchmark ML applied; no matched rule does not establish benign traffic.`;
    const first = result.results.find((item) => item.alert_generated);
    if (first) {
      const button = document.createElement("button");
      button.textContent = "View capture evidence";
      button.addEventListener("click", () => showDetails(first.alert_id));
      $("capture-result").append(button);
    }
    await refreshAfterChange();
  } catch (error) {
    $("capture-result").textContent =
      `Capture analysis failed: ${error.message}`;
  } finally {
    $("process-capture").disabled = false;
  }
});
loadCaptures();
