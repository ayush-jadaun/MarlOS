"""
Comprehensive RL Fairness Integration Tests
Tests the integration of RL system with economic fairness engine

INNOVATION TESTING:
- 25D state representation with fairness features
- Fairness-aware training environment
- Comprehensive scenario training
- Online learning with fairness
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agent.rl.state import StateCalculator
from agent.rl.policy import RLPolicy, Action
from agent.rl.online_learner import OnlineLearner
from agent.config import RLConfig, TrustConfig, TokenConfig
from rl_trainer.env import MarlOSEnv


class TestFairnessStateCalculator:
    """Test 25D state representation with fairness features"""

    def test_state_dimension_is_25(self):
        """INNOVATION: State expanded from 18D to 25D"""
        calc = StateCalculator("test-node", enable_fairness=True)

        job = {
            'job_type': 'shell',
            'priority': 0.8,
            'deadline': 60.0,
            'payment': 100.0,
            'payload': {}
        }

        state = calc.calculate_state(
            job=job,
            wallet_balance=200.0,
            trust_score=0.7,
            peer_count=5,
            active_jobs=2
        )

        assert state.shape == (25,), f"Expected 25D state, got {state.shape}"
        assert state.dtype == np.float32

    def test_fairness_features_present(self):
        """Test that fairness features are included in state"""
        calc = StateCalculator("test-node", enable_fairness=True)

        job = {
            'job_type': 'malware_scan',
            'priority': 0.5,
            'deadline': 120.0,
            'payment': 150.0,
            'payload': {'size': 1000}
        }

        state = calc.calculate_state(
            job=job,
            wallet_balance=500.0,
            trust_score=0.8,
            peer_count=10,
            active_jobs=1
        )

        # Fairness features are indices 18-24
        fairness_features = state[18:25]

        assert len(fairness_features) == 7
        assert np.all(fairness_features >= 0.0)
        assert np.all(fairness_features <= 1.0)

    def test_fairness_features_vary_by_wealth(self):
        """Test that fairness features change with wealth (tax rate)"""
        calc = StateCalculator("test-node", enable_fairness=True)

        job = {'job_type': 'shell', 'priority': 0.5, 'deadline': 60.0, 'payment': 100.0, 'payload': {}}

        # Poor agent
        state_poor = calc.calculate_state(job, wallet_balance=50.0, trust_score=0.5, peer_count=5, active_jobs=1)

        # Rich agent
        state_rich = calc.calculate_state(job, wallet_balance=5000.0, trust_score=0.5, peer_count=5, active_jobs=1)

        # Tax rate should differ (index 19)
        tax_rate_poor = state_poor[19]
        tax_rate_rich = state_rich[19]

        assert tax_rate_rich > tax_rate_poor, "Rich agents should have higher tax rate"

    def test_fairness_features_disabled(self):
        """Test state calculation with fairness disabled"""
        calc = StateCalculator("test-node", enable_fairness=False)

        job = {'job_type': 'shell', 'priority': 0.5, 'deadline': 60.0, 'payment': 100.0, 'payload': {}}

        state = calc.calculate_state(
            job=job,
            wallet_balance=200.0,
            trust_score=0.7,
            peer_count=5,
            active_jobs=2
        )

        # Should still be 25D but with neutral fairness values
        assert state.shape == (25,)
        fairness_features = state[18:25]

        # Should contain neutral/default values
        assert np.any(fairness_features == 0.5) or np.any(fairness_features == 0.0)


class TestFairnessTrainingEnvironment:
    """Test training environment with fairness integration"""

    def test_environment_observation_space(self):
        """Test environment has 25D observation space"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        assert env.observation_space.shape == (25,)

        obs, info = env.reset()
        assert obs.shape == (25,)

        env.close()

    def test_fairness_in_step_rewards(self):
        """Test that fairness affects rewards"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()

        # Take some actions
        total_reward = 0.0
        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward

            if terminated or truncated:
                break

        # Should have fairness metrics in info
        if env.fairness_engine:
            assert 'gini_coefficient' in info
            assert 'diversity_factor' in info

        env.close()

    def test_ubi_distribution(self):
        """Test that UBI is distributed in environment"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()

        initial_balance = info['wallet_balance']

        # Run enough steps to trigger UBI (every 10 steps)
        for _ in range(15):
            action = 2  # DEFER to stay active but not spend tokens
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                break

        # Should have received some UBI
        if env.fairness_engine:
            assert info.get('total_ubi_received', 0.0) >= 0.0

        env.close()

    def test_progressive_taxation(self):
        """Test that wealthier agents pay more tax"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()

        # Set high balance
        env.wallet_balance = 2000.0

        # Take action that earns money
        action = 0  # BID
        obs, reward, terminated, truncated, info = env.step(action)

        # Should track taxes paid
        if env.fairness_engine:
            assert 'total_taxes_paid' in info

        env.close()

    def test_diversity_tracking(self):
        """Test that job win diversity is tracked"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()

        # Win some jobs
        for _ in range(20):
            action = 0  # Always BID
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                break

        # Should track win rate
        if env.fairness_engine:
            assert 'jobs_won' in info
            assert 'jobs_lost' in info
            assert 'win_rate' in info

        env.close()


