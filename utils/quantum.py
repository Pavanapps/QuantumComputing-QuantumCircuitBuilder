"""
Quantum helper functions for Quantum Circuit Builder Pro
Compatible with Qiskit 2.x
"""

import os

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit import transpile
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import logging



# --------------------------------------------------------------------
# Create Circuit
# --------------------------------------------------------------------

def create_circuit(qubits: int = 2) -> QuantumCircuit:
    """
    Create a new quantum circuit.

    Parameters
    ----------
    qubits : int

    Returns
    -------
    QuantumCircuit
    """

    if qubits < 1:
        qubits = 1

    if qubits > 5:
        qubits = 5

    qc = QuantumCircuit(qubits)

    return qc


# --------------------------------------------------------------------
# Reset Circuit
# --------------------------------------------------------------------

def reset_circuit(qubits: int = 2) -> QuantumCircuit:
    """
    Reset simply creates a brand-new circuit.
    """

    return create_circuit(qubits)


# --------------------------------------------------------------------
# Apply Gate
# --------------------------------------------------------------------

from typing import Optional

def apply_gate(
    circuit: QuantumCircuit,
    gate: str,
    target: int,
    control: Optional[int] = None
):
    """
    Apply a quantum gate.
    Supports both single-qubit and controlled gates.
    """

    if circuit is None:
        raise ValueError("Circuit is None")

    gate = gate.upper()
    logging.basicConfig(level=logging.INFO)
    logging.info(
        f"Gate={gate}, Control={control}, Target={target}"
    )
    if target < 0 or target >= circuit.num_qubits:
        raise ValueError("Invalid target qubit.")

    # ------------------------
    # Single-qubit gates
    # ------------------------

    if gate == "H":
        circuit.h(target)

    elif gate == "X":
        circuit.x(target)

    elif gate == "Y":
        circuit.y(target)

    elif gate == "Z":
        circuit.z(target)

    elif gate == "S":
        circuit.s(target)

    elif gate == "T":
        circuit.t(target)

    # ------------------------
    # Two-qubit gates
    # ------------------------

    elif gate == "CX":

        if control is None:
            raise ValueError("CX gate requires a control qubit.")

        if control == target:
            raise ValueError(
                "Control and target must be different."
            )

        circuit.cx(control, target)

    elif gate == "CZ":

        if control is None:
            raise ValueError("CZ gate requires a control qubit.")

        if control == target:
            raise ValueError(
                "Control and target must be different."
            )

        circuit.cz(control, target)

    elif gate == "CH":

        if control is None:
            raise ValueError("CH gate requires a control qubit.")

        if control == target:
            raise ValueError(
                "Control and target must differ."
            )

        circuit.ch(control, target)

    elif gate == "CCX":

        if control is None:
            raise ValueError("CH gate requires a control qubit.")

        if control == target:
            raise ValueError(
                "Control and target must differ."
            )

        circuit.ch(control, target)

    elif gate == "SWAP":

        if control is None:
            raise ValueError("SWAP gate requires another qubit.")

        if control == target:
            raise ValueError(
                "Control and target must be different."
            )

        circuit.swap(control, target)
    elif gate == "CY":

        if control is None:
            raise ValueError("CY gate requires a control qubit.")

        if control == target:
            raise ValueError(
                "Control and target must differ."
            )

        circuit.cy(control, target)
    elif gate == "BARRIER":
        circuit.barrier()

    else:

        raise ValueError(
            f"Unsupported gate '{gate}'."
        )

    return circuit


# --------------------------------------------------------------------
# Gate Validation
# --------------------------------------------------------------------

SUPPORTED_GATES = {

    "H",
    "X",
    "Y",
    "Z",
    "S",
    "T",

    "CX",
    "CZ",
    "CY",
    "SWAP"

}


def is_supported_gate(gate: str) -> bool:
    """
    Check whether a gate is supported.
    """

    return gate.upper() in SUPPORTED_GATES


# --------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------

def get_statistics(
    circuit: QuantumCircuit
):
    """
    Return basic circuit statistics.
    """

    measurement_count = sum(
        1
        for instruction in circuit.data
        if instruction.operation.name == "measure"
    )

    stats = {
        "qubits": circuit.num_qubits,
        "clbits": circuit.num_clbits,
        "depth": circuit.depth(),
        "width": circuit.width(),
        "gate_count": len(circuit.data),
        "operations": dict(circuit.count_ops()),
        "measurements": measurement_count
    }

    return stats
# --------------------------------------------------------------------
# Draw Circuit
# --------------------------------------------------------------------




def draw_circuit(
    circuit: QuantumCircuit,
    output_folder: Path,
    filename: str = "circuit.png"
) -> str:
    """
    Draw the circuit and save it as a PNG image.
    Returns the full path to the generated image.
    """

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs("projects", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    image_path = output_folder / filename

    try:

        figure = circuit.draw(
            output="mpl",
            idle_wires=False,
            fold=-1
        )

        figure.savefig(
            str(image_path),
            dpi=200,
            bbox_inches="tight"
        )

        plt.close(figure)

    except Exception as e:

        raise RuntimeError(
            f"Unable to draw circuit: {e}"
        )

    return str(image_path)

# --------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------

def simulate_circuit(
    circuit: QuantumCircuit,
    shots: int = 1024
):
    """
    Simulate the circuit.

    Returns
    -------
    dict

        statevector
        counts
    """

    simulator = AerSimulator()

    measured = circuit.copy()

    measured.measure_all()

    compiled = transpile(
        measured,
        simulator
    )
    result = simulator.run(
        compiled,
        shots=shots
    ).result()

    counts = result.get_counts()

    statevector = Statevector.from_instruction(
        circuit.remove_final_measurements(inplace=False)
    )

    amplitudes = {}

    for index, amplitude in enumerate(statevector.data):

        if abs(amplitude) > 1e-10:

            binary = format(
                index,
                f"0{circuit.num_qubits}b"
            )

            amplitudes[binary] = {
                "real": round(float(amplitude.real), 6),
                "imag": round(float(amplitude.imag), 6),
                "probability": round(
                    float(abs(amplitude) ** 2),
                    6
                )
            }

    return {

        "counts": counts,

        "statevector": amplitudes

    }


# --------------------------------------------------------------------
# Export Statevector
# --------------------------------------------------------------------

def statevector_text(
    circuit: QuantumCircuit
) -> str:

    state = Statevector.from_instruction(circuit)

    lines = []

    for index, amp in enumerate(state.data):

        binary = format(
            index,
            f"0{circuit.num_qubits}b"
        )

        probability = abs(amp) ** 2

        lines.append(

            f"|{binary}> : "

            f"{amp.real:.5f}"

            f"+"

            f"{amp.imag:.5f}j"

            f"   "

            f"P={probability:.5f}"

        )

    return "\n".join(lines)


# --------------------------------------------------------------------
# Version
# --------------------------------------------------------------------

def quantum_version():

    return {

        "engine": "Qiskit",

        "supported_gates": sorted(
            list(SUPPORTED_GATES)
        )

    }