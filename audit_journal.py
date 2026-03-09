"""
Audit Journal - Tamper-Proof Trade Journal
Provides immutable audit trail for all trading decisions
"""

import csv
import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditJournal:
    """
    Tamper-proof trade journal with hash chain verification.
    
    Each entry includes a hash of the previous entry, creating a chain.
    Any tampering can be detected by verifying the hash chain.
    """
    
    def __init__(self, filepath: str = "logs/audit_journal.csv",
                 hash_filepath: str = "logs/audit_journal.hash"):
        
        self.filepath = filepath
        self.hash_filepath = hash_filepath
        
        # Ensure directory exists
        self._ensure_dir()
        
        # Initialize file if not exists
        self._ensure_file()
        
        # Load last hash
        self._last_hash = self._load_last_hash()
        
        logger.info(f"AuditJournal initialized: {filepath}")
    
    def _ensure_dir(self):
        """Ensure log directory exists"""
        dir_path = os.path.dirname(self.filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    def _ensure_file(self):
        """Ensure journal file exists with headers"""
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'event_type', 'trade_id', 'action', 'symbol',
                    'direction', 'entry', 'sl', 'tp', 'volume', 'pnl',
                    'status', 'reason', 'balance', 'hash', 'previous_hash'
                ])
            logger.info(f"Created new audit journal: {self.filepath}")
    
    def _load_last_hash(self) -> str:
        """Load the last hash from storage"""
        if os.path.exists(self.hash_filepath):
            try:
                with open(self.hash_filepath, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning(f"Failed to load last hash: {e}")
        
        # Return genesis hash (all zeros)
        return "0" * 64
    
    def _save_last_hash(self, hash_value: str):
        """Save the last hash to storage"""
        try:
            with open(self.hash_filepath, 'w') as f:
                f.write(hash_value)
        except Exception as e:
            logger.error(f"Failed to save last hash: {e}")
    
    def _compute_hash(self, data: Dict) -> str:
        """Compute SHA-256 hash of entry data"""
        # Create deterministic string representation
        entry_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(entry_str.encode()).hexdigest()
    
    # =========================
    # LOGGING
    # =========================
    
    def log(self, event_type: str, action: str = "", trade_data: Optional[Dict] = None,
            reason: str = "", balance: float = 0) -> bool:
        """
        Log an event to the journal.
        
        Args:
            event_type: Type of event (TRADE, DECISION, ERROR, etc.)
            action: Action taken (BUY, SELL, NO_TRADE, etc.)
            trade_data: Trade parameters if applicable
            reason: Reason for decision/action
            balance: Account balance at time of event
            
        Returns:
            True if logged successfully
        """
        try:
            # Prepare entry data
            entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'trade_id': trade_data.get('trade_id', '') if trade_data else '',
                'action': action,
                'symbol': trade_data.get('symbol', '') if trade_data else '',
                'direction': trade_data.get('direction', '') if trade_data else '',
                'entry': trade_data.get('entry', '') if trade_data else '',
                'sl': trade_data.get('sl', '') if trade_data else '',
                'tp': trade_data.get('tp', '') if trade_data else '',
                'volume': trade_data.get('volume', '') if trade_data else '',
                'pnl': trade_data.get('pnl', '') if trade_data else '',
                'status': trade_data.get('status', '') if trade_data else '',
                'reason': reason,
                'balance': balance,
                'previous_hash': self._last_hash
            }
            
            # Compute hash
            entry_hash = self._compute_hash(entry)
            entry['hash'] = entry_hash
            
            # Write to CSV
            with open(self.filepath, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    entry['timestamp'], entry['event_type'], entry['trade_id'],
                    entry['action'], entry['symbol'], entry['direction'],
                    entry['entry'], entry['sl'], entry['tp'], entry['volume'],
                    entry['pnl'], entry['status'], entry['reason'],
                    entry['balance'], entry['hash'], entry['previous_hash']
                ])
            
            # Update last hash
            self._last_hash = entry_hash
            self._save_last_hash(entry_hash)
            
            logger.info(f"Audit: {event_type} | {action} | {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")
            return False
    
    def log_trade(self, trade_data: Dict, balance: float = 0):
        """Log a trade event"""
        self.log(event_type='TRADE', action=trade_data.get('action', ''),
                trade_data=trade_data, balance=balance)
    
    def log_decision(self, action: str, reason: str, trade_data: Optional[Dict] = None,
                    balance: float = 0):
        """Log a trading decision"""
        self.log(event_type='DECISION', action=action, trade_data=trade_data,
                reason=reason, balance=balance)
    
    def log_error(self, error: str, context: str = ""):
        """Log an error"""
        self.log(event_type='ERROR', action='ERROR', reason=error)
        logger.error(f"Audit ERROR: {context} - {error}")
    
    def log_system_event(self, event: str, details: str = ""):
        """Log a system event"""
        self.log(event_type='SYSTEM', action=event, reason=details)
    
    # =========================
    # VERIFICATION
    # =========================
    
    def verify_integrity(self) -> tuple[bool, List[str]]:
        """
        Verify journal integrity by checking hash chain.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        if not os.path.exists(self.filepath):
            return True, []
        
        try:
            previous_hash = "0" * 64
            
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    # Verify previous hash
                    if row['previous_hash'] != previous_hash:
                        errors.append(f"Row {row_num}: Previous hash mismatch")
                    
                    # Verify current hash
                    entry_data = {k: v for k, v in row.items() 
                                 if k not in ['hash', 'previous_hash']}
                    expected_hash = self._compute_hash(entry_data)
                    
                    if row['hash'] != expected_hash:
                        errors.append(f"Row {row_num}: Hash mismatch (possible tampering)")
                    
                    previous_hash = row['hash']
            
            if errors:
                logger.error(f"Journal verification failed: {len(errors)} errors")
                return False, errors
            
            logger.info("Journal integrity verified successfully")
            return True, []
            
        except Exception as e:
            logger.error(f"Failed to verify journal: {e}")
            return False, [str(e)]
    
    def get_recent_entries(self, count: int = 10) -> List[Dict]:
        """Get recent journal entries"""
        entries = []
        
        if not os.path.exists(self.filepath):
            return entries
        
        try:
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            return rows[-count:] if len(rows) > count else rows
            
        except Exception as e:
            logger.error(f"Failed to get recent entries: {e}")
            return []
    
    def get_entries_by_type(self, event_type: str, limit: int = 100) -> List[Dict]:
        """Get entries by event type"""
        entries = []
        
        if not os.path.exists(self.filepath):
            return entries
        
        try:
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                
            for row in reader:
                if row['event_type'] == event_type:
                    entries.append(row)
                    if len(entries) >= limit:
                        break
            
            return entries
            
        except Exception as e:
            logger.error(f"Failed to get entries by type: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get journal statistics"""
        stats = {
            'total_entries': 0,
            'trades': 0,
            'decisions': 0,
            'errors': 0,
            'last_entry': None
        }
        
        if not os.path.exists(self.filepath):
            return stats
        
        try:
            with open(self.filepath, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            stats['total_entries'] = len(rows)
            
            for row in rows:
                event_type = row['event_type']
                if event_type == 'TRADE':
                    stats['trades'] += 1
                elif event_type == 'DECISION':
                    stats['decisions'] += 1
                elif event_type == 'ERROR':
                    stats['errors'] += 1
            
            if rows:
                stats['last_entry'] = rows[-1]['timestamp']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return stats


# Singleton instance
_audit_journal = None

def get_audit_journal() -> AuditJournal:
    """Get singleton audit journal instance"""
    global _audit_journal
    if _audit_journal is None:
        _audit_journal = AuditJournal()
    return _audit_journal
