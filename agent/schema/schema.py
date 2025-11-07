import time
import math
from typing import Dict, List, Tuple, Optional
from collections import deque, defaultdict
from dataclasses import dataclass


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
