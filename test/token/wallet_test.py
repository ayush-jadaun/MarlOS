"""
Test suite for Wallet token management
Tests deposits, withdrawals, staking, unstaking, and ledger integration
"""
import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import os 
import sys
import sys
sys.path.insert(0, '../')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agent.token.wallet import Wallet
from agent.token.ledger import TransactionLedger, LedgerEntry
from agent.schema.schema import Transaction


class TestWalletBasics:
    """Test basic wallet operations"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data"""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def wallet(self, temp_dir):
        """Create a fresh wallet for testing"""
        return Wallet(
            node_id="test_node_001",
            starting_balance=100.0,
            data_dir=temp_dir
        )
    
    def test_wallet_initialization(self, wallet):
        """Test wallet initializes with correct values"""
        assert wallet.node_id == "test_node_001"
        assert wallet.balance == 100.0
        assert wallet.staked == 0.0
        assert wallet.lifetime_earned == 0.0
        assert wallet.lifetime_spent == 0.0
        assert len(wallet.transactions) == 0
    
    def test_wallet_with_signing_key(self, temp_dir):
        """Test wallet with cryptographic signing"""
        mock_key = Mock()
        mock_key.sign.return_value = Mock(hex=lambda: "mock_signature")
        
        wallet = Wallet(
            node_id="test_node_002",
            starting_balance=50.0,
            data_dir=temp_dir,
            signing_key=mock_key
        )
        
        assert wallet.signing_key == mock_key
        assert wallet.balance == 50.0


class TestDeposits:
    """Test deposit (earning) operations"""
    
    @pytest.fixture
    def wallet(self):
        temp_path = tempfile.mkdtemp()
        w = Wallet("test_node", 100.0, temp_path)
        yield w
        shutil.rmtree(temp_path)
    
    def test_simple_deposit(self, wallet):
        """Test basic token deposit"""
        initial_balance = wallet.balance
        
        tx = wallet.deposit(
            amount=50.0,
            reason="Job completed",
            job_id="job_001"
        )
        
        assert wallet.balance == initial_balance + 50.0
        assert wallet.lifetime_earned == 50.0
        assert tx.tx_type == "DEPOSIT"
        assert tx.amount == 50.0
        assert tx.reason == "Job completed"
        assert tx.job_id == "job_001"
    
    def test_deposit_updates_ledger(self, wallet):
        """Test deposit creates ledger entry"""
        wallet.deposit(
            amount=25.0,
            reason="Test deposit",
            from_node="node_sender"
        )
        
        # Check ledger was updated
        entries = wallet.ledger.get_recent_entries(limit=1)
        assert len(entries) == 1
        assert entries[0].amount == 25.0
        assert entries[0].tx_type == "DEPOSIT"
        assert entries[0].from_node == "node_sender"
        assert entries[0].to_node == wallet.node_id
    
    def test_deposit_with_signing(self):
        """Test deposit signs transaction properly"""
        temp_path = tempfile.mkdtemp()
        
        mock_key = Mock()
        mock_signature = Mock()
        mock_signature.hex.return_value = "abcd1234signature"
        mock_key.sign.return_value = mock_signature
        
        wallet = Wallet(
            "signed_node",
            100.0,
            temp_path,
            signing_key=mock_key
        )
        
        wallet.deposit(50.0, "Test", job_id="job_001")
        
        # Verify signing was called
        assert mock_key.sign.called
        
        # Check ledger entry has signature
        entries = wallet.ledger.get_recent_entries(limit=1)
        assert entries[0].signature == "abcd1234signature"
        
        shutil.rmtree(temp_path)
    
    def test_deposit_negative_amount(self, wallet):
        """Test deposit rejects negative amounts"""
        with pytest.raises(ValueError, match="must be positive"):
            wallet.deposit(-10.0, "Invalid")
    
    def test_deposit_zero_amount(self, wallet):
        """Test deposit rejects zero amounts"""
        with pytest.raises(ValueError, match="must be positive"):
            wallet.deposit(0.0, "Invalid")
    
    def test_multiple_deposits(self, wallet):
        """Test multiple deposits accumulate correctly"""
        wallet.deposit(10.0, "First")
        wallet.deposit(20.0, "Second")
        wallet.deposit(30.0, "Third")
        
        assert wallet.balance == 160.0  # 100 + 10 + 20 + 30
        assert wallet.lifetime_earned == 60.0
        assert len(wallet.transactions) == 3


