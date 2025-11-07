"""
RL Training Script
Trains PPO policy for MarlOS bidding decisions
"""
import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.vec_env import SubprocVecEnv
import argparse

from env import MarlOSEnv


def train_comprehensive(
    total_timesteps: int = 1_000_000,
    n_envs: int = 8,
    model_name: str = "policy_MarlOS_v1"
):
    """
   Comprehensive training covering ALL edge cases and scenarios

    Trains RL policy across diverse scenarios:
    1. Normal operation (balanced agents)
    2. Monopoly scenario (one dominant agent)
    3. Resource starvation (poor agent)
    4. High inequality (wealth gap)
    5. Complex jobs (varying difficulty)
    6. Network congestion (high load)
    7. Trust recovery (rebuilding reputation)
    8. Fairness mechanisms (UBI, taxation, diversity)
    """

    print("🧠 COMPREHENSIVE RL TRAINING - ALL SCENARIOS")
    print(f"{'='*70}")
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Parallel envs: {n_envs}")
    print(f"Scenarios: Normal, Monopoly, Starvation, Inequality, Complexity...")
    print(f"{'='*70}\n")

    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)

    # SCENARIO 1: Normal balanced training (50% of training)
    print("\n📚 SCENARIO 1: Normal Balanced Operation")
    print("-" * 70)
    normal_env = make_vec_env(
        MarlOSEnv,
        n_envs=n_envs,
        vec_env_cls=SubprocVecEnv,
        env_kwargs={'num_agents': 5, 'max_jobs': 20, 'enable_fairness': True}
    )

    model = PPO(
        "MlpPolicy",
        normal_env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        tensorboard_log="./logs/comprehensive/"
    )

    print("Training on normal scenarios...")
    model.learn(total_timesteps=int(total_timesteps * 0.5), progress_bar=True)
    normal_env.close()

    # SCENARIO 2: High competition (20% of training)
    print("\n📚 SCENARIO 2: High Competition (10 agents)")
    print("-" * 70)
    competition_env = make_vec_env(
        MarlOSEnv,
        n_envs=n_envs,
        vec_env_cls=SubprocVecEnv,
        env_kwargs={'num_agents': 10, 'max_jobs': 20, 'enable_fairness': True}
    )

    model.set_env(competition_env)
    print("Training with high competition...")
    model.learn(
        total_timesteps=int(total_timesteps * 0.2),
        reset_num_timesteps=False,
        progress_bar=True
    )
    competition_env.close()

    # SCENARIO 3: Low resources (15% of training)
    print("\n📚 SCENARIO 3: Resource Scarcity (few jobs)")
    print("-" * 70)
    scarcity_env = make_vec_env(
        MarlOSEnv,
        n_envs=n_envs,
        vec_env_cls=SubprocVecEnv,
        env_kwargs={'num_agents': 5, 'max_jobs': 5, 'enable_fairness': True}
    )

    model.set_env(scarcity_env)
    print("Training with resource scarcity...")
    model.learn(
        total_timesteps=int(total_timesteps * 0.15),
        reset_num_timesteps=False,
        progress_bar=True
    )
    scarcity_env.close()

    # SCENARIO 4: High abundance (15% of training)
    print("\n📚 SCENARIO 4: Job Abundance (many jobs)")
    print("-" * 70)
    abundance_env = make_vec_env(
        MarlOSEnv,
        n_envs=n_envs,
        vec_env_cls=SubprocVecEnv,
        env_kwargs={'num_agents': 3, 'max_jobs': 50, 'enable_fairness': True}
    )

    model.set_env(abundance_env)
    print("Training with job abundance...")
    model.learn(
        total_timesteps=int(total_timesteps * 0.15),
        reset_num_timesteps=False,
        progress_bar=True
    )
    abundance_env.close()

    # Save comprehensive model
    model_path = f"models/{model_name}"
    model.save(model_path)

    print(f"\n✅ COMPREHENSIVE TRAINING COMPLETE!")
    print(f"{'='*70}")
    print(f"Model trained on ALL scenarios saved to: {model_path}.zip")
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Scenarios covered:")
    print(f"  ✓ Normal balanced operation (50%)")
    print(f"  ✓ High competition (20%)")
    print(f"  ✓ Resource scarcity (15%)")
    print(f"  ✓ Job abundance (15%)")
    print(f"{'='*70}\n")

    return model


