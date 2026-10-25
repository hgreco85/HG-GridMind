import unittest
from causal_invariants import CausalModel, CausalSimulator


class TestCausalInvariants(unittest.TestCase):

    def setUp(self):
        # Standard DAG: X -> Z, Y -> Z, Z -> W
        # Non-ancestor relationship: W does not cause X, Y, or Z
        self.adj = {
            "X": ["Z"],
            "Y": ["Z"],
            "Z": ["W"],
            "W": []
        }
        self.model = CausalModel(self.adj)
        self.sim = CausalSimulator(self.model)
        self.base_state = {"X": 10, "Y": 5}

    def test_deterministic_simulation(self):
        res = self.sim.simulate(self.base_state)
        # Z = 10 + 2*5 = 20
        # W = 20 * 3 = 60
        self.assertEqual(res["Z"], 20)
        self.assertEqual(res["W"], 60)

    def test_non_ancestral_invariance(self):
        # Intervening on W should NOT change Z, X, or Y since W is a downstream descendant
        holds_for_z = self.sim.check_non_ancestral_invariance(
            baseline_state=self.base_state,
            target_node="Z",
            intervened_node="W",
            intervention_val=999
        )
        self.assertTrue(holds_for_z)

        holds_for_x = self.sim.check_non_ancestral_invariance(
            baseline_state=self.base_state,
            target_node="X",
            intervened_node="W",
            intervention_val=999
        )
        self.assertTrue(holds_for_x)

    def test_ancestor_error_on_invariance_check(self):
        # Attempting non-ancestral check on an actual ancestor should raise ValueError
        with self.assertRaises(ValueError):
            self.sim.check_non_ancestral_invariance(
                baseline_state=self.base_state,
                target_node="W",
                intervened_node="X",
                intervention_val=50
            )

    def test_falsification_of_unrelated_cause(self):
        # Claim: W causes X. Falsification should return True (claim falsified)
        is_falsified = self.sim.falsify_hypothesized_cause(
            baseline_state=self.base_state,
            target_node="X",
            hypothesized_cause="W",
            test_values=[0, 100, -50]
        )
        self.assertTrue(is_falsified)

    def test_falsification_of_true_cause_rejected(self):
        # Claim: X causes W. True causal link, so falsification test should return False (not falsified)
        is_falsified = self.sim.falsify_hypothesized_cause(
            baseline_state=self.base_state,
            target_node="W",
            hypothesized_cause="X",
            test_values=[20, 30]
        )
        self.assertFalse(is_falsified)


if __name__ == "__main__":
    unittest.main()
