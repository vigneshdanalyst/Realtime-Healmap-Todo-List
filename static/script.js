const heatmap = document.getElementById("heatmap");
const monthLabels = document.getElementById("month-labels");
const yearLabel = document.getElementById("current-year");
const chart = document.getElementById("taskChart");

const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function renderActivityHeatmap(savedData) {
    if (!heatmap) return;

    heatmap.innerHTML = "";
    if (monthLabels) monthLabels.innerHTML = "";

    const targetYear = new Date().getFullYear();
    const daysInYear = new Date(targetYear, 1, 29).getMonth() === 1 ? 366 : 365;

    if (yearLabel) yearLabel.textContent = targetYear;

    if (monthLabels) {
        months.forEach((month) => {
            const label = document.createElement("span");
            label.textContent = month;
            monthLabels.appendChild(label);
        });
    }

    const startDate = new Date(targetYear, 0, 1);
    const startDay = startDate.getDay();
    const offset = startDay === 0 ? 6 : startDay - 1;

    for (let i = 0; i < offset; i += 1) {
        const empty = document.createElement("div");
        empty.className = "day";
        empty.style.visibility = "hidden";
        heatmap.appendChild(empty);
    }

    for (let i = 0; i < daysInYear; i += 1) {
        const square = document.createElement("div");
        const intensity = Number(savedData[i] || 0);
        const currentDate = new Date(targetYear, 0, i + 1);
        const dateString = currentDate.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });

        square.className = `day level-${Math.min(intensity, 5)}`;
        square.title = `${dateString} - Level ${intensity}`;
        heatmap.appendChild(square);
    }
}

function renderTaskChart(data) {
    if (!chart || !data || !Array.isArray(data.labels)) return;

    chart.innerHTML = "";
    const values = data.values || [];
    const maxValue = Math.max(...values, 1);

    data.labels.forEach((label, index) => {
        const value = values[index] || 0;
        const bar = document.createElement("div");
        bar.className = "chart-bar";
        bar.style.height = `${Math.max((value / maxValue) * 100, value ? 8 : 4)}%`;
        bar.title = `${label}: ${value} task${value === 1 ? "" : "s"}`;

        const caption = document.createElement("span");
        caption.textContent = label;
        bar.appendChild(caption);
        chart.appendChild(bar);
    });
}

async function loadDashboardData() {
    try {
        const [heatmapResponse, chartResponse] = await Promise.all([
            fetch("/data"),
            fetch("/chart-data"),
        ]);

        if (heatmapResponse.ok) {
            renderActivityHeatmap(await heatmapResponse.json());
        }

        if (chartResponse.ok) {
            renderTaskChart(await chartResponse.json());
        }
    } catch (error) {
        console.error("Dashboard data failed to load", error);
    }
}

document.addEventListener("DOMContentLoaded", loadDashboardData);
