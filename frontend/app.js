const API = "http://127.0.0.1:8000";

/* =====================================================
   LOAD DASHBOARD (index.html)
===================================================== */

window.onload = function () {
    initialiseChat();

    // Overview page only
    if (document.getElementById("movementChart")) {
        loadOverview();
        loadMovement();
        loadStay();
        loadInsight();
    }

    // City page only
    if (document.getElementById("heatmapFrame")) {
        loadCityInsight();
    }
};


/* =====================================================
   OVERVIEW KPI
===================================================== */

async function loadOverview() {
    try {
        const r    = await fetch(`${API}/overview`);
        const data = await r.json();

        document.getElementById("movement").innerText = Math.round(data.movement).toLocaleString();
        document.getElementById("events").innerText   = data.events;
        document.getElementById("stay").innerText     = data.avg_stay.toFixed(1) + " min";
    } catch (error) {
        console.error(error);
    }
}


/* =====================================================
   AI INSIGHT CARD
===================================================== */

async function loadInsight() {
    try {
        const r    = await fetch(`${API}/insight`);
        const data = await r.json();

        document.getElementById("insight").innerText = data.insight;
    } catch (error) {
        console.error(error);
        document.getElementById("insight").innerText = "AI insight unavailable.";
    }
}


/* =====================================================
   MOVEMENT CHART
===================================================== */

async function loadMovement() {
    try {
        const r    = await fetch(`${API}/movement`);
        const data = await r.json();

        Plotly.newPlot(
            "movementChart",
            [{
                x:    data.map(d => d.timestamp),
                y:    data.map(d => d.amount),
                type: "scatter",
                mode: "lines",
                line: { color: "#17324d", width: 3 },
                fill: "tozeroy",
            }],
            {
                margin:       { t: 20 },
                paper_bgcolor: "white",
                plot_bgcolor:  "white",
                xaxis: { showgrid: false },
                yaxis: { gridcolor: "#e5e7eb" },
            }
        );
    } catch (error) {
        console.error(error);
    }
}


/* =====================================================
   STAY CHART
===================================================== */

async function loadStay() {
    try {
        const r    = await fetch(`${API}/stay`);
        const data = await r.json();

        Plotly.newPlot(
            "stayChart",
            [{
                x:           data.map(d => d.avg_stay_min),
                y:           data.map(d => d.sensor),
                type:        "bar",
                orientation: "h",
                marker:      { color: "#17324d" },
            }],
            {
                margin:        { t: 20 },
                paper_bgcolor: "white",
                plot_bgcolor:  "white",
            }
        );
    } catch (error) {
        console.error(error);
    }
}


/* =====================================================
   CHAT — INITIALISE
===================================================== */

function initialiseChat() {
    const popup    = document.getElementById("chat-popup");
    const toggle   = document.getElementById("chat-toggle");
    const textarea = document.getElementById("question");

    toggle.onclick = function () {
        if (popup.style.display === "flex") {
            popup.style.display = "none";
        } else {
            popup.style.display = "flex";
            textarea.focus();
        }
    };

    textarea.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = Math.min(this.scrollHeight, 120) + "px";
    });

    textarea.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            askAI();
        }
    });

    setTimeout(() => toggle.classList.add("pulse"),    1500);
    setTimeout(() => toggle.classList.remove("pulse"), 7000);
}


/* =====================================================
   CHAT — HELPERS
===================================================== */

function quickAsk(btn) {
    document.getElementById("question").value = btn.innerText;
    askAI();
}

function addMessage(text, type) {
    const chat   = document.getElementById("chat-messages");
    const bubble = document.createElement("div");
    bubble.className   = type === "user" ? "user-msg" : "ai-msg";
    bubble.textContent = text;
    chat.appendChild(bubble);
    chat.scrollTo({ top: chat.scrollHeight, behavior: "smooth" });
}

function showTyping() {
    const chat   = document.getElementById("chat-messages");
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.id        = "typing";
    typing.innerHTML = "<span></span><span></span><span></span>";
    chat.appendChild(typing);
    chat.scrollTo({ top: chat.scrollHeight, behavior: "smooth" });
}

function removeTyping() {
    const t = document.getElementById("typing");
    if (t) t.remove();
}


/* =====================================================
   CHAT — ASK AI
===================================================== */

async function askAI() {
    const questionEl = document.getElementById("question");
    const question   = questionEl.value.trim();
    if (!question) return;

    addMessage(question, "user");
    questionEl.value      = "";
    questionEl.style.height = "auto";
    showTyping();

    try {
        const r = await fetch(`${API}/ask`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ question }),
        });
        const data = await r.json();
        removeTyping();
        addMessage(data.answer, "ai");
    } catch (error) {
        console.error(error);
        removeTyping();
        addMessage("AI service unavailable.", "ai");
    }
}


