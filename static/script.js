// ======================================================
// Quantum Circuit Builder Pro
// script.js
// Part 1
// ======================================================

let selectedGate = "H";
let selectedTarget = 0;

// -----------------------------
// DOM Elements
// -----------------------------

const gateButtons = document.querySelectorAll(".gate-btn");

const targetSelect = document.getElementById("target");

const newCircuitBtn = document.getElementById("new-circuit");

const applyGateBtn = document.getElementById("apply-gate");

const simulateBtn = document.getElementById("simulate");

const resetBtn = document.getElementById("reset");

const qubitSelect = document.getElementById("qubits");

const circuitImage = document.getElementById("circuit-image");

const statsPanel = document.getElementById("stats");

const countsPanel = document.getElementById("counts");

const statevectorPanel = document.getElementById("statevector");


// ======================================================
// Helper
// ======================================================

async function postJSON(url, data = {}) {

    const response = await fetch(url, {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify(data)

    });

    return await response.json();

}

// ======================================================
// Circuit Image
// ======================================================

function updateCircuitImage(image) {

    if (!image)
        return;

    circuitImage.src = image + "?t=" + Date.now();

}


// ======================================================
// Statistics
// ======================================================

function updateStatistics(stats) {

    if (!stats)
        return;

    statsPanel.innerHTML = `

        <p><strong>Qubits:</strong> ${stats.qubits}</p>

        <p><strong>Depth:</strong> ${stats.depth}</p>

        <p><strong>Gate Count:</strong> ${stats.gate_count}</p>

        <p><strong>Measurements:</strong> ${stats.measurements}</p>

    `;

}

// ======================================================
// Measurement Counts
// ======================================================

function updateCounts(counts) {

    if (!counts) {

        countsPanel.innerHTML = "";

        return;

    }

    let html = "<h3>Measurement Counts</h3>";

    html += "<table>";

    html += "<tr><th>State</th><th>Counts</th></tr>";

    for (const state in counts) {

        html += `

            <tr>

                <td>${state}</td>

                <td>${counts[state]}</td>

            </tr>

        `;

    }

    html += "</table>";

    countsPanel.innerHTML = html;

}

// ======================================================
// Statevector
// ======================================================

function updateStatevector(statevector) {

    if (!statevector) {

        statevectorPanel.innerHTML = "";

        return;

    }

    let html = "<h3>Statevector</h3>";

    html += "<table>";

    html += "<tr>";

    html += "<th>Basis</th>";

    html += "<th>Probability</th>";

    html += "</tr>";

    for (const basis in statevector) {

        html += `

            <tr>

                <td>|${basis}⟩</td>

                <td>${statevector[basis].probability}</td>

            </tr>

        `;

    }

    html += "</table>";

    statevectorPanel.innerHTML = html;

}

// ======================================================
// Gate Selection
// ======================================================

gateButtons.forEach(button => {

    button.addEventListener("click", () => {

        gateButtons.forEach(btn =>
            btn.classList.remove("active")
        );

        button.classList.add("active");

        selectedGate = button.dataset.gate;

    });

});

// ======================================================
// Create Circuit
// ======================================================

newCircuitBtn.addEventListener("click", async () => {

    const qubits = parseInt(qubitSelect.value);

    const result = await postJSON(
        "/new_circuit",
        {
            qubits: qubits
        }
    );

    if (!result.success) {

        alert(result.error);

        return;

    }

    updateCircuitImage(result.image);

    updateStatistics(result.stats);

    updateCounts({});

    updateStatevector({});

    updateTargetList(qubits);

});

// ======================================================
// Apply Gate
// ======================================================

applyGateBtn.addEventListener("click", async () => {

    const result = await postJSON(

        "/apply_gate",

        {

            gate: selectedGate,

            target: parseInt(
                targetSelect.value
            )

        }

    );

    if (!result.success) {

        alert(result.error);

        return;

    }

    updateCircuitImage(result.image);

    updateStatistics(result.stats);

});

// ======================================================
// Simulation
// ======================================================

simulateBtn.addEventListener("click", async () => {

    const result = await postJSON(
        "/simulate"
    );

    if (!result.success) {

        alert(result.error);

        return;

    }

    updateCircuitImage(result.image);

    updateStatistics(result.stats);

    updateCounts(result.counts);

    updateStatevector(result.statevector);

});

// ======================================================
// Reset
// ======================================================

resetBtn.addEventListener("click", async () => {

    const result = await postJSON(
        "/reset"
    );

    if (!result.success) {

        alert(result.error);

        return;

    }

    updateCircuitImage(result.image);

    updateStatistics(result.stats);

    updateCounts({});

    updateStatevector({});

});

// ======================================================
// Download
// ======================================================

document

.getElementById("download")

.addEventListener(

    "click",

    () => {

        window.location = "/download";

    }

);

// ======================================================
// Target Selector
// ======================================================

function updateTargetList(qubits) {

    targetSelect.innerHTML = "";

    for (let i = 0; i < qubits; i++) {

        const option = document.createElement("option");

        option.value = i;

        option.textContent = `q${i}`;

        targetSelect.appendChild(option);

    }

}

// ======================================================
// Initial Setup
// ======================================================

window.onload = () => {

    gateButtons[0].classList.add("active");

    updateTargetList(
        parseInt(qubitSelect.value)
    );

};
