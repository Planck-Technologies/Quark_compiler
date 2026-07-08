import pytest
from src.gate import Gate, GateType

def test_valid_gate_creation():
    """Test that a valid gate sets up properties correctly."""
    gate = Gate(GateType.CNOT, target_qubits=(1,), control_qubits=(0,))
    # Write assertions to verify gate_type, target_qubits, and control_qubits match
    assert gate.gate_type == GateType.CNOT
    assert gate.target_qubits == (1,)
    assert gate.control_qubits == (0,)
    assert gate.all_qubits == {0, 1}
    # Add assertions for targets, controls, and all_qubits here...

def test_overlapping_qubits_raises_error():
    """Test that a non-physical gate triggers a ValueError."""
    with pytest.raises(expected_exception=ValueError):
        Gate(GateType.CNOT, target_qubits=(0,), control_qubits=(0,))
        # Instantiate a gate where a qubit is both target and control
        pass

def test_gate_immutability():
    """Test that public properties cannot be overwritten."""
    gate = Gate(GateType.X, target_qubits=(0,))
    with pytest.raises(expected_exception=AttributeError):
        gate.gate_type = GateType.H
        # Try to manually change gate.gate_type to GateType.H
        pass

@pytest.mark.parametrize(
    argnames="gate_a, gate_b, expected_commute",
    argvalues=[
        # --- CASE 1: Completely disjoint qubits ---
        (
            Gate(GateType.X, target_qubits=(0,)), 
            Gate(GateType.Z, target_qubits=(1,)), 
            True
        ),
        # --- CASE 2: Same qubit, non-commuting Pauli operators ---
        (
            Gate(GateType.X, target_qubits=(0,)), 
            Gate(GateType.Z, target_qubits=(0,)), 
            False
        ),
        # --- CASE 3: Rule 3 (X gate on CNOT control line) ---
        (
            Gate(GateType.X, target_qubits=(0,)), 
            Gate(GateType.CNOT, target_qubits=(1,), control_qubits=(0,)), 
            False
        ),
        # --- CASE 4: Rule 4 (Z gate on CNOT target line) ---
        (
            Gate(GateType.Z, target_qubits=(1,)), 
            Gate(GateType.CNOT, target_qubits=(1,), control_qubits=(0,)), 
            False
        ),
        # --- CASE 5: X gate on CNOT target line ---
        (
            Gate(GateType.X, target_qubits=(1,)), 
            Gate(GateType.CNOT, target_qubits=(1,), control_qubits=(0,)), 
            True
        ),
        # --- CASE 6: Z gate on CNOT control line ---
        (
            Gate(GateType.Z, target_qubits=(0,)), 
            Gate(GateType.CNOT, target_qubits=(1,), control_qubits=(0,)), 
            True
        )
    ]
)
def test_gate_commutation_rules(gate_a: Gate, gate_b: Gate, expected_commute: bool):
    """Verify that commutation rules resolve correctly across different gate layouts."""
    assert gate_a.commutes_with(other=gate_b) == expected_commute
    # Commutation is symmetric (A fixes B implies B fixes A)
    assert gate_b.commutes_with(other=gate_a) == expected_commute