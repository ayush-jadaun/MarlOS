"""
RL Policy - Decision Engine
Uses trained PPO model to make bidding decisions
"""
import numpy as np
import os
from typing import Tuple, Optional
from enum import IntEnum

from ..config import RLConfig
from .state import StateCalculator
from .reward import RewardCalculator


class Action(IntEnum):
    """RL Actions"""
    BID = 0      # Compete for this job
    FORWARD = 1  # Forward to better peer
    DEFER = 2    # Skip this job


class RLPolicy:
    """
    RL-based decision policy using Stable-Baselines3 PPO
    """
    
    def __init__(self, node_id: str, config: RLConfig, enable_fairness: bool = True):
        self.node_id = node_id
        self.config = config


        self.state_calc = StateCalculator(node_id, enable_fairness=enable_fairness)
        self.reward_calc = RewardCalculator()

        # Load trained model
        self.model = None
        self._load_model()

        # Exploration
        self.exploration_rate = config.exploration_rate
        self.episode_experiences = []  # Store experiences

        # Episode tracking (for online learning)
        self.current_episode = []
        self.episode_count = 0

        # Online learner (will be set by main agent)
        self.online_learner = None

        # Current state/action for learning
        self.current_state = None
        self.current_action = None
    
    def _load_model(self):
        """Load trained PPO model"""
        try:
            if os.path.exists(self.config.model_path):
                from stable_baselines3 import PPO
                self.model = PPO.load(self.config.model_path)
                print(f"[RL] Loaded model from {self.config.model_path}")
            else:
                print(f"[RL] No trained model found at {self.config.model_path}")
                print("[RL] Will use random policy")
        except Exception as e:
            print(f"[RL] Error loading model: {e}")
            print("[RL] Will use random policy")
    
    def decide(self, job: dict, wallet_balance: float, trust_score: float,
              peer_count: int, active_jobs: int, deterministic: bool = False) -> Tuple[Action, float]:
        """
        Decide action for a job - WITH LEARNING
        """
        # Calculate state
        state = self.state_calc.calculate_state(
            job=job,
            wallet_balance=wallet_balance,
            trust_score=trust_score,
            peer_count=peer_count,
            active_jobs=active_jobs
        )
        
        # Store state for learning
        self.current_state = state.copy() 
        
        # Exploration vs exploitation
        if not deterministic and np.random.random() < self.exploration_rate:
            # Explore: random action
            action = Action(np.random.randint(0, 3))
            confidence = 0.33
            print(f"[RL] 🎲 Exploring: {action.name}")
        else:
            # Exploit: use model
            if self.model is not None and self.config.enabled:
                try:
                    action_idx, _states = self.model.predict(state, deterministic=deterministic)
                    action = Action(action_idx)
                    confidence = 0.8
                except Exception as e:
                    print(f"[RL] Model prediction failed: {e}, using heuristic")
                    action = self._heuristic_decision(job, wallet_balance, trust_score, active_jobs)
                    confidence = 0.5
            else:
                # Fallback: heuristic decision
                action = self._heuristic_decision(job, wallet_balance, trust_score, active_jobs)
                confidence = 0.5
        
        # Store action for learning
        self.current_action = action  # ← NEW
        
        return (action, confidence)
     
    def _heuristic_decision(self, job: dict, wallet_balance: float, 
                           trust_score: float, active_jobs: int) -> Action:
        """
        Fallback heuristic when model not available
        """
        # Simple rule-based logic
        priority = job.get('priority', 0.5)
        payment = job.get('payment', 100.0)
        
        # Don't bid if too busy
        if active_jobs >= 3:
            return Action.DEFER
        
        # Don't bid if can't afford stake
        if wallet_balance < 20.0:
            return Action.DEFER
        
        # Don't bid if trust too low
        if trust_score < 0.3:
            return Action.DEFER
        
        # Forward if high priority but we're not ideal
        if priority > 0.8 and active_jobs >= 2:
            return Action.FORWARD
        
        # Bid if good payment and we're available
        if payment > 100.0 and active_jobs < 2:
            return Action.BID
        
        # Default: bid
        return Action.BID
    
    def record_transition(self, 
                         state: np.ndarray,
                         action: Action,
                         reward: float,
                         next_state: np.ndarray,
                         done: bool):
        """
        Record experience for online learning
        """
        if self.config.online_learning:
            transition = {
                'state': state,
                'action': action,
                'reward': reward,
                'next_state': next_state,
                'done': done
            }
            self.current_episode.append(transition)
            
            if done:
                self.episode_count += 1
                # TODO: Implement online learning update
                self.current_episode = []
    
    def update_job_history(self, job_type: str, success: bool, completion_time: float):
        """Update state calculator with job outcome"""
        self.state_calc.update_job_history(job_type, success, completion_time)
    
    def get_state_dim(self) -> int:
        """Get state dimension"""
        return self.state_calc.get_state_dim()
    
    def get_action_dim(self) -> int:
        """Get action dimension"""
        return 3  # BID, FORWARD, DEFER
    
    def record_outcome(self, success: bool, reward: float, 
                      new_state: np.ndarray, done: bool = False):
        """
        Record outcome of decision for learning - NEW METHOD
        
        Args:
            success: Whether action succeeded
            reward: Reward received
            new_state: State after action
            done: Episode done?
        """
        if self.current_state is None or self.current_action is None:
            return  # No decision was made
        
        # Create experience tuple
        experience = {
            'state': self.current_state,
            'action': self.current_action,
            'reward': reward,
            'next_state': new_state,
            'done': done
        }
        
        # Send to online learner
        if self.online_learner:
            self.online_learner.record_experience(
                self.current_state,
                int(self.current_action),
                reward,
                new_state,
                done
            )
        
        # Store in episode
        self.episode_experiences.append(experience)
        
        # Reset current state/action
        self.current_state = None
        self.current_action = None
        
        # Decay exploration rate
        self.exploration_rate = max(0.01, self.exploration_rate * 0.999)
