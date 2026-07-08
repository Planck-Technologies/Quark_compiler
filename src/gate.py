from typing import Tuple, Optional
import enum


class GateType(enum.Enum):
    """Supported gate types for the Clifford+T optimization pass."""

    H = "H"
    X = "X"
    Y = "Y"
    Z = "Z"
    S = "S"
    T = "T"
    CNOT = "CNOT"


class Gate:
    """Represents a single quantum gate operation in a circuit."""

    __slots__ = (
        "_gate_type",
        "_target_qubits",
        "_control_qubits",
        "_all_qubits",
    )

    def __init__(
        self,
        _gate_type: GateType,
        target_qubits: Tuple[int, ...],
        control_qubits: Optional[Tuple[int, ...]] = None,
    ):
        if not target_qubits:
            raise ValueError("Gate must have at least one target qubit.")

        self._gate_type: GateType = _gate_type
        self._target_qubits: Tuple[int, ...] = tuple(target_qubits)
        self._control_qubits: Tuple[int, ...] = (
            tuple(control_qubits) if control_qubits else ()
        )
        # Make all qubits a frozenset so that new qubits can be added to the
        # set without mutating the original set.
        self._all_qubits: frozenset[int] = frozenset(self._target_qubits).union(
            self._control_qubits
        )

        # Verify no qubit is used as both a target and a control simultaneously
        if len(self._all_qubits) != (
            len(self._target_qubits) + len(self._control_qubits)
        ):
            raise ValueError(
                f"Overlapping qubits found in target {self._target_qubits} and control {self._control_qubits}"
            )

    @property
    def is_self_inverse(self) -> bool:
        """Returns True if applying this gate twice results in Identity."""
        # H, X, Y, Z, and CNOT are self-inverse. S and T are not (S^2 = Z, T^2 = S).
        return self._gate_type in {
            GateType.H,
            GateType.X,
            GateType.Y,
            GateType.Z,
            GateType.CNOT,
        }

    @property
    def gate_type(self) -> GateType:
        """Returns the type of the gate."""
        return self._gate_type

    @property
    def target_qubits(self) -> Tuple[int, ...]:
        """Returns the target qubits of the gate."""
        return self._target_qubits

    @property
    def control_qubits(self) -> Tuple[int, ...]:
        """Returns the control qubits of the gate."""
        return self._control_qubits

    @property
    def all_qubits(self) -> frozenset[int]:
        """Returns all qubits involved in the gate."""
        return self._all_qubits

    def commutes_with(self, other: "Gate") -> bool:
        """
        Determines if this gate commutes with another gate.
        """
        # If they don't share any qubits, they always commute
        if not self.all_qubits.intersection(other.all_qubits):
            return True

        # Rule 1: Identical single-qubit Pauli/Clifford gates on the same qubit commute
        if self._gate_type == other._gate_type and len(self.all_qubits) == 1:
            return True

        # Rule 2: Z-basis gates (Z, S, T) commute with each other on the same qubit
        z_basis: set[GateType] = {GateType.Z, GateType.S, GateType.T}
        if self._gate_type in z_basis and other._gate_type in z_basis:
            return True

        # Helper function to check asymmetric commutation rules
        def commutes_asymmetric(g1: "Gate", g2: "Gate") -> bool:
            if g2._gate_type == GateType.CNOT:
                # Rule 3: X gate commutes with the TARGET line of a CNOT gate
                if (
                    g1._gate_type == GateType.X
                    and g1.target_qubits[0] in g2.target_qubits
                ):
                    return True
                # Rule 4: Z-basis gates commute with the CONTROL line of a CNOT gate
                if (
                    g1._gate_type in z_basis
                    and g1.target_qubits[0] in g2.control_qubits
                ):
                    return True
            return False

        if commutes_asymmetric(self, other) or commutes_asymmetric(other, self):
            return True

        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate):
            return False
        return (
            self._gate_type == other._gate_type
            and self.target_qubits == other.target_qubits
            and self.control_qubits == other.control_qubits
        )

    def __repr__(self) -> str:
        controls: str = (
            f" ctrl={list(self.control_qubits)}" if self.control_qubits else ""
        )
        return f"Gate({self._gate_type.value}, targets={list(self.target_qubits)}{controls})"

    def __hash__(self) -> int:
        return hash((self._gate_type, self.target_qubits, self.control_qubits))
