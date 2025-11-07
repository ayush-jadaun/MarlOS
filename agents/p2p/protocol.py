"""
Message Protocol Definitions
Defines all message types and schemas for P2P communication
"""
import time
import uuid
from typing import Dict, Any, Literal
from dataclasses import dataclass, asdict
from enum import Enum


class MessageType(str, Enum):
    """Message types"""
    # Discovery
    PEER_ANNOUNCE = "peer_announce"
    PEER_GOODBYE = "peer_goodbye"

    # Jobs
    JOB_BROADCAST = "job_broadcast"
    JOB_BID = "job_bid"
    JOB_CLAIM = "job_claim"
    JOB_FORWARD = "job_forward"
    JOB_RESULT = "job_result"
    JOB_HEARTBEAT = "job_heartbeat"
    AUCTION_COORDINATE = "auction_coordinate"  # Coordinator announcement

    # Reputation
    REPUTATION_UPDATE = "reputation_update"
    REPUTATION_QUERY = "reputation_query"
    REPUTATION_RESPONSE = "reputation_response"

    # Tokens
    TOKEN_TRANSACTION = "token_transaction"

    # System
    PING = "ping"
    PONG = "pong"
    ACK = "ack"


@dataclass
class BaseMessage:
    """Base message structure"""
    type: str = None
    node_id: str = None
    timestamp: float = None
    message_id: str = None
    signature: str = None
    public_key: str = None

    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PeerAnnounceMessage(BaseMessage):
    """Peer discovery announcement"""
    node_name: str = None
    ip: str = None
    port: int = None
    capabilities: list = None
    trust_score: float = 0.5
    token_balance: float = 0.0

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.PEER_ANNOUNCE


@dataclass
class JobBroadcastMessage(BaseMessage):
    """Job submission broadcast"""
    job_id: str = None
    job_type: str = None
    priority: float = 0.5
    payment: float = 100.0
    deadline: float = None
    requirements: list = None
    payload: dict = None
    verify: bool = False
    verifiers: int = 1

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.JOB_BROADCAST
        if self.job_id is None:
            self.job_id = f"job-{str(uuid.uuid4())[:8]}"
        if self.deadline is None:
            self.deadline = time.time() + 300  # 5 minutes default


@dataclass
class JobBidMessage(BaseMessage):
    """Node bidding on a job"""
    job_id: str = None
    bid_score: float = 0.0
    estimated_time: float = 0.0
    stake_amount: float = 10.0

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.JOB_BID


@dataclass
class JobClaimMessage(BaseMessage):
    """Job claim by winner"""
    job_id: str = None
    winner_node_id: str = None
    backup_node_id: str = None
    stake_amount: float = 10.0
    winning_score: float = 1.0

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.JOB_CLAIM


@dataclass
class JobResultMessage(BaseMessage):
    """Job execution result"""
    job_id: str = None
    status: Literal["success", "failure", "timeout"] = "success"
    duration: float = 0.0
    output: dict = None
    error: str = None

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.JOB_RESULT


@dataclass
class JobHeartbeatMessage(BaseMessage):
    """Job execution heartbeat"""
    job_id: str = None
    progress: float = 0.0  # 0.0 to 1.0

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.JOB_HEARTBEAT


@dataclass
class ReputationUpdateMessage(BaseMessage):
    """Reputation score update"""
    subject_node_id: str = None
    new_score: float = 0.5
    reason: str = None
    event: str = None  # job_success, job_failure, malicious, etc.

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.REPUTATION_UPDATE


@dataclass
class TokenTransactionMessage(BaseMessage):
    """Token transaction"""
    from_node: str = None
    to_node: str = None
    amount: float = 0.0
    reason: str = None
    job_id: str = None

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.TOKEN_TRANSACTION


@dataclass
class PingMessage(BaseMessage):
    """Ping health check"""
    ping_id: str = None

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.PING


@dataclass
class PongMessage(BaseMessage):
    """Pong response"""
    ping_id: str = None

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.PONG


@dataclass
class AckMessage(BaseMessage):
    """Acknowledgment for reliable delivery"""
    ack_message_id: str = None  # ID of message being acknowledged

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.ACK


@dataclass
class AuctionCoordinateMessage(BaseMessage):
    """Coordinator announcement for auction"""
    job_id: str = None
    coordinator_id: str = None
    bid_deadline: float = None

    def __post_init__(self):
        super().__post_init__()
        self.type = MessageType.AUCTION_COORDINATE


def create_message(message_type: MessageType, **kwargs) -> BaseMessage:
    """Factory function to create messages"""
    message_classes = {
        MessageType.PEER_ANNOUNCE: PeerAnnounceMessage,
        MessageType.JOB_BROADCAST: JobBroadcastMessage,
        MessageType.JOB_BID: JobBidMessage,
        MessageType.JOB_CLAIM: JobClaimMessage,
        MessageType.JOB_RESULT: JobResultMessage,
        MessageType.JOB_HEARTBEAT: JobHeartbeatMessage,
        MessageType.AUCTION_COORDINATE: AuctionCoordinateMessage,
        MessageType.REPUTATION_UPDATE: ReputationUpdateMessage,
        MessageType.TOKEN_TRANSACTION: TokenTransactionMessage,
        MessageType.PING: PingMessage,
        MessageType.PONG: PongMessage,
        MessageType.ACK: AckMessage,
    }

    message_class = message_classes.get(message_type, BaseMessage)
    return message_class(**kwargs)
