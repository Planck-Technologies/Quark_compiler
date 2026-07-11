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
        dag = circuit.to_dag()

        # TODO:
        # 1. Run a loop while changes are being made:
        #    - Sort nodes topologically: sorted_nodes = list(nx.topological_sort(dag))
        #    - Search for a self-inverse node that has a cancellation partner:
        #      - For each node in sorted_nodes (if node in dag and node[1].is_self_inverse):
        #        - Find its partner: partner = self._find_cancellation_partner(dag, node)
        #        - If partner is not None:
        #          - Rewire and remove both nodes: self._rewire_and_remove(dag, node, partner)
        #          - Mark modified = True and break the inner loop to restart sorting.
        #    - If no modifications were made, break the outer loop.

        # 2. Rebuild and return the new Circuit instance from the remaining nodes in topological order.
        circ_new = Circuit(num_qubits=circuit.num_qubits)
        while True:
            sorted_nodes = list(nx.topological_sort(dag))
            modified = False
            for node in sorted_nodes:
                if node in dag and node[1].is_self_inverse:
                    partner = self._find_cancellation_partner(dag, node)
                    if partner is not None:
                        self._rewire_and_remove(dag, node, partner)
                        modified = True
                        break
            if not modified:
                break

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

    def _rewire_and_remove(
        self,
        dag: nx.DiGraph,
        node1: tuple[int, Gate],
        node2: tuple[int, Gate],
    ) -> None:
        """Helper to rewire edges around two canceling nodes and then remove them from the DAG.

        Args:
            dag: The dependency graph (DAG).
            node1: The first node tuple to cancel.
            node2: The second node tuple to cancel.
        """
        # TODO:
        # 1. Get the list of all qubits involved in node1's gate: qubits = list(node1[1].all_qubits).
        # 2. For each qubit q in qubits:
        #    - Find the immediate predecessor of node1 on wire q:
        #      - Loop through dag.predecessors(node1) and find p such that q in p[1].all_qubits.
        #    - Find the immediate successor of node1 on wire q: next_q = self._next_node_on_wire(dag, node1, q).
        #    - If next_q == node2 (they are adjacent on wire q):
        #      - Find the successor of node2 on wire q: succ_q = self._next_node_on_wire(dag, node2, q).
        #      - Connect pred_q directly to succ_q if both are not None.
        #    - Else (if there are intervening gates on wire q):
        #      - Connect pred_q directly to next_q (the first intervening gate).
        #      - Find the predecessor of node2 on wire q (the last intervening gate):
        #        - Loop through dag.predecessors(node2) and find p_node2 such that q in p_node2[1].all_qubits.
        #      - Find the successor of node2 on wire q: succ_q = self._next_node_on_wire(dag, node2, q).
        #      - Connect p_node2 directly to succ_q if both are not None.
        # 3. Remove node1 and node2 from the DAG using dag.remove_node().
        qubits = list(node1[1].all_qubits)
        for q in qubits:
            pred_node_1 = next(
                (
                    p_node_1
                    for p_node_1 in dag.predecessors(node1)
                    if q in p_node_1[1].all_qubits
                ),
                None,
            )
            succ_node_1 = self._next_node_on_wire(dag, node1, q)
            if succ_node_1 == node2:
                succ_node_2 = self._next_node_on_wire(dag, node2, q)
                if pred_node_1 is not None and succ_node_2 is not None:
                    dag.add_edge(pred_node_1, succ_node_2)
            else:
                pred_node_2 = next(
                    (
                        p_node_2
                        for p_node_2 in dag.predecessors(node2)
                        if q in p_node_2[1].all_qubits
                    ),
                    None,
                )
                succ_node_2 = self._next_node_on_wire(dag, node2, q)
                if pred_node_1 is not None and succ_node_1 is not None:
                    dag.add_edge(pred_node_1, succ_node_1)
                if pred_node_2 is not None and succ_node_2 is not None:
                    dag.add_edge(pred_node_2, succ_node_2)
        dag.remove_node(node1)
        dag.remove_node(node2)
