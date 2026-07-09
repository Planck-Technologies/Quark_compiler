"""Unit tests for the Circuit class."""

import pytest

from src.circuit import Circuit
from src.gate import Gate, GateType


def test_circuit_creation() -> None:
    """Tests that a Circuit can be initialized with the correct number of qubits."""
    circuit = Circuit(3)
    assert circuit.num_qubits == 3
    assert circuit.gates == ()


def test_add_gate_in_bounds() -> None:
    """Tests adding valid gates to the circuit within qubit bounds."""
    circuit = Circuit(3)
    gate = Gate(GateType.CNOT, (1,), (0,))
    circuit.add_gate(gate)
    assert circuit.gates == (gate,)


def test_add_gate_out_of_bounds() -> None:
    """Tests that adding a gate with out-of-bounds qubits raises IndexError."""
    circuit = Circuit(2)
    gate = Gate(GateType.H, (2,))
    with pytest.raises(IndexError):
        circuit.add_gate(gate)
