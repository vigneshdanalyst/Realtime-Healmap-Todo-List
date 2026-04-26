/**
 * Intelligence OS: Pulse Engine 2.0
 * Unified 53-week chronological grid for 2026.
 */

console.log("Intelligence OS: Pulse Engine Online");

const heatmap = document.getElementById("heatmap");
const monthLabels = document.getElementById("month-labels");
const yearLabel = document.getElementById("current-year");

const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/**
 * Renders the 53-week chronological pulse.
 * @param {Object} savedData - Map of day_index to intensity levels.
 */
function renderOperationalPulse(savedData) {
    if (!heatmap) return;
    
    // Reset display state to prevent duplication
    heatmap.innerHTML = "";
    if (monthLabels) monthLabels.innerHTML = "";

    const targetYear = 2026; 
    if (yearLabel) yearLabel.innerText = targetYear;

    // 1. Generate Chronological Month Labels (X-Axis)
    if (monthLabels) {
        months.forEach(m => {
            const span = document.createElement("span");
            span.innerText = m;
            span.classList.add("text-left", "pl-1");
            monthLabels.appendChild(span);
        });
    }

    /**
     * 2. Alignment Logic for 2026
     * January 1st, 2026 is a Thursday.
     * For a professional Monday-start grid, we offset the first 3 squares.
     */
    const startDate = new Date(targetYear, 0, 1);
    let startDay = startDate.getDay(); 
    const offset = startDay === 0 ? 6 : startDay - 1; // Maps Sun(0) to 6, Mon(1) to 0

    // 3. Render Leading Padding (Invisible Coordinate Alignment)
    for (let i = 0; i < offset; i++) {
        const empty = document.createElement("div");
        empty.classList.add("day");
        empty.style.opacity = "0"; 
        empty.style.pointerEvents = "none";
        heatmap.appendChild(empty);
    }

    // 4. Render Operational Days (365 Day Cycle)
    for (let i = 0; i < 365; i++) {
        const daySquare = document.createElement("div");
        daySquare.classList.add("day");

        // Calculate absolute date for tooltips
        const currentDate = new Date(targetYear, 0, i + 1);
        const dateString = currentDate.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });

        // Pull intensity from PostgreSQL metrics
        const intensity = savedData[i] || 0;
        if (intensity > 0) {
            daySquare.classList.add(`level-${intensity}`);
        }

        // Professional SaaS Detail: Clean, date-centric tooltips
        daySquare.setAttribute('title', `${dateString} • Level ${intensity}`);
        
        heatmap.appendChild(daySquare);
    }
}

/**
 * Global Synchronizer: Fetches latest metrics from backend.
 */
async function syncIntelligencePulse() {
    try {
        const response = await fetch("/data");
        if (!response.ok) throw new Error("Flux Sync failure");
        
        const data = await response.json();
        renderOperationalPulse(data);
        
        console.log("Intelligence OS: Pulse Synchronization Complete");
    } catch (err) {
        console.error("Critical Engine Error:", err);
    }
}

// Global Initialization on DOM Ready
document.addEventListener("DOMContentLoaded", syncIntelligencePulse);