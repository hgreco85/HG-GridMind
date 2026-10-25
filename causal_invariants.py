from typing import Dict, List, Set, Any, Optional


class CausalModel:
    """Represents a deterministic causal DAG and structural equations."""

    def __init__(self, adjacency: Optional[Dict[str, List[str]]] = None):
        self.adjacency: Dict[str, List[str]] = adjacency or {}
        self.nodes: Set[str] = set(self.adjacency.keys())
        for targets in self.adjacency.values():
            self.nodes.update(targets)

    def is_ancestor(self, u: str, v: str) -> bool:
        """Returns True if u is an ancestor of v (i.e. directed path u -> ... -> v)."""
        if u == v:
            return True
        visited = set()
        queue = [u]
        while queue:
            curr = queue.pop(0)
            if curr == v:
                return True
            if curr not in visited:
                visited.add(curr)
                queue.extend(self.adjacency.get(curr, []))
        return False

    def get_ancestors(self, target: str) -> Set[str]:
        """Get all ancestors of target including itself."""
        ancestors = set()
        for node in self.nodes:
            if self.is_ancestor(node, target):
                ancestors.add(node)
        return ancestors


class CausalSimulator:
    """Deterministic structural equation simulation and falsification checker."""

    def __init__(self, causal_model: CausalModel):
        self.model = causal_model

    def simulate(self, system_state: Dict[str, Any], interventions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes deterministic evaluation over DAG: 
        Z = X + 2*Y
        W = Z * 3
        Interventions override the endogenous equations.
        """
        state = dict(system_state)
        interventions = interventions or {}

        # Apply intervention values
        for var, val in interventions.items():
            state[var] = val

        # Deterministic structural equation evaluations
        if "Z" not in interventions:
            state["Z"] = state.get("X", 0) + 2 * state.get("Y", 0)
        if "W" not in interventions:
            state["W"] = state.get("Z", 0) * 3

        return state

    def check_non_ancestral_invariance(
        self,
        baseline_state: Dict[str, Any],
        target_node: str,
        intervened_node: str,
        intervention_val: Any
    ) -> bool:
        """
        Causal Invariant: If intervened_node is NOT an ancestor of target_node,
        intervening on intervened_node must leave target_node invariant.
        Returns True if invariant holds, False if violated/falsified.
        """
        if self.model.is_ancestor(intervened_node, target_node):
            raise ValueError(f"{intervened_node} is an ancestor of {target_node}; invariance not guaranteed.")

        base_res = self.simulate(baseline_state)
        intervened_res = self.simulate(baseline_state, interventions={intervened_node: intervention_val})

        return base_res.get(target_node) == intervened_res.get(target_node)

    def falsify_hypothesized_cause(
        self,
        baseline_state: Dict[str, Any],
        target_node: str,
        hypothesized_cause: str,
        test_values: List[Any]
    ) -> bool:
        """
        Deterministic falsification test:
        If hypothesized_cause truly causally influences target_node,
        there should exist at least one intervention that changes target_node's value.
        If no change is observed across all perturbations, the causal claim is falsified.
        Returns True if falsified (claim rejected), False if effect confirmed.
        """
        base_res = self.simulate(baseline_state)
        target_base_val = base_res.get(target_node)

        changed = False
        for val in test_values:
            res = self.simulate(baseline_state, interventions={hypothesized_cause: val})
            if res.get(target_node) != target_base_val:
                changed = True
                break

        # Falsified if no intervention caused a difference
        return not changed
