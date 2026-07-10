"""Optimization passes for quantum circuits."""

import networkx as nx

from src.circuit import Circuit
from src.gate import Gate


class GateCancellationPass:
    """Base class for circuit optimization passes that cancel redundant gates.

    All optimization passes should be non-mutating, returning a new Circuit.
    """

    def optimize(self, circuit: Circuit) -> Circuit:
        """Applies the gate cancellation pass to a quantum circuit.

        Args:
            circuit: The input Circuit to optimize.

        Returns:
            A new, optimized Circuit instance.
        """
        # TODO:
        # 1. Retrieve the DAG representation from the circuit.
        # 2. Perform graph traversal and cancellation logic (implemented in later days).
        # 3. Build and return a brand new Circuit instance with the remaining gates.
        circ_new = Circuit(num_qubits=circuit.num_qubits)
        sorted_nodes = list(nx.topological_sort(circuit.to_dag()))
        for _, gate in sorted_nodes:
            circ_new.add_gate(gate)
        return circ_new

    def _next_node_on_wire(
        self,
        dag: nx.DiGraph,
        current_node: tuple[int, Gate],
        qubit: int,
    ) -> tuple[int, Gate] | None:
        """Finds the immediate next node in the DAG that acts on the specified qubit wire.

        Args:
            dag: The dependency graph (DAG).
            current_node: The starting node tuple (idx, gate).
            qubit: The qubit wire to trace.

        Returns:
            The successor node tuple (idx, gate) touching the qubit wire,
            or None if current_node is the last gate on that wire.
        """
        # TODO:
        # 1. Loop through all successors of current_node in the DAG using dag.successors(current_node).
        # 2. For each successor node (which is a tuple (idx, gate)), check if the specified
        #    qubit is involved in the successor's gate (qubit in successor_node[1].all_qubits).
        # 3. If a match is found, return that successor node.
        # 4. If the loop completes without finding a match, return None.
        for succ_node in dag.successors(current_node):
            if qubit in succ_node[1].all_qubits:
                return succ_node
        return None

    def _find_cancellation_partner(
        self,
        dag: nx.DiGraph,
        node: tuple[int, Gate],
    ) -> tuple[int, Gate] | None:
        """Looks ahead along the qubit wires to find an identical gate that can commute to meet this node.

        Args:
            dag: The dependency graph (DAG).
            node: The node tuple (idx, gate) to find a partner for.

        Returns:
            The matching node tuple (idx, gate) if one exists and commutes with all
            intervening gates, otherwise None.
        """
        # TODO:
        # 1. Get all qubits involved in this gate: qubits = node[1].all_qubits.
        # 2. Pick a starting qubit to trace (e.g., next(iter(qubits))).
        # 3. Trace forward along this qubit wire using self._next_node_on_wire:
        #    - Set current = node.
        #    - Loop:
        #      - next_node = self._next_node_on_wire(dag, current, start_qubit)
        #      - If next_node is None: return None.
        #      - If next_node[1] == node[1]: we found a candidate partner node. Break and verify.
        #      - If not, check if node[1].commutes_with(next_node[1]).
        #      - If they do NOT commute: return None (blocked).
        #      - Set current = next_node and repeat.
        # 4. For any other qubits in the gate (e.g., the target or control of CNOT):
        #    - Trace forward along that wire:
        #      - Set current = node.
        #      - Loop:
        #        - next_node = self._next_node_on_wire(dag, current, other_qubit)
        #        - If next_node == candidate_partner: this wire is clear. Break.
        #        - If next_node is None or not node[1].commutes_with(next_node[1]): return None.
        #        - Set current = next_node and repeat.
        # 5. If all wires are clear, return candidate_partner.
        involved_qubits = list(node[1].all_qubits)
        current = node
        candidate_partner = None
        start_qubit = involved_qubits[0]
        while True:
            next_node = self._next_node_on_wire(dag, current, start_qubit)
            if next_node is None:
                return None
            if next_node[1] == node[1]:
                candidate_partner = next_node
                break
            if not node[1].commutes_with(next_node[1]):
                return None
            current = next_node
        for other_qubit in involved_qubits[1:]:
            current = node
            while True:
                next_node = self._next_node_on_wire(dag, current, other_qubit)
                if next_node == candidate_partner:
                    break
                if next_node is None or not node[1].commutes_with(next_node[1]):
                    return None
                current = next_node
        return candidate_partner
