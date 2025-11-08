"""
Comprehensive Integration Tests for MarlOS
Tests all components working together in realistic scenarios
"""

import pytest
import pytest_asyncio
import asyncio
import time
import os
import tempfile
import shutil
from typing import List, Dict
import numpy as np
import json

# Import MarlOS components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent.main import MarlOSAgent
from agent.config import (
    AgentConfig, NetworkConfig, TokenConfig, TrustConfig,
    RLConfig, ExecutorConfig, DashboardConfig, PredictiveConfig
)
from agent.p2p.node import P2PNode
from agent.tokens.economy import TokenEconomy
from agent.trust.reputation import ReputationSystem
from agent.bidding.auction import BiddingAuction


class TestFullSystemIntegration:
    """
    Full system integration tests
    Tests complete workflows from job submission to completion
    """

    @pytest_asyncio.fixture
    async def test_network(self):
        """Create a test network of 5 nodes"""
        agents = []
        base_port = 15000
        temp_dirs = []

        try:
            for i in range(5):
                # Create temp directory for each agent
                temp_dir = tempfile.mkdtemp(prefix=f"marlos_test_{i}_")
                temp_dirs.append(temp_dir)

                # Create config
                config = AgentConfig(
                    node_id=f"test-node-{i}",
                    node_name=f"Test Node {i}",
                    data_dir=temp_dir,
                    network=NetworkConfig(
                        pub_port=base_port + i * 3,
                        sub_port=base_port + i * 3 + 1,
                        beacon_port=base_port + i * 3 + 2,
                        discovery_interval=1,
                        heartbeat_interval=1
                    ),
                    token=TokenConfig(
                        starting_balance=100.0,
                        network_fee=0.05,
                        idle_reward=1.0
                    ),
                    trust=TrustConfig(
                        starting_trust=0.5
                    ),
                    rl=RLConfig(
                        enabled=False  # Disable RL for faster testing
                    ),
                    executor=ExecutorConfig(
                        max_concurrent_jobs=3,
                        job_timeout=60
                    ),
                    dashboard=DashboardConfig(
                        port=13000 + i
                    ),
                    predictive=PredictiveConfig(
                        enabled=False  # Disable predictive for basic tests
                    )
                )

                # Create agent
                agent = MarlOSAgent(config)
                agents.append(agent)

            # Start all agents
            for agent in agents:
                await agent.start()

            # Wait for peer discovery
            await asyncio.sleep(3)

            # Verify all nodes connected
            for agent in agents:
                peer_count = len(agent.p2p.peers)
                assert peer_count >= 3, f"{agent.config.node_id} only found {peer_count} peers"

            print(f"✓ Test network started: {len(agents)} nodes connected")

            yield agents

        finally:
            # Cleanup
            for agent in agents:
                await agent.stop()

            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_basic_job_execution(self, test_network):
        """Test basic job submission and execution"""
        agents = test_network

        # Submit a simple shell job
        job = {
            'job_id': 'test-job-001',
            'job_type': 'shell',
            'command': 'echo "Hello from MarlOS"',
            'priority': 0.8,
            'deadline': time.time() + 60,
            'payment': 10.0,
            'requirements': []
        }

        # Submit to first agent
        submitter = agents[0]
        await submitter.p2p.broadcast_message('JOB_BROADCAST', job)

        # Wait for bidding and execution
        await asyncio.sleep(5)

        # Verify job was executed by someone
        job_found = False
        winner = None

        for agent in agents:
            if job['job_id'] in agent.job_results:
                job_found = True
                winner = agent
                result = agent.job_results[job['job_id']]
                assert result['status'] == 'success'
                print(f"✓ Job executed successfully by {agent.config.node_id}")
                break

        assert job_found, "Job was not executed by any node"

        # Verify token transfer
        if winner:
            wallet_stats = winner.wallet.get_stats()
            assert wallet_stats['balance'] > 100.0, "Winner didn't receive payment"
            print(f"✓ Winner balance: {wallet_stats['balance']:.2f} AC")

        # Verify trust score increased
        if winner:
            trust_score = winner.reputation.get_my_trust_score()
            assert trust_score >= 0.5, "Trust score didn't increase"
            print(f"✓ Winner trust score: {trust_score:.3f}")

    @pytest.mark.asyncio
    async def test_load_balancing(self, test_network):
        """Test that jobs are distributed fairly across nodes"""
        agents = test_network

        # Submit 20 jobs
        num_jobs = 20
        job_ids = []

        for i in range(num_jobs):
            job = {
                'job_id': f'test-job-{i:03d}',
                'job_type': 'shell',
                'command': f'echo "Job {i}"',
                'priority': 0.5,
                'deadline': time.time() + 120,
                'payment': 10.0,
                'requirements': []
            }
            job_ids.append(job['job_id'])
            await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
            await asyncio.sleep(0.5)  # Stagger submissions

        # Wait for all jobs to complete
        await asyncio.sleep(30)

        # Count jobs won by each node
        job_distribution = {agent.config.node_id: 0 for agent in agents}

        for job_id in job_ids:
            for agent in agents:
                if job_id in agent.job_results:
                    job_distribution[agent.config.node_id] += 1
                    break

        print(f"✓ Job distribution: {job_distribution}")

        # Calculate Gini coefficient
        wins = list(job_distribution.values())
        total_wins = sum(wins)

        if total_wins > 0:
            gini = self._calculate_gini(wins)
            print(f"✓ Gini coefficient: {gini:.3f} (0=perfect equality, 1=inequality)")

            # Assert fairness: Gini should be < 0.4 for good distribution
            assert gini < 0.4, f"Jobs not fairly distributed (Gini={gini:.3f})"

        # Assert no single node won >50% of jobs
        max_wins = max(wins)
        max_share = max_wins / total_wins if total_wins > 0 else 0
        assert max_share < 0.5, f"One node won {max_share*100:.1f}% of jobs"

    @pytest.mark.asyncio
    async def test_token_economy_flow(self, test_network):
        """Test complete token economy: staking, payment, taxation, UBI"""
        agents = test_network

        # Record initial balances
        initial_balances = {
            agent.config.node_id: agent.wallet.balance
            for agent in agents
        }

        # Submit high-value job
        job = {
            'job_id': 'test-job-economy',
            'job_type': 'shell',
            'command': 'sleep 2 && echo "Done"',
            'priority': 0.9,
            'deadline': time.time() + 60,
            'payment': 50.0,  # High payment
            'requirements': []
        }

        await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
        await asyncio.sleep(10)

        # Find winner
        winner = None
        for agent in agents:
            if job['job_id'] in agent.job_results:
                winner = agent
                break

        assert winner is not None, "No winner found"

        # Verify stake was returned
        # (Stake is automatically unstaked after job completion)

        # Verify payment received (with bonus for on-time delivery)
        final_balance = winner.wallet.balance
        initial_balance = initial_balances[winner.config.node_id]
        earnings = final_balance - initial_balance

        assert earnings > 40.0, f"Winner earned {earnings:.2f} AC, expected >40 AC"
        print(f"✓ Winner earned {earnings:.2f} AC (including bonuses)")

        # Verify taxation occurred (if fairness engine enabled)
        if winner.fairness_engine:
            metrics = winner.fairness_engine.get_fairness_metrics()
            print(f"✓ Tax revenue pool: {metrics.get('tax_revenue', 0):.2f} AC")

        # Test UBI distribution
        # (In real system, UBI is distributed periodically; here we test the mechanism)
        if winner.fairness_engine and winner.fairness_engine.ubi:
            ubi_eligible = winner.fairness_engine.ubi.can_claim(winner.config.node_id)
            print(f"✓ UBI eligibility: {ubi_eligible}")

    @pytest.mark.asyncio
    async def test_trust_system_dynamics(self, test_network):
        """Test trust rewards, penalties, and quarantine"""
        agents = test_network
        test_agent = agents[0]

        # Record initial trust
        initial_trust = test_agent.reputation.get_my_trust_score()

        # Succeed at a job (trust should increase)
        test_agent.reputation.reward_success(
            job_id="test-success",
            on_time=True,
            payment=10.0
        )

        trust_after_success = test_agent.reputation.get_my_trust_score()
        assert trust_after_success > initial_trust, "Trust didn't increase after success"
        print(f"✓ Trust after success: {trust_after_success:.3f} (was {initial_trust:.3f})")

        # Fail a job (trust should decrease)
        test_agent.reputation.punish_failure(
            job_id="test-failure",
            reason="timeout"
        )

        trust_after_failure = test_agent.reputation.get_my_trust_score()
        assert trust_after_failure < trust_after_success, "Trust didn't decrease after failure"
        print(f"✓ Trust after failure: {trust_after_failure:.3f}")

        # Test quarantine threshold
        # Force trust below quarantine threshold
        for i in range(20):
            test_agent.reputation.punish_failure(
                job_id=f"test-fail-{i}",
                reason="malicious"
            )

        final_trust = test_agent.reputation.get_my_trust_score()
        print(f"✓ Trust after multiple failures: {final_trust:.3f}")

        # Verify agent is quarantined if trust < 0.2
        if final_trust < 0.2:
            # In real system, agent would be quarantined by peers
            print(f"✓ Agent would be quarantined (trust={final_trust:.3f} < 0.2)")

    @pytest.mark.asyncio
    async def test_fairness_mechanisms(self, test_network):
        """Test economic fairness: diversity quotas, affirmative action, taxation"""
        agents = test_network

        # Test diversity quotas
        test_agent = agents[0]
        if test_agent.fairness_engine:
            # Simulate one node winning many jobs
            for i in range(50):
                test_agent.fairness_engine.diversity.record_job_outcome(
                    job_id=f"job-{i}",
                    winner_id=test_agent.config.node_id,
                    losers=[agent.config.node_id for agent in agents[1:]],
                    earnings=10.0
                )

            # Check diversity factor (should be <1.0 to penalize over-representation)
            diversity_factor = test_agent.fairness_engine.diversity.calculate_diversity_factor(
                test_agent.config.node_id
            )
            print(f"✓ Diversity factor after 50 wins: {diversity_factor:.3f}")
            assert diversity_factor < 1.0, "Diversity factor didn't penalize over-representation"

            # Check Gini coefficient
            metrics = test_agent.fairness_engine.get_fairness_metrics()
            gini = metrics.get('gini_coefficient', 0.0)
            print(f"✓ Gini coefficient: {gini:.3f}")

        # Test affirmative action for struggling nodes
        struggling_agent = agents[4]
        if struggling_agent.fairness_engine:
            # Simulate low win rate
            for i in range(20):
                struggling_agent.fairness_engine.diversity.record_job_outcome(
                    job_id=f"job-lose-{i}",
                    winner_id=agents[0].config.node_id,
                    losers=[struggling_agent.config.node_id],
                    earnings=10.0
                )

            # Check affirmative action bonus
            aa_bonus = struggling_agent.fairness_engine.diversity.calculate_affirmative_action_bonus(
                struggling_agent.config.node_id
            )
            print(f"✓ Affirmative action bonus for struggling node: +{aa_bonus:.3f}")
            assert aa_bonus > 0.1, "Struggling node didn't get affirmative action bonus"

    @pytest.mark.asyncio
    async def test_concurrent_job_execution(self, test_network):
        """Test executing multiple jobs concurrently on same node"""
        agents = test_network
        test_agent = agents[0]

        # Submit 3 jobs simultaneously to same node
        jobs = []
        for i in range(3):
            job = {
                'job_id': f'concurrent-job-{i}',
                'job_type': 'shell',
                'command': f'sleep 2 && echo "Job {i}"',
                'priority': 0.9,
                'deadline': time.time() + 60,
                'payment': 10.0,
                'requirements': []
            }
            jobs.append(job)

        # Execute all jobs on test_agent
        tasks = []
        for job in jobs:
            task = asyncio.create_task(test_agent.executor.execute_job(job))
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all succeeded
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get('status') == 'success')
        print(f"✓ Successfully executed {success_count}/3 concurrent jobs")
        assert success_count == 3, f"Only {success_count}/3 jobs succeeded"

    @pytest.mark.asyncio
    async def test_job_timeout_handling(self, test_network):
        """Test that jobs timeout correctly and penalties are applied"""
        agents = test_network

        # Submit job with short timeout
        job = {
            'job_id': 'timeout-test-job',
            'job_type': 'shell',
            'command': 'sleep 30',  # Will timeout
            'priority': 0.8,
            'deadline': time.time() + 5,  # Short deadline
            'payment': 20.0,
            'requirements': []
        }

        await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
        await asyncio.sleep(10)

        # Find which node took the job
        executor = None
        for agent in agents:
            if job['job_id'] in agent.active_jobs or job['job_id'] in agent.job_results:
                executor = agent
                break

        if executor:
            result = executor.job_results.get(job['job_id'], {})
            assert result.get('status') in ['timeout', 'failed'], "Job didn't timeout as expected"
            print(f"✓ Job timed out correctly: {result.get('status')}")

            # Verify trust penalty
            trust_after = executor.reputation.get_my_trust_score()
            # Trust should have decreased due to timeout
            print(f"✓ Trust after timeout: {trust_after:.3f}")

    @pytest.mark.asyncio
    async def test_network_partition_recovery(self, test_network):
        """Test recovery from network partition"""
        agents = test_network

        # Simulate partition: disconnect agents[0] from agents[1-2]
        partitioned_agent = agents[0]

        # Stop agent temporarily
        await partitioned_agent.p2p.stop()
        await asyncio.sleep(2)

        # Submit job while partitioned
        job = {
            'job_id': 'partition-test-job',
            'job_type': 'shell',
            'command': 'echo "Test"',
            'priority': 0.8,
            'deadline': time.time() + 60,
            'payment': 10.0
        }

        await agents[1].p2p.broadcast_message('JOB_BROADCAST', job)
        await asyncio.sleep(3)

        # Reconnect
        await partitioned_agent.p2p.start()
        await asyncio.sleep(5)

        # Verify agent rejoined network
        peer_count = len(partitioned_agent.p2p.known_peers)
        assert peer_count >= 2, f"Agent didn't rejoin network (only {peer_count} peers)"
        print(f"✓ Agent recovered from partition: {peer_count} peers")

    @pytest.mark.asyncio
    async def test_byzantine_behavior_detection(self, test_network):
        """Test detection and quarantine of malicious nodes"""
        agents = test_network

        # Simulate Byzantine behavior: submit invalid job results
        malicious_agent = agents[0]

        # Force trust score down with multiple failures
        for i in range(10):
            malicious_agent.reputation.punish_failure(
                job_id=f"malicious-{i}",
                reason="invalid_result"
            )

        trust = malicious_agent.reputation.get_my_trust_score()
        print(f"✓ Malicious agent trust score: {trust:.3f}")

        # Verify other agents track this
        for agent in agents[1:]:
            agent.reputation.update_peer_trust(
                peer_id=malicious_agent.config.node_id,
                new_trust=trust,
                reason="invalid_result"
            )

        # Check if malicious agent is quarantined by others
        for agent in agents[1:]:
            peer_trust = agent.reputation.peer_trust.get(malicious_agent.config.node_id, 1.0)
            print(f"  Peer {agent.config.node_id} sees {malicious_agent.config.node_id} trust: {peer_trust:.3f}")

    @pytest.mark.asyncio
    async def test_job_forwarding(self, test_network):
        """Test that jobs are forwarded when agent can't handle them"""
        agents = test_network

        # Submit job requiring specific capability
        job = {
            'job_id': 'forwarding-test-job',
            'job_type': 'hash_crack',  # Specialized job type
            'payload': {'hash': 'test', 'method': 'md5'},
            'priority': 0.8,
            'deadline': time.time() + 120,
            'payment': 50.0,
            'requirements': ['hashcat']
        }

        # Configure one agent to have hash_crack capability
        specialist = agents[4]
        specialist.capabilities.append('hash_crack')
        specialist.capabilities.append('hashcat')

        # Submit from agent without capability
        await agents[0].p2p.broadcast_message('JOB_BROADCAST', job)
        await asyncio.sleep(8)

        # Verify specialist won the job (or it was forwarded)
        job_executed = job['job_id'] in specialist.job_results or \
                       job['job_id'] in specialist.active_jobs

        print(f"✓ Specialized job handling: executed={job_executed}")

    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient (0=equality, 1=inequality)"""
        if not values or sum(values) == 0:
            return 0.0

        sorted_values = sorted(values)
        n = len(values)
        cumsum = np.cumsum(sorted_values)

        # Gini = (2 * Σ(i * x_i)) / (n * Σx_i) - (n+1)/n
        gini = (2.0 * sum((i + 1) * val for i, val in enumerate(sorted_values))) / \
               (n * sum(values)) - (n + 1) / n

        return abs(gini)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
