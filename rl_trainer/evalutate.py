"""
RL Policy Evaluation and Visualization
"""
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from env import AetherSwarmEnv


def visualize_learning_curve(log_dir: str = "./logs/"):
    """
    Visualize training learning curve
    """
    # TODO: Parse tensorboard logs
    print("📊 Visualizing learning curve...")
    print("Run: tensorboard --logdir ./logs/")


def test_policy_decisions(model_path: str, n_scenarios: int = 10):
    """
    Test policy on specific scenarios
    """
    print(f"\n🧪 Testing policy decisions: {model_path}\n")
    
    model = PPO.load(model_path)
    env = AetherSwarmEnv()
    
    action_names = ['BID', 'FORWARD', 'DEFER']
    
    for i in range(n_scenarios):
        obs, info = env.reset()
        
        print(f"\n{'='*60}")
        print(f"Scenario {i+1}")
        print(f"{'='*60}")
        print(f"Trust: {info['trust_score']:.3f}")
        print(f"Balance: {info['wallet_balance']:.2f} AC")
        print(f"Active jobs: {info['active_jobs']}")
        print(f"Job type: {env.current_job['job_type']}")
        print(f"Job priority: {env.current_job['priority']:.2f}")
        print(f"Job payment: {env.current_job['payment']:.2f} AC")
        
        # Get action
        action, _states = model.predict(obs, deterministic=True)
        
        print(f"\n🧠 RL Decision: {action_names[action]}")
        
        # Execute
        obs, reward, terminated, truncated, info = env.step(action)
        
        print(f"Reward: {reward:.3f}")
        print(f"Success rate: {info['success_rate']:.2%}")
    
    env.close()


def compare_policies(model_paths: list, n_episodes: int = 10):
    """
    Compare multiple trained policies
    """
    print("\n📊 Comparing policies...\n")
    
    results = {}
    
    for model_path in model_paths:
        print(f"Testing: {model_path}")
        model = PPO.load(model_path)
        env = AetherSwarmEnv()
        
        rewards = []
        success_rates = []
        
        for _ in range(n_episodes):
            obs, info = env.reset()
            episode_reward = 0
            done = False
            
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward
                done = terminated or truncated
            
            rewards.append(episode_reward)
            success_rates.append(info['success_rate'])
        
        results[model_path] = {
            'avg_reward': np.mean(rewards),
            'std_reward': np.std(rewards),
            'avg_success': np.mean(success_rates)
        }
        
        env.close()
    
    # Print comparison
    print(f"\n{'='*80}")
    print("COMPARISON RESULTS")
    print(f"{'='*80}")
    print(f"{'Model':<30} {'Avg Reward':<15} {'Std Reward':<15} {'Success Rate':<15}")
    print(f"{'-'*80}")
    
    for model_path, stats in results.items():
        print(f"{model_path:<30} "
              f"{stats['avg_reward']:<15.2f} "
              f"{stats['std_reward']:<15.2f} "
              f"{stats['avg_success']:<15.2%}")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Test policy
    test_policy_decisions("models/policy_MarlOS_v1", n_scenarios=5)