/* =====================================================
   CITY — HEATMAP TABS
===================================================== */

function switchHeatmap(type, btn) {
    const frame = document.getElementById("heatmapFrame");
    if (!frame) return;

    const buttons = document.querySelectorAll(".tab-btn");

    buttons.forEach(b => b.classList.remove("active"));
    if (btn) btn.classList.add("active");

    const MAP = {
        weekday: { file: "./plotly_heatmaps/plotly_heatmap_weekday.html",        key: "Weekday" },
        weekend: { file: "./plotly_heatmaps/plotly_heatmap_weekend.html",        key: "Weekend" },
        holiday: { file: "./plotly_heatmaps/plotly_heatmap_public_holiday.html", key: "Public holiday" },
    };

    const entry = MAP[type];
    if (!entry) return;

    frame.src = entry.file;
    loadCityInsight(entry.key);
}


/* =====================================================
   CITY — AI INSIGHT
===================================================== */

async function loadCityInsight(key) {
    const el = document.getElementById("heatmapInsight");
    if (!el) return;

    try {
        const r    = await fetch(`${API}/city-insight`);
        const data = await r.json();
        el.innerText = key ? data[key] : (data["Weekday"] || "");
    } catch (error) {
        el.innerText = "AI city insight unavailable.";
    }
}

// Initialise city page tab
switchHeatmap("weekday");


/* =====================================================
   PARKING PAGE
===================================================== */

async function loadParkingAnalysis(date) {
    const d = date || (document.getElementById("parkingDate") || {}).value || "2026-02-14";
    try {
        const r   = await fetch(`${API}/parking-analysis?date=${d}`);
        const fig = await r.json();
        Plotly.newPlot("parkingChart", fig.data, fig.layout, { responsive: true, displayModeBar: false });
    } catch (error) {
        console.error(error);
    }
}

async function loadCongestionAnalysis(date) {
    const d = date || (document.getElementById("parkingDate") || {}).value || "2026-02-14";
    try {
        const r   = await fetch(`${API}/congestion-analysis?date=${d}`);
        const fig = await r.json();
        Plotly.newPlot("congestionChart", fig.data, fig.layout, { responsive: true, displayModeBar: false });
    } catch (error) {
        console.error(error);
    }
}

async function loadParkingInsight() {
    try {
        const r    = await fetch(`${API}/parking-insight`);
        const data = await r.json();
        document.getElementById("parkingInsight").innerText = data.insight;
    } catch (error) {
        document.getElementById("parkingInsight").innerText = "AI insight unavailable.";
    }
}

function reloadParkingCharts() {
    const date = document.getElementById("parkingDate").value;
    loadParkingAnalysis(date);
    loadCongestionAnalysis(date);
}

if (document.getElementById("parkingChart")) {
    loadParkingAnalysis();
    loadCongestionAnalysis();
    loadParkingInsight();
}


/* =====================================================
   FORECAST PAGE
===================================================== */

const DAY      = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const DAYSHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const ACCENT   = "#185fa5";
const ACTUAL   = "#c0392b";
const hrs      = [...Array(24).keys()];
const fmt      = n => n.toLocaleString("en-US");
const CFG      = { displayModeBar: false, responsive: true };
const AXIS     = { gridcolor: "#eee", zeroline: false };

let FORECAST_DATA = null;


async function loadForecastData() {
    try {
        const r     = await fetch(`${API}/forecast-data`);
        FORECAST_DATA = await r.json();
        forecast();
        rangeForecast();
    } catch (error) {
        console.error("Forecast error:", error);
    }
}


async function loadForecastInsight(expected, lo, hi, peak) {
    const el = document.getElementById("forecastInsight");
    if (!el) return;

    try {
        const scenario = document.getElementById("fcEvent").selectedOptions[0].text;
        const r        = await fetch(`${API}/forecast-insight`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ scenario, expected, range: `${lo}-${hi}`, peak: `${peak}:00` }),
        });
        const data = await r.json();
        el.innerText = data.insight;
    } catch {
        el.innerText = "AI forecast insight temporarily unavailable.";
    }
}


