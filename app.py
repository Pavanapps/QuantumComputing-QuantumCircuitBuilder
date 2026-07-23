from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    send_file
)

from pathlib import Path
import uuid
import os
import logging
import json
from qiskit import QuantumCircuit
from utils.project import CircuitProject

import traceback

from utils.quantum import (
    create_circuit,
    apply_gate,
    draw_circuit,
    simulate_circuit,
    get_statistics,
    reset_circuit
)
from utils.history import CircuitHistory
from flask import send_from_directory


app = Flask(__name__)

# ----------------------------------------------------
# Application Configuration
# ----------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

BASE_DIR = Path(__file__).resolve().parent

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "QuantumCircuitBuilderPro"
)

app.config["OUTPUT_FOLDER"] = BASE_DIR / "outputs"
app.config["SAVE_FOLDER"] = BASE_DIR / "projects"
app.config["MAX_QUBITS"] = 5

app.secret_key = app.config["SECRET_KEY"]

for folder in (
    app.config["OUTPUT_FOLDER"],
    app.config["SAVE_FOLDER"]
):
    folder.mkdir(exist_ok=True)

APP_VERSION = "1.0.0"

# Convenience variables (optional)
OUTPUT_FOLDER = app.config["OUTPUT_FOLDER"]
SAVE_FOLDER = app.config["SAVE_FOLDER"]

circuit_manager = {}

# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

def get_session_id():

    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())

    return session["session_id"]


def get_user_circuit():

    sid = get_session_id()

    if sid not in circuit_manager:
        circuit_manager[sid] = create_circuit(2)

    return circuit_manager[sid]


def save_user_circuit(circuit):

    circuit_manager[get_session_id()] = circuit


history_manager = {}

def get_user_history():

    session_id = get_session_id()

    if session_id not in history_manager:

        history_manager[session_id] = CircuitHistory()

    return history_manager[session_id]

def clear_user_circuit():

    circuit_manager.pop(get_session_id(), None)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

def success(data=None, message=""):

    response = {

        "success": True,

        "message": message

    }

    if data:
        response.update(data)

    return jsonify(response)

def failure(message, status=400):

    return jsonify({

        "success": False,

        "error": message

    }), status



@app.route("/")
def index():

    circuit = get_user_circuit()

    image_path = draw_circuit(
        circuit,
        OUTPUT_FOLDER,
        filename=f"circuit_{get_session_id()}.png"
    )

    stats = get_statistics(circuit)



    logging.info(f"[DRAW] Saving image to: {image_path}")


    return render_template(
        "index.html",
        circuit_image="/circuit_image",
        stats=stats
    )


# ------------------------------------------------------------------
# Create New Circuit
# ------------------------------------------------------------------

@app.route("/new_circuit", methods=["POST"])
def new_circuit():

    try:

        data = request.get_json(silent=True) or {}

        qubits = int(data.get("qubits", 2))

        MAX_QUBITS = app.config["MAX_QUBITS"]

        qubits = max(

            1,

            min(qubits, MAX_QUBITS)

        )

        circuit = create_circuit(qubits)

        save_user_circuit(circuit)

        image_path = draw_circuit(
            circuit,
            OUTPUT_FOLDER,
            filename=f"circuit_{get_session_id()}.png"
        )

        stats = get_statistics(circuit)

        return success({

            "image": "/circuit_image",

            "stats": stats

        })




    except Exception as e:

        logging.exception(e)

        return failure(str(e), 500)

# ------------------------------------------------------------------
# Apply Quantum Gate
# ------------------------------------------------------------------

