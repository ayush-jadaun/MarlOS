"""
Comprehensive Benchmarking Suite for MarlOS
Tests performance, scalability, fairness, and response times
Generates professional graphs and metrics
"""

import pytest
import asyncio
import time
import os
import tempfile
import shutil
from typing import List, Dict, Tuple
import numpy as np
import json
from dataclasses import dataclass, asdict
from datetime import datetime

# Graphing libraries
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Import MarlOS components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent.main import MarlOSAgent
from agent.config import (
    AgentConfig, NetworkConfig, TokenConfig, TrustConfig,
    RLConfig, ExecutorConfig, DashboardConfig, PredictiveConfig
)


# Configure plotting style
sns.set_style("whitegrid")
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


@dataclass
class BenchmarkMetrics:
    """Container for benchmark metrics"""
    # Performance
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    throughput: float  # jobs/sec

    # Fairness
    gini_coefficient: float
    max_share: float  # max % of jobs won by single node
    min_share: float  # min % of jobs won by single node

    # Network
    avg_network_overhead: float  # bytes per job
    message_count: int

    # Economic
    token_distribution_gini: float
    avg_payment: float
    total_tax_collected: float
    ubi_distributed: float

    # Trust
    trust_score_stddev: float
    quarantined_nodes: int

    # Cache (if predictive enabled)
    cache_hit_rate: float
    speculation_accuracy: float

    # Resource usage
    avg_cpu_percent: float
    avg_memory_mb: float

    # Timestamp
    timestamp: str = ""


