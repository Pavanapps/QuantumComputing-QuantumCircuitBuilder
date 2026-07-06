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

from utils.quantum import (
    create_circuit,
    apply_gate,
    draw_circuit,
    simulate_circuit,
    get_statistics,
    reset_circuit
)

app = Flask(__name__)

app.secret_key = "QuantumCircuitBuilderPro"

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_FOLDER = BASE_DIR / "outputs"

OUTPUT_FOLDER.mkdir(exist_ok=True)

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


def clear_user_circuit():

    circuit_manager.pop(get_session_id(), None)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/")
def index():

    circuit = get_user_circuit()

    image_path = draw_circuit(
        circuit,
        OUTPUT_FOLDER,
        filename=f"circuit_{get_session_id()}.png"
    )

    stats = get_statistics(circuit)

    print(f"[DRAW] Saving image to: {image_path}")

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

        qubits = max(1, min(qubits, 5))

        circuit = create_circuit(qubits)

        save_user_circuit(circuit)

        image_path = draw_circuit(
            circuit,
            OUTPUT_FOLDER,
            filename=f"circuit_{get_session_id()}.png"
        )

        stats = get_statistics(circuit)

        return jsonify({
            "success": True,
            "message": f"Created {qubits}-qubit circuit.",
            "image": "/circuit_image",
            "stats": stats
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ------------------------------------------------------------------
# Apply Quantum Gate
# ------------------------------------------------------------------

@app.route("/apply_gate", methods=["POST"])
def apply_gate_route():

    try:

        data = request.get_json(silent=True) or {}

        gate = str(
            data.get("gate", "")
        ).strip().upper()

        target = int(
            data.get("target", 0)
        )

        circuit = get_user_circuit()

        # Validate target qubit
        if target < 0 or target >= circuit.num_qubits:
            return jsonify({

                "success": False,

                "error": "Invalid target qubit."

            }), 400

        # Apply gate

        apply_gate(

            circuit=circuit,

            gate=gate,

            target=target

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

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

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

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

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

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

# ------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "application": "Quantum Circuit Builder Pro",
        "version": "1.0.0"
    })

# ------------------------------------------------------------------
# Cleanup Route
# ------------------------------------------------------------------

@app.route("/cleanup")
def cleanup():

    try:

        remove_user_circuit()

        return jsonify({

            "success": True,

            "message": "Session cleared."

        })

    except Exception as e:

        return jsonify({

            "success": False,

            "error": str(e)

        })

# ------------------------------------------------------------------
# Error Handlers
# ------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success": False,

        "error": "404 - Page Not Found"

    }), 404

@app.errorhandler(500)
def internal_error(error):

    return jsonify({

        "success": False,

        "error": "500 - Internal Server Error"

    }), 500

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

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

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

        "version": "1.0",

        "framework": "Flask",

        "backend": "Qiskit",

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
from flask import send_from_directory

@app.route("/circuit_image")
def circuit_image():

    filename = f"circuit_{get_session_id()}.png"
    print(f"[SERVE] Looking for: {OUTPUT_FOLDER / filename}")

    return send_from_directory(
        OUTPUT_FOLDER,
        filename,
        mimetype="image/png"
    )
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