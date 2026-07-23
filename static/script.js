/******************************************************************************
 * Quantum Circuit Builder Pro
 * script.js
 * Part 1
 ******************************************************************************/

/* ==========================================================================
   DOM ELEMENTS
========================================================================== */

const gateSelect = document.getElementById("gate");
const targetSelect = document.getElementById("target-qubit");
const controlSelect = document.getElementById("control-qubit");
const controlContainer = document.getElementById("control-container");

const newCircuitBtn = document.getElementById("new-circuit");
const applyGateBtn = document.getElementById("apply-gate");
const simulateBtn = document.getElementById("simulate");
const resetBtn = document.getElementById("reset");

const saveCircuitBtn = document.getElementById("save-project");
const loadCircuitBtn = document.getElementById("load-project");
const exportQasmBtn = document.getElementById("export-qasm");

const qubitSelect = document.getElementById("qubits");

const circuitImage = document.getElementById("circuit-image");

const statsPanel = document.getElementById("statistics");
const countsPanel = document.getElementById("counts");
const histogramPanel = document.getElementById("histogram");
const statevectorPanel = document.getElementById("statevector");
const undoBtn = document.getElementById("undo");
const redoBtn = document.getElementById("redo");
const downloadBtn = document.getElementById("download");


const MULTI_QUBIT_GATES = [
    "CX",
    "CY",
    "CZ",
    "CH",
    "SWAP",
    "CCX"
];



/* ==========================================================================
   HISTOGRAM
========================================================================== */

let histogramChart = null;



/* ==========================================================================
   API HELPER
========================================================================== */

async function postJSON(url, data = {}) {

    try {

        const response = await fetch(url, {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify(data)

        });

        return await response.json();

    }

    catch (error) {

        console.error(error);

        return {

            success: false,

            error: error.message

        };

    }

}



/* ==========================================================================
   IMAGE
========================================================================== */

function updateCircuitImage(imageUrl) {

    if (!imageUrl)
        return;

    const placeholder =
        document.getElementById("preview-placeholder");

    if (placeholder)
        placeholder.style.display = "none";

    circuitImage.style.display = "block";

    circuitImage.src =
        imageUrl + "?t=" + Date.now();

}



/* ==========================================================================
   QUBIT DROPDOWNS
========================================================================== */

function populateQubits(count) {

    targetSelect.innerHTML = "";
    controlSelect.innerHTML = "";

    for (let i = 0; i < count; i++) {

        const targetOption = document.createElement("option");
        targetOption.value = i;
        targetOption.textContent = "q" + i;
        targetSelect.appendChild(targetOption);

        const controlOption = document.createElement("option");
        controlOption.value = i;
        controlOption.textContent = "q" + i;
        controlSelect.appendChild(controlOption);
    }
}



/* ==========================================================================
   SHOW / HIDE CONTROL QUBIT
========================================================================== */

function updateControlVisibility() {

    console.log("Gate Changed:", gateSelect.value);

    if (MULTI_QUBIT_GATES.includes(gateSelect.value)) {

        console.log("SHOW");

        controlContainer.style.display = "block";

    } else {

        console.log("HIDE");

        controlContainer.style.display = "none";

    }

}



/* ==========================================================================
   STATISTICS
========================================================================== */

function updateStatistics(stats) {

    if (!stats)
        return;

    statsPanel.innerHTML = `

        <div class="stat-row">

            <span>Qubits</span>

            <span>${stats.qubits}</span>

        </div>

        <div class="stat-row">

            <span>Depth</span>

            <span>${stats.depth}</span>

        </div>

        <div class="stat-row">

            <span>Gate Count</span>

            <span>${stats.gate_count}</span>

        </div>

        <div class="stat-row">

            <span>Measurements</span>

            <span>${stats.measurements}</span>

        </div>

    `;

}



/* ==========================================================================
   COUNTS TABLE
========================================================================== */

function updateCounts(counts) {

    if (!counts || Object.keys(counts).length === 0) {

        countsPanel.innerHTML =

            `<p class="placeholder">

                Run simulation to view counts.

            </p>`;

        return;

    }

    let html = `

        <table class="results-table">

        <thead>

            <tr>

                <th>State</th>

                <th>Counts</th>

            </tr>

        </thead>

        <tbody>

    `;

    Object.entries(counts).forEach(([state, value]) => {

        html += `

            <tr>

                <td>${state}</td>

                <td>${value}</td>

            </tr>

        `;

    });

    html += `

        </tbody>

        </table>

    `;

    countsPanel.innerHTML = html;

}
/* ==========================================================================
   STATEVECTOR TABLE
========================================================================== */

function updateStatevector(statevector) {

    if (!statevector || Object.keys(statevector).length === 0) {

        statevectorPanel.innerHTML = `
            <p class="placeholder">
                Run simulation to view statevector.
            </p>
        `;

        return;

    }

    let html = `
        <table class="results-table">

            <thead>

                <tr>

                    <th>Basis</th>

                    <th>Amplitude</th>

                </tr>

            </thead>

            <tbody>
    `;

    Object.entries(statevector).forEach(([basis, amplitude]) => {

        html += `
            <tr>

                <td>${basis}</td>

                <td>${amplitude}</td>

            </tr>
        `;

    });

    html += `
            </tbody>

        </table>
    `;

    statevectorPanel.innerHTML = html;

}


