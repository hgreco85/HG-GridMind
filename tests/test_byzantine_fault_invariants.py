import unittest
from consensus.byzantine import ByzantineConsensusNetwork, Message, sign_message


class TestByzantineFaultInvariants(unittest.TestCase):
    """
    Deterministic falsification tests verifying consensus invariants under Byzantine faults:
    - Invariant 1: Agreement (All non-faulty nodes decide on the identical value).
    - Invariant 2: Validity (If all honest nodes propose V, any decision reached must be V).
    - Invariant 3: Falsification Boundary (When f > (N-1)//3, consensus guarantees break deterministically).
    """

    def test_agreement_under_equivocation_within_bound(self):
        """
        Test Byzantine Agreement with N=4, f=1 (f <= (4-1)//3 = 1) under equivocation strategy.
        Invariant: All honest nodes must reach the exact same decision.
        """
        total_nodes = 4
        byzantine_nodes = 1
        net = ByzantineConsensusNetwork(total_nodes=total_nodes, byzantine_count=byzantine_nodes, strategy="equivocate")
        
        # Honest nodes propose True
        for node in net.nodes:
            node.propose(True)

        net.run_round(round_num=1)

        honest_decisions = net.get_honest_decisions()
        self.assertEqual(len(honest_decisions), 3)
        # Check unanimous agreement
        self.assertTrue(all(d == honest_decisions[0] for d in honest_decisions))
        # Ensure decision was actually reached (not None) and equals the valid proposal
        self.assertEqual(honest_decisions[0], True)

    def test_validity_under_silent_and_corrupt_nodes(self):
        """
        Test Validity Invariant with N=7, f=2 (tolerable limit: (7-1)//3 = 2).
        Byzantine nodes either stay silent or forge invalid signatures.
        Invariant: Honest nodes must never decide on a Byzantine/invalid value.
        """
        total_nodes = 7
        byzantine_nodes = 2
        net = ByzantineConsensusNetwork(total_nodes=total_nodes, byzantine_count=byzantine_nodes, strategy="corrupt_signature")

        for i, node in enumerate(net.nodes):
            if not node.is_byzantine:
                node.propose("BLOCK_HASH_A")
            else:
                node.propose("MALICIOUS_BLOCK_B")

        net.run_round(round_num=1)

        honest_decisions = net.get_honest_decisions()
        self.assertEqual(len(honest_decisions), 5)
        for decision in honest_decisions:
            self.assertEqual(decision, "BLOCK_HASH_A", "Honest node must decide on valid honest proposal")

    def test_falsification_when_byzantine_nodes_exceed_theoretical_bound(self):
        """
        Deterministic falsification test: Falsify consensus guarantees when f > (N-1)//3.
        For N=4, max tolerable f=1. Setting f=2 exceeds tolerance.
        With f=2 sending conflicting/flipped votes, honest nodes fail to reach quorum consensus.
        """
        total_nodes = 4
        byzantine_nodes = 2  # Exceeds max tolerance 1
        net = ByzantineConsensusNetwork(total_nodes=total_nodes, byzantine_count=byzantine_nodes, strategy="flip")

        # Honest nodes propose True
        for node in net.nodes:
            node.propose(True)

        net.run_round(round_num=1)

        honest_decisions = net.get_honest_decisions()
        # Since quorum is 2*1 + 1 = 3, but honest nodes are only 2 and Byzantine nodes flipped,
        # honest nodes cannot reach the quorum threshold of 3, falsifying liveness/decision invariant.
        for dec in honest_decisions:
            self.assertIsNone(dec, "Consensus invariant must be falsified when Byzantine faults exceed theoretical limit")

    def test_cryptographic_verification_drops_forged_messages(self):
        """
        Verify that cryptographically tampered or forged messages are deterministically
        rejected before state transitions.
        """
        valid_sig = sign_message(sender_id=1, round_num=1, value="DATA")
        valid_msg = Message(sender_id=1, round_num=1, value="DATA", signature=valid_sig)
        invalid_msg = Message(sender_id=1, round_num=1, value="DATA", signature="TAMPERED")

        self.assertTrue(valid_msg.is_valid())
        self.assertFalse(invalid_msg.is_valid())


if __name__ == '__main__':
    unittest.main()
