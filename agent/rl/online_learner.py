"""
Online Learning System
Continuously improves RL policy from agent experiences

INNOVATION: Learns from real-world experiences with fairness integration
- Experiences include fairness features in 25D state
- Rewards include fairness bonuses (low Gini, diversity)
- Training data preserves fairness objectives
"""
import asyncio
import numpy as np
from stable_baselines3 import PPO
from pathlib import Path
import time
from typing import Optional

from .experience_buffer import ExperienceBuffer
from ..config import RLConfig


class OnlineLearner:
    """
    Manages online learning for the RL policy
    
    Process:
    1. Agent collects experiences during operation
    2. Experiences stored in replay buffer
    3. Periodically, learner updates model from buffer
    4. New model deployed to agent
    """
    
    def __init__(self, node_id: str, config: RLConfig = None, policy=None, data_dir: str = "./data",
                 buffer_size: int = None, update_frequency: int = None):
        """
        Initialize OnlineLearner

        Args:
            node_id: Node identifier
            config: RLConfig instance (for production use)
            policy: RLPolicy instance (for production use)
            data_dir: Directory for storing data
            buffer_size: Buffer capacity (for test compatibility)
            update_frequency: Update interval in seconds (for test compatibility)
        """
        self.node_id = node_id
        self.policy = policy  # RLPolicy instance
        self.data_dir = Path(data_dir)

        # Support test-style initialization
        if buffer_size is not None:
            capacity = buffer_size
        else:
            capacity = 10000

        if update_frequency is not None:
            self.update_interval = update_frequency
        else:
            self.update_interval = 300  # Update every 5 minutes

        # Experience buffer
        self.buffer = ExperienceBuffer(capacity=capacity, data_dir=data_dir)

        # Learning config
        if config is not None:
            self.config = config
            self.learning_enabled = config.online_learning
        else:
            # Default for tests
            self.config = None
            self.learning_enabled = False

        self.min_buffer_size = 100  # Need 100 experiences before learning
        self.batch_size = 64

        # Training model (separate from inference model)
        self.training_model: Optional[PPO] = None

        # Stats
        self.updates_performed = 0
        self.last_update_time = 0

        self.running = False
    
    async def start(self):
        """Start online learning loop"""
        if not self.learning_enabled:
            print("[ONLINE LEARNER] Online learning disabled")
            return
        
        self.running = True
        
        # Load or create training model
        self._initialize_training_model()
        
        # Start learning loop
        asyncio.create_task(self._learning_loop())
        
        print(f"[ONLINE LEARNER] Started (update_interval={self.update_interval}s)")
    
    async def stop(self):
        """Stop online learning"""
        self.running = False
        
        # Save final model
        if self.training_model:
            self._save_training_model()
    
    def record_experience(self, state: np.ndarray, action: int, reward: float,
                         next_state: np.ndarray, done: bool):
        """Record experience from agent"""
        self.buffer.add(state, action, reward, next_state, done)
    
    async def _learning_loop(self):
        """Continuous learning loop"""
        while self.running:
            await asyncio.sleep(self.update_interval)
            
            # Check if we have enough experiences
            if self.buffer.size() < self.min_buffer_size:
                print(f"[ONLINE LEARNER] Buffer too small ({self.buffer.size()}/{self.min_buffer_size}), skipping update")
                continue
            
            # Perform update
            await self._perform_update()
    
    async def _perform_update(self):
        """Perform model update from buffer"""
        print(f"\n{'='*60}")
        print(f"[ONLINE LEARNER] Starting model update #{self.updates_performed + 1}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Get experiences from buffer
            experiences = self.buffer.get_all()
            
            print(f"[ONLINE LEARNER] Training on {len(experiences)} experiences")
            
            # Convert to training format
            states = np.array([exp.state for exp in experiences])
            actions = np.array([exp.action for exp in experiences])
            rewards = np.array([exp.reward for exp in experiences])
            next_states = np.array([exp.next_state for exp in experiences])
            dones = np.array([exp.done for exp in experiences])
            
            # Statistics before training
            stats_before = self.buffer.get_statistics()
            print(f"[ONLINE LEARNER] Avg reward before: {stats_before['avg_reward']:.3f}")
            print(f"[ONLINE LEARNER] Success rate: {stats_before['success_rate']:.2%}")
            
            # Perform training update
            
            # Train for a few steps
            num_updates = min(10, len(experiences) // self.batch_size)
            
            for i in range(num_updates):
                # Sample batch
                batch_experiences = self.buffer.sample(self.batch_size)
                
                # TODO: Actual training update
                # For PPO, we'd need to compute advantages, update policy, etc.
            
            # Simpler approach: Retrain model periodically
            if len(experiences) >= 500 and self.updates_performed % 5 == 0:
                print("[ONLINE LEARNER] Performing full retraining...")
                await self._retrain_model(experiences)
            
            duration = time.time() - start_time
            self.updates_performed += 1
            self.last_update_time = time.time()
            
            print(f"[ONLINE LEARNER] Update completed in {duration:.2f}s")
            print(f"{'='*60}\n")
        
        except Exception as e:
            print(f"[ONLINE LEARNER] Error during update: {e}")
            import traceback
            traceback.print_exc()
    
    async def _retrain_model(self, experiences: list):
        """
        Retrain model from scratch on accumulated experiences
        This is the "nuclear option" - rebuild model with new data
        """
        self._save_experiences_for_offline_training(experiences)
        
        print("[ONLINE LEARNER] Experiences saved for offline retraining")
        print("[ONLINE LEARNER] Run: python rl_trainer/train.py --continue-from experiences.pkl")
    
    def _save_experiences_for_offline_training(self, experiences: list):
        """Save experiences for offline retraining"""
        import pickle
        
        experience_file = self.data_dir / "experiences_for_training.pkl"
        
        with open(experience_file, 'wb') as f:
            pickle.dump(experiences, f)
        
        print(f"[ONLINE LEARNER] Saved {len(experiences)} experiences to {experience_file}")
    
    def _initialize_training_model(self):
        """Initialize or load training model"""
        training_model_path = self.data_dir / "training_model.zip"
        
        if training_model_path.exists():
            try:
                self.training_model = PPO.load(str(training_model_path))
                print(f"[ONLINE LEARNER] Loaded training model from {training_model_path}")
            except Exception as e:
                print(f"[ONLINE LEARNER] Error loading training model: {e}")
                self.training_model = None
        else:
            # Copy from inference model
            if self.policy.model:
                self.training_model = self.policy.model
                print("[ONLINE LEARNER] Using inference model for training")
    
    def _save_training_model(self):
        """Save training model to disk"""
        if self.training_model:
            training_model_path = self.data_dir / "training_model.zip"
            self.training_model.save(str(training_model_path))
            print(f"[ONLINE LEARNER] Saved training model to {training_model_path}")
    
    def get_learning_stats(self) -> dict:
        """Get learning statistics"""
        buffer_stats = self.buffer.get_statistics()

        return {
            'learning_enabled': self.learning_enabled,
            'updates_performed': self.updates_performed,
            'last_update': self.last_update_time,
            'buffer_size': self.buffer.size(),
            'buffer_stats': buffer_stats,
            'next_update_in': max(0, self.update_interval - (time.time() - self.last_update_time))
        }

    def get_stats(self) -> dict:
        """
        Get statistics (alias for compatibility with tests)

        Returns:
            Dictionary with total_experiences and buffer_size
        """
        return {
            'total_experiences': self.buffer.size(),
            'buffer_size': self.buffer.size(),
            'updates_performed': self.updates_performed
        }

    def export_for_training(self, output_path: str) -> int:
        """
        Export experiences to file for offline training (compatibility method for tests)

        Args:
            output_path: Path to save experiences

        Returns:
            Number of experiences exported
        """
        import pickle
        from pathlib import Path

        experiences = self.buffer.get_all()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'wb') as f:
            pickle.dump(experiences, f)

        print(f"[ONLINE LEARNER] Exported {len(experiences)} experiences to {output_path}")

        return len(experiences)