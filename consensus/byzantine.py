from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import hashlib


@dataclass
class Message:
    sender_id: int
    round_num: int
    value: Any
    signature: str

    def is_valid(self) -> bool:
        # Deterministic verification based on hash
        expected = hashlib.sha256(f"{self.sender_id}:{self.round_num}:{self.value}".encode()).hexdigest()[:8]
        return self.signature == expected


def sign_message(sender_id: int, round_num: int, value: Any) -> str:
    return hashlib.sha256(f"{sender_id}:{round_num}:{value}".encode()).hexdigest()[:8]


class Node:
    def __init__(self, node_id: int, total_nodes: int, is_byzantine: bool = False, byzantine_strategy: Optional[str] = None):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.is_byzantine = is_byzantine
        self.byzantine_strategy = byzantine_strategy
        self.current_round = 0
        self.decided_value: Optional[Any] = None
        self.received_messages: Dict[int, List[Message]] = {}
        self.initial_value: Optional[Any] = None

    def propose(self, value: Any) -> None:
        self.initial_value = value

    def broadcast(self, round_num: int, target_node_id: Optional[int] = None) -> List[Message]:
        # Honest nodes send their proposal/message to all nodes
        if not self.is_byzantine:
            val = self.decided_value if self.decided_value is not None else self.initial_value
            sig = sign_message(self.node_id, round_num, val)
            return [Message(sender_id=self.node_id, round_num=round_num, value=val, signature=sig)]

        # Byzantine behaviors
        if self.byzantine_strategy == "silent":
            # Drop messages completely
            return []
        elif self.byzantine_strategy == "equivocate":
            # Send conflicting values depending on recipient target
            val = f"equivocate_val_{target_node_id}"
            sig = sign_message(self.node_id, round_num, val)
            return [Message(sender_id=self.node_id, round_num=round_num, value=val, signature=sig)]
        elif self.byzantine_strategy == "corrupt_signature":
            # Send invalid signature
            return [Message(sender_id=self.node_id, round_num=round_num, value=self.initial_value, signature="INVALID_SIG")]
        elif self.byzantine_strategy == "flip":
            # Deliberately invert or flip binary value
            val = not self.initial_value if isinstance(self.initial_value, bool) else -1
            sig = sign_message(self.node_id, round_num, val)
            return [Message(sender_id=self.node_id, round_num=round_num, value=val, signature=sig)]
        
        # Fallback
        val = self.initial_value
        sig = sign_message(self.node_id, round_num, val)
        return [Message(sender_id=self.node_id, round_num=round_num, value=val, signature=sig)]

    def receive(self, msg: Message) -> None:
        if not msg.is_valid():
            return  # Drop cryptographically invalid messages
        if msg.round_num not in self.received_messages:
            self.received_messages[msg.round_num] = []
        self.received_messages[msg.round_num].append(msg)

    def step(self, round_num: int, threshold_quorum: int) -> None:
        self.current_round = round_num
        msgs = self.received_messages.get(round_num, [])
        
        # Tally valid proposals per value
        counts: Dict[Any, int] = {}
        unique_senders: Set[int] = set()
        for msg in msgs:
            if msg.sender_id not in unique_senders:
                unique_senders.add(msg.sender_id)
                counts[msg.value] = counts.get(msg.value, 0) + 1
        
        # Quorum rule: if any value gets >= threshold_quorum, decide on it
        for val, cnt in counts.items():
            if cnt >= threshold_quorum:
                self.decided_value = val
                break


class ByzantineConsensusNetwork:
    """
    A deterministic simulator for Byzantine consensus.
    Tolerates up to f Byzantine faults in N nodes where N >= 3f + 1.
    Quorum requirement for safety is 2f + 1.
    """
    def __init__(self, total_nodes: int, byzantine_count: int, strategy: str = "silent"):
        self.total_nodes = total_nodes
        self.byzantine_count = byzantine_count
        self.strategy = strategy
        self.max_tolerated_faults = (total_nodes - 1) // 3
        self.quorum_threshold = 2 * self.max_tolerated_faults + 1

        self.nodes: List[Node] = []
        for i in range(total_nodes):
            is_byz = i < byzantine_count
            strat = strategy if is_byz else None
            self.nodes.append(Node(node_id=i, total_nodes=total_nodes, is_byzantine=is_byz, byzantine_strategy=strat))

    def run_round(self, round_num: int) -> None:
        # Deliver messages to each peer deterministically
        for src in self.nodes:
            for dst in self.nodes:
                msgs = src.broadcast(round_num=round_num, target_node_id=dst.node_id)
                for m in msgs:
                    dst.receive(m)

        for node in self.nodes:
            node.step(round_num, self.quorum_threshold)

    def get_honest_decisions(self) -> List[Any]:
        return [node.decided_value for node in self.nodes if not node.is_byzantine]
