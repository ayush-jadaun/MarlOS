"""
Token Economy Rules
Implements economic logic, rewards, penalties, and network fees with fairness
"""
from typing import Tuple, Optional
from ..config import TokenConfig

try:
    from ..economy.fairness import EconomicFairnessEngine
except ImportError:
    EconomicFairnessEngine = None


class TokenEconomy:
    """
    Economic rules engine for the token system
    """
    
    def __init__(self, config: TokenConfig, enable_fairness: bool = True):
        self.config = config
        self.reward_pool = 10000.0  # Initial reward pool for bonuses

        # INNOVATION: Economic fairness engine
        if EconomicFairnessEngine and enable_fairness:
            self.fairness_engine = EconomicFairnessEngine()
            print("[ECONOMY] Fairness engine enabled")
        else:
            self.fairness_engine = None
    
    def calculate_job_payment(self, base_payment: float,
                            completion_time: float,
                            deadline: float,
                            success: bool,
                            job: Optional[dict] = None,
                            node_id: Optional[str] = None,
                            node_wealth: Optional[float] = None) -> Tuple[float, float, str]:
        """
        Calculate final payment based on performance
        
        Returns: (payment_amount, bonus_amount, reason)
        """
        if not success:
            return (0.0, 0.0, "Job failed")

        # INNOVATION: Calculate complexity-based payment
        if self.fairness_engine and job and node_id and node_wealth is not None:
            # Use fairness engine for fair payment calculation
            net_payment, tax, reason = self.fairness_engine.calculate_fair_payment(
                base_payment=base_payment,
                job=job,
                node_id=node_id,
                wealth=node_wealth,
                completion_time=completion_time
            )

            # Add tax to reward pool
            self.reward_pool += tax

            # Check for on-time bonus
            time_remaining = deadline - completion_time
            if time_remaining > 0:
                bonus_rate = self.config.success_bonus
                bonus = net_payment * bonus_rate
                if self.reward_pool >= bonus:
                    self.reward_pool -= bonus
                    net_payment += bonus
                    reason += f" + {int(bonus_rate*100)}% on-time bonus"

            return (net_payment, tax, reason)

        # FALLBACK: Original payment calculation
        # Network fee
        network_fee = base_payment * self.config.network_fee
        payment_after_fee = base_payment - network_fee
        
        # Performance bonus/penalty
        time_remaining = deadline - completion_time
        
        if time_remaining > 0:
            # Completed on time - bonus!
            bonus_rate = self.config.success_bonus
            bonus = payment_after_fee * bonus_rate
            
            # Mint from reward pool
            if self.reward_pool >= bonus:
                self.reward_pool -= bonus
                total_payment = payment_after_fee + bonus
                reason = f"On-time completion (+{int(bonus_rate*100)}% bonus)"
            else:
                # Pool depleted, give smaller bonus
                bonus = min(bonus, self.reward_pool)
                self.reward_pool = max(0, self.reward_pool - bonus)
                total_payment = payment_after_fee + bonus
                reason = f"On-time completion (reduced bonus, pool low)"
        
        elif time_remaining > -60:
            # Slightly late (< 1 min) - reduced payment
            penalty_rate = self.config.late_penalty
            penalty = payment_after_fee * penalty_rate
            total_payment = payment_after_fee - penalty
            bonus = -penalty
            reason = f"Late completion (-{int(penalty_rate*100)}% penalty)"
        
        else:
            # Very late - minimal payment
            total_payment = payment_after_fee * 0.5
            bonus = -(payment_after_fee * 0.5)
            reason = "Very late completion (-50% penalty)"
        
        return (total_payment, bonus, reason)
    
    def calculate_stake_requirement(self, job_payment: float, job_priority: float) -> float:
        """
        Calculate required stake for a job
        Higher payment and priority = higher stake
        """
        base_stake = self.config.stake_requirement
        
        # Scale with job payment (10% of payment, min base_stake)
        payment_stake = max(base_stake, job_payment * 0.10)
        
        # Scale with priority
        priority_multiplier = 1.0 + (job_priority * 0.5)  # 1.0x to 1.5x
        
        return payment_stake * priority_multiplier
    
    def calculate_idle_reward(self, hours_idle: float) -> float:
        """
        Calculate reward for being online and idle (available)
        """
        return self.config.idle_reward * hours_idle
    
    def calculate_referral_fee(self, job_payment: float) -> float:
        """
        Calculate referral fee for forwarding a job
        """
        return job_payment * 0.05  # 5% referral fee
    
    def calculate_verification_reward(self, job_payment: float, num_verifiers: int) -> float:
        """
        Calculate reward for each verification node
        """
        total_verification_budget = job_payment * 0.10  # 10% for verification
        return total_verification_budget / num_verifiers
    
    def replenish_reward_pool(self, amount: float):
        """
        Add tokens back to reward pool (from slashed stakes, network fees)
        """
        self.reward_pool += amount
        print(f" [ECONOMY] Reward pool replenished: +{amount:.2f} AC → Pool: {self.reward_pool:.2f} AC")
    
    def get_pool_status(self) -> dict:
        """Get reward pool status"""
        return {
            'reward_pool': self.reward_pool,
            'pool_health': 'healthy' if self.reward_pool > 5000 else 'low'
        }

    def distribute_ubi(self, node_id: str) -> float:
        """
        Distribute UBI to eligible node

        INNOVATION: Universal Basic Income prevents resource starvation

        Returns:
            UBI amount distributed
        """
        if not self.fairness_engine:
            return 0.0

        ubi_amount = self.fairness_engine.distribute_ubi_if_eligible(node_id)

        if ubi_amount > 0:
            print(f"[ECONOMY] UBI distributed to {node_id}: {ubi_amount:.2f} AC")

        return ubi_amount

    def get_fairness_metrics(self) -> dict:
        """Get comprehensive fairness metrics"""
        if self.fairness_engine:
            return self.fairness_engine.get_fairness_metrics()
        return {}