class TestWithdrawals:
    """Test withdrawal (spending) operations"""
    
    @pytest.fixture
    def wallet(self):
        temp_path = tempfile.mkdtemp()
        w = Wallet("test_node", 100.0, temp_path)
        yield w
        shutil.rmtree(temp_path)
    
    def test_simple_withdrawal(self, wallet):
        """Test basic token withdrawal"""
        tx = wallet.withdraw(
            amount=30.0,
            reason="Job payment",
            job_id="job_001",
            to_node="recipient_node"
        )
        
        assert wallet.balance == 70.0
        assert wallet.lifetime_spent == 30.0
        assert tx is not None
        assert tx.tx_type == "WITHDRAW"
        assert tx.amount == -30.0
        assert tx.to_node == "recipient_node"
    
    def test_withdrawal_insufficient_funds(self, wallet):
        """Test withdrawal fails with insufficient funds"""
        tx = wallet.withdraw(200.0, "Too much")
        
        assert tx is None
        assert wallet.balance == 100.0
        assert wallet.lifetime_spent == 0.0
    
    def test_withdrawal_exact_balance(self, wallet):
        """Test withdrawing exact balance"""
        tx = wallet.withdraw(100.0, "All funds")
        
        assert tx is not None
        assert wallet.balance == 0.0
        assert wallet.lifetime_spent == 100.0
    
    def test_withdrawal_negative_amount(self, wallet):
        """Test withdrawal rejects negative amounts"""
        with pytest.raises(ValueError, match="must be positive"):
            wallet.withdraw(-10.0, "Invalid")
    
    def test_multiple_withdrawals(self, wallet):
        """Test multiple withdrawals"""
        wallet.withdraw(10.0, "First")
        wallet.withdraw(20.0, "Second")
        wallet.withdraw(15.0, "Third")
        
        assert wallet.balance == 55.0
        assert wallet.lifetime_spent == 45.0
        assert len(wallet.transactions) == 3


class TestStaking:
    """Test staking operations"""
    
    @pytest.fixture
    def wallet(self):
        temp_path = tempfile.mkdtemp()
        w = Wallet("test_node", 100.0, temp_path)
        yield w
        shutil.rmtree(temp_path)
    
    def test_simple_stake(self, wallet):
        """Test basic token staking"""
        success = wallet.stake(20.0, "job_001")
        
        assert success is True
        assert wallet.balance == 80.0
        assert wallet.staked == 20.0
        assert len(wallet.transactions) == 1
        assert wallet.transactions[0].tx_type == "STAKE"
    
    def test_stake_insufficient_funds(self, wallet):
        """Test staking fails with insufficient funds"""
        success = wallet.stake(150.0, "job_001")
        
        assert success is False
        assert wallet.balance == 100.0
        assert wallet.staked == 0.0
    
    def test_stake_negative_amount(self, wallet):
        """Test staking rejects negative amounts"""
        with pytest.raises(ValueError, match="must be positive"):
            wallet.stake(-10.0, "job_001")
    
    def test_multiple_stakes(self, wallet):
        """Test multiple concurrent stakes"""
        wallet.stake(20.0, "job_001")
        wallet.stake(30.0, "job_002")
        wallet.stake(10.0, "job_003")
        
        assert wallet.balance == 40.0
        assert wallet.staked == 60.0
        assert len(wallet.transactions) == 3


