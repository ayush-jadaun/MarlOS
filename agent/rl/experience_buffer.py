"""
Experience Replay Buffer
Stores agent experiences for online learning
"""
import numpy as np
from collections import deque
from typing import List, Tuple
import pickle
from pathlib import Path


class Experience:
    """Single experience tuple (s, a, r, s', done)"""
    def __init__(self, state, action, reward, next_state, done):
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done
    
    def to_tuple(self):
        return (self.state, self.action, self.reward, self.next_state, self.done)


class ExperienceBuffer:
    """
    Circular buffer for storing experiences
    Implements experience replay for online learning
    """
    
    def __init__(self, capacity: int = 10000, data_dir: str = "./data"):
        self.capacity = capacity
        self.buffer = deque(maxlen=capacity)
        self.data_dir = Path(data_dir)
        self.buffer_file = self.data_dir / "experience_buffer.pkl"
        
        # Load existing buffer if exists
        self._load_buffer()
    
    def add(self, state: np.ndarray, action: int, reward: float, 
            next_state: np.ndarray, done: bool):
        """Add experience to buffer"""
        exp = Experience(state, action, reward, next_state, done)
        self.buffer.append(exp)
        
        # Periodically save to disk
        if len(self.buffer) % 100 == 0:
            self._save_buffer()
    
    def sample(self, batch_size: int) -> List[Experience]:
        """Sample random batch from buffer"""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]
    
    def get_recent(self, n: int) -> List[Experience]:
        """Get n most recent experiences"""
        return list(self.buffer)[-n:]
    
    def get_all(self) -> List[Experience]:
        """Get all experiences"""
        return list(self.buffer)
    
    def clear(self):
        """Clear buffer"""
        self.buffer.clear()
        self._save_buffer()
    
    def size(self) -> int:
        """Get buffer size"""
        return len(self.buffer)
    
    def _save_buffer(self):
        """Save buffer to disk"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.buffer_file, 'wb') as f:
            pickle.dump(list(self.buffer), f)
    
    def _load_buffer(self):
        """Load buffer from disk"""
        if self.buffer_file.exists():
            try:
                with open(self.buffer_file, 'rb') as f:
                    experiences = pickle.load(f)
                    self.buffer.extend(experiences)
                
                print(f"[RL BUFFER] Loaded {len(self.buffer)} experiences from disk")
            except Exception as e:
                print(f"[RL BUFFER] Error loading buffer: {e}")
    
    def get_statistics(self) -> dict:
        """Get buffer statistics"""
        if len(self.buffer) == 0:
            return {
                'size': 0,
                'avg_reward': 0.0,
                'success_rate': 0.0
            }
        
        rewards = [exp.reward for exp in self.buffer]
        successes = sum(1 for exp in self.buffer if exp.reward > 0)
        
        return {
            'size': len(self.buffer),
            'capacity': self.capacity,
            'utilization': len(self.buffer) / self.capacity,
            'avg_reward': np.mean(rewards),
            'max_reward': np.max(rewards),
            'min_reward': np.min(rewards),
            'success_rate': successes / len(self.buffer)
        }