/* ==========================================================================
   HISTOGRAM
========================================================================== */

function updateHistogram(counts) {

    const canvas = document.getElementById("histogramChart");

    if (!canvas)
        return;

    const ctx = canvas.getContext("2d");

    if (histogramChart) {

        histogramChart.destroy();

    }

    if (!counts || Object.keys(counts).length === 0)
        return;

    histogramChart = new Chart(ctx, {

        type: "bar",

        data: {

            labels: Object.keys(counts),

            datasets: [

                {

                    label: "Counts",

                    data: Object.values(counts)

                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {

                    display: false

                }

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}


/* ==========================================================================
   CREATE CIRCUIT
========================================================================== */

newCircuitBtn.addEventListener("click", async () => {

    const result = await postJSON("/new_circuit", {
        qubits: parseInt(qubitSelect.value)
    });

    if (!result.success) {
        alert(result.error);
        return;
    }

    // Refresh the UI
    updateCircuitImage(result.image);
    updateStatistics(result.stats);

    // Repopulate qubit dropdowns
    populateQubits(parseInt(qubitSelect.value));

    // Update Control Qubit visibility
    updateControlVisibility();

});

/* ==========================================================================
   HELPER FUNCTIONS
========================================================================== */
function resetOutputPanels() {

    updateCounts({});

    updateStatevector({});

    updateHistogram({});

    }

/* ==========================================================================
   APPLY GATE
========================================================================== */
if (applyGateBtn) {
applyGateBtn.addEventListener("click", async () => {

    const gate = gateSelect.value;
    const target = parseInt(targetSelect.value);

    let control = null;

    if (MULTI_QUBIT_GATES.includes(gate)) {
        control = parseInt(controlSelect.value);
    }

    console.log({
        gate,
        target,
        control
    });


    const payload = {
        gate: gate,
        target: target,
        control: control
    };

    // THIS LINE WAS MISSING
    const result = await postJSON("/apply_gate", payload);

    if (!result.success) {
        alert(result.error);
        return;
    }

    updateCircuitImage(result.image);
    updateStatistics(result.stats);

});
}

/* ==========================================================================
   SIMULATE
========================================================================== */
if (simulateBtn) {
    simulateBtn.addEventListener("click", async () => {

        simulateBtn.disabled = true;
        setLoading(true);

        try {

            const result = await postJSON("/simulate");

            if (!result.success) {

                alert(result.error);
                return;

            }

            updateCircuitImage(result.image);

            updateCounts(result.counts);
            updateStatevector(result.statevector);

        } catch (error) {

            alert("Simulation failed.");

        } finally {

            simulateBtn.disabled = false;
            setLoading(false);

        }

    });
}


/* ==========================================================================
   RESET
========================================================================== */
if (resetBtn) {
    resetBtn.addEventListener("click", async () => {

        if (!confirm("Reset the current circuit?")) {
            return;
        }

        const result = await postJSON("/reset");

        if (!result.success) {
            alert(result.error);
            return;
        }


        resetOutputPanels();

    });
}
/* ==========================================================================
   LOAD
========================================================================== */
if (loadCircuitBtn) {
    loadCircuitBtn.addEventListener("click", async () => {

        if (!confirm("Load the current circuit?")) {
            return;
        }

        const result = await postJSON("/load");

        if (!result.success) {
            alert(result.error);
            return;
        }


        resetOutputPanels();

    });
}

/* ==========================================================================
   DOWNLOAD
========================================================================== */
if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {

        window.location.href = "/download";

    });
}

/* ==========================================================================
   EXPORT OPENQASM
========================================================================== */
if (exportQasmBtn) {
    exportQasmBtn.addEventListener("click", () => {

        window.location.href = "/export_qasm";

    });
}

/* ==========================================================================
   PLACEHOLDER BUTTONS
========================================================================== */

if (saveCircuitBtn) {
    saveCircuitBtn.addEventListener("click", async () => {

        alert("Save Circuit feature will be available in Version 2.1.");

    });
}



    /* ==========================================================================
       GATE CHANGE
    ========================================================================== */

    gateSelect.addEventListener("change", updateControlVisibility);


    /* ==========================================================================
       INITIALIZE
    ========================================================================== */

    document.addEventListener("DOMContentLoaded", () => {

        populateQubits(parseInt(qubitSelect.value));
        updateControlVisibility();

        updateStatistics({
            qubits: "-",
            depth: "-",
            gate_count: "-",
            measurements: "-"
        });

        updateCounts({});

        updateStatevector({});

    });

    undoBtn.addEventListener("click", async () => {

        const result = await postJSON("/undo");

        if (!result.success) {
            alert(result.error);
            return;
        }


    });

    redoBtn.addEventListener("click", async () => {

        const result = await postJSON("/redo");

        if (!result.success) {
            alert(result.error);
            return;
        }


    });

    loadCircuitBtn.onclick = async () => {

        const file = document
            .getElementById("project-file")
            .files[0];

        const form = new FormData();

        form.append("file", file);

        const response = await fetch(
            "/load_project",

            {

                method: "POST",

                body: form

            }
        );

        const result = await response.json();


    };

    function setLoading(isLoading) {
        document.body.style.cursor = isLoading ? "wait" : "default";
    }