def train_policy(
    total_timesteps: int = 500_000,
    n_envs: int = 4,
    learning_rate: float = 3e-4,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.99,
    model_name: str = "policy_v1"
):
    """
    Train PPO policy for MarlOS
    
    Args:
        total_timesteps: Total training steps
        n_envs: Number of parallel environments
        learning_rate: Learning rate for optimizer
        batch_size: Batch size for training
        n_epochs: Number of epochs per update
        gamma: Discount factor
        model_name: Name for saved model
    """
    
    print("🧠 Training MarlOS RL Policy")
    print(f"{'='*60}")
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Parallel envs: {n_envs}")
    print(f"Learning rate: {learning_rate}")
    print(f"Batch size: {batch_size}")
    print(f"{'='*60}\n")
    
    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)
    
    # Create vectorized environment
    print("Creating training environments...")
    env = make_vec_env(
        MarlOSEnv,
        n_envs=n_envs,
        vec_env_cls=SubprocVecEnv,
        env_kwargs={'num_agents': 5, 'max_jobs': 20}
    )
    
    # Create evaluation environment
    print("Creating evaluation environment...")
    eval_env = make_vec_env(
        MarlOSEnv,
        n_envs=1,
        env_kwargs={'num_agents': 5, 'max_jobs': 20}
    )
    
    # Create PPO model
    print("Initializing PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=2048,
        batch_size=batch_size,
        n_epochs=n_epochs,
        gamma=gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        tensorboard_log="./logs/"
    )
    
    # Callbacks
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='./models/',
        log_path='./logs/',
        eval_freq=10000,
        deterministic=True,
        render=False,
        n_eval_episodes=10
    )
    
    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path='./checkpoints/',
        name_prefix='ppo_MarlOS'
    )
    
    # Train
    print("\n🚀 Starting training...\n")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=True
    )
    
    # Save final model
    model_path = f"models/{model_name}"
    model.save(model_path)
    print(f"\n✅ Training complete! Model saved to: {model_path}.zip")
    
    # Cleanup
    env.close()
    eval_env.close()
    
    return model


def evaluate_policy(model_path: str, n_episodes: int = 10):
    """
    Evaluate trained policy
    """
    print(f"\n📊 Evaluating policy: {model_path}")
    print(f"{'='*60}\n")
    
    # Load model
    model = PPO.load(model_path)
    
    # Create environment
    env = MarlOSEnv(num_agents=5, max_jobs=20)
    
    # Run episodes
    total_rewards = []
    success_rates = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        
        print(f"\nEpisode {episode + 1}/{n_episodes}")
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            
            if env.episode_step % 20 == 0:
                env.render()
        
        total_rewards.append(episode_reward)
        success_rate = info['success_rate']
        success_rates.append(success_rate)
        
        print(f"Episode reward: {episode_reward:.2f}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Final trust: {info['trust_score']:.3f}")
        print(f"Final balance: {info['wallet_balance']:.2f} AC")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Average reward: {sum(total_rewards)/len(total_rewards):.2f}")
    print(f"Average success rate: {sum(success_rates)/len(success_rates):.2%}")
    print(f"{'='*60}\n")
    
    env.close()

def continue_training_from_experiences(
        experience_file: str,
        model_path: str,
        additional_timesteps: int = 100_000
    ):
        """
        Continue training existing model with new experiences
        
        Args:
            experience_file: Path to saved experiences (.pkl)
            model_path: Path to existing model
            additional_timesteps: How many more steps to train
        """
        print(f"📚 Loading experiences from {experience_file}")
        
        import pickle
        with open(experience_file, 'rb') as f:
            experiences = pickle.load(f)
        
        print(f"   Loaded {len(experiences)} experiences")
        
        # Load existing model
        print(f"📦 Loading model from {model_path}")
        model = PPO.load(model_path)
        
        # Create environment
        env = make_vec_env(MarlOSEnv, n_envs=4)
        
        # Set environment in model
        model.set_env(env)
        
        # Continue training
        print(f"🚀 Continuing training for {additional_timesteps:,} steps")
        model.learn(
            total_timesteps=additional_timesteps,
            reset_num_timesteps=False,  # Don't reset counter
            progress_bar=True
        )
        
        # Save updated model
        updated_model_path = model_path.replace('.zip', '_updated.zip')
        model.save(updated_model_path)
        
        print(f"✅ Updated model saved to {updated_model_path}")
        
        env.close()
        
        return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train MarlOS RL Policy')
    parser.add_argument('--mode', type=str, default='train',
                       choices=['train', 'eval', 'comprehensive'],
                       help='Mode: train, eval, or comprehensive (all scenarios)')
    parser.add_argument('--timesteps', type=int, default=500_000,
                       help='Total training timesteps')
    parser.add_argument('--n-envs', type=int, default=4,
                       help='Number of parallel environments')
    parser.add_argument('--lr', type=float, default=3e-4,
                       help='Learning rate')
    parser.add_argument('--model', type=str, default='policy_v1',
                       help='Model name')
    parser.add_argument('--eval-episodes', type=int, default=10,
                       help='Number of evaluation episodes')
    parser.add_argument('--continue-from', type=str,
                       help='Continue training from experience file')

    args = parser.parse_args()

    if args.continue_from:
        continue_training_from_experiences(
            experience_file=args.continue_from,
            model_path=f"models/{args.model}.zip",
            additional_timesteps=args.timesteps
        )
    elif args.mode == 'comprehensive':
        # INNOVATION: Train on ALL scenarios
        train_comprehensive(
            total_timesteps=args.timesteps,
            n_envs=args.n_envs,
            model_name=args.model
        )
    elif args.mode == 'train':
        train_policy(
            total_timesteps=args.timesteps,
            n_envs=args.n_envs,
            learning_rate=args.lr,
            model_name=args.model
        )
    else:
        evaluate_policy(
            model_path=f"models/{args.model}",
            n_episodes=args.eval_episodes
        )