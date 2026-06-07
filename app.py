from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file
)

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
from qiskit.visualization import (
    circuit_drawer,
    plot_bloch_multivector
)

import qiskit.qasm2

from reportlab.pdfgen import canvas

import matplotlib
import os
import uuid

matplotlib.use("Agg")

app = Flask(__name__)

STATIC_DIR = "static"

os.makedirs(STATIC_DIR, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_circuit():

    data = request.get_json()

    num_qubits = int(data["num_qubits"])
    gates = data["gates"]

    qc = QuantumCircuit(num_qubits)

    generated_code = [
        f"qc = QuantumCircuit({num_qubits})"
    ]

    for gate in gates:

        gate_name = gate["gate"]

        if gate_name == "CX":

            control = int(gate["control"])
            target = int(gate["target"])

            qc.cx(control, target)

            generated_code.append(
                f"qc.cx({control}, {target})"
            )

        else:

            q = int(gate["qubit"])

            if gate_name == "H":
                qc.h(q)

            elif gate_name == "X":
                qc.x(q)

            elif gate_name == "Y":
                qc.y(q)

            elif gate_name == "Z":
                qc.z(q)

            elif gate_name == "S":
                qc.s(q)

            elif gate_name == "T":
                qc.t(q)

            generated_code.append(
                f"qc.{gate_name.lower()}({q})"
            )

    # -------- STATEVECTOR --------

    statevector = Statevector.from_instruction(qc)

    statevector_data = [
        str(v)
        for v in statevector.data
    ]

    # -------- CIRCUIT PNG --------

    image_name = f"circuit_{uuid.uuid4().hex}.png"

    image_path = os.path.join(
        STATIC_DIR,
        image_name
    )

    circuit_drawer(
        qc,
        output="mpl",
        filename=image_path
    )

    # circuit_drawer supports mpl output and saving to file in current Qiskit releases. :contentReference[oaicite:1]{index=1}

    # -------- BLOCH SPHERE --------

    bloch_name = f"bloch_{uuid.uuid4().hex}.png"

    bloch_path = os.path.join(
        STATIC_DIR,
        bloch_name
    )

    fig = plot_bloch_multivector(
        statevector
    )

    fig.savefig(
        bloch_path,
        bbox_inches="tight"
    )

    # -------- QASM EXPORT --------

    qasm_text = qiskit.qasm2.dumps(qc)

    # Qiskit 2.x exports OpenQASM 2 via qasm2.dumps(). :contentReference[oaicite:2]{index=2}

    # -------- SIMULATION --------

    measured = qc.copy()

    measured.measure_all()

    simulator = AerSimulator()

    compiled = transpile(
        measured,
        simulator
    )

    result = simulator.run(
        compiled,
        shots=1024
    ).result()

    counts = result.get_counts()

    app.config["LAST_CIRCUIT"] = image_path

    return jsonify(
        {
            "counts": counts,
            "statevector": statevector_data,
            "qasm": qasm_text,
            "code": "\n".join(
                generated_code
            ),
            "circuit_image":
                "/" + image_path.replace("\\", "/"),
            "bloch_image":
                "/" + bloch_path.replace("\\", "/")
        }
    )


@app.route("/download_png")
def download_png():

    file_path = app.config.get(
        "LAST_CIRCUIT"
    )

    if not file_path:
        return "No circuit generated"

    return send_file(
        file_path,
        as_attachment=True
    )


@app.route("/download_pdf")
def download_pdf():

    image_path = app.config.get(
        "LAST_CIRCUIT"
    )

    if not image_path:
        return "No circuit generated"

    pdf_name = "quantum_report.pdf"

    c = canvas.Canvas(pdf_name)

    c.drawString(
        100,
        800,
        "Quantum Circuit Builder Report"
    )

    c.drawImage(
        image_path,
        50,
        350,
        width=500,
        height=250
    )

    c.save()

    return send_file(
        pdf_name,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)