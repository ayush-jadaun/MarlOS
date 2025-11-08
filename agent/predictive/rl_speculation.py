"""
RL-Based Speculation Policy
Learns optimal speculation decisions through reinforcement learning
"""

import numpy as np
import os
from typing import Tuple, Optional


class RLSpeculationPolicy:
    """
    RL policy that learns when to speculate based on context

    State (7D):
        - prediction confidence (0-1)
        - CPU idle % (0-1)
        - cache utilization (0-1)
        - recent hit rate (0-1)
        - token balance (normalized)
        - time until job expected (normalized)
        - active jobs (normalized)

    Action (2):
        - 0 = WAIT (don't speculate)
        - 1 = SPECULATE (pre-execute)

    Reward:
        - +20 if speculation leads to cache hit
        - -5 if speculation wasted (job never came)
        - 0 if waited (no action)
    """

    def __init__(self, model_path: str = "rl_trainer/models/speculation_policy.zip", enabled: bool = True):
        self.model_path = model_path
        self.enabled = enabled
        self.model = None

        # Learning history
        self.state_history = []
        self.action_history = []
        self.reward_history = []

        # Statistics
        self.decisions_made = 0
        self.speculations_chosen = 0
        self.correct_speculations = 0

        if enabled:
            self._load_model()

        print(f"[RL-SPEC] Policy initialized (enabled={enabled}, model_loaded={self.model is not None})")

    def _load_model(self):
        """Load trained PPO model"""
        try:
            from stable_baselines3 import PPO

            if os.path.exists(self.model_path):
                self.model = PPO.load(self.model_path)
                print(f"[RL-SPEC] Loaded model from {self.model_path}")
            else:
                print(f"[RL-SPEC] Model not found at {self.model_path}, using heuristic fallback")
                self.model = None

        except ImportError:
            print(f"[RL-SPEC] stable-baselines3 not available, using heuristic fallback")
            self.model = None
        except Exception as e:
            print(f"[RL-SPEC] Error loading model: {e}")
            self.model = None

    def decide(
        self,
        prediction: dict,
        agent_context: dict
    ) -> Tuple[bool, float, np.ndarray]:
        """
        Decide whether to speculate on this prediction

        Args:
            prediction: From pattern detector {confidence, reason, expected_in, ...}
            agent_context: Current agent state {cpu_idle, cache_util, balance, ...}

        Returns:
            (should_speculate, decision_confidence, state_vector)
        """
        self.decisions_made += 1

        # Calculate state vector
        state = self._calculate_state(prediction, agent_context)

        if self.model and self.enabled:
            # RL decision
            action, _states = self.model.predict(state, deterministic=True)
            should_speculate = (action == 1)

            # Get value estimate as confidence
            obs_tensor = self.model.policy.obs_to_tensor(state)[0]
            with self.model.policy.set_training_mode(False):
                value = self.model.policy.predict_values(obs_tensor)[0].item()
            decision_confidence = min(abs(value) / 20.0, 1.0)  # Normalize value to 0-1

        else:
            # Fallback heuristic
            should_speculate, decision_confidence = self._heuristic_decision(prediction, agent_context)

        if should_speculate:
            self.speculations_chosen += 1

        # Record for potential learning
        self.state_history.append(state)
        self.action_history.append(1 if should_speculate else 0)

        return should_speculate, decision_confidence, state

    def record_outcome(self, state: np.ndarray, action: int, reward: float):
        """
        Record the outcome of a speculation decision

        Args:
            state: State when decision was made
            action: 0=WAIT, 1=SPECULATE
            reward: +20 for cache hit, -5 for waste, 0 for wait
        """
        self.reward_history.append(reward)

        # Track speculation attempts
        if action == 1:
            self.speculations_chosen += 1

            # Track successes (positive reward means cache hit)
            if reward > 0:
                self.correct_speculations += 1

        # Could be used for online learning later
        # For now, just track statistics

    def _calculate_state(self, prediction: dict, context: dict) -> np.ndarray:
        """
        Calculate 7D state vector for RL policy

        Features:
            [0] prediction confidence (0-1)
            [1] CPU idle % (0-1)
            [2] cache utilization (0-1)
            [3] recent hit rate (0-1)
            [4] token balance (normalized 0-1)
            [5] time until expected (normalized 0-1)
            [6] active jobs (normalized 0-1)
        """

        state = np.array([
            # Feature 0: Prediction confidence
            float(prediction.get('confidence', 0.5)),

            # Feature 1: CPU idle percentage
            float(context.get('cpu_idle_pct', 0.5)),

            # Feature 2: Cache utilization (how full is cache)
            float(context.get('cache_utilization', 0.0)),

            # Feature 3: Recent cache hit rate
            float(context.get('recent_hit_rate', 0.0)),

            # Feature 4: Token balance (normalized to 0-1, assume max 1000)
            min(float(context.get('balance', 100)) / 1000.0, 1.0),

            # Feature 5: Time until job expected (normalize to 0-1, max 300s)
            min(float(prediction.get('expected_in', 60)) / 300.0, 1.0),

            # Feature 6: Active jobs (normalize to 0-1, max 10)
            min(float(context.get('active_jobs', 0)) / 10.0, 1.0),

        ], dtype=np.float32)

        # Clamp all values to [0, 1] range to handle negative or out-of-range inputs
        state = np.clip(state, 0.0, 1.0)

        return state

    def _heuristic_decision(self, prediction: dict, context: dict) -> Tuple[bool, float]:
        """
        Fallback heuristic when RL model not available

        Simple rule: Speculate if expected value > 3.0 AC
        """
        confidence = prediction.get('confidence', 0.0)

        # Calculate expected value
        correct_reward = 20
        wrong_penalty = 5
        expected_value = (confidence * correct_reward) - ((1 - confidence) * wrong_penalty)

        should_speculate = expected_value >= 3.0

        return should_speculate, confidence

    def get_stats(self) -> dict:
        """Get policy statistics"""
        success_rate = 0.0
        if self.speculations_chosen > 0:
            success_rate = (self.correct_speculations / self.speculations_chosen) * 100

        speculation_rate = 0.0
        if self.decisions_made > 0:
            speculation_rate = (self.speculations_chosen / self.decisions_made) * 100

        return {
            'model_loaded': self.model is not None,
            'decisions_made': self.decisions_made,
            'speculations_chosen': self.speculations_chosen,
            'correct_speculations': self.correct_speculations,
            'success_rate': success_rate,
            'speculation_rate': speculation_rate,
            'avg_reward': np.mean(self.reward_history) if self.reward_history else 0.0
        }
