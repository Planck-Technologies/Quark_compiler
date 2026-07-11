from src.circuit import Circuit
from src.gate import Gate, GateType
from src.optimizer import GateCancellationPass


def test_baseline_optimizer_returns_copy() -> None:
    """Test that the baseline optimizer returns a new Circuit instance with identical gates."""
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.H, (0,)))
    circ.add_gate(Gate(GateType.X, (1,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit is not circ
    assert optimized_circuit.num_qubits == circ.num_qubits
    assert optimized_circuit.gates == circ.gates


def test_single_qubit_cancellation() -> None:
    """Test that two adjacent identical self-inverse gates cancel.

    TODO:
    1. Create a 1-qubit Circuit.
    2. Add X on qubit 0 twice.
    3. Run optimizer.
    4. Assert that the optimized circuit has 0 gates.
    """
    circ = Circuit(1)
    circ.add_gate(Gate(GateType.X, (0,)))
    circ.add_gate(Gate(GateType.X, (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == ()


def test_single_qubit_commutation_cancellation() -> None:
    """Test that two identical self-inverse gates cancel after commuting past an intervening gate.

    TODO:
    1. Create a 2-qubit Circuit.
    2. Add X on qubit 0, Z on qubit 1, and X on qubit 0.
    3. Run optimizer.
    4. Assert that the optimized circuit has exactly 1 gate (the Z gate on qubit 1).
    """
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.X, (0,)))
    circ.add_gate(Gate(GateType.Z, (1,)))
    circ.add_gate(Gate(GateType.X, (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == (Gate(GateType.Z, (1,)),)


def test_multi_qubit_cancellation() -> None:
    """Test CNOT adjacent cancellation.

    TODO:
    1. Create a 2-qubit Circuit.
    2. Add CNOT (target 1, control 0) twice.
    3. Run optimizer.
    4. Assert that the optimized circuit has 0 gates.
    """
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == ()


def test_multi_qubit_commutation_cancellation() -> None:
    """Test CNOT lookahead cancellation with commuting gates on target and control lines.

    TODO:
    1. Create a 2-qubit Circuit.
    2. Add CNOT (target 1, control 0), X on qubit 1, Z on qubit 0, and CNOT (target 1, control 0).
    3. Run optimizer.
    4. Assert that the CNOTs cancel, leaving only X on qubit 1 and Z on qubit 0.
    """
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    circ.add_gate(Gate(GateType.X, (1,)))
    circ.add_gate(Gate(GateType.Z, (0,)))
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == (
        Gate(GateType.X, (1,)),
        Gate(GateType.Z, (0,)),
    )


def test_non_cancellation_due_to_non_commutation() -> None:
    """Test that non-commuting intervening gates block cancellation.

    TODO:
    1. Create a 1-qubit Circuit.
    2. Add X on qubit 0, Z on qubit 0, and X on qubit 0.
    3. Run optimizer.
    4. Assert that no gates cancel (optimized circuit has 3 gates).
    """
    circ = Circuit(1)
    circ.add_gate(Gate(GateType.X, (0,)))
    circ.add_gate(Gate(GateType.Z, (0,)))
    circ.add_gate(Gate(GateType.X, (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == (
        Gate(GateType.X, (0,)),
        Gate(GateType.Z, (0,)),
        Gate(GateType.X, (0,)),
    )


def test_nested_cancellation() -> None:
    """Test that cancellations can be nested and repeated across multiple passes.

    TODO:
    1. Create a 2-qubit circuit with the sequence: H(0), CNOT(1,0), CNOT(1,0), H(0).
       H(0) is self-inverse, and the two CNOTs should cancel each other out.
    2. Run the optimizer and assert that the result has 0 gates.

    Note: The current implementation runs only a single pass. This test may need to be
    updated to run the optimizer in a loop if multiple passes are required for more complex
    circuits (though for this specific case, one pass should suffice as the CNOTs are adjacent).
    """
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.H, (0,)))
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    circ.add_gate(Gate(GateType.H, (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == ()


def test_cnot_lookahead_fails_on_second_wire() -> None:
    """Test that lookahead fails if one of the CNOT lines is blocked by a non-commuting gate.

    TODO:
    1. Create a 2-qubit circuit with CNOT(1,0), Z(1), CNOT(1,0).
    2. Run optimizer.
    3. Assert that the gates do NOT cancel (optimized circuit has 3 gates).
    """
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    circ.add_gate(Gate(GateType.Z, (1,)))
    circ.add_gate(Gate(GateType.CNOT, (1,), (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == (
        Gate(GateType.CNOT, (1,), (0,)),
        Gate(GateType.Z, (1,)),
        Gate(GateType.CNOT, (1,), (0,)),
    )


def test_rewiring_intervening_gates_with_outer_neighbors() -> None:
    """Test that graph rewiring correctly bridges intervening gates when outer neighbors exist.

    TODO:
    1. Create a 2-qubit circuit: H(0), X(0), CNOT(0,1) (Wait, target 0, control 1), X(0), H(0).
    2. Run optimizer.
    3. Assert that the X gates cancel, leaving: H(0) -> CNOT(0,1) -> H(0).
    """
    circ = Circuit(2)
    circ.add_gate(Gate(GateType.H, (0,)))
    circ.add_gate(Gate(GateType.X, (0,)))
    circ.add_gate(Gate(GateType.CNOT, (0,), (1,)))
    circ.add_gate(Gate(GateType.X, (0,)))
    circ.add_gate(Gate(GateType.H, (0,)))
    optimizer = GateCancellationPass()
    optimized_circuit = optimizer.optimize(circ)
    assert optimized_circuit.gates == (
        Gate(GateType.H, (0,)),
        Gate(GateType.CNOT, (0,), (1,)),
        Gate(GateType.H, (0,)),
    )