@app.route("/apply_gate", methods=["POST"])
def apply_gate_route():

    try:

        data = request.get_json(silent=True) or {}
        logging.info(f"Received data: {data}")

        gate = str(
            data.get("gate", "")
        ).strip().upper()

        target = data.get("target")

        if target is None or str(target).strip() == "":
            return jsonify({
                "success": False,
                "error": "Please select a target qubit."
            }), 400

        target = int(target)

        circuit = get_user_circuit()

        # Validate target qubit
        if target < 0 or target >= circuit.num_qubits:
            return jsonify({

                "success": False,

                "error": "Invalid target qubit."

            }), 400

        # Apply gate

        history = get_user_history()

        history.save(circuit)

        control = data.get("control")

        if control not in (None, ""):
            control = int(control)
        else:
            control = None

        apply_gate(
            circuit=circuit,
            gate=gate,
            target=target,
            control=control
        )

        save_user_circuit(circuit)

        image_path = draw_circuit(
            circuit,
            OUTPUT_FOLDER,
            filename=f"circuit_{get_session_id()}.png"
        )

        stats = get_statistics(circuit)

        return jsonify({

            "success": True,

            "message": f"{gate} gate applied to q{target}.",

            "image": "/circuit_image",

            "stats": stats

        })


    except Exception as e:

        logging.exception(e)

        return failure(str(e), 500)

# ------------------------------------------------------------------
# Simulate Circuit
# ------------------------------------------------------------------

@app.route("/simulate", methods=["POST"])
def simulate():

    try:

        circuit = get_user_circuit()

        simulation = simulate_circuit(
            circuit,
            shots=1024
        )

        image_path = draw_circuit(
            circuit,
            OUTPUT_FOLDER,
            filename=f"circuit_{get_session_id()}.png"
        )

        stats = get_statistics(circuit)

        return jsonify({

            "success": True,

            "message": "Simulation completed successfully.",

            "image": "/circuit_image",

            "stats": stats,

            "counts": simulation.get("counts", {}),

            "statevector": simulation.get("statevector", {})

        })


    except Exception as e:

        logging.exception(e)

        return failure(str(e), 500)

# ------------------------------------------------------------------
# Reset Circuit
# ------------------------------------------------------------------

@app.route("/reset", methods=["POST"])
def reset():

    try:

        current = get_user_circuit()

        qubits = current.num_qubits

        circuit = reset_circuit(qubits)

        save_user_circuit(circuit)

        image_path = draw_circuit(
            circuit,
            OUTPUT_FOLDER,
            filename=f"circuit_{get_session_id()}.png"
        )

        stats = get_statistics(circuit)

        return jsonify({

            "success": True,

            "message": "Circuit has been reset.",

            "image": "/circuit_image",

            "stats": stats

        })


    except Exception as e:

        logging.exception(e)

        return failure(str(e), 500)

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------

@app.route("/health")
def health():
    @app.route("/health")
    def health():
        return success({

            "version": APP_VERSION,

            "status": "OK"

        })

# ------------------------------------------------------------------
# Cleanup Route
# ------------------------------------------------------------------

@app.route("/cleanup")
def cleanup():

    try:

        clear_user_circuit()

        return jsonify({

            "success": True,

            "message": "Session cleared."

        })


    except Exception as e:

        logging.exception(e)

        return failure(str(e), 500)

# ------------------------------------------------------------------
# Download Circuit PNG
# ------------------------------------------------------------------

@app.route("/download")
def download():

    try:

        image_path = OUTPUT_FOLDER / f"circuit_{get_session_id()}.png"

        if not image_path.exists():
            return jsonify({

                "success": False,

                "error": "Circuit image not found."

            }), 404

        return send_file(

            image_path,

            mimetype="image/png",

            as_attachment=True,

            download_name="quantum_circuit.png"

        )


    except Exception as e:

        logging.exception(e)

        return failure(str(e), 500)

# ------------------------------------------------------------------
# Circuit Statistics
# ------------------------------------------------------------------

