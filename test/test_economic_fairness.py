import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
import time

try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from agent.economy.fairness import ProgressiveTaxation
except ImportError:
    # Placeholder class definition for demonstration if module import fails
    print("Warning: ProgressiveTaxation class not found via module path. Using generic stub.")
    class ProgressiveTaxation:
        def __init__(self):
            self.tax_brackets = []
            self.tax_revenue_pool = 0.0
        def calculate_tax(self, wealth: float, earnings: float) -> float:
            rate = self.get_tax_rate(wealth)
            tax = earnings * rate
            self.tax_revenue_pool += tax
            return tax
        def get_tax_rate(self, wealth: float) -> float:
            for threshold, rate in reversed(self.tax_brackets):
                if wealth >= threshold:
                    return rate
            return 0.0


def create_taxation_instance(brackets):
    """Creates a ProgressiveTaxation object with custom brackets."""
    tax = ProgressiveTaxation()
    tax.tax_brackets = brackets
    tax.tax_revenue_pool = 0.0 
    return tax

# --- 1. Define All Tax Policies (Including Policy D) ---

# Policy A: Current Progressive Policy (Max 30%)
POLICY_A_BRACKETS = [
    (0, 0.00), (100, 0.05), (500, 0.10), (1000, 0.15),
    (2000, 0.20), (5000, 0.25), (10000, 0.30), 
]

# Policy B: Flat Tax (10%)
POLICY_B_BRACKETS = [
    (0, 0.10) 
]

# Policy C: Highly Progressive (Max 40%)
POLICY_C_BRACKETS = [
    (0, 0.00), (500, 0.05), (2000, 0.15),
    (5000, 0.30), (15000, 0.40), 
]

# --- Policy D: 20-Bracket Granular Policy ---
POLICY_D_BRACKETS = [(0, 0.00)] # Start at 0%
rate_increment = 0.015  # 1.5% per bracket
wealth_increment = 500  # New bracket every 500 AC

# Generate 20 brackets (1 to 20)
for i in range(1, 21):
    threshold = i * wealth_increment # 500, 1000, 1500, ..., 10000
    rate = i * rate_increment        # 0.015, 0.030, 0.045, ..., 0.300
    POLICY_D_BRACKETS.append((threshold, round(rate, 4)))

# Combine all policies for iteration
POLICIES = {
    'A: Current (Max 30%)': POLICY_A_BRACKETS,
    'B: Flat Tax (10%)': POLICY_B_BRACKETS,
    'C: Highly Progressive (Max 40%)': POLICY_C_BRACKETS,
    'D: 20-Bracket Granular (Max 30%)': POLICY_D_BRACKETS,
}

# --- 2. Simulation Parameters ---
N_AGENTS = 10000
EARNINGS = 100.0 

# Simulate log-normal wealth distribution
# Added a random seed for reproducibility in a simulation context
np.random.seed(42) 
WEALTH = np.exp(np.random.normal(loc=7.5, scale=1.0, size=N_AGENTS)) 
WEALTH = np.clip(WEALTH, 0, 20000) 

# --- 3. Run Simulation and Collect Results ---
results = []
revenue_data = {}

for name, brackets in POLICIES.items():
    tax_engine = create_taxation_instance(brackets)
    total_tax = 0.0
    
    # We need to manually fix the 100.0 boundary for Policy A 
    # to match the previously fixed behavior, just in case the core file hasn't been committed yet.
    if name == 'A: Current (Max 30%)':
        # Simple fix for the 100.0 AC boundary being excluded from 5% bracket start
        tax_engine.tax_brackets = [(0, 0.00), (100.0001, 0.05), (500, 0.10), (1000, 0.15),
                                   (2000, 0.20), (5000, 0.25), (10000, 0.30)]


    for wealth in WEALTH:
        tax_collected = tax_engine.calculate_tax(wealth=wealth, earnings=EARNINGS)
        total_tax += tax_collected
        
        results.append({
            'Policy': name,
            'Wealth': wealth,
            'Tax_Rate': tax_engine.get_tax_rate(wealth) * 100,
            'Tax_Amount': tax_collected
        })
    revenue_data[name] = total_tax

df = pd.DataFrame(results)

# --- 4. Plotting and Analysis ---
sns.set_theme(style="whitegrid")

# Figure 1: Tax Rate vs. Wealth (Highlighting Granularity)
plt.figure(figsize=(12, 7))
sns.lineplot(data=df, x='Wealth', y='Tax_Rate', hue='Policy', errorbar=None, linewidth=2.5)
plt.title('Tax Rate Applied Across Different Wealth Levels (Comparing Granularity)')
plt.xlabel('Agent Wealth (AC)')
plt.ylabel('Tax Rate (%)')
plt.xlim(0, 15000)
plt.ylim(0, 42)
plt.legend(title='Tax Policy')
plt.show() # 

# Figure 2: Revenue Comparison (Best Policy Determination)
revenue_df = pd.DataFrame(list(revenue_data.items()), columns=['Policy', 'Total_Revenue'])
plt.figure(figsize=(10, 6))
sns.barplot(data=revenue_df.sort_values(by='Total_Revenue', ascending=False), 
            x='Policy', y='Total_Revenue', palette='viridis')
plt.title(f'Total Tax Revenue Generated (N={N_AGENTS} Agents, Earnings={EARNINGS} AC)')
plt.ylabel('Total Tax Revenue (AC)')
plt.xlabel('')
plt.xticks(rotation=15)
plt.show() # 

# --- 5. Terminal Conclusion ---
print("\n--- Tax Policy Revenue Analysis ---")
print(revenue_df.sort_values(by='Total_Revenue', ascending=False).to_markdown(index=False))