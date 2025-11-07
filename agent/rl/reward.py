"""
RL Reward Calculation
Calculates rewards for RL policy based on job outcomes
"""
import time
from typing import Tuple


class RewardCalculator:
    """
    Calculates rewards for reinforcement learning
    """
    
    def __init__(self):
        # Reward weights
        self.SUCCESS_REWARD = 1.0
        self.FAILURE_PENALTY = -1.0
        self.TIMEOUT_PENALTY = -0.5
        self.LATE_PENALTY = -0.3
        
        # Bonus rewards
        self.ON_TIME_BONUS = 0.5
        self.TRUST_IMPROVEMENT_BONUS = 0.2
        self.TOKEN_PROFIT_WEIGHT = 0.01  # Small weight for token profit
        
        # Opportunity cost
        self.DEFER_COST = -0.1  # Cost of not bidding
        self.FORWARD_REWARD = 0.2  # Reward for smart forwarding
    
    def calculate_job_reward(self, 
                            success: bool,
                            completion_time: float,
                            deadline: float,
                            start_time: float,
                            trust_delta: float,
                            token_delta: float) -> Tuple[float, str]:
        """
        Calculate reward for job execution
        
        Returns: (reward, reason)
        """
        reward = 0.0
        reasons = []
        
        if success:
            # Base success reward
            reward += self.SUCCESS_REWARD
            reasons.append("success")
            
            # Time-based bonus/penalty
            actual_time = completion_time - start_time
            time_remaining = deadline - completion_time
            
            if time_remaining > 0:
                # Completed on time
                reward += self.ON_TIME_BONUS
                reasons.append("on_time")
                
                # Extra bonus for finishing early
                time_efficiency = time_remaining / (deadline - start_time)
                early_bonus = time_efficiency * 0.3
                reward += early_bonus
                reasons.append(f"early_bonus_{early_bonus:.2f}")
            else:
                # Late completion
                reward += self.LATE_PENALTY
                reasons.append("late")
        
        else:
            # Failure
            reward += self.FAILURE_PENALTY
            reasons.append("failure")
            
            # Check if timeout
            if time.time() > deadline:
                reward += self.TIMEOUT_PENALTY
                reasons.append("timeout")
        
        # Trust score improvement
        if trust_delta > 0:
            reward += trust_delta * self.TRUST_IMPROVEMENT_BONUS
            reasons.append(f"trust_up_{trust_delta:.3f}")
        elif trust_delta < 0:
            reward += trust_delta * 2.0  # Amplify trust loss
            reasons.append(f"trust_down_{trust_delta:.3f}")
        
        # Token profit (small influence)
        if token_delta > 0:
            profit_reward = min(0.5, token_delta * self.TOKEN_PROFIT_WEIGHT)
            reward += profit_reward
            reasons.append(f"profit_{token_delta:.1f}AC")
        elif token_delta < 0:
            loss_penalty = max(-0.5, token_delta * self.TOKEN_PROFIT_WEIGHT)
            reward += loss_penalty
            reasons.append(f"loss_{abs(token_delta):.1f}AC")
        
        reason_str = " + ".join(reasons)
        return (reward, reason_str)
    
    def calculate_bid_reward(self, won_bid: bool, was_good_match: bool) -> float:
        """
        Reward for bidding decision itself
        """
        if won_bid and was_good_match:
            return 0.1  # Small reward for winning good matches
        elif won_bid and not was_good_match:
            return -0.1  # Penalty for winning bad matches
        elif not won_bid and was_good_match:
            return -0.05  # Small penalty for missing good opportunities
        else:
            return 0.0  # No reward for correctly avoiding bad matches
    
    def calculate_forward_reward(self, 
                                forwarded_successfully: bool,
                                referral_fee: float) -> Tuple[float, str]:
        """
        Reward for forwarding job to better peer
        """
        if forwarded_successfully:
            reward = self.FORWARD_REWARD + (referral_fee * 0.01)
            return (reward, f"forward_success +{referral_fee:.1f}AC")
        else:
            return (-0.1, "forward_failed")
    
    def calculate_defer_reward(self, 
                              deferred_correctly: bool,
                              missed_opportunity: bool) -> Tuple[float, str]:
        """
        Reward for deferring a job
        """
        if deferred_correctly:
            # Correctly avoided a job we couldn't handle
            return (0.05, "defer_correct")
        elif missed_opportunity:
            # Should have bid but didn't
            return (self.DEFER_COST, "defer_missed_opportunity")
        else:
            # Neutral defer
            return (0.0, "defer_neutral")
    
    def normalize_reward(self, reward: float) -> float:
        """
        Normalize reward to reasonable range (-2, 2)
        """
        return max(-2.0, min(2.0, reward))