class TestUnstaking:
    """Test unstaking operations"""
    
    @pytest.fixture
    def wallet_with_stake(self):
        temp_path = tempfile.mkdtemp()
        w = Wallet("test_node", 100.0, temp_path)
        w.stake(30.0, "job_001")
        yield w
        shutil.rmtree(temp_path)
    
    def test_unstake_success(self, wallet_with_stake):
        """Test successful unstake returns tokens"""
        tx = wallet_with_stake.unstake(30.0, "job_001", success=True)
        
        assert wallet_with_stake.balance == 100.0  # Returned to balance
        assert wallet_with_stake.staked == 0.0
        assert tx.tx_type == "UNSTAKE"
        assert tx.amount == 30.0
    
    def test_unstake_failure_slash(self, wallet_with_stake):
        """Test failed unstake slashes tokens"""
        tx = wallet_with_stake.unstake(30.0, "job_001", success=False)
        
        assert wallet_with_stake.balance == 70.0  # Not returned
        assert wallet_with_stake.staked == 0.0
        assert tx.tx_type == "SLASH"
        assert tx.amount == -30.0
    
    def test_unstake_more_than_staked(self, wallet_with_stake):
        """Test unstaking more than staked amount fails"""
        with pytest.raises(ValueError, match="only 30.0 staked"):
            wallet_with_stake.unstake(50.0, "job_001", success=True)
    
    def test_unstake_negative_amount(self, wallet_with_stake):
        """Test unstaking negative amount fails"""
        with pytest.raises(ValueError, match="must be positive"):
            wallet_with_stake.unstake(-10.0, "job_001", success=True)
    
    def test_partial_unstake(self, wallet_with_stake):
        """Test partial unstaking"""
        wallet_with_stake.unstake(10.0, "job_001", success=True)
        
        assert wallet_with_stake.balance == 80.0
        assert wallet_with_stake.staked == 20.0


class TestWalletQueries:
    """Test wallet query methods"""
    
    @pytest.fixture
    def wallet(self):
        temp_path = tempfile.mkdtemp()
        w = Wallet("test_node", 100.0, temp_path)
        yield w
        shutil.rmtree(temp_path)
    
    def test_can_afford_true(self, wallet):
        """Test can_afford with sufficient balance"""
        assert wallet.can_afford(50.0) is True
        assert wallet.can_afford(100.0) is True
    
    def test_can_afford_false(self, wallet):
        """Test can_afford with insufficient balance"""
        assert wallet.can_afford(150.0) is False
    
    def test_get_total_value(self, wallet):
        """Test total value calculation"""
        wallet.stake(20.0, "job_001")
        
        total = wallet.get_total_value()
        assert total == 100.0  # 80 balance + 20 staked
    
    def test_get_transaction_history(self, wallet):
        """Test transaction history retrieval"""
        wallet.deposit(10.0, "First")
        wallet.withdraw(5.0, "Second")
        wallet.stake(15.0, "job_001")
        
        # Get last 2 transactions
        history = wallet.get_transaction_history(limit=2)
        assert len(history) == 2
        assert history[0].reason == "Second"
        assert history[1].reason == "Staked for job job_001"
    
    def test_get_stats(self, wallet):
        """Test wallet statistics"""
        wallet.deposit(50.0, "Earned")
        wallet.withdraw(20.0, "Spent")
        wallet.stake(10.0, "job_001")
        
        stats = wallet.get_stats()
        
        assert stats['balance'] == 120.0  # 100 + 50 - 20 - 10
        assert stats['staked'] == 10.0
        assert stats['total_value'] == 130.0
        assert stats['lifetime_earned'] == 50.0
        assert stats['lifetime_spent'] == 20.0
        assert stats['net_profit'] == 30.0
        assert stats['transaction_count'] == 3