@app.route("/statistics")
def statistics():

    try:

        circuit = get_user_circuit()

        stats = get_statistics(circuit)

        return jsonify({

            "success": True,

            "stats": stats

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

# ------------------------------------------------------------------
# About
# ------------------------------------------------------------------

@app.route("/about")
def about():
    return jsonify({

        "application": "Quantum Circuit Builder Pro",

        "version": APP_VERSION,

        "framework": "Flask",

        "backend": "Qiskit",

        "simulator": "AerSimulator",

        "developer": "Pavan"

    })

# ------------------------------------------------------------------
# Error Pages
# ------------------------------------------------------------------

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "error": "Page not found."

    }), 404

@app.errorhandler(500)
def server_error(error):

    return jsonify({

        "success": False,

        "error": "Internal Server Error."

    }), 500


@app.route("/circuit_image")
def circuit_image():

    filename = f"circuit_{get_session_id()}.png"

    logging.info(f"[SERVE] Looking for: {OUTPUT_FOLDER / filename}")


    return send_from_directory(
        OUTPUT_FOLDER,
        filename,
        mimetype="image/png"
    )
# ------------------------------------------------------------------
# export_qasm
# ------------------------------------------------------------------

@app.route("/export_qasm")
def export_qasm():

    circuit = get_user_circuit()

    qasm = circuit.qasm()

    return (
        qasm,
        200,
        {
            "Content-Type":"text/plain",
            "Content-Disposition":
            "attachment; filename=circuit.qasm"
        }
    )

# ------------------------------------------------------------------
# undo
# ------------------------------------------------------------------

@app.route("/undo", methods=["POST"])
def undo():

    circuit = get_user_circuit()

    history = get_user_history()

    circuit = history.undo(circuit)

    save_user_circuit(circuit)

    draw_circuit(
        circuit,
        OUTPUT_FOLDER,
        filename=f"circuit_{get_session_id()}.png"
    )

    return jsonify({

        "success": True,

        "image": "/circuit_image",

        "stats": get_statistics(circuit),

        "undo": history.undo_count,

        "redo": history.redo_count

    })

# ------------------------------------------------------------------
# redo
# ------------------------------------------------------------------
@app.route("/redo", methods=["POST"])
def redo():

    circuit = get_user_circuit()

    history = get_user_history()

    circuit = history.redo(circuit)

    save_user_circuit(circuit)

    draw_circuit(
        circuit,
        OUTPUT_FOLDER,
        filename=f"circuit_{get_session_id()}.png"
    )

    return jsonify({

        "success": True,

        "image": "/circuit_image",

        "stats": get_statistics(circuit),

        "undo": history.undo_count,

        "redo": history.redo_count

    })

# ------------------------------------------------------------------
# save_project
# ------------------------------------------------------------------

@app.route("/save_project", methods=["POST"])
def save_project():

    circuit = get_user_circuit()

    project = CircuitProject.circuit_to_json(circuit)

    filename = f"project_{get_session_id()}.json"

    filepath = SAVE_FOLDER / filename

    CircuitProject.save(project, filepath)

    return send_file(

        filepath,

        as_attachment=True

    )

# ------------------------------------------------------------------
# load_project
# ------------------------------------------------------------------
@app.route("/load_project", methods=["POST"])
def load_project():

    file = request.files.get("file")

    if file is None:
        return jsonify({
            "success": False,
            "error": "No project file uploaded."
        }), 400

    CircuitProject.load(...)

    circuit = QuantumCircuit(project["qubits"])

    for op in project["operations"]:

        gate = op["gate"]

        target = op["target"]

        if gate == "H":

            circuit.h(target)

        elif gate == "X":

            circuit.x(target)

        elif gate == "Y":

            circuit.y(target)

        elif gate == "Z":

            circuit.z(target)

        elif gate == "CX":

            circuit.cx(

                op["control"],

                target

            )

    save_user_circuit(circuit)

    draw_circuit(

        circuit,

        OUTPUT_FOLDER,

        filename=f"circuit_{get_session_id()}.png"

    )

    return jsonify({

        "success":True,

        "image":"/circuit_image",

        "stats":get_statistics(circuit)

    })









# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(

        debug=True,
        use_reloader=False,
        host="127.0.0.1",

        port=5000

    )
