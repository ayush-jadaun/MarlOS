# MarlOS Economic Model: Fairness-Aware Token Economics for Decentralized Compute

**Version 1.0 | March 2026**

## Abstract

MarlOS introduces a token-based economic model for decentralized compute markets where autonomous agents bid for jobs using reinforcement learning. Traditional distributed systems use static schedulers or simple heuristics; MarlOS embeds fairness directly into the economic protocol through progressive taxation, universal basic income (UBI), affirmative action bidding, and Gini coefficient monitoring. This paper formalizes the token supply model, incentive mechanisms, and presents simulation results proving stability and fairness.

---

## 1. Introduction

Decentralized compute networks face a fundamental tension: **efficiency vs. fairness**. Without intervention, rational agents converge on monopolistic equilibria where a few high-capability nodes capture most jobs, leaving others idle. This creates fragility (single points of failure) and discourages participation (why join if you never win?).

MarlOS addresses this through a multi-layered economic system:

1. **Token economy** — MarlCredits (AC) as the unit of account
2. **Stake/slash** — skin in the game for every job
3. **Progressive taxation** — wealth-proportional contributions
4. **Universal Basic Income** — redistribution to low-wealth nodes
5. **Affirmative action** — bid boosts for underutilized nodes
6. **Gini monitoring** — system-wide inequality as a health metric

---

## 2. Token Supply Model

### 2.1 MarlCredits (AC)

Each node starts with an initial balance of **100 AC** (configurable). There is no fixed total supply — tokens are minted through job completion bonuses and UBI, and burned through failed stakes and network fees.

| Parameter | Default | Purpose |
|---|---|---|
| Starting balance | 100.0 AC | Initial endowment per node |
| Network fee | 5% of payment | Funds network operations |
| Success bonus | 20% of payment | Rewards on-time completion |
| Late penalty | 10% of payment | Deducted for late jobs |
| Failure penalty | 100% of stake | Full stake loss on failure |
| Idle reward | 1.0 AC/hour | Incentivizes staying online |

### 2.2 Token Flow

```
Job Submitter --[payment]--> Auction Winner
                              |
                     [stake deducted]
                              |
                    [job execution]
                        /          \
                   success         failure
                  /                     \
           [stake returned]      [stake burned]
           [payment + 20% bonus]  [to tax pool]
           [tax deducted]
                 |
          [tax pool] --[UBI]--> low-wealth nodes
```

---

## 3. Stake/Slash Mechanism

Every job requires a **stake** — tokens locked before execution that are returned on success or slashed on failure.

**Stake formula:**

```
stake = payment * 0.25 * (1 + priority)
```

Where `priority` is 0.0-1.0. High-priority jobs require more stake, increasing skin in the game.

**Slash conditions:**
- Job timeout → 100% stake burned
- Job failure → 100% stake burned
- Malicious behavior → 100% stake + additional trust penalty

**This mechanism:**
- Prevents spam bidding (must risk real tokens)
- Discourages malicious nodes (loss exceeds potential gain)
- Creates economic pressure for reliability

---

## 4. Progressive Taxation

Nodes pay tax on earnings proportional to their total wealth.

| Wealth Bracket | Tax Rate |
|---|---|
| 0 – 100 AC | 0% |
| 100 – 500 AC | 5% |
| 500 – 1,000 AC | 10% |
| 1,000 – 2,000 AC | 15% |
| 2,000 – 5,000 AC | 20% |
| 5,000 – 10,000 AC | 25% |
| 10,000+ AC | 30% |

**Properties:**
- New nodes (< 100 AC) pay zero tax, maximizing early growth
- Wealthy nodes contribute proportionally more
- Tax revenue funds the UBI pool
- Brackets are configurable per-network

---

## 5. Universal Basic Income (UBI)

Periodically, the tax revenue pool is distributed to nodes below median wealth.

**Distribution rules:**
1. Triggered every N jobs (default: 50)
2. 50% of tax pool distributed per cycle
3. Only nodes below median wealth are eligible
4. Equal distribution among eligible nodes

**Purpose:**
- Prevents wealth starvation
- Keeps low-capability nodes economically viable
- Encourages continued participation
- Smooths out variance from bad luck

---

## 6. Affirmative Action Bidding

Nodes that have never won a job receive a **bid score boost** in auctions.

```
if node.jobs_won == 0 and network_age > threshold:
    bid_score += affirmative_boost  # default: 0.15-0.2
```

Additionally, nodes with wealth below the starting balance receive a smaller boost:

```
if node.balance < starting_balance:
    bid_score += low_wealth_boost  # default: 0.1
```

**This ensures:**
- New nodes aren't permanently locked out
- The "cold start problem" has a defined solution
- Diversity of execution is maintained

---

## 7. Gini Coefficient as System Health

The Gini coefficient measures wealth inequality on a 0-1 scale (0 = perfect equality, 1 = one node has everything).

MarlOS computes Gini across all node balances and includes it in the RL state vector (dimension 23 of the 25D state). The PPO policy can observe inequality and factor it into bidding decisions.

