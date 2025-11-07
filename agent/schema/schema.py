import time
import math
from typing import Dict, List, Tuple, Optional
from collections import deque, defaultdict
from dataclasses import dataclass,asdict
from enum import Enum

@dataclass
class ReputationEvent:
    """Reputation event record"""
    timestamp: float
    event_type: str  # success, failure, timeout, malicious
    trust_delta: float
    trust_after: float
    reason: str
    job_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JobDistributionStats:
    """Track job distribution across nodes"""
    node_id: str
    jobs_won: int
    jobs_lost: int
    total_earnings: float
    last_win_time: float
    win_rate: float


@dataclass
class Bid:
    """Bid information"""
    job_id: str
    node_id: str
    score: float
    stake_amount: float
    estimated_time: float
    timestamp: float



@dataclass
class JobBackup:
    """Backup job information"""
    job_id: str
    job: dict
    primary_node: str
    backup_node: str
    last_heartbeat: float
    progress: float


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Job execution result"""
    job_id: str
    status: JobStatus
    output: dict
    error: Optional[str]
    start_time: float
    end_time: float
    duration: float
    
    def to_dict(self) -> dict:
        return {
            'job_id': self.job_id,
            'status': self.status,
            'output': self.output,
            'error': self.error,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration
        }




@dataclass
class LedgerEntry:
    """Single ledger entry"""
    entry_id: str
    timestamp: float
    from_node: Optional[str]
    to_node: Optional[str]
    amount: float
    tx_type: str  # DEPOSIT, WITHDRAW, STAKE, UNSTAKE, SLASH, TRANSFER
    reason: str
    job_id: Optional[str]
    balance_after: float
    signature: str  # Cryptographic proof
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Transaction:
    """Token transaction record"""
    tx_id: str
    timestamp: float
    tx_type: str  # DEPOSIT, WITHDRAW, STAKE, UNSTAKE, SLASH
    amount: float
    balance_after: float
    reason: str
    job_id: Optional[str] = None
    from_node: Optional[str] = None
    to_node: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
