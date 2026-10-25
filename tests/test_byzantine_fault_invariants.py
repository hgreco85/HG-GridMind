import unittest
from consensus.byzantine_simulator import (
    ByzantineNetworkSimulator,
    NodeBehavior,
)


class TestByzantineFaultInvariants(unittest.TestCase):
    """
    Deterministic falsification suite verifying safety and agreement invariants
    under adversarial Byzantine conditions (f < n/3 vs f >= n/3).
    """

    def test_agreement_invariant_under_tolerable_byzantine_faults(self):
        # n = 4, f = 1 (Honest >= 2f + 1 = 3)
        # Leader (Node 0) is malicious and equivocates
        node_configs = [
            (0, NodeBehavior.EQUIVOCATING),
            (1, NodeBehavior.HONEST),
            (2, NodeBehavior.HONEST),
            (3, NodeBehavior.HONEST),
        ]
        sim = ByzantineNetworkSimulator(node_configs)
        # Adversarial leader sends equivocated proposals
        proposals = sim.nodes[0].propose("TX_ROOT")
        sim.message_queue.extend(proposals)
        sim.run_until_quiescence()

        committed = sim.get_committed_values(honest_only=True)
        decided_values = {v for v in committed.values() if v is not None}
        # Safety invariant: Never commit conflicting values among honest nodes
        self.assertLessEqual(
            len(decided_values),
            1,
            f"Safety violated: Honest nodes committed conflicting values: {committed}"
        )

    def test_safety_preserved_under_silent_byzantine_nodes(self):
        # n = 4, f = 1. Byzantine node drops all outgoing messages
        node_configs = [
            (0, NodeBehavior.HONEST),
            (1, NodeBehavior.SILENT),
            (2, NodeBehavior.HONEST),
            (3, NodeBehavior.HONEST),
        ]
        sim = ByzantineNetworkSimulator(node_configs)
        proposals = sim.nodes[0].propose("BLOCK_HASH_42")
        sim.message_queue.extend(proposals)
        sim.run_until_quiescence()

        committed = sim.get_committed_values(honest_only=True)
        for nid in [0, 2, 3]:
            self.assertEqual(
                committed[nid],
                "BLOCK_HASH_42",
                f"Node {nid} failed to commit valid proposal despite f < n/3"
            )

    def test_falsification_invariant_exceeding_byzantine_threshold(self):
        # Counter-example demonstration: n = 4, f = 2 (exceeding f < n/3 tolerance bound)
        # Two adversarial nodes actively equivocate to split the quorum
        node_configs = [
            (0, NodeBehavior.EQUIVOCATING),
            (1, NodeBehavior.EQUIVOCATING),
            (2, NodeBehavior.HONEST),
            (3, NodeBehavior.HONEST),
        ]
        sim = ByzantineNetworkSimulator(node_configs)
        # In an overwhelmed network (honest count = 2 < quorum = 3),
        # honest nodes cannot reach a safe decision if adversaries act maliciously
        proposals_0 = sim.nodes[0].propose("VALUE_A")
        proposals_1 = sim.nodes[1].propose("VALUE_B")
        sim.message_queue.extend(proposals_0)
        sim.message_queue.extend(proposals_1)
        sim.run_until_quiescence()

        committed = sim.get_committed_values(honest_only=True)
        # Invariant check: Neither honest node should be misled into committing corrupted split state
        for nid in [2, 3]:
            self.assertIsNone(
                committed[nid],
                f"Falsification breached: Honest node {nid} committed under unquorate Byzantine threshold"
            )

    def test_deterministic_replay_consistency(self):
        # Verify simulation trajectory is strictly deterministic under identical initial seed/order
        def run_trial():
            configs = [
                (0, NodeBehavior.HONEST),
                (1, NodeBehavior.MALICIOUS_DATA),
                (2, NodeBehavior.HONEST),
                (3, NodeBehavior.HONEST),
            ]
            s = ByzantineNetworkSimulator(configs)
            s.message_queue.extend(s.nodes[0].propose("VALID_BLOCK"))
            steps = s.run_until_quiescence()
            return steps, s.get_committed_values(honest_only=True)

        steps1, committed1 = run_trial()
        steps2, committed2 = run_trial()
        self.assertEqual(steps1, steps2)
        self.assertEqual(committed1, committed2)


if __name__ == "__main__":
    unittest.main()
