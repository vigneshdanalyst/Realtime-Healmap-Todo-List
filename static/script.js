console.log("Heatmap loaded (read-only)");

const heatmap = document.getElementById("heatmap");

// Load saved data

fetch("/data")
.then(response => response.json())
.then(savedData => {

    createGrid(savedData);

})
.catch(error => {

    console.error("Error loading heatmap:", error);

});

function createGrid(savedData) {

    for (let i = 0; i < 365; i++) {

        let day = document.createElement("div");

        day.classList.add("day");

        let value = savedData[i] || 0;

        updateColor(day, value);

        // ❌ Removed click event
        // Heatmap is now visualization only

        heatmap.appendChild(day);
    }
}

function updateColor(day, value) {

    day.className = "day";

    if (value > 0) {
        day.classList.add("level-" + value);
    }
}