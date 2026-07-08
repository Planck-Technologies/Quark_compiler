def test_circuit_creation() -> None:
    """
    Test that a Circuit can be initialized with the correct number of qubits.

    TODO:
    1. Instantiate a Circuit with a specific number of qubits (e.g., 3).
    2. Assert that the num_qubits property returns the expected value (e.g., 3).
    3. Assert that the gates property returns an empty list.
    """
    # Your code here
    pass


def test_add_gate_in_bounds() -> None:
    """
    Test adding valid gates to the circuit.

    TODO:
    1. Instantiate a Circuit with a specific number of qubits (e.g., 3).
    2. Create a Gate operating on qubits that are within bounds (e.g., target 1, control 0).
    3. Add the gate to the circuit using add_gate.
    4. Assert that the gate is in the gates list.
    """
    # Your code here
    pass


def test_add_gate_out_of_bounds() -> None:
    """
    Test that adding a gate with out-of-bounds qubits raises IndexError.

    TODO:
    1. Instantiate a Circuit with a specific number of qubits (e.g., 2).
    2. Create a Gate operating on a qubit index out of bounds (e.g., target 2).
    3. Use pytest.raises(IndexError) to assert that calling add_gate raises IndexError.
    """
    # Your code here
    pass
