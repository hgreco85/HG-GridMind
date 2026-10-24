"""Deterministic causal invariant discovery, verification, and falsification engine.

Provides formal representation for causal Directed Acyclic Graphs (DAGs),
structural causal models (SCMs) with deterministic interventions (do-calculus),
and invariance testing across interventional distributions to falsify or validate
hypothesized causal structures.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Mapping, Optional, Sequence, Set, Tuple
import math


@dataclass(frozen=True)
class CausalNode:
    """Represents an observed or latent variable in a causal model."""
    name: str


@dataclass
class CausalGraph:
    """Directed Acyclic Graph (DAG) representing causal relationships."""
    nodes: Set[str] = field(default_factory=set)
    parents: Dict[str, Set[str]] = field(default_factory=dict)
    children: Dict[str, Set[str]] = field(default_factory=dict)

    def add_node(self, node: str) -> None:
        self.nodes.add(node)
        self.parents.setdefault(node, set())
        self.children.setdefault(node, set())

    def add_edge(self, source: str, target: str) -> None:
        self.add_node(source)
        self.add_node(target)
        if source == target:
            raise ValueError(f"Self-loops are not permitted in DAGs: {source} -> {target}")
        self.children[source].add(target)
        self.parents[target].add(source)
        if not self.is_acyclic():
            self.children[source].remove(target)
            self.parents[target].remove(source)
            raise ValueError(f"Cycle detected when adding edge {source} -> {target}")

    def is_acyclic(self) -> bool:
        in_degree = {n: len(self.parents[n]) for n in self.nodes}
        queue = deque([n for n, deg in in_degree.items() if deg == 0])
        visited = 0
        while queue:
            curr = queue.popleft()
            visited += 1
            for child in self.children[curr]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        return visited == len(self.nodes)

    def topological_sort(self) -> List[str]:
        in_degree = {n: len(self.parents[n]) for n in self.nodes}
        queue = deque(sorted([n for n, deg in in_degree.items() if deg == 0]))
        order = []
        while queue:
            curr = queue.popleft()
            order.append(curr)
            for child in sorted(self.children[curr]):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        if len(order) != len(self.nodes):
            raise ValueError("Graph contains cycles; cannot produce topological order.")
        return order

    def get_ancestors(self, node: str) -> Set[str]:
        ancestors = set()
        queue = deque(self.parents.get(node, set()))
        while queue:
            curr = queue.popleft()
            if curr not in ancestors:
                ancestors.add(curr)
                queue.extend(self.parents.get(curr, set()))
        return ancestors


@dataclass
class StructuralEquation:
    """Deterministic structural assignment: X_i := f_i(PA_i, U_i)."""
    target: str
    parents: Sequence[str]
    function: Callable[[Mapping[str, float], float], float]


class StructuralCausalModel:
    """Defines a deterministic Structural Causal Model (SCM)."""

    def __init__(self, graph: CausalGraph) -> None:
        self.graph = graph
        self.equations: Dict[str, StructuralEquation] = {}

    def set_equation(self, target: str, parents: Sequence[str], func: Callable[[Mapping[str, float], float], float]) -> None:
        for p in parents:
            if p not in self.graph.parents.get(target, set()):
                self.graph.add_edge(p, target)
        self.equations[target] = StructuralEquation(target=target, parents=parents, function=func)

    def evaluate(
        self,
        exogenous: Mapping[str, float],
        interventions: Optional[Mapping[str, float]] = None
    ) -> Dict[str, float]:
        """Executes deterministic forward evaluation under do(interventions)."""
        interventions = interventions or {}
        top_order = self.graph.topological_sort()
        state: Dict[str, float] = {}

        for node in top_order:
            if node in interventions:
                state[node] = float(interventions[node])
            else:
                u_val = exogenous.get(node, 0.0)
                if node in self.equations:
                    eq = self.equations[node]
                    parent_vals = {p: state[p] for p in eq.parents}
                    state[node] = float(eq.function(parent_vals, u_val))
                else:
                    # Base/root variable driven directly by exogenous noise
                    state[node] = float(u_val)
        return state


@dataclass(frozen=True)
class InvariantCandidate:
    """Hypothesized invariance property P(Y | PA(Y)) or invariant functional relation Y = h(S)."""
    target: str
    subsystem: FrozenSet[str]
    relation: Callable[[Mapping[str, float]], float]
    tolerance: float = 1e-6


@dataclass
class FalsificationResult:
    is_invariant: bool
    max_discrepancy: float
    falsifying_intervention: Optional[Dict[str, float]] = None
    details: str = ""


class CausalInvariantTester:
    """Tests and falsifies causal invariant relationships across interventional environments."""

    def __init__(self, scm: StructuralCausalModel) -> None:
        self.scm = scm

    def verify_invariant(
        self,
        candidate: InvariantCandidate,
        noise_scenarios: Sequence[Mapping[str, float]],
        interventions_pool: Sequence[Mapping[str, float]]
    ) -> FalsificationResult:
        """Tests if Y = relation(S) holds invariantly across all intervention regimes.

        An invariant condition requires that for all interventions do(I) where target not in I,
        the relation holds within tolerance across all exogenous noise scenarios.
        """
        max_err = 0.0

        for intervention in interventions_pool:
            # If target variable itself is intervened on, the structural assignment is severed
            if candidate.target in intervention:
                continue

            for u_scenario in noise_scenarios:
                sim_state = self.scm.evaluate(u_scenario, interventions=intervention)
                actual_target = sim_state[candidate.target]
                expected_target = candidate.relation({k: sim_state[k] for k in candidate.subsystem})
                err = abs(actual_target - expected_target)
                if err > max_err:
                    max_err = err
                if err > candidate.tolerance:
                    return FalsificationResult(
                        is_invariant=False,
                        max_discrepancy=err,
                        falsifying_intervention=dict(intervention),
                        details=f"Invariant violated for target {candidate.target} with discrepancy {err:.6e}"
                    )

        return FalsificationResult(
            is_invariant=True,
            max_discrepancy=max_err,
            falsifying_intervention=None,
            details="Invariant holds across all evaluated interventions."
        )

    def falsify_correlational_heuristic(
        self,
        target: str,
        correlated_non_parent: str,
        spurious_predictor: Callable[[float], float],
        noise_scenarios: Sequence[Mapping[str, float]],
        interventions: Sequence[Mapping[str, float]],
        tolerance: float = 1e-4
    ) -> FalsificationResult:
        """Demonstrates that an observational/correlational model fails (is falsified)
        when interventional perturbations are applied to the spurious covariate.
        """
        candidate = InvariantCandidate(
            target=target,
            subsystem=frozenset([correlated_non_parent]),
            relation=lambda vals: spurious_predictor(vals[correlated_non_parent]),
            tolerance=tolerance
        )
        return self.verify_invariant(candidate, noise_scenarios, interventions)
