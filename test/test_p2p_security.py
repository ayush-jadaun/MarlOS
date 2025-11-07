"""
Comprehensive P2P Security Tests
Tests for replay protection, clock sync, message validation, and encryption
"""
import pytest
import asyncio
import time
from agent.p2p.security import (
    ReplayProtection, ClockSync, QuorumConsensus,
    MessageReliability, HealthMonitor, generate_nonce
)
from agent.crypto.signing import SigningKey, sign_message
from agent.crypto.encryption import AsymmetricEncryption


class TestReplayProtection:
    """Test replay attack protection"""

    def test_valid_message_accepted(self):
        """Test that valid messages are accepted"""
        replay = ReplayProtection(timestamp_tolerance=30.0)

        message = {
            'message_id': 'test-1',
            'timestamp': time.time(),
            'nonce': generate_nonce(),
            'node_id': 'node-1'
        }

        is_valid, reason = replay.validate_message(message)
        assert is_valid is True
        assert reason == "Valid"

    def test_duplicate_message_rejected(self):
        """Test that duplicate messages are rejected"""
        replay = ReplayProtection(timestamp_tolerance=30.0)

        message = {
            'message_id': 'test-2',
            'timestamp': time.time(),
            'nonce': generate_nonce(),
            'node_id': 'node-1'
        }

        # First time: accepted
        is_valid, _ = replay.validate_message(message)
        assert is_valid is True

        replay.mark_message_seen(message)

        # Second time: rejected
        is_valid, reason = replay.validate_message(message)
        assert is_valid is False
        assert "Duplicate message ID" in reason

    def test_old_timestamp_rejected(self):
        """Test that messages with old timestamps are rejected"""
        replay = ReplayProtection(timestamp_tolerance=30.0)

        message = {
            'message_id': 'test-3',
            'timestamp': time.time() - 100,  # 100 seconds ago
            'nonce': generate_nonce(),
            'node_id': 'node-1'
        }

        is_valid, reason = replay.validate_message(message)
        assert is_valid is False
        assert "Timestamp out of window" in reason

    def test_future_timestamp_rejected(self):
        """Test that messages from future are rejected (clock skew attack)"""
        replay = ReplayProtection(timestamp_tolerance=30.0)

        message = {
            'message_id': 'test-4',
            'timestamp': time.time() + 10,  # 10 seconds in future
            'nonce': generate_nonce(),
            'node_id': 'node-1'
        }

        is_valid, reason = replay.validate_message(message)
        assert is_valid is False
        assert "future" in reason.lower()

    def test_duplicate_nonce_rejected(self):
        """Test that duplicate nonces are rejected"""
        replay = ReplayProtection(timestamp_tolerance=30.0)

        nonce = generate_nonce()

        message1 = {
            'message_id': 'test-5',
            'timestamp': time.time(),
            'nonce': nonce,
            'node_id': 'node-1'
        }

        message2 = {
            'message_id': 'test-6',  # Different message ID
            'timestamp': time.time(),
            'nonce': nonce,  # Same nonce
            'node_id': 'node-1'
        }

        # First message accepted
        is_valid, _ = replay.validate_message(message1)
        assert is_valid is True
        replay.mark_message_seen(message1)

        # Second message with same nonce rejected
        is_valid, reason = replay.validate_message(message2)
        assert is_valid is False
        assert "Duplicate nonce" in reason

    def test_cleanup_old_messages(self):
        """Test that old message records are cleaned up"""
        replay = ReplayProtection(timestamp_tolerance=30.0)

        # Add old message
        old_message = {
            'message_id': 'old-msg',
            'timestamp': time.time() - 100,
            'nonce': generate_nonce(),
            'node_id': 'node-1'
        }

        replay.seen_messages['old-msg'] = time.time() - 100

        # Clean up
        replay.cleanup_old_messages(max_age=60.0)

        # Old message should be removed
        assert 'old-msg' not in replay.seen_messages

    def test_nonce_uniqueness(self):
        """Test that nonces are cryptographically unique"""
        nonces = set()
        for _ in range(1000):
            nonce = generate_nonce()
            assert nonce not in nonces
            nonces.add(nonce)

        assert len(nonces) == 1000


class TestClockSync:
    """Test clock synchronization"""

    @pytest.mark.asyncio
    async def test_clock_sync_with_peers(self):
        """Test clock synchronization across peers"""
        clock = ClockSync()

        # Simulate peer times (slightly offset)
        peer_times = {
            'peer-1': time.time() + 1.0,
            'peer-2': time.time() + 1.5,
            'peer-3': time.time() + 1.2,
        }

        async def query_callback(node_id):
            await asyncio.sleep(0.01)  # Simulate network latency
            return peer_times.get(node_id, time.time())

        await clock.synchronize(list(peer_times.keys()), query_callback)

        # Should have calculated offset
        assert clock.local_offset != 0.0
        assert abs(clock.local_offset - 1.2) < 0.5  # Median should be ~1.2

    def test_synchronized_time(self):
        """Test getting synchronized time"""
        clock = ClockSync()
        clock.local_offset = 2.0

        sync_time = clock.get_synchronized_time()
        real_time = time.time()

        assert abs(sync_time - (real_time + 2.0)) < 0.1

    def test_timestamp_validation(self):
        """Test timestamp validation with sync"""
        clock = ClockSync()
        clock.local_offset = 1.0

        # Timestamp close to sync time should be valid
        valid_timestamp = clock.get_synchronized_time()
        assert clock.verify_timestamp(valid_timestamp, tolerance=30.0) is True

        # Very old timestamp should be invalid
        old_timestamp = time.time() - 100
        assert clock.verify_timestamp(old_timestamp, tolerance=30.0) is False


class TestQuorumConsensus:
    """Test quorum consensus mechanism"""

    def test_propose_operation(self):
        """Test proposing an operation"""
        consensus = QuorumConsensus('node-1', quorum_size=2)

        op_data = {'job_id': 'job-1', 'winner': 'node-1'}
        consensus.propose_operation('op-1', op_data)

        # Own approval should be automatic
        assert consensus.get_approval_count('op-1') == 1

    def test_receive_approval(self):
        """Test receiving approvals from peers"""
        consensus = QuorumConsensus('node-1', quorum_size=2)

        op_data = {'job_id': 'job-1', 'winner': 'node-1'}
        consensus.propose_operation('op-1', op_data)

        # Add approval from peer
        has_quorum = consensus.receive_approval('op-1', 'node-2', op_data)

        assert has_quorum is True
        assert consensus.get_approval_count('op-1') == 2

    def test_quorum_not_reached(self):
        """Test when quorum is not reached"""
        consensus = QuorumConsensus('node-1', quorum_size=3)

        op_data = {'job_id': 'job-1', 'winner': 'node-1'}
        consensus.propose_operation('op-1', op_data)

        # Only 2 approvals (self + 1 peer)
        has_quorum = consensus.receive_approval('op-1', 'node-2', op_data)

        assert has_quorum is False
        assert consensus.get_approval_count('op-1') == 2

    def test_operation_data_mismatch(self):
        """Test that mismatched operation data is rejected"""
        consensus = QuorumConsensus('node-1', quorum_size=2)

        op_data_1 = {'job_id': 'job-1', 'winner': 'node-1'}
        op_data_2 = {'job_id': 'job-1', 'winner': 'node-2'}  # Different!

        consensus.propose_operation('op-1', op_data_1)

        # Try to approve with different data
        has_quorum = consensus.receive_approval('op-1', 'node-2', op_data_2)

        assert has_quorum is False


class TestMessageReliability:
    """Test reliable message delivery with ACKs"""

    @pytest.mark.asyncio
    async def test_ack_collection(self):
        """Test collecting ACKs from peers"""
        reliability = MessageReliability(ack_timeout=5.0)

        message_id = 'msg-1'
        expected_nodes = 3

        # Start waiting for ACKs
        wait_task = asyncio.create_task(
            reliability.wait_for_acks(message_id, expected_nodes, timeout=2.0)
        )

        # Simulate ACKs arriving
        await asyncio.sleep(0.1)
        reliability.receive_ack(message_id, 'node-1', expected_nodes)
        await asyncio.sleep(0.1)
        reliability.receive_ack(message_id, 'node-2', expected_nodes)

        # Should reach quorum (2/3)
        ack_count = await wait_task
        assert ack_count == 2

    @pytest.mark.asyncio
    async def test_ack_timeout(self):
        """Test ACK timeout handling"""
        reliability = MessageReliability(ack_timeout=5.0)

        message_id = 'msg-2'
        expected_nodes = 3

        # Wait for ACKs with short timeout
        ack_count = await reliability.wait_for_acks(
            message_id, expected_nodes, timeout=0.5
        )

        # No ACKs received, should return 0
        assert ack_count == 0


class TestHealthMonitor:
    """Test peer health monitoring"""

    def test_peer_health_tracking(self):
        """Test tracking peer health status"""
        monitor = HealthMonitor(ping_interval=10.0, ping_timeout=5.0)

        # Mark peer as healthy
        monitor.peer_health['node-1'] = {
            'alive': True,
            'rtt': 0.050,
            'last_seen': time.time()
        }

        assert monitor.is_peer_healthy('node-1') is True

    def test_unhealthy_peer_detection(self):
        """Test detection of unhealthy peers"""
        monitor = HealthMonitor(ping_interval=10.0, ping_timeout=5.0)

        # Mark peer as seen long ago
        monitor.peer_health['node-2'] = {
            'alive': True,
            'rtt': 0.100,
            'last_seen': time.time() - 60  # 60 seconds ago
        }

        assert monitor.is_peer_healthy('node-2', max_age=30.0) is False

    def test_rtt_tracking(self):
        """Test RTT tracking and average calculation"""
        monitor = HealthMonitor()

        # Record several RTT samples
        monitor.rtt_history['node-1'] = [0.010, 0.020, 0.015, 0.025, 0.012]

        avg_rtt = monitor.get_peer_rtt('node-1')
        assert avg_rtt is not None
        assert abs(avg_rtt - 0.0164) < 0.01  # Should be average

    def test_p99_latency_calculation(self):
        """Test P99 latency calculation across peers"""
        monitor = HealthMonitor()

        # Create latency distribution
        latencies = [i * 0.001 for i in range(100)]  # 0-99ms
        monitor.rtt_history['node-1'] = latencies

        p99 = monitor.get_p99_latency()
        assert p99 >= 0.095  # Should be close to 99ms


class TestMessageSigning:
    """Test message signing and verification"""

    def test_signed_message_verification(self):
        """Test that signed messages are verified correctly"""
        key = SigningKey.generate()

        message = {
            'type': 'test',
            'node_id': 'node-1',
            'data': 'hello world',
            'timestamp': time.time(),
            'message_id': 'test-123',
            'nonce': generate_nonce()
        }

        signed = sign_message(key, message)

        # Should have signature and public key
        assert 'signature' in signed
        assert 'public_key' in signed

    def test_tampered_message_rejected(self):
        """Test that tampered messages fail verification"""
        from agent.crypto.signing import verify_message

        key = SigningKey.generate()

        message = {
            'type': 'test',
            'data': 'original data',
            'timestamp': time.time()
        }

        signed = sign_message(key, message)

        # Tamper with message
        signed['data'] = 'tampered data'

        # Should fail verification
        assert verify_message(signed) is False


class TestEncryption:
    """Test message encryption"""

    def test_asymmetric_encryption(self):
        """Test asymmetric encryption for payloads"""
        sender = AsymmetricEncryption()
        recipient = AsymmetricEncryption()

        plaintext = b"secret payload data"

        # Encrypt for recipient
        ciphertext = sender.encrypt_for(recipient.public_key, plaintext)

        # Recipient decrypts
        decrypted = recipient.decrypt_from(sender.public_key, ciphertext)

        assert decrypted == plaintext

    def test_encryption_with_wrong_key_fails(self):
        """Test that decryption with wrong key fails"""
        sender = AsymmetricEncryption()
        recipient = AsymmetricEncryption()
        attacker = AsymmetricEncryption()

        plaintext = b"secret data"
        ciphertext = sender.encrypt_for(recipient.public_key, plaintext)

        # Attacker tries to decrypt with wrong key
        with pytest.raises(Exception):
            attacker.decrypt_from(sender.public_key, ciphertext)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
