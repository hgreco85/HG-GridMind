import enum
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass


class MessageType(enum.Enum):
    PROPOSE = "PROPOSE"
    PREPARE = "PREPARE"
    COMMIT = "COMMIT"


class NodeBehavior(enum.Enum):
    HONEST = "HONEST"
    SILENT = "SILENT"
    EQUIVOCATING = "EQUIVOCATING"
    MALICIOUS_DATA = "MALICIOUS_DATA"


@dataclass(frozen=True)
class VoteMessage:
    msg_type: MessageType
    view: int
    sender_id: int
    target_id: int
    value: str


class Node:
    def __init__(self, node_id: int, total_nodes: int, behavior: NodeBehavior = NodeBehavior.HONEST):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.f = (total_nodes - 1) // 3
        self.quorum = 2 * self.f + 1
        self.behavior = behavior
        self.view = 0
        self.prepared_value: Optional[str] = None
        self.committed_value: Optional[str] = None
        self.prepare_votes: Dict[Tuple[int, str], Set[int]] = {}
        self.commit_votes: Dict[Tuple[int, str], Set[int]] = {}

    def propose(self, value: str) -> List[VoteMessage]:
        messages: List[VoteMessage] = []
        if self.behavior == NodeBehavior.SILENT:
            return messages
        elif self.behavior == NodeBehavior.EQUIVOCATING:
            for peer_id in range(self.total_nodes):
                val = f"{value}_split_{peer_id % 2}"
                messages.append(VoteMessage(MessageType.PROPOSE, self.view, self.node_id, peer_id, val))
        elif self.behavior == NodeBehavior.MALICIOUS_DATA:
            for peer_id in range(self.total_nodes):
                messages.append(VoteMessage(MessageType.PROPOSE, self.view, self.node_id, peer_id, "CORRUPT"))
        else:
            for peer_id in range(self.total_nodes):
                messages.append(VoteMessage(MessageType.PROPOSE, self.view, self.node_id, peer_id, value))
        return messages

    def handle_propose(self, msg: VoteMessage) -> List[VoteMessage]:
        if msg.view != self.view or self.prepared_value is not None:
            return []
        messages: List[VoteMessage] = []
        if self.behavior == NodeBehavior.SILENT:
            return []
        elif self.behavior == NodeBehavior.EQUIVOCATING:
            for peer_id in range(self.total_nodes):
                val = f"{msg.value}_equiv_{peer_id % 2}"
                messages.append(VoteMessage(MessageType.PREPARE, self.view, self.node_id, peer_id, val))
        else:
            for peer_id in range(self.total_nodes):
                messages.append(VoteMessage(MessageType.PREPARE, self.view, self.node_id, peer_id, msg.value))
        return messages

    def handle_prepare(self, msg: VoteMessage) -> List[VoteMessage]:
        if msg.view != self.view:
            return []
        key = (msg.view, msg.value)
        if key not in self.prepare_votes:
            self.prepare_votes[key] = set()
        self.prepare_votes[key].add(msg.sender_id)

        if self.prepared_value is None and len(self.prepare_votes[key]) >= self.quorum:
            self.prepared_value = msg.value
            if self.behavior == NodeBehavior.SILENT:
                return []
            messages: List[VoteMessage] = []
            for peer_id in range(self.total_nodes):
                messages.append(VoteMessage(MessageType.COMMIT, self.view, self.node_id, peer_id, msg.value))
            return messages
        return []

    def handle_commit(self, msg: VoteMessage) -> None:
        if msg.view != self.view:
            return
        key = (msg.view, msg.value)
        if key not in self.commit_votes:
            self.commit_votes[key] = set()
        self.commit_votes[key].add(msg.sender_id)

        if self.committed_value is None and len(self.commit_votes[key]) >= self.quorum:
            self.committed_value = msg.value


class ByzantineNetworkSimulator:
    def __init__(self, node_configs: List[Tuple[int, NodeBehavior]]):
        self.total_nodes = len(node_configs)
        self.nodes = {nid: Node(nid, self.total_nodes, b) for nid, b in node_configs}
        self.message_queue: List[VoteMessage] = []

    def step(self) -> bool:
        if not self.message_queue:
            return False
        msg = self.message_queue.pop(0)
        target = self.nodes.get(msg.target_id)
        if target is None:
            return bool(self.message_queue)

        new_msgs: List[VoteMessage] = []
        if msg.msg_type == MessageType.PROPOSE:
            new_msgs = target.handle_propose(msg)
        elif msg.msg_type == MessageType.PREPARE:
            new_msgs = target.handle_prepare(msg)
        elif msg.msg_type == MessageType.COMMIT:
            target.handle_commit(msg)

        self.message_queue.extend(new_msgs)
        return True

    def run_until_quiescence(self, max_steps: int = 10000) -> int:
        steps = 0
        while steps < max_steps and self.step():
            steps += 1
        return steps

    def get_committed_values(self, honest_only: bool = True) -> Dict[int, Optional[str]]:
        result = {}
        for nid, node in self.nodes.items():
            if honest_only and node.behavior != NodeBehavior.HONEST:
                continue
            result[nid] = node.committed_value
        return result