**Health interpretation:**
| Gini | Interpretation |
|---|---|
| < 0.2 | Very fair |
| 0.2 – 0.3 | Fair |
| 0.3 – 0.5 | Moderate inequality |
| 0.5 – 0.7 | High inequality |
| > 0.7 | Critical — system is monopolized |

---

## 8. Simulation Results

We simulated 100 nodes processing 1,000 jobs, comparing fairness ON vs OFF.

### 8.1 Setup
- 100 nodes with normally distributed capabilities (mean=0.5, std=0.15)
- 1,000 jobs with random payments (20-100 AC) and priorities (0.3-0.9)
- Seed fixed for reproducibility (seed=42)

### 8.2 Results

| Metric | Fairness ON | Fairness OFF |
|---|---|---|
| **Gini Coefficient** | **0.549** | 0.822 |
| **Participation Rate** | **100%** | 27% |
| Min Balance | 314 AC | 79 AC |
| Max Balance | 13,633 AC | 19,063 AC |
| Median Balance | 325 AC | 100 AC |
| Nodes < 10 AC | 0 | 0 |

### 8.3 Key Findings

1. **33% reduction in inequality** — Gini drops from 0.822 to 0.549
2. **100% participation vs 27%** — Every node wins at least one job with fairness
3. **No starvation** — Minimum balance is 314 AC (3x starting balance) with fairness
4. **Median wealth grows** — 325 AC vs 100 AC, indicating broad-based wealth creation
5. **Top earners still rewarded** — Maximum balance is 13,633 AC, showing that skill is still rewarded

### 8.4 Charts

See `docs/charts/` for:
- `gini_over_time.png` — Inequality trajectory comparison
- `wealth_distribution.png` — Final wealth histograms
- `participation.png` — Node participation rates
- `job_distribution.png` — Job win distribution

---

## 9. Adversarial Resistance

We tested with 10 honest + 3 malicious nodes over 100 jobs.

**Malicious behavior:** 80% chance of failing/returning garbage, 20% chance of honest execution (to avoid immediate detection).

**Results:**
- **Detection rate: 100%** — All 3 malicious nodes quarantined
- **False positive rate: 0%** — No honest nodes incorrectly quarantined
- **Detection speed:** First malicious node quarantined at job 17, all by job 90

The trust decay system (penalty of 0.05 per failure, 0.50 for detected malice, quarantine threshold at 0.2) provides robust detection while tolerating honest failures.

---

## 10. Online Learning Integration

The economic model integrates with the PPO reinforcement learning policy:

**RL State Vector (25 dimensions):**
- Dimensions 0-4: Agent state (load, capacity, balance, trust, stake)
- Dimensions 5-9: Job features (type, priority, payment, deadline, complexity)
- Dimensions 10-14: Historical performance (win rate, avg reward, etc.)
- Dimensions 15-17: Network state (peers, latency, congestion)
- Dimensions 18-24: **Fairness features** (Gini, own percentile, tax rate, UBI eligible, diversity score, starvation indicator, wealth ratio)

The policy learns to:
- Bid aggressively on high-payment jobs when trust and balance are high
- Defer when the network is congested or the node is under-resourced
- Account for fairness metrics in bidding decisions

**Online learning results (500 jobs):**
- Win rate improved from 52% to 61% (+9pp)
- Exploration decayed from 0.10 to 0.01
- Bid threshold adapted from 0.5 to 0.6

---

## 11. Design Principles

1. **No free lunch** — Every job requires stake. No risk-free income except UBI.
2. **Meritocratic with guardrails** — Capable nodes earn more, but not everything.
3. **Self-correcting** — Inequality triggers redistribution automatically.
4. **Observable** — Gini coefficient makes system health visible and measurable.
5. **Configurable** — All parameters (tax brackets, UBI frequency, stake ratios) are per-network configurable.
6. **Byzantine tolerant** — Malicious nodes are economically punished (stake loss + quarantine).

---

## 12. Limitations and Future Work

- **No cross-network token transfers** — Tokens are local to each network
- **No formal game-theoretic proof of equilibrium** — Simulation evidence only
- **UBI may create free-rider incentives** — Mitigated by minimum participation requirements
- **Tax brackets may need dynamic adjustment** — Currently static
- **Sybil attacks** — Partially mitigated by stake requirements and subnet limits in public mode

Future work includes formal Nash equilibrium analysis, dynamic tax bracket adjustment based on network size, and cross-network token bridges.

---

## References

1. Sutton & Barto. *Reinforcement Learning: An Introduction*. MIT Press, 2018.
2. Schulman et al. *Proximal Policy Optimization Algorithms*. arXiv:1707.06347, 2017.
3. Piketty, T. *Capital in the Twenty-First Century*. Harvard University Press, 2014.
4. Gini, C. *Variabilità e mutabilità*. 1912.

---

*This document describes the MarlOS economic model as implemented in v1.0. Parameters and mechanisms are subject to change as the system evolves.*
