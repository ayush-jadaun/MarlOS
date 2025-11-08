"""
Gymnasium Environment for Training Speculation Policy
Simulates speculation decisions and their outcomes
"""

import gymnasium as gym
import numpy as np
from typing import Optional


class SpeculationEnv(gym.Env):
    """
    Environment for learning optimal speculation strategy

    The agent learns to decide: "Should I speculate on this prediction?"

    State Space (7D):
        [0] prediction confidence (0-1)
        [1] CPU idle % (0-1)
        [2] cache utilization (0-1)
        [3] recent hit rate (0-1)
        [4] token balance (0-1, normalized)
        [5] time until expected (0-1, normalized)
        [6] active jobs (0-1, normalized)

    Action Space:
        0 = WAIT (don't speculate)
        1 = SPECULATE (pre-execute job)

    Reward:
        - If SPECULATE and prediction correct: +20
        - If SPECULATE and prediction wrong: -5
        - If WAIT: 0 (missed opportunity if prediction was correct)

    Episode:
        - Each episode simulates 100 speculation decisions
        - Environment generates realistic prediction scenarios
    """

    metadata = {'render_modes': []}

    def __init__(self, render_mode: Optional[str] = None):
        super().__init__()

        # State: 7D continuous
        self.observation_space = gym.spaces.Box(
            low=0.0,
            high=1.0,
            shape=(7,),
            dtype=np.float32
        )

        # Action: 0=WAIT, 1=SPECULATE
        self.action_space = gym.spaces.Discrete(2)

        # Episode tracking
        self.current_step = 0
        self.max_steps = 100
        self.total_reward = 0

        # State variables
        self.state = None
        self.prediction_actually_correct = False

        # Statistics
        self.correct_speculations = 0
        self.wrong_speculations = 0
        self.missed_opportunities = 0

        self.reset()

    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)

        self.current_step = 0
        self.total_reward = 0
        self.correct_speculations = 0
        self.wrong_speculations = 0
        self.missed_opportunities = 0

        # Generate initial state
        self.state = self._generate_state()
        self.prediction_actually_correct = self._is_prediction_correct(self.state)

        return self.state, {}

    def step(self, action: int):
        """
        Execute one speculation decision

        Args:
            action: 0=WAIT, 1=SPECULATE

        Returns:
            (observation, reward, terminated, truncated, info)
        """
        self.current_step += 1

        # Calculate reward based on action and ground truth
        reward = self._calculate_reward(action, self.prediction_actually_correct)
        self.total_reward += reward

        # Update statistics
        if action == 1:  # SPECULATE
            if self.prediction_actually_correct:
                self.correct_speculations += 1
            else:
                self.wrong_speculations += 1
        elif action == 0 and self.prediction_actually_correct:  # WAIT but should have speculated
            self.missed_opportunities += 1

        # Generate next state
        self.state = self._generate_state()
        self.prediction_actually_correct = self._is_prediction_correct(self.state)

        # Episode ends after max_steps
        terminated = (self.current_step >= self.max_steps)
        truncated = False

        info = {
            'correct_speculations': self.correct_speculations,
            'wrong_speculations': self.wrong_speculations,
            'missed_opportunities': self.missed_opportunities,
            'total_reward': self.total_reward
        }

        return self.state, reward, terminated, truncated, info

    def _generate_state(self) -> np.ndarray:
        """
        Generate realistic state representing a speculation scenario

        Creates diverse scenarios:
        - High confidence + idle resources → should speculate
        - Low confidence + busy → should wait
        - High confidence + low balance → risky
        - etc.
        """

        # Mix of random states to create diverse training data
        scenario = self.np_random.choice(['high_conf', 'medium_conf', 'low_conf', 'busy', 'idle'])

        if scenario == 'high_conf':
            # High confidence prediction, good conditions
            state = np.array([
                self.np_random.uniform(0.8, 1.0),   # [0] high confidence
                self.np_random.uniform(0.6, 1.0),   # [1] high CPU idle
                self.np_random.uniform(0.0, 0.3),   # [2] low cache utilization
                self.np_random.uniform(0.7, 1.0),   # [3] good hit rate
                self.np_random.uniform(0.5, 1.0),   # [4] good balance
                self.np_random.uniform(0.1, 0.4),   # [5] coming soon
                self.np_random.uniform(0.0, 0.3),   # [6] few active jobs
            ], dtype=np.float32)

        elif scenario == 'low_conf':
            # Low confidence prediction
            state = np.array([
                self.np_random.uniform(0.3, 0.6),   # [0] low confidence
                self.np_random.uniform(0.3, 0.7),   # [1] some CPU idle
                self.np_random.uniform(0.2, 0.6),   # [2] medium cache
                self.np_random.uniform(0.3, 0.6),   # [3] medium hit rate
                self.np_random.uniform(0.3, 0.8),   # [4] medium balance
                self.np_random.uniform(0.3, 0.8),   # [5] uncertain timing
                self.np_random.uniform(0.2, 0.6),   # [6] some active jobs
            ], dtype=np.float32)

        elif scenario == 'busy':
            # System is busy
            state = np.array([
                self.np_random.uniform(0.6, 0.9),   # [0] decent confidence
                self.np_random.uniform(0.0, 0.3),   # [1] LOW CPU idle (busy!)
                self.np_random.uniform(0.6, 1.0),   # [2] high cache utilization
                self.np_random.uniform(0.4, 0.7),   # [3] medium hit rate
                self.np_random.uniform(0.2, 0.6),   # [4] medium balance
                self.np_random.uniform(0.2, 0.5),   # [5] coming soon
                self.np_random.uniform(0.6, 1.0),   # [6] MANY active jobs
            ], dtype=np.float32)

        else:  # idle or medium_conf
            # Random state
            state = self.np_random.uniform(0, 1, size=7).astype(np.float32)

        return state

    def _is_prediction_correct(self, state: np.ndarray) -> bool:
        """
        Determine if the prediction will actually come true

        Probability based on confidence (state[0]) with some randomness
        """
        confidence = state[0]

        # Add some noise: confidence isn't perfect
        actual_probability = confidence * 0.9 + 0.05  # 90% correlation + 5% base

        return self.np_random.random() < actual_probability

    def _calculate_reward(self, action: int, prediction_correct: bool) -> float:
        """
        Calculate reward for the action taken

        Args:
            action: 0=WAIT, 1=SPECULATE
            prediction_correct: Was the prediction actually correct?

        Returns:
            Reward value
        """
        if action == 1:  # SPECULATE
            if prediction_correct:
                # Successful speculation - cache hit!
                return 20.0
            else:
                # Wasted computation
                return -5.0
        else:  # WAIT
            # No action taken
            # Could add small penalty for missed opportunities
            if prediction_correct:
                return -0.5  # Missed a good opportunity
            else:
                return 0.0  # Correctly avoided waste

    def render(self):
        """Render environment (not implemented)"""
        pass


# Test the environment
if __name__ == "__main__":
    env = SpeculationEnv()

    print("Testing Speculation Environment")
    print("=" * 60)

    # Run one episode
    obs, info = env.reset()
    print(f"\nInitial state: {obs}")

    total_reward = 0
    for step in range(10):
        # Random action
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        total_reward += reward
        print(f"Step {step+1}: action={action}, reward={reward:.1f}, total={total_reward:.1f}")

        if terminated:
            break

    print(f"\nEpisode finished!")
    print(f"Total reward: {total_reward:.1f}")
    print(f"Stats: {info}")
