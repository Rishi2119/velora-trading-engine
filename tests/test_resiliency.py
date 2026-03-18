"""
Phase 14 test gate — Journal & Network Resiliency checks.
Run: python -m pytest tests/test_resiliency.py -v
"""
import sys
import os
import pytest
import sqlite3
import tempfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.network import is_network_available
from backend.app.analytics.journal import TradeJournal


class TestResiliency:
    
    def test_network_availability(self):
        # We can mock socket.socket to simulate pass/fail without actually hitting internet
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.connect.return_value = None
            assert is_network_available() is True
            
        with patch('socket.socket') as mock_socket:
            import socket
            mock_socket.return_value.__enter__.return_value.connect.side_effect = socket.error("Offline")
            assert is_network_available() is False

    @pytest.mark.asyncio
    async def test_journal_local_persistence(self):
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        try:
            journal = TradeJournal(db_path=path)
            
            trade = {
                "ticket": 12345,
                "symbol": "EURUSD",
                "direction": "BUY",
                "lots": 0.1,
                "entry_price": 1.10,
                "exit_price": 1.12,
                "sl": 1.09,
                "tp": 1.15,
                "pnl": 20.0,
                "strategy_name": "EmaRsi_Trend",
                "entry_time": "2024-01-01T00:00:00Z",
                "exit_time": "2024-01-01T01:00:00Z"
            }
            
            # Since Supabase credentials aren't going to be present, it will skip sync gracefully
            await journal.log_trade(trade)
            
            # Validate SQLite
            with sqlite3.connect(path) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM trades WHERE ticket = 12345").fetchone()
                
                assert row is not None
                assert row["symbol"] == "EURUSD"
                assert row["pnl"] == 20.0
                assert row["synced_to_cloud"] == 0 # because we skipped push
        finally:
            try:
                os.unlink(path)
            except PermissionError:
                pass
