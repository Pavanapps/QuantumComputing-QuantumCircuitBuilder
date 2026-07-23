import json
from datetime import datetime
from pathlib import Path
import uuid




class CircuitProject:
    PROJECT_VERSION = "1.0"

    @staticmethod
    def save(project: dict, filename: Path):

        filename.parent.mkdir(
            exist_ok=True,
            parents=True
        )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                project,
                f,
                indent=4,
                ensure_ascii=False
            )

    @staticmethod
    def load(filename: Path):

        # ------------------------------------------
        # Validate file extension
        # ------------------------------------------
        if filename.suffix.lower() != ".json":
            raise ValueError(
                "Invalid project file. Expected a JSON file."
            )

        # ------------------------------------------
        # File must exist
        # ------------------------------------------
        if not filename.exists():
            raise FileNotFoundError(
                f"Project not found: {filename}"
            )

        try:

            with open(
                    filename,
                    "r",
                    encoding="utf-8"
            ) as f:

                project = json.load(f)

        except json.JSONDecodeError as e:

            raise ValueError(
                "Project file is corrupted."
            ) from e

        # ------------------------------------------
        # Validate metadata
        # ------------------------------------------

        metadata = project.get("metadata")

        if metadata is None:
            raise ValueError(
                "Invalid project format."
            )

        version = metadata.get("project_version")

        if version != CircuitProject.PROJECT_VERSION:
            raise ValueError(
                f"Unsupported project version: {version}"
            )

        return project

    @staticmethod
    def circuit_to_json(circuit):

        data = []

        measurement_count = 0

        for instruction in circuit.data:

            gate = instruction.operation.name.upper()

            qubits = [
                circuit.find_bit(q).index
                for q in instruction.qubits
            ]

            operation = {
                "gate": gate,
                "target": qubits[-1]
            }

            if len(qubits) == 2:
                operation["control"] = qubits[0]

            data.append(operation)

            if gate == "MEASURE":
                measurement_count += 1

        timestamp = datetime.now().isoformat()

        return {

            # ==========================================
            # Project Metadata
            # ==========================================
            "metadata": {

                "project_id": str(uuid.uuid4()),

                "project_name": "Untitled Circuit",

                "description": "",

                "tags": [],

                "project_version": CircuitProject.PROJECT_VERSION,

                "created_by": "AppsOnline.online",

                "created_on": timestamp,

                "modified_on": timestamp,

                "thumbnail": ""

            },

            # ==========================================
            # Circuit Statistics
            # ==========================================
            "statistics": {

                "qubits": circuit.num_qubits,

                "classical_bits": circuit.num_clbits,

                "gate_count": len(data),

                "depth": circuit.depth(),

                "measurement_count": measurement_count

            },

            # ==========================================
            # Circuit Operations
            # ==========================================
            "operations": data

        }

    @staticmethod
    def list_projects(folder: Path):

        folder.mkdir(
            exist_ok=True,
            parents=True
        )

        return sorted(
            folder.glob("*.json"),
            key=lambda file: file.stat().st_mtime,
            reverse=True
        )

    @staticmethod
    def delete(filename: Path):

        if filename.exists():
            filename.unlink()