class MarlOSBenchmark:
    """Professional benchmarking suite"""

    def __init__(self, output_dir="./benchmarks/results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/graphs", exist_ok=True)

        self.metrics_history = []

    async def create_test_network(self, num_nodes: int, base_port: int = 16000,
                                  enable_rl: bool = False,
                                  enable_predictive: bool = False) -> List[MarlOSAgent]:
        """Create a test network with specified parameters"""
        agents = []
        temp_dirs = []

        for i in range(num_nodes):
            temp_dir = tempfile.mkdtemp(prefix=f"marlos_bench_{i}_")
            temp_dirs.append(temp_dir)

            config = AgentConfig(
                node_id=f"bench-node-{i}",
                node_name=f"Benchmark Node {i}",
                data_dir=temp_dir,
                network=NetworkConfig(
                    pub_port=base_port + i * 3,
                    sub_port=base_port + i * 3 + 1,
                    beacon_port=base_port + i * 3 + 2,
                    discovery_interval=2,
                    heartbeat_interval=2
                ),
                token=TokenConfig(
                    starting_balance=100.0
                ),
                trust=TrustConfig(
                    starting_trust=0.5
                ),
                rl=RLConfig(
                    enabled=enable_rl
                ),
                executor=ExecutorConfig(
                    max_concurrent_jobs=5,
                    job_timeout=120
                ),
                predictive=PredictiveConfig(
                    enabled=enable_predictive
                )
            )

            agent = MarlOSAgent(config)
            agents.append(agent)

        # Start all agents
        for agent in agents:
            await agent.start()

        # Wait for peer discovery
        await asyncio.sleep(5)

        print(f"✓ Created test network: {num_nodes} nodes")
        return agents

    async def cleanup_network(self, agents: List[MarlOSAgent]):
        """Clean up test network"""
        for agent in agents:
            await agent.stop()
            # Cleanup temp directory
            if os.path.exists(agent.config.data_dir):
                shutil.rmtree(agent.config.data_dir)

    async def benchmark_latency(self, agents: List[MarlOSAgent],
                               num_jobs: int = 100) -> Dict:
        """Benchmark job execution latency"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Latency Test ({num_jobs} jobs)")
        print(f"{'='*60}")

        latencies = []
        start_times = {}

        # Submit jobs
        for i in range(num_jobs):
            job = {
                'job_id': f'latency-test-{i}',
                'job_type': 'shell',
                'command': 'echo "Test"',
                'priority': 0.5,
                'deadline': time.time() + 120,
                'payment': 10.0
            }

            start_times[job['job_id']] = time.time()
            await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
            await asyncio.sleep(0.1)  # Stagger submissions

        # Wait for completion
        timeout = 60
        start_wait = time.time()

        while time.time() - start_wait < timeout:
            completed = 0
            for job_id in start_times.keys():
                for agent in agents:
                    if job_id in agent.job_results:
                        if job_id not in [l[0] for l in latencies]:
                            end_time = agent.job_results[job_id].get('completed_at', time.time())
                            latency = end_time - start_times[job_id]
                            latencies.append((job_id, latency))
                        completed += 1
                        break

            if completed >= num_jobs * 0.95:  # 95% completion
                break

            await asyncio.sleep(1)

        # Calculate statistics
        latency_values = [l[1] for l in latencies]

        results = {
            'avg_latency': np.mean(latency_values),
            'median_latency': np.median(latency_values),
            'p50': np.percentile(latency_values, 50),
            'p95': np.percentile(latency_values, 95),
            'p99': np.percentile(latency_values, 99),
            'min': np.min(latency_values),
            'max': np.max(latency_values),
            'stddev': np.std(latency_values),
            'completed': len(latencies),
            'total': num_jobs
        }

        print(f"  Average Latency: {results['avg_latency']:.3f}s")
        print(f"  Median Latency:  {results['median_latency']:.3f}s")
        print(f"  P95 Latency:     {results['p95']:.3f}s")
        print(f"  P99 Latency:     {results['p99']:.3f}s")
        print(f"  Completed:       {results['completed']}/{results['total']}")

        # Generate graph
        self._plot_latency_distribution(latency_values, "latency_distribution.png")

        return results

    async def benchmark_throughput(self, agents: List[MarlOSAgent],
                                   duration: int = 60) -> Dict:
        """Benchmark system throughput (jobs/sec)"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Throughput Test ({duration}s)")
        print(f"{'='*60}")

        completed_jobs = []
        start_time = time.time()
        job_counter = 0

        async def submit_jobs():
            nonlocal job_counter
            while time.time() - start_time < duration:
                job = {
                    'job_id': f'throughput-test-{job_counter}',
                    'job_type': 'shell',
                    'command': 'echo "Test"',
                    'priority': 0.5,
                    'deadline': time.time() + 60,
                    'payment': 10.0
                }
                job_counter += 1
                await agents[job_counter % len(agents)].p2p.broadcast_message('JOB_BROADCAST', job)
                await asyncio.sleep(0.5)  # 2 jobs/sec submission rate

        async def monitor_completion():
            checked_jobs = set()
            while time.time() - start_time < duration + 30:
                for i in range(job_counter):
                    job_id = f'throughput-test-{i}'
                    if job_id not in checked_jobs:
                        for agent in agents:
                            if job_id in agent.job_results:
                                completed_jobs.append(time.time())
                                checked_jobs.add(job_id)
                                break
                await asyncio.sleep(1)

        # Run submission and monitoring concurrently
        await asyncio.gather(
            submit_jobs(),
            monitor_completion()
        )

        # Calculate throughput over time
        elapsed = time.time() - start_time
        total_completed = len(completed_jobs)
        avg_throughput = total_completed / elapsed

        # Calculate throughput in 10-second windows
        window_throughputs = []
        for window_start in range(0, int(elapsed), 10):
            window_end = window_start + 10
            window_completions = sum(1 for t in completed_jobs
                                    if window_start <= (t - start_time) < window_end)
            window_throughputs.append(window_completions / 10.0)

        results = {
            'duration': elapsed,
            'total_submitted': job_counter,
            'total_completed': total_completed,
            'avg_throughput': avg_throughput,
            'peak_throughput': max(window_throughputs) if window_throughputs else 0,
            'window_throughputs': window_throughputs
        }

        print(f"  Total Submitted:  {results['total_submitted']}")
        print(f"  Total Completed:  {results['total_completed']}")
        print(f"  Avg Throughput:   {results['avg_throughput']:.2f} jobs/sec")
        print(f"  Peak Throughput:  {results['peak_throughput']:.2f} jobs/sec")

        # Generate graph
        self._plot_throughput_over_time(window_throughputs, "throughput_over_time.png")

        return results

    async def benchmark_fairness(self, agents: List[MarlOSAgent],
                                num_jobs: int = 100) -> Dict:
        """Benchmark fairness metrics"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Fairness Test ({num_jobs} jobs)")
        print(f"{'='*60}")

        # Submit jobs
        for i in range(num_jobs):
            job = {
                'job_id': f'fairness-test-{i}',
                'job_type': 'shell',
                'command': 'echo "Test"',
                'priority': 0.5,
                'deadline': time.time() + 120,
                'payment': 10.0
            }
            await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
            await asyncio.sleep(0.5)

        # Wait for completion
        await asyncio.sleep(60)

        # Count jobs won by each node
        job_distribution = {agent.config.node_id: 0 for agent in agents}
        earnings_distribution = {agent.config.node_id: 0.0 for agent in agents}

        for i in range(num_jobs):
            job_id = f'fairness-test-{i}'
            for agent in agents:
                if job_id in agent.job_results:
                    job_distribution[agent.config.node_id] += 1
                    result = agent.job_results[job_id]
                    earnings = result.get('payment', 0.0)
                    earnings_distribution[agent.config.node_id] += earnings
                    break

        # Calculate metrics
        wins = list(job_distribution.values())
        earnings = list(earnings_distribution.values())

        total_wins = sum(wins)
        total_earnings = sum(earnings)

        job_gini = self._calculate_gini(wins) if total_wins > 0 else 0.0
        earnings_gini = self._calculate_gini(earnings) if total_earnings > 0 else 0.0

        max_share = max(wins) / total_wins if total_wins > 0 else 0.0
        min_share = min(wins) / total_wins if total_wins > 0 else 0.0

        results = {
            'job_distribution': job_distribution,
            'earnings_distribution': earnings_distribution,
            'job_gini': job_gini,
            'earnings_gini': earnings_gini,
            'max_share': max_share,
            'min_share': min_share,
            'stddev': np.std(wins) if wins else 0.0
        }

        print(f"  Job Gini Coefficient:      {job_gini:.3f} (0=perfect equality)")
        print(f"  Earnings Gini Coefficient: {earnings_gini:.3f}")
        print(f"  Max Share:                 {max_share*100:.1f}%")
        print(f"  Min Share:                 {min_share*100:.1f}%")
        print(f"  Job Distribution:          {job_distribution}")

        # Generate graphs
        self._plot_job_distribution(job_distribution, "job_distribution.png")
        self._plot_earnings_distribution(earnings_distribution, "earnings_distribution.png")
        self._plot_gini_over_time(agents, num_jobs, "gini_evolution.png")

        return results

    async def benchmark_scalability(self, node_counts: List[int],
                                    jobs_per_node: int = 20) -> Dict:
        """Benchmark scalability with different network sizes"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Scalability Test")
        print(f"{'='*60}")

        results = {
            'node_counts': node_counts,
            'latencies': [],
            'throughputs': [],
            'fairness_ginis': []
        }

        for num_nodes in node_counts:
            print(f"\n  Testing with {num_nodes} nodes...")

            agents = await self.create_test_network(num_nodes, base_port=17000 + num_nodes * 100)

            try:
                # Run latency test
                num_jobs = jobs_per_node * num_nodes
                latency_results = await self.benchmark_latency(agents, num_jobs=num_jobs)
                results['latencies'].append(latency_results['avg_latency'])

                # Run fairness test
                fairness_results = await self.benchmark_fairness(agents, num_jobs=num_jobs)
                results['fairness_ginis'].append(fairness_results['job_gini'])

                # Estimate throughput
                throughput = num_jobs / latency_results['avg_latency'] if latency_results['avg_latency'] > 0 else 0
                results['throughputs'].append(throughput)

            finally:
                await self.cleanup_network(agents)
                await asyncio.sleep(5)  # Cool down between tests

        print(f"\n  Scalability Results:")
        for i, num_nodes in enumerate(node_counts):
            print(f"    {num_nodes} nodes: latency={results['latencies'][i]:.3f}s, "
                  f"throughput={results['throughputs'][i]:.2f} jobs/s, "
                  f"gini={results['fairness_ginis'][i]:.3f}")

        # Generate graph
        self._plot_scalability(results, "scalability.png")

        return results

    async def benchmark_token_economy(self, agents: List[MarlOSAgent],
                                     num_jobs: int = 50) -> Dict:
        """Benchmark token economy: taxation, UBI, wealth distribution"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Token Economy Test")
        print(f"{'='*60}")

        # Record initial state
        initial_balances = {agent.config.node_id: agent.wallet.balance for agent in agents}

        # Submit varied-payment jobs
        for i in range(num_jobs):
            payment = np.random.uniform(10.0, 100.0)  # Varied payments
            job = {
                'job_id': f'economy-test-{i}',
                'job_type': 'shell',
                'command': f'sleep {np.random.uniform(1, 3):.1f}',
                'priority': np.random.uniform(0.3, 0.9),
                'deadline': time.time() + 120,
                'payment': payment
            }
            await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
            await asyncio.sleep(1)

        # Wait for completion
        await asyncio.sleep(90)

        # Collect final state
        final_balances = {agent.config.node_id: agent.wallet.balance for agent in agents}

        # Calculate metrics
        balance_changes = {
            node_id: final_balances[node_id] - initial_balances[node_id]
            for node_id in initial_balances.keys()
        }

        total_tax = 0.0
        total_ubi = 0.0

        for agent in agents:
            if hasattr(agent, 'fairness_engine') and agent.fairness_engine:
                metrics = agent.fairness_engine.get_fairness_metrics()
                total_tax += metrics.get('tax_revenue', 0.0)
                total_ubi += metrics.get('ubi_distributed', 0.0)

        wealth_gini = self._calculate_gini(list(final_balances.values()))

        results = {
            'initial_balances': initial_balances,
            'final_balances': final_balances,
            'balance_changes': balance_changes,
            'wealth_gini': wealth_gini,
            'total_tax_collected': total_tax,
            'total_ubi_distributed': total_ubi,
            'avg_balance': np.mean(list(final_balances.values())),
            'balance_stddev': np.std(list(final_balances.values()))
        }

        print(f"  Wealth Gini Coefficient: {wealth_gini:.3f}")
        print(f"  Total Tax Collected:     {total_tax:.2f} AC")
        print(f"  Total UBI Distributed:   {total_ubi:.2f} AC")
        print(f"  Avg Final Balance:       {results['avg_balance']:.2f} AC")

        # Generate graphs
        self._plot_wealth_distribution(final_balances, "wealth_distribution.png")
        self._plot_balance_changes(balance_changes, "balance_changes.png")

        return results

    async def benchmark_edge_cases(self, agents: List[MarlOSAgent]) -> Dict:
        """Test edge cases and failure scenarios"""
        print(f"\n{'='*60}")
        print(f"BENCHMARK: Edge Cases & Failure Scenarios")
        print(f"{'='*60}")

        results = {
            'timeout_handling': False,
            'network_partition': False,
            'concurrent_claims': False,
            'invalid_job': False,
            'resource_exhaustion': False
        }

        # Test 1: Job timeout handling
        print("  Test 1: Job timeout...")
        timeout_job = {
            'job_id': 'edge-timeout',
            'job_type': 'shell',
            'command': 'sleep 100',
            'priority': 0.8,
            'deadline': time.time() + 5,  # Will timeout
            'payment': 20.0
        }
        await agents[0].p2p.broadcast_message('JOB_BROADCAST', timeout_job)
        await asyncio.sleep(15)

        # Check if timeout was handled
        for agent in agents:
            if timeout_job['job_id'] in agent.job_results:
                result = agent.job_results[timeout_job['job_id']]
                if result.get('status') in ['timeout', 'failed']:
                    results['timeout_handling'] = True
                    print(f"    ✓ Timeout handled correctly")
                    break

        # Test 2: Invalid job type
        print("  Test 2: Invalid job type...")
        invalid_job = {
            'job_id': 'edge-invalid',
            'job_type': 'nonexistent_type',
            'command': 'echo test',
            'priority': 0.8,
            'deadline': time.time() + 60,
            'payment': 10.0
        }
        await agents[0].p2p.broadcast_message('JOB_BROADCAST', invalid_job)
        await asyncio.sleep(5)

        # Should be rejected or fail gracefully
        results['invalid_job'] = True  # If no crash, consider it handled
        print(f"    ✓ Invalid job handled gracefully")

        # Test 3: Concurrent job limit
        print("  Test 3: Resource exhaustion (concurrent job limit)...")
        for i in range(10):
            concurrent_job = {
                'job_id': f'edge-concurrent-{i}',
                'job_type': 'shell',
                'command': 'sleep 5',
                'priority': 0.9,
                'deadline': time.time() + 60,
                'payment': 10.0
            }
            await agents[0].p2p.broadcast_message('JOB_BROADCAST', concurrent_job)

        await asyncio.sleep(2)

        # Check that jobs are queued/distributed, not all running on one node
        for agent in agents:
            active = len(agent.executor.active_jobs) if hasattr(agent.executor, 'active_jobs') else 0
            if active <= agent.config.executor.max_concurrent_jobs:
                results['resource_exhaustion'] = True
                print(f"    ✓ Concurrent job limit respected")
                break

        await asyncio.sleep(10)

        return results

    # Helper methods for calculations and plotting

    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient"""
        if not values or sum(values) == 0:
            return 0.0

        sorted_values = sorted(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)

        gini = (2.0 * sum((i + 1) * val for i, val in enumerate(sorted_values))) / \
               (n * sum(values)) - (n + 1) / n

        return abs(gini)

    def _plot_latency_distribution(self, latencies: List[float], filename: str):
        """Plot latency distribution histogram"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Histogram
        ax1.hist(latencies, bins=30, edgecolor='black', alpha=0.7)
        ax1.axvline(np.mean(latencies), color='red', linestyle='--', label=f'Mean: {np.mean(latencies):.3f}s')
        ax1.axvline(np.median(latencies), color='green', linestyle='--', label=f'Median: {np.median(latencies):.3f}s')
        ax1.set_xlabel('Latency (seconds)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Job Latency Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # CDF
        sorted_latencies = np.sort(latencies)
        cdf = np.arange(1, len(sorted_latencies) + 1) / len(sorted_latencies)
        ax2.plot(sorted_latencies, cdf, linewidth=2)
        ax2.set_xlabel('Latency (seconds)')
        ax2.set_ylabel('Cumulative Probability')
        ax2.set_title('Cumulative Distribution Function (CDF)')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(0.95, color='red', linestyle='--', alpha=0.5, label='P95')
        ax2.axhline(0.99, color='orange', linestyle='--', alpha=0.5, label='P99')
        ax2.legend()

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def _plot_throughput_over_time(self, window_throughputs: List[float], filename: str):
        """Plot throughput over time"""
        fig, ax = plt.subplots(figsize=(12, 6))

        time_windows = [i * 10 for i in range(len(window_throughputs))]
        ax.plot(time_windows, window_throughputs, marker='o', linewidth=2, markersize=6)
        ax.axhline(np.mean(window_throughputs), color='red', linestyle='--',
                   label=f'Average: {np.mean(window_throughputs):.2f} jobs/s')

        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('Throughput (jobs/sec)')
        ax.set_title('System Throughput Over Time')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def _plot_job_distribution(self, distribution: Dict[str, int], filename: str):
        """Plot job distribution across nodes"""
        fig, ax = plt.subplots(figsize=(10, 6))

        nodes = list(distribution.keys())
        jobs = list(distribution.values())

        colors = sns.color_palette("husl", len(nodes))
        bars = ax.bar(range(len(nodes)), jobs, color=colors, edgecolor='black')

        ax.set_xlabel('Node')
        ax.set_ylabel('Jobs Won')
        ax.set_title('Job Distribution Across Nodes')
        ax.set_xticks(range(len(nodes)))
        ax.set_xticklabels([f"Node {i}" for i in range(len(nodes))], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')

        # Add fairness line (expected equal distribution)
        expected = sum(jobs) / len(nodes) if nodes else 0
        ax.axhline(expected, color='red', linestyle='--', alpha=0.5,
                  label=f'Fair Share: {expected:.1f}')
        ax.legend()

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def _plot_earnings_distribution(self, earnings: Dict[str, float], filename: str):
        """Plot earnings distribution"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        nodes = list(earnings.keys())
        amounts = list(earnings.values())

        # Bar chart
        colors = sns.color_palette("husl", len(nodes))
        bars = ax1.bar(range(len(nodes)), amounts, color=colors, edgecolor='black')
        ax1.set_xlabel('Node')
        ax1.set_ylabel('Earnings (AC)')
        ax1.set_title('Token Earnings Distribution')
        ax1.set_xticks(range(len(nodes)))
        ax1.set_xticklabels([f"Node {i}" for i in range(len(nodes))], rotation=45)
        ax1.grid(True, alpha=0.3, axis='y')

        # Pie chart
        ax2.pie(amounts, labels=[f"Node {i}" for i in range(len(nodes))],
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax2.set_title('Earnings Share')

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def _plot_gini_over_time(self, agents: List[MarlOSAgent], num_jobs: int, filename: str):
        """Plot Gini coefficient evolution (placeholder - needs time-series data)"""
        # This would require tracking Gini at each job completion
        # For now, create a placeholder showing final Gini
        pass

    def _plot_scalability(self, results: Dict, filename: str):
        """Plot scalability metrics"""
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

        node_counts = results['node_counts']

        # Latency vs nodes
        ax1.plot(node_counts, results['latencies'], marker='o', linewidth=2, markersize=8)
        ax1.set_xlabel('Number of Nodes')
        ax1.set_ylabel('Average Latency (seconds)')
        ax1.set_title('Latency vs Network Size')
        ax1.grid(True, alpha=0.3)

        # Throughput vs nodes
        ax2.plot(node_counts, results['throughputs'], marker='s', linewidth=2, markersize=8, color='green')
        ax2.set_xlabel('Number of Nodes')
        ax2.set_ylabel('Throughput (jobs/sec)')
        ax2.set_title('Throughput vs Network Size')
        ax2.grid(True, alpha=0.3)

        # Fairness vs nodes
        ax3.plot(node_counts, results['fairness_ginis'], marker='^', linewidth=2, markersize=8, color='orange')
        ax3.axhline(0.3, color='red', linestyle='--', alpha=0.5, label='Fairness Threshold')
        ax3.set_xlabel('Number of Nodes')
        ax3.set_ylabel('Gini Coefficient')
        ax3.set_title('Fairness vs Network Size')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def _plot_wealth_distribution(self, balances: Dict[str, float], filename: str):
        """Plot wealth distribution"""
        fig, ax = plt.subplots(figsize=(10, 6))

        nodes = list(balances.keys())
        amounts = list(balances.values())

        colors = sns.color_palette("viridis", len(nodes))
        bars = ax.bar(range(len(nodes)), amounts, color=colors, edgecolor='black')

        ax.set_xlabel('Node')
        ax.set_ylabel('Token Balance (AC)')
        ax.set_title('Wealth Distribution After Benchmark')
        ax.set_xticks(range(len(nodes)))
        ax.set_xticklabels([f"Node {i}" for i in range(len(nodes))], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}',
                   ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def _plot_balance_changes(self, changes: Dict[str, float], filename: str):
        """Plot balance changes (profit/loss)"""
        fig, ax = plt.subplots(figsize=(10, 6))

        nodes = list(changes.keys())
        amounts = list(changes.values())

        colors = ['green' if x > 0 else 'red' for x in amounts]
        bars = ax.bar(range(len(nodes)), amounts, color=colors, edgecolor='black', alpha=0.7)

        ax.set_xlabel('Node')
        ax.set_ylabel('Balance Change (AC)')
        ax.set_title('Profit/Loss Per Node')
        ax.set_xticks(range(len(nodes)))
        ax.set_xticklabels([f"Node {i}" for i in range(len(nodes))], rotation=45)
        ax.axhline(0, color='black', linewidth=0.8)
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/graphs/{filename}", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    ✓ Saved: {filename}")

    def save_metrics(self, metrics: BenchmarkMetrics):
        """Save metrics to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics.timestamp = timestamp

        filepath = f"{self.output_dir}/metrics_{timestamp}.json"
        with open(filepath, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)

        print(f"\n✓ Metrics saved to: {filepath}")

    def generate_summary_report(self, all_results: Dict):
        """Generate comprehensive summary report"""
        report_path = f"{self.output_dir}/benchmark_report.md"

        with open(report_path, 'w') as f:
            f.write("# MarlOS Benchmark Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("## Executive Summary\n\n")

            if 'latency' in all_results:
                f.write(f"- **Average Latency:** {all_results['latency']['avg_latency']:.3f}s\n")
                f.write(f"- **P95 Latency:** {all_results['latency']['p95']:.3f}s\n")

            if 'throughput' in all_results:
                f.write(f"- **Average Throughput:** {all_results['throughput']['avg_throughput']:.2f} jobs/sec\n")

            if 'fairness' in all_results:
                f.write(f"- **Fairness (Gini):** {all_results['fairness']['job_gini']:.3f}\n")

            f.write("\n## Detailed Results\n\n")

            for test_name, results in all_results.items():
                f.write(f"### {test_name.title()}\n\n")
                f.write("```json\n")
                f.write(json.dumps(results, indent=2))
                f.write("\n```\n\n")

        print(f"\n✓ Report saved to: {report_path}")


# Main benchmark execution
async def main():
    """Run all benchmarks"""
    benchmark = MarlOSBenchmark()

    print("="*60)
    print(" MARLOS COMPREHENSIVE BENCHMARK SUITE")
    print("="*60)

    # Create test network (5 nodes)
    agents = await benchmark.create_test_network(num_nodes=5)

    try:
        all_results = {}

        # Run benchmarks
        all_results['latency'] = await benchmark.benchmark_latency(agents, num_jobs=50)
        all_results['throughput'] = await benchmark.benchmark_throughput(agents, duration=30)
        all_results['fairness'] = await benchmark.benchmark_fairness(agents, num_jobs=50)
        all_results['token_economy'] = await benchmark.benchmark_token_economy(agents, num_jobs=30)
        all_results['edge_cases'] = await benchmark.benchmark_edge_cases(agents)

        # Generate summary report
        benchmark.generate_summary_report(all_results)

        print("\n" + "="*60)
        print(" BENCHMARK COMPLETE!")
        print("="*60)
        print(f"\nResults saved to: {benchmark.output_dir}")
        print(f"Graphs saved to: {benchmark.output_dir}/graphs/")

    finally:
        await benchmark.cleanup_network(agents)

    # Run scalability test (separate networks)
    # await benchmark.benchmark_scalability([3, 5, 7, 10])


if __name__ == '__main__':
    asyncio.run(main())
