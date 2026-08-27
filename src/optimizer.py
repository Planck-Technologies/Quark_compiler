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
        circ_new = Circuit(num_qubits=circuit.num_qubits)

        # Generator for a unique ID for new nodes
        def _get_new_id(d):
            if not d.nodes:
                return 0
            return max(n[0] for n in d.nodes) + 1

        while True:
            sorted_nodes = list(nx.topological_sort(dag))
            modified = False
            for node in sorted_nodes:
                if node not in dag:
                    continue
                partner = self._find_cancellation_partner(dag, node)
                if partner is not None:
                    try:
                        merged_gate = node[1].merge_with(partner[1])
                    except ValueError:
                        # Cannot be merged (e.g. they are not on the same axis)
                        if node[1] == partner[1] and node[1].is_self_inverse:
                            # Self-inverse cancellation
                            self._rewire_and_remove(dag, node, partner)
                            modified = True
                            break
                        continue

                    if merged_gate is None:
                        # Identity, remove both
                        self._rewire_and_remove(dag, node, partner)
                        modified = True
                        break
                    else:
                        # We have a valid merged_gate that is not identity.
                        # We will replace `node` with `new_node` in the same topological position,
                        # and remove `partner` by rewiring its edges exactly like `_rewire_and_remove`
                        # would if we were cancelling it.
                        new_node = (_get_new_id(dag), merged_gate)
                        dag.add_node(new_node)

                        # Replace `node` with `new_node` directly
                        for p in list(dag.predecessors(node)):
                            dag.add_edge(p, new_node)
                        for s in list(dag.successors(node)):
                            # Only add if it's not partner (though partner is usually further down)
                            if s != partner:
                                dag.add_edge(new_node, s)

                        # The partner's predecessors and successors need to be bridged around partner
                        # just like in _rewire_and_remove, but we must make sure if node was
                        # its predecessor, we bridge from new_node instead.
                        qubits = list(partner[1].all_qubits)
                        for q in qubits:
                            pred_node_2 = next(
                                (
                                    p
                                    for p in dag.predecessors(partner)
                                    if q in p[1].all_qubits
                                ),
                                None,
                            )
                            succ_node_2 = self._next_node_on_wire(dag, partner, q)

                            # If the immediate predecessor is the original `node`, use `new_node`
                            if pred_node_2 == node:
                                pred_node_2 = new_node

                            if pred_node_2 is not None and succ_node_2 is not None:
                                # Ensure we don't accidentally create self-loops
                                if pred_node_2 != succ_node_2:
                                    dag.add_edge(pred_node_2, succ_node_2)

                        dag.remove_node(node)
                        dag.remove_node(partner)

                        modified = True
                        break

            if not modified:
                break

        for _, gate in nx.topological_sort(dag):
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
        for succ_node in dag.successors(current_node):
            if qubit in succ_node[1].all_qubits:
                return succ_node
        return None

    def _find_cancellation_partner(
        self,
        dag: nx.DiGraph,
        node: tuple[int, Gate],
    ) -> tuple[int, Gate] | None:
        """Looks ahead along the qubit wires to find a gate that can commute to meet this node and can be merged or cancelled.

        Args:
            dag: The dependency graph (DAG).
            node: The node tuple (idx, gate) to find a partner for.

        Returns:
            The matching node tuple (idx, gate) if one exists and commutes with all
            intervening gates, otherwise None.
        """
        involved_qubits = list(node[1].all_qubits)
        current = node
        candidate_partner = None
        start_qubit = involved_qubits[0]
        while True:
            next_node = self._next_node_on_wire(dag, current, start_qubit)
            if next_node is None:
                return None

            # Check if it's a potential merge partner: acts on exactly the same qubits
            if next_node[1].target_qubits == node[1].target_qubits and next_node[1].control_qubits == node[1].control_qubits:
                # It must either be identical (for cancellation) or mergeable
                try:
                    node[1].merge_with(next_node[1])
                    is_mergeable = True
                except ValueError:
                    is_mergeable = False

                if next_node[1] == node[1] or is_mergeable:
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
