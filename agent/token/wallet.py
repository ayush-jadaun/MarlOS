"""
Transaction Ledger
Stores all token transactions for audit trail and sync
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import time
from ..schema.schema import Transaction

class TransactionLedger:
    """
    Distributed transaction ledger
    
    Stores all token movements for:
    - Audit trail
    - Dispute resolution
    - Distributed sync (future)
    """
    
    def __init__(self, node_id: str, data_dir: str = "./data"):
        self.node_id = node_id
        self.db_path = Path(data_dir) / f"ledger_{node_id}.db"
        
        # Create database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ledger (
                entry_id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,
                from_node TEXT,
                to_node TEXT,
                amount REAL NOT NULL,
                tx_type TEXT NOT NULL,
                reason TEXT,
                job_id TEXT,
                balance_after REAL NOT NULL,
                signature TEXT NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # Indexes for fast queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON ledger(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_id ON ledger(job_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_from_node ON ledger(from_node)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_to_node ON ledger(to_node)')
        
        conn.commit()
        conn.close()
    
    def add_entry(self, entry: LedgerEntry):
        """Add entry to ledger"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ledger (
                entry_id, timestamp, from_node, to_node, amount,
                tx_type, reason, job_id, balance_after, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.entry_id,
            entry.timestamp,
            entry.from_node,
            entry.to_node,
            entry.amount,
            entry.tx_type,
            entry.reason,
            entry.job_id,
            entry.balance_after,
            entry.signature
        ))
        
        conn.commit()
        conn.close()
    
    def get_entries(self, 
                   limit: int = 100,
                   offset: int = 0,
                   job_id: Optional[str] = None,
                   from_node: Optional[str] = None,
                   to_node: Optional[str] = None) -> List[LedgerEntry]:
        """Query ledger entries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ledger WHERE 1=1'
        params = []
        
        if job_id:
            query += ' AND job_id = ?'
            params.append(job_id)
        
        if from_node:
            query += ' AND from_node = ?'
            params.append(from_node)
        
        if to_node:
            query += ' AND to_node = ?'
            params.append(to_node)
        
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        entries = []
        for row in rows:
            entries.append(LedgerEntry(
                entry_id=row['entry_id'],
                timestamp=row['timestamp'],
                from_node=row['from_node'],
                to_node=row['to_node'],
                amount=row['amount'],
                tx_type=row['tx_type'],
                reason=row['reason'],
                job_id=row['job_id'],
                balance_after=row['balance_after'],
                signature=row['signature']
            ))
        
        conn.close()
        return entries
    
    def get_balance_at_time(self, timestamp: float) -> float:
        """Get balance at specific timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT balance_after FROM ledger
            WHERE timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (timestamp,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0.0
    
    def get_statistics(self) -> dict:
        """Get ledger statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute('SELECT COUNT(*) FROM ledger')
        total_entries = cursor.fetchone()[0]
        
        # Total earned
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) FROM ledger
            WHERE tx_type = 'DEPOSIT'
        ''')
        total_earned = cursor.fetchone()[0]
        
        # Total spent
        cursor.execute('''
            SELECT COALESCE(SUM(ABS(amount)), 0) FROM ledger
            WHERE tx_type IN ('WITHDRAW', 'SLASH')
        ''')
        total_spent = cursor.fetchone()[0]
        
        # Current balance
        cursor.execute('''
            SELECT balance_after FROM ledger
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        result = cursor.fetchone()
        current_balance = result[0] if result else 0.0
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'total_earned': total_earned,
            'total_spent': total_spent,
            'current_balance': current_balance,
            'net_profit': total_earned - total_spent
        }
    
    def export_to_json(self, output_file: str):
        """Export ledger to JSON for backup/audit"""
        entries = self.get_entries(limit=1000000)  # All entries
        
        data = {
            'node_id': self.node_id,
            'exported_at': time.time(),
            'entries': [e.to_dict() for e in entries],
            'statistics': self.get_statistics()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[LEDGER] Exported {len(entries)} entries to {output_file}")