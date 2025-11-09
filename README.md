<h1 align="center">MarlOS: A Multi-Agent Reinforcement Learning Operating System</h1>
<p align="center">
</p>

[![Built at Hack36](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)


## Introduction:
**MarlOS** is a **decentralized, fairness-aware distributed computing operating system** that removes the need for centralized orchestrators like Kubernetes or cloud controllers.  
It operates as a **peer-to-peer (P2P)** network using **ZeroMQ (PUB/SUB)** for communication — where every node is equal, autonomous, and cryptographically authenticated via **Ed25519 signatures**.  

MarlOS introduces a **Fairness-Aware Economic Layer**, using adaptive tokenomics (**MarlCredits**) to ensure equitable participation and prevent resource monopolies.  
Through **multi-agent reinforcement learning**, nodes learn cooperative bidding, resource sharing, and self-healing behaviors — creating a **self-regulating computational swarm** without any central authority.

---

## Demo Video Link:
<a href="#">Coming Soon</a>

---

## Presentation Link:
<a href="https://docs.google.com/presentation/d/10vXArIEf-o9x8L8SwAFzW25JaCazC9Aice8XeP9UAkM/edit?usp=sharing">PPT Link Here</a>

---

## Table of Contents:
1. [Core Architecture & Network](#core-architecture--network)  
2. [Reinforcement Learning Engine](#reinforcement-learning-engine)  
3. [Economic Fairness Engine](#economic-fairness-engine)  
4. [Job Execution & Management](#job-execution--management)  
5. [Technology Stack](#technology-stack)  
6. [Contributors](#contributors)

---

## Core Architecture & Network
- **Fully Decentralized:** No master node; peer discovery via ZeroMQ gossip protocol.  
- **Cryptographic Security:** Every P2P message is signed using Ed25519 with timestamps and nonces to prevent replay attacks.  
- **Self-Healing:** Detects node failure and automatically migrates active jobs to backup nodes.  
- **Quorum Consensus:** Maintains consistency and prevents double-claims even under network partitions.

---

## Reinforcement Learning Engine
- **RL-Based Bidding:** Each node runs a PPO agent that decides to **Bid**, **Forward**, or **Defer** tasks based on a 25-dimensional state vector representing local and global conditions.  
- **Speculative Execution:** A secondary predictive agent anticipates likely future jobs and executes them in advance for zero-latency responses.

---

## Economic Fairness Engine
- **Token Economy (MarlCredits):** Nodes stake, earn, and spend credits in decentralized job auctions.  
- **Trust & Reputation System:** Each node maintains a 0.0–1.0 trust score; low-trust peers are quarantined automatically.  
- **Progressive Taxation + UBI:** Wealth redistribution mechanisms promote network balance and inclusivity.  
- **Diversity Quotas & Starvation Prevention:** Dynamic bid modifiers ensure all nodes get fair access to jobs.  
- **Proof-of-Work Verification:** Random audits validate completed jobs to deter Byzantine behavior.

---

## Job Execution & Management
- **Extensible Job Runners:** Supports shell, Docker, and cybersecurity tasks (`malware_scan`, `vuln_scan`, `hash_crack`, `forensics`).  
- **Dynamic Complexity Scoring:** Rewards scale (1×–5×) with task difficulty.  
- **Deterministic Coordinator Election:** Transparent synchronization for distributed job allocation.  
- **Self-Healing Runtime:** When a node fails, jobs migrate seamlessly to a verified backup peer.

---

## Technology Stack:
1. **Python** – Core system logic and RL agent implementation  
2. **ZeroMQ** – Decentralized PUB/SUB messaging network  
3. **PyTorch / Stable Baselines3** – Reinforcement learning framework  
4. **Ed25519** – Digital signature and cryptographic authentication  
5. **Docker** – Job containerization and isolated execution  
6. **SQLite / JSON-Ledger** – Local token economy and trust tracking

---

## Contributors:

**Team Name:** async_await

- [Ayush Jadaun](https://github.com/ayushjadaun)
- [Shreeya Srivastava](https://github.com/shreesriv12)
- [Arnav Raj](https://github.com/arnavraj-7)

---

### Made at:
[![Built at Hack36](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)](https://raw.githubusercontent.com/nihal2908/Hack-36-Readme-Template/main/BUILT-AT-Hack36-9-Secure.png)

## For more detailed architecture, look at `docs` and `guides` folder.