class TestWalletPersistence:
    """Test wallet save/load functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    def test_save_and_load_wallet(self, temp_dir):
        """Test wallet persists to disk and reloads"""
        # Create wallet and perform operations
        wallet1 = Wallet("persist_test", 100.0, temp_dir)
        wallet1.deposit(50.0, "Earned")
        wallet1.withdraw(20.0, "Spent")
        wallet1.stake(10.0, "job_001")
        
        balance1 = wallet1.balance
        staked1 = wallet1.staked
        earned1 = wallet1.lifetime_earned
        spent1 = wallet1.lifetime_spent
        tx_count1 = len(wallet1.transactions)
        
        # Create new wallet with same node_id (should load from disk)
        wallet2 = Wallet("persist_test", 999.0, temp_dir)
        
        assert wallet2.balance == balance1
        assert wallet2.staked == staked1
        assert wallet2.lifetime_earned == earned1
        assert wallet2.lifetime_spent == spent1
        assert len(wallet2.transactions) == tx_count1
    
    def test_wallet_file_creation(self, temp_dir):
        """Test wallet file is created"""
        wallet = Wallet("file_test", 100.0, temp_dir)
        wallet.deposit(10.0, "Test")
        
        wallet_file = Path(temp_dir) / "wallet_file_test.json"
        assert wallet_file.exists()
    
    def test_corrupted_wallet_file(self, temp_dir):
        """Test wallet handles corrupted file gracefully"""
        wallet = Wallet("corrupt_test", 100.0, temp_dir)
        wallet.deposit(10.0, "Test")
        
        # Corrupt the file
        wallet_file = Path(temp_dir) / "wallet_corrupt_test.json"
        with open(wallet_file, 'w') as f:
            f.write("invalid json{{{")
        
        # Should start fresh without crashing
        wallet2 = Wallet("corrupt_test", 200.0, temp_dir)
        assert wallet2.balance == 200.0


class TestWalletIntegration:
    """Integration tests with realistic scenarios"""
    
    @pytest.fixture
    def wallet(self):
        temp_path = tempfile.mkdtemp()
        w = Wallet("integration_test", 100.0, temp_path)
        yield w
        shutil.rmtree(temp_path)
    
    def test_complete_job_lifecycle(self, wallet):
        """Test complete job lifecycle: stake -> complete -> unstake"""
        # Stake for job
        wallet.stake(20.0, "job_001")
        assert wallet.balance == 80.0
        assert wallet.staked == 20.0
        
        # Complete job and earn reward
        wallet.deposit(50.0, "Job reward", job_id="job_001")
        assert wallet.balance == 130.0
        
        # Return stake
        wallet.unstake(20.0, "job_001", success=True)
        assert wallet.balance == 150.0
        assert wallet.staked == 0.0
        
        # Verify net profit
        stats = wallet.get_stats()
        assert stats['net_profit'] == 50.0
    
    def test_failed_job_lifecycle(self, wallet):
        """Test failed job: stake -> fail -> slash"""
        # Stake for job
        wallet.stake(20.0, "job_002")
        
        # Job fails - stake is slashed
        wallet.unstake(20.0, "job_002", success=False)
        
        assert wallet.balance == 80.0  # Lost 20 to slash
        assert wallet.staked == 0.0
        assert wallet.lifetime_spent == 0.0  # Slash doesn't count as spent
    
    def test_multiple_concurrent_jobs(self, wallet):
        """Test handling multiple jobs simultaneously"""
        # Start 3 jobs
        wallet.stake(10.0, "job_001")
        wallet.stake(15.0, "job_002")
        wallet.stake(20.0, "job_003")
        
        assert wallet.balance == 55.0
        assert wallet.staked == 45.0
        
        # Complete jobs with varying outcomes
        wallet.unstake(10.0, "job_001", success=True)   # Success
        wallet.deposit(30.0, "Reward job_001")
        
        wallet.unstake(15.0, "job_002", success=False)  # Failed
        
        wallet.unstake(20.0, "job_003", success=True)   # Success
        wallet.deposit(40.0, "Reward job_003")
        
        # Final balance: 55 + 10 + 30 + 20 + 40 = 155
        # (15 was slashed)
        assert wallet.balance == 155.0
        assert wallet.staked == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])