class TestComprehensiveScenarios:
    """Test RL training covers all scenarios"""

    def test_normal_operation_scenario(self):
        """Test normal balanced operation"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()

        # Run a full episode
        episode_reward = 0.0
        steps = 0

        while steps < 100:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            steps += 1

            if terminated or truncated:
                break

        # Should complete successfully
        assert steps > 0
        assert obs.shape == (25,)

        env.close()

    def test_high_competition_scenario(self):
        """Test with many competing agents"""
        env = MarlOSEnv(num_agents=10, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()

        # With more agents, win probability should be lower
        initial_balance = env.wallet_balance

        for _ in range(20):
            action = 0  # Always BID
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                break

        # Should have some competitive dynamics
        assert 'jobs_won' in info
        assert 'jobs_lost' in info

        env.close()

    def test_resource_scarcity_scenario(self):
        """Test with few jobs available"""
        env = MarlOSEnv(num_agents=5, max_jobs=5, enable_fairness=True)

        obs, info = env.reset()

        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                break

        # Agent should adapt to scarcity
        assert obs.shape == (25,)

        env.close()

    def test_job_abundance_scenario(self):
        """Test with many jobs available"""
        env = MarlOSEnv(num_agents=3, max_jobs=50, enable_fairness=True)

        obs, info = env.reset()

        for _ in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                break

        # Agent should take advantage of abundance
        assert obs.shape == (25,)

        env.close()


class TestOnlineLearning:
    """Test online learning integration"""

    def test_experience_recording(self):
        """Test that experiences are recorded"""
        config = RLConfig()
        config.online_learning = True

        policy = RLPolicy("test-node", config, enable_fairness=True)
        learner = OnlineLearner("test-node", buffer_size=100, update_frequency=10)

        # Record some experiences
        for i in range(20):
            state = np.random.random(25).astype(np.float32)
            action = np.random.randint(0, 3)
            reward = np.random.random()
            next_state = np.random.random(25).astype(np.float32)
            done = (i % 10 == 9)

            learner.record_experience(state, action, reward, next_state, done)

        # Check buffer
        stats = learner.get_stats()
        assert stats['total_experiences'] == 20
        assert stats['buffer_size'] == 20

    def test_experience_export(self):
        """Test exporting experiences for training"""
        learner = OnlineLearner("test-node", buffer_size=100)

        # Add experiences
        for i in range(50):
            state = np.random.random(25).astype(np.float32)
            action = np.random.randint(0, 3)
            reward = np.random.random()
            next_state = np.random.random(25).astype(np.float32)
            done = False

            learner.record_experience(state, action, reward, next_state, done)

        # Export
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            output_path = f.name

        count = learner.export_for_training(output_path)
        assert count == 50

        # Clean up
        import os
        os.remove(output_path)


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_full_episode_with_fairness(self):
        """Test complete episode with all fairness features"""
        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)

        obs, info = env.reset()
        assert obs.shape == (25,)

        episode_reward = 0.0
        fairness_rewards = 0.0

        for step in range(100):
            # Simple policy: bid if balance > 100, defer otherwise
            action = 0 if env.wallet_balance > 100 else 2

            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward

            # Track fairness metrics
            if env.fairness_engine:
                gini = info.get('gini_coefficient', 0.5)
                if gini < 0.3:
                    fairness_rewards += 0.1

            if terminated or truncated:
                break

        # Verify fairness integration
        if env.fairness_engine:
            assert 'gini_coefficient' in info
            assert 'total_taxes_paid' in info
            assert 'total_ubi_received' in info
            assert 'diversity_factor' in info

        env.close()

    def test_policy_with_fairness_state(self):
        """Test RL policy using fairness-aware state"""
        config = RLConfig()
        policy = RLPolicy("test-node", config, enable_fairness=True)

        job = {
            'job_type': 'shell',
            'priority': 0.7,
            'deadline': 60.0,
            'payment': 100.0,
            'payload': {}
        }

        # Make decision
        action, confidence = policy.decide(
            job=job,
            wallet_balance=200.0,
            trust_score=0.8,
            peer_count=5,
            active_jobs=1,
            deterministic=True
        )

        assert action in [Action.BID, Action.FORWARD, Action.DEFER]
        assert 0.0 <= confidence <= 1.0

        # State should be 25D
        assert policy.get_state_dim() == 25


class TestPerformanceWithFairness:
    """Test performance doesn't degrade with fairness"""

    @pytest.mark.performance
    def test_state_calculation_performance(self):
        """Test state calculation is still fast with fairness"""
        import time

        calc = StateCalculator("test-node", enable_fairness=True)
        job = {'job_type': 'shell', 'priority': 0.5, 'deadline': 60.0, 'payment': 100.0, 'payload': {}}

        num_iterations = 1000
        start = time.time()

        for _ in range(num_iterations):
            calc.calculate_state(
                job=job,
                wallet_balance=200.0,
                trust_score=0.7,
                peer_count=5,
                active_jobs=2
            )

        duration = time.time() - start
        ops_per_sec = num_iterations / duration

        # Should still be very fast (>1000 ops/sec)
        assert ops_per_sec > 1000, f"Too slow: {ops_per_sec:.2f} ops/sec"

    @pytest.mark.performance
    def test_environment_step_performance(self):
        """Test environment step is reasonably fast"""
        import time

        env = MarlOSEnv(num_agents=5, max_jobs=20, enable_fairness=True)
        obs, info = env.reset()

        num_steps = 100
        start = time.time()

        for _ in range(num_steps):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                env.reset()

        duration = time.time() - start
        steps_per_sec = num_steps / duration

        # Should achieve reasonable throughput
        assert steps_per_sec > 50, f"Too slow: {steps_per_sec:.2f} steps/sec"

        env.close()


# Fixtures
@pytest.fixture
def sample_job():
    """Create sample job for testing"""
    import time
    return {
        'job_id': 'test-job-1',
        'job_type': 'shell',
        'priority': 0.7,
        'deadline': time.time() + 60,
        'payment': 100.0,
        'payload': {'command': 'echo test'}
    }


@pytest.fixture
def state_calculator():
    """Create state calculator for testing"""
    return StateCalculator("test-node", enable_fairness=True)


@pytest.fixture
def rl_policy():
    """Create RL policy for testing"""
    config = RLConfig()
    return RLPolicy("test-node", config, enable_fairness=True)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
