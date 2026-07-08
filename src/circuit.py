from src.gate import Gate


class Circuit:
    """Represents a quantum circuit consisting of multiple gates."""

    def __init__(self, num_qubits: int) -> None:
        """
        Initialize the Circuit.

        TODO:
        1. Store num_qubits.
        2. Initialize an internal list self._gates to track added gates.
        """
        # Your code here
        pass

    @property
    def num_qubits(self) -> int:
        """
        Returns the number of qubits in the circuit (read-only).

        TODO: Return the stored number of qubits.
        """
        # Your code here
        return 0

    @property
    def gates(self) -> list[Gate]:
        """
        Returns the list of gates in the circuit.

        TODO: Return the internal gate tracking list.
        """
        # Your code here
        return [Gate("X", (0,))]  # type: ignore

    def add_gate(self, gate: Gate) -> None:
        """
        Adds a gate to the circuit after validating qubit boundaries.

        TODO:
        1. Iterate through gate.all_qubits.
        2. Raise IndexError if any qubit index is >= self.num_qubits.
        3. Append the gate to self._gates.
        """
        # Your code here
        pass
