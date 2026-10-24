"""Unit tests for deterministic causal invariant verification and falsification."""

import unittest
from causal_invariants import (
    CausalGraph,
    StructuralCausalModel,
    CausalInvariantTester,
    InvariantCandidate,
)


class TestCausalInvariants(unittest.TestCase):
    def setUp(self) -> None:
        """Setup standard confounding and chain DAGs for causal invariant testing.

        Confounder model:
            Z -> X
            Z -> Y
            X -> Y
        Structural equations:
            X := 2.0 * Z + U_X
            Y := 3.0 * X - 1.5 * Z + U_Y
        """
        self.graph = CausalGraph()
        self.graph.add_edge("Z", "X")
        self.graph.add_edge("Z", "Y")
        self.graph.add_edge("X", "Y")

        self.scm = StructuralCausalModel(self.graph)
        self.scm.set_equation("X", ["Z"], lambda p, u: 2.0 * p["Z"] + u)
        self.scm.set_equation("Y", ["X", "Z"], lambda p, u: 3.0 * p["X"] - 1.5 * p["Z"] + u)

        self.tester = CausalInvariantTester(self.scm)
        self.noise_scenarios = [
            {"Z": 1.0, "X": 0.5, "Y": 0.2},
            {"Z": -2.0, "X": -0.1, "Y": 0.8},
            {"Z": 0.0, "X": 1.2, "Y": -0.5},
            {"Z": 3.5, "X": -1.0, "Y": 2.0},
        ]

    def test_causal_graph_topology_and_cycles(self) -> None:
        """Verify DAG invariant: acyclicity enforcement and topological ordering."""
        g = CausalGraph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "D")

        order = g.topological_sort()
        self.assertEqual(order, ["A", "B", "C", "D"])
        self.assertTrue(g.is_acyclic())
        self.assertEqual(g.get_ancestors("D"), {"A", "B", "C"})

        with self.assertRaises(ValueError):
            g.add_edge("D", "A")  # Introduce cycle

    def test_true_causal_mechanism_invariant_holds_under_interventions(self) -> None:
        """True causal parent mechanism Y := f(X, Z) + U_Y remains invariant
        under interventions on antecedent nodes do(X=k) and do(Z=m).
        """
        # The mechanism Y := 3*X - 1.5*Z + U_Y must hold when U_Y is known or tested per noise state
        candidate = InvariantCandidate(
            target="Y",
            subsystem=frozenset(["X", "Z"]),
            relation=lambda p: 3.0 * p["X"] - 1.5 * p["Z"],
            tolerance=1e-6
        )

        interventions = [
            {},  # Observational
            {"X": 10.0},
            {"X": -5.0},
            {"Z": 4.0},
            {"Z": -2.5, "X": 1.0},
        ]

        # Set U_Y = 0 to test pure invariant mechanism
        deterministic_noise = [{"Z": 1.0, "X": 0.5, "Y": 0.0}, {"Z": -3.0, "X": 2.0, "Y": 0.0}]
        res = self.tester.verify_invariant(candidate, deterministic_noise, interventions)
        self.assertTrue(res.is_invariant)
        self.assertAlmostEqual(res.max_discrepancy, 0.0, places=6)
        self.assertIsNone(res.falsifying_intervention)

    def test_spurious_correlational_relation_is_falsified(self) -> None:
        """Under purely observational data with U_X = 0, U_Y = 0:
            X = 2 * Z  => Z = 0.5 * X
            Y = 3 * X - 1.5 * (0.5 * X) = 2.25 * X
        A non-causal predictor Y = 2.25 * X fits observational data perfectly,
        but MUST be falsified under intervention do(X = k) or do(Z = k).
        """
        clean_noise = [{"Z": 2.0, "X": 0.0, "Y": 0.0}, {"Z": -1.0, "X": 0.0, "Y": 0.0}]
        spurious_candidate = InvariantCandidate(
            target="Y",
            subsystem=frozenset(["X"]),
            relation=lambda p: 2.25 * p["X"],
            tolerance=1e-5
        )

        # In pure observational state, the spurious invariant holds
        obs_res = self.tester.verify_invariant(spurious_candidate, clean_noise, [{}])
        self.assertTrue(obs_res.is_invariant, "Spurious relation holds under observational regime")

        # Under intervention do(X=10), Z remains unchanged, breaking the correlation
        # For Z=2: actual Y = 3*(10) - 1.5*(2) = 27; spurious Y = 2.25 * 10 = 22.5 (error = 4.5)
        interventions = [{"X": 10.0}]
        falsify_res = self.tester.verify_invariant(spurious_candidate, clean_noise, interventions)
        self.assertFalse(falsify_res.is_invariant, "Intervention must falsify spurious correlation")
        self.assertGreater(falsify_res.max_discrepancy, 1.0)
        self.assertEqual(falsify_res.falsifying_intervention, {"X": 10.0})

    def test_falsify_correlational_heuristic_helper(self) -> None:
        """Ensure the tester falsification helper correctly flags spurious invariants."""
        clean_noise = [{"Z": 4.0, "X": 0.0, "Y": 0.0}]
        res = self.tester.falsify_correlational_heuristic(
            target="Y",
            correlated_non_parent="X",
            spurious_predictor=lambda x: 2.25 * x,
            noise_scenarios=clean_noise,
            interventions=[{"X": -5.0}],
            tolerance=1e-3
        )
        self.assertFalse(res.is_invariant)
        self.assertIsNotNone(res.falsifying_intervention)


if __name__ == "__main__":
    unittest.main()
