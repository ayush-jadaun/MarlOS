"""
Token Wallet Management
Handles token balance, transactions, staking, and ledger
"""
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from .ledger import TransactionLedger, LedgerEntry

@dataclass
class Transaction:
    """Token transaction record"""
    tx_id: str
    timestamp: float
    tx_type: str  # DEPOSIT, WITHDRAW, STAKE, UNSTAKE, SLASH
    amount: float
    balance_after: float
    reason: str
    job_id: Optional[str] = None
    from_node: Optional[str] = None
    to_node: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class Wallet:
    """
    Token wallet for managing AetherCredits (AC)
    """

    def __init__(self, node_id: str, starting_balance: float = 100.0, data_dir: str = "./data", signing_key=None):
        self.node_id = node_id
        self.balance = starting_balance
        self.staked = 0.0
        self.lifetime_earned = 0.0
        self.lifetime_spent = 0.0
        self.transactions: List[Transaction] = []
        self.ledger = TransactionLedger(node_id, data_dir)
        self.signing_key = signing_key  # For signing transactions

        # Storage
        self.data_dir = Path(data_dir)
        self.wallet_file = self.data_dir / f"wallet_{node_id}.json"

        # Load existing wallet if exists
        self._load_wallet()
    
    def deposit(self, amount: float, reason: str, job_id: str = None, from_node: str = None) -> Transaction:
        """Deposit tokens (earn) - WITH LEDGER"""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        self.balance += amount
        self.lifetime_earned += amount

        tx = Transaction(
            tx_id=self._generate_tx_id(),
            timestamp=time.time(),
            tx_type="DEPOSIT",
            amount=amount,
            balance_after=self.balance,
            reason=reason,
            job_id=job_id,
            from_node=from_node
        )

        self.transactions.append(tx)

        # Add to ledger
        from .ledger import LedgerEntry

        # Sign transaction
        if self.signing_key:
            import hashlib
            tx_data = f"{tx.tx_id}:{tx.timestamp}:{tx.amount}:{tx.balance_after}".encode()
            signature = self.signing_key.sign(hashlib.sha256(tx_data).digest()).hex()
        else:
            signature = "unsigned"  # No signing key provided

        ledger_entry = LedgerEntry(
            entry_id=tx.tx_id,
            timestamp=tx.timestamp,
            from_node=from_node,
            to_node=self.node_id,
            amount=amount,
            tx_type="DEPOSIT",
            reason=reason,
            job_id=job_id,
            balance_after=self.balance,
            signature=signature
        )

        self.ledger.add_entry(ledger_entry)

        self._save_wallet()

        print(f"💰 [WALLET] +{amount:.2f} AC ({reason}) → Balance: {self.balance:.2f} AC")
        return tx
    
    def withdraw(self, amount: float, reason: str, job_id: str = None, to_node: str = None) -> Optional[Transaction]:
        """
        Withdraw tokens (spend)
        Returns None if insufficient funds
        """
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")
        
        if self.balance < amount:
            print(f"❌ [WALLET] Insufficient funds! Need {amount:.2f} AC, have {self.balance:.2f} AC")
            return None
        
        self.balance -= amount
        self.lifetime_spent += amount
        
        tx = Transaction(
            tx_id=self._generate_tx_id(),
            timestamp=time.time(),
            tx_type="WITHDRAW",
            amount=-amount,
            balance_after=self.balance,
            reason=reason,
            job_id=job_id,
            to_node=to_node
        )
        
        self.transactions.append(tx)
        self._save_wallet()
        
        print(f"��� [WALLET] -{amount:.2f} AC ({reason}) → Balance: {self.balance:.2f} AC")
        return tx
    
    def stake(self, amount: float, job_id: str) -> bool:
        """
        Stake tokens as collateral for a job
        Returns False if insufficient funds
        """
        if amount <= 0:
            raise ValueError("Stake amount must be positive")
        
        if self.balance < amount:
            print(f"❌ [WALLET] Cannot stake! Need {amount:.2f} AC, have {self.balance:.2f} AC")
            return False
        
        self.balance -= amount
        self.staked += amount
        
        tx = Transaction(
            tx_id=self._generate_tx_id(),
            timestamp=time.time(),
            tx_type="STAKE",
            amount=-amount,
            balance_after=self.balance,
            reason=f"Staked for job {job_id}",
            job_id=job_id
        )
        
        self.transactions.append(tx)
        self._save_wallet()
        
        print(f"��� [WALLET] Staked {amount:.2f} AC for job {job_id} → Available: {self.balance:.2f} AC, Staked: {self.staked:.2f} AC")
        return True
    
    def unstake(self, amount: float, job_id: str, success: bool) -> Transaction:
        """
        Release staked tokens
        If success=True, tokens returned to balance
        If success=False, tokens are slashed (lost)
        """
        if amount <= 0:
            raise ValueError("Unstake amount must be positive")
        
        if self.staked < amount:
            raise ValueError(f"Cannot unstake {amount}, only {self.staked} staked")
        
        self.staked -= amount
        
        if success:
            # Return stake to balance
            self.balance += amount
            tx_type = "UNSTAKE"
            reason = f"Stake returned for job {job_id}"
            print(f"��� [WALLET] Stake returned: +{amount:.2f} AC → Balance: {self.balance:.2f} AC")
        else:
            # Slash stake (lost forever)
            tx_type = "SLASH"
            reason = f"Stake slashed for job {job_id}"
            print(f"��� [WALLET] Stake slashed: -{amount:.2f} AC")
        
        tx = Transaction(
            tx_id=self._generate_tx_id(),
            timestamp=time.time(),
            tx_type=tx_type,
            amount=amount if success else -amount,
            balance_after=self.balance,
            reason=reason,
            job_id=job_id
        )
        
        self.transactions.append(tx)
        self._save_wallet()
        
        return tx
    
    def can_afford(self, amount: float) -> bool:
        """Check if wallet has sufficient balance"""
        return self.balance >= amount
    
    def get_total_value(self) -> float:
        """Get total value (balance + staked)"""
        return self.balance + self.staked
    
    def get_transaction_history(self, limit: int = 10) -> List[Transaction]:
        """Get recent transactions"""
        return self.transactions[-limit:]
    
    def get_stats(self) -> dict:
        """Get wallet statistics"""
        return {
            'balance': self.balance,
            'staked': self.staked,
            'total_value': self.get_total_value(),
            'lifetime_earned': self.lifetime_earned,
            'lifetime_spent': self.lifetime_spent,
            'net_profit': self.lifetime_earned - self.lifetime_spent,
            'transaction_count': len(self.transactions)
        }
    
    def _generate_tx_id(self) -> str:
        """Generate unique transaction ID"""
        import uuid
        return f"tx-{str(uuid.uuid4())[:8]}"
    
    def _save_wallet(self):
        """Save wallet state to disk"""
        wallet_data = {
            'node_id': self.node_id,
            'balance': self.balance,
            'staked': self.staked,
            'lifetime_earned': self.lifetime_earned,
            'lifetime_spent': self.lifetime_spent,
            'transactions': [tx.to_dict() for tx in self.transactions]
        }
        
        self.wallet_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.wallet_file, 'w') as f:
            json.dump(wallet_data, f, indent=2)
    
    def _load_wallet(self):
        """Load wallet state from disk"""
        if self.wallet_file.exists():
            try:
                with open(self.wallet_file, 'r') as f:
                    wallet_data = json.load(f)
                
                self.balance = wallet_data.get('balance', self.balance)
                self.staked = wallet_data.get('staked', 0.0)
                self.lifetime_earned = wallet_data.get('lifetime_earned', 0.0)
                self.lifetime_spent = wallet_data.get('lifetime_spent', 0.0)
                
                # Load transactions
                self.transactions = [
                    Transaction(**tx_data)
                    for tx_data in wallet_data.get('transactions', [])
                ]
                
                print(f"��� [WALLET] Loaded existing wallet: {self.balance:.2f} AC")
            except Exception as e:
                print(f"⚠️  [WALLET] Error loading wallet: {e}, starting fresh")
