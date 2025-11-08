"""
Train RL Speculation Policy
Trains a PPO agent to make optimal speculation decisions
"""

import os
import sys
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from speculation_env import SpeculationEnv


def make_env():
    """Create environment instance"""
    return SpeculationEnv()


def train_speculation_policy(
    total_timesteps: int = 100_000,
    n_envs: int = 4,
    eval_freq: int = 5000,
    save_path: str = "models/speculation_policy"
):
    """
    Train speculation policy using PPO

    Args:
        total_timesteps: Total training steps
        n_envs: Number of parallel environments
        eval_freq: Evaluation frequency
        save_path: Where to save the model
    """

    print("=" * 60)
    print("TRAINING RL SPECULATION POLICY")
    print("=" * 60)
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Parallel envs: {n_envs}")
    print(f"Algorithm: PPO")
    print()

    # Create vectorized environments for parallel training
    if n_envs > 1:
        env = SubprocVecEnv([make_env for _ in range(n_envs)])
    else:
        env = DummyVecEnv([make_env])

    # Create eval environment
    eval_env = DummyVecEnv([make_env])

    # Create callbacks
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='./models/speculation_best/',
        log_path='./logs/speculation/',
        eval_freq=max(eval_freq // n_envs, 1),
        deterministic=True,
        render=False,
        n_eval_episodes=10
    )

    checkpoint_callback = CheckpointCallback(
        save_freq=max(10_000 // n_envs, 1),
        save_path='./models/speculation_checkpoints/',
        name_prefix='spec_policy'
    )

    # Create PPO model
    print("Creating PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        tensorboard_log="./logs/speculation_tensorboard/"
    )

    print("\nStarting training...")
    print("-" * 60)

    # Train
    model.learn(
        total_timesteps=total_timesteps,
        callback=[eval_callback, checkpoint_callback],
        progress_bar=True
    )

    # Save final model
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    model.save(save_path)
    print(f"\n✓ Model saved to: {save_path}.zip")

    # Cleanup
    env.close()
    eval_env.close()

    print("\nTraining complete!")
    return model


def evaluate_policy(model_path: str = "models/speculation_policy.zip", n_episodes: int = 10):
    """
    Evaluate trained policy

    Args:
        model_path: Path to saved model
        n_episodes: Number of evaluation episodes
    """
    print("\n" + "=" * 60)
    print("EVALUATING SPECULATION POLICY")
    print("=" * 60)

    # Load model
    model = PPO.load(model_path)
    env = SpeculationEnv()

    total_rewards = []
    success_rates = []

    for episode in range(n_episodes):
        obs, _ = env.reset()
        episode_reward = 0
        done = False

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated

        total_rewards.append(episode_reward)

        # Calculate success rate
        total_speculations = info['correct_speculations'] + info['wrong_speculations']
        if total_speculations > 0:
            success_rate = info['correct_speculations'] / total_speculations
        else:
            success_rate = 0.0

        success_rates.append(success_rate)

        print(f"Episode {episode+1}: Reward={episode_reward:.1f}, "
              f"Success={success_rate:.1%}, "
              f"Correct={info['correct_speculations']}, "
              f"Wrong={info['wrong_speculations']}, "
              f"Missed={info['missed_opportunities']}")

    # Summary
    print("\n" + "-" * 60)
    print(f"Average reward: {sum(total_rewards)/len(total_rewards):.1f}")
    print(f"Average success rate: {sum(success_rates)/len(success_rates):.1%}")
    print(f"Best episode: {max(total_rewards):.1f}")
    print(f"Worst episode: {min(total_rewards):.1f}")

    env.close()


def compare_with_heuristic(model_path: str = "models/speculation_policy.zip", n_episodes: int = 10):
    """
    Compare RL policy with simple heuristic

    Heuristic: Speculate if confidence > 0.75
    """
    print("\n" + "=" * 60)
    print("COMPARING RL POLICY VS HEURISTIC")
    print("=" * 60)

    model = PPO.load(model_path)
    env = SpeculationEnv()

    rl_rewards = []
    heuristic_rewards = []

    for episode in range(n_episodes):
        # Test RL policy
        obs, _ = env.reset(seed=episode)
        rl_reward = 0
        done = False

        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            rl_reward += reward
            done = terminated or truncated

        rl_rewards.append(rl_reward)

        # Test heuristic (confidence > 0.75)
        obs, _ = env.reset(seed=episode)  # Same seed for fair comparison
        heuristic_reward = 0
        done = False

        while not done:
            # Heuristic: speculate if confidence > 0.75
            action = 1 if obs[0] > 0.75 else 0
            obs, reward, terminated, truncated, info = env.step(action)
            heuristic_reward += reward
            done = terminated or truncated

        heuristic_rewards.append(heuristic_reward)

        print(f"Episode {episode+1}: RL={rl_reward:.1f}, Heuristic={heuristic_reward:.1f}, "
              f"Diff={rl_reward - heuristic_reward:+.1f}")

    # Summary
    rl_avg = sum(rl_rewards) / len(rl_rewards)
    heuristic_avg = sum(heuristic_rewards) / len(heuristic_rewards)
    improvement = ((rl_avg - heuristic_avg) / abs(heuristic_avg)) * 100

    print("\n" + "-" * 60)
    print(f"RL Policy average: {rl_avg:.1f}")
    print(f"Heuristic average: {heuristic_avg:.1f}")
    print(f"Improvement: {improvement:+.1f}%")

    if rl_avg > heuristic_avg:
        print("\n*** RL POLICY WINS! ***")
    else:
        print("\n*** Heuristic is better (RL needs more training) ***")

    env.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train speculation policy')
    parser.add_argument('--mode', type=str, default='train',
                       choices=['train', 'eval', 'compare'],
                       help='Mode: train, eval, or compare')
    parser.add_argument('--timesteps', type=int, default=100_000,
                       help='Total training timesteps')
    parser.add_argument('--envs', type=int, default=4,
                       help='Number of parallel environments')
    parser.add_argument('--model', type=str, default='models/speculation_policy',
                       help='Model path')

    args = parser.parse_args()

    if args.mode == 'train':
        train_speculation_policy(
            total_timesteps=args.timesteps,
            n_envs=args.envs,
            save_path=args.model
        )
        print("\nNow evaluating trained model...")
        evaluate_policy(f"{args.model}.zip")

    elif args.mode == 'eval':
        evaluate_policy(f"{args.model}.zip")

    elif args.mode == 'compare':
        compare_with_heuristic(f"{args.model}.zip")