function forecast() {
    if (!FORECAST_DATA) return;

    const dateStr = document.getElementById("fcDate").value;
    const d       = new Date(dateStr + "T12:00:00");
    if (isNaN(d)) return;

    const dow  = (d.getDay() + 6) % 7;
    const mult = parseFloat(document.getElementById("fcEvent").value);
    const mean = FORECAST_DATA.model.level_mean[dow];
    const std  = FORECAST_DATA.model.level_std[dow];
    const frac = FORECAST_DATA.model.frac[dow];

    const exp  = hrs.map(h => mean * frac[h] * mult);
    const band = hrs.map(h => std  * frac[h] * mult);
    const low  = exp.map((v, i) => Math.max(0, v - band[i]));
    const high = exp.map((v, i) => v + band[i]);

    const total = Math.round(mean * mult);
    const lo    = Math.round(Math.max(0, (mean - std) * mult));
    const hi    = Math.round((mean + std) * mult);

    let pk = 0;
    exp.forEach((v, i) => { if (v > exp[pk]) pk = i; });

    document.getElementById("fcWeekday").innerText = DAY[dow];
    document.getElementById("fcTotal").innerText   = fmt(total);
    document.getElementById("fcRange").innerText   = `${fmt(lo)}-${fmt(hi)}`;
    document.getElementById("fcPeak").innerText    = String(pk).padStart(2, "0") + ":00";

    const traces = [
        { x: hrs, y: high, type: "scatter", mode: "lines", line: { width: 0 }, showlegend: false },
        { x: hrs, y: low,  type: "scatter", mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: "rgba(24,95,165,.15)", name: "Likely range" },
        { x: hrs, y: exp,  type: "scatter", mode: "lines", name: "Forecast", line: { color: ACCENT, width: 3 } },
    ];

    const actual = FORECAST_DATA.actuals[dateStr];
    if (actual) {
        traces.push({ x: hrs, y: actual.h, type: "scatter", mode: "lines+markers", name: "Actual", line: { color: ACTUAL, width: 3 } });
    }

    Plotly.react(
        "forecastChart",
        traces,
        {
            margin: { t: 20, r: 20, b: 50, l: 55 },
            height: 650,
            legend: { orientation: "h" },
            xaxis:  { ...AXIS, title: "Hour" },
            yaxis:  { ...AXIS, title: "Arrivals" },
        },
        CFG
    );

    // Update actual comparison panel
    const actualEl = document.getElementById("fcActual");
    if (actual && actualEl) {
        const peak_h = actual.h.indexOf(Math.max(...actual.h));
        const err    = Math.round(((total - actual.t) / actual.t) * 100);
        document.getElementById("fcActualTotal").innerText = fmt(actual.t);
        document.getElementById("fcActualErr").innerText   = `${err > 0 ? "+" : ""}${err}%`;
        document.getElementById("fcActualPeak").innerText  = String(peak_h).padStart(2, "0") + ":00";
    }

    loadForecastInsight(total, lo, hi, pk);
}


function rangeForecast() {
    if (!FORECAST_DATA) return;

    const from = document.getElementById("rgFrom").value;
    const to   = document.getElementById("rgTo").value;
    const mult = parseFloat(document.getElementById("rgEvent").value);

    if (!from || !to || from > to) return;

    const dates = [], forecasts = [], actuals = [];
    let fcSum = 0, actSum = 0, actCount = 0, busiestVal = 0, busiestDay = "";

    let d   = new Date(from + "T12:00:00");
    const end = new Date(to   + "T12:00:00");

    while (d <= end) {
        const iso  = d.toISOString().slice(0, 10);
        const dow  = (d.getDay() + 6) % 7;
        const pred = Math.round(FORECAST_DATA.model.level_mean[dow] * mult);

        dates.push(iso);
        forecasts.push(pred);
        fcSum += pred;

        const act = FORECAST_DATA.daily_actuals[iso];
        if (act !== undefined) {
            actuals.push(act);
            actSum += act;
            actCount++;
            if (act > busiestVal) {
                busiestVal = act;
                busiestDay = DAYSHORT[dow] + " " + iso.slice(5);
            }
        } else {
            actuals.push(null);
        }

        d.setDate(d.getDate() + 1);
    }

    document.getElementById("rgDays").innerText    = dates.length;
    document.getElementById("rgFcTotal").innerText = fmt(fcSum);
    document.getElementById("rgActTotal").innerText = actCount > 0 ? fmt(actSum) : "-";
    document.getElementById("rgBusiest").innerText  = busiestVal > 0 ? busiestDay : "-";

    Plotly.react(
        "rangeChart",
        [
            { x: dates, y: forecasts, type: "scatter", mode: "lines", name: "Forecast", line: { color: ACCENT, width: 3 } },
            { x: dates, y: actuals,   type: "scatter", mode: "lines", name: "Actual",   line: { color: ACTUAL,  width: 3 } },
        ],
        {
            margin: { t: 20, r: 20, b: 70, l: 55 },
            height: 650,
            legend: { orientation: "h" },
            xaxis:  { ...AXIS, tickangle: -45 },
            yaxis:  { ...AXIS, title: "Daily arrivals" },
        },
        CFG
    );
}


if (document.getElementById("fcDate")) {
    loadForecastData();

    document.getElementById("fcDate").addEventListener("change",  forecast);
    document.getElementById("fcEvent").addEventListener("change", forecast);
    document.getElementById("rgFrom").addEventListener("change",  rangeForecast);
    document.getElementById("rgTo").addEventListener("change",    rangeForecast);
    document.getElementById("rgEvent").addEventListener("change", rangeForecast);
}