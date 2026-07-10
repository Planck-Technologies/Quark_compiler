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
