"""
Phase 11 test gate — Account Manager tests.
Run: python -m pytest tests/test_account_manager.py -v
"""
import sys
import os
import pytest
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.account_manager import AccountManager, AccountCreate


class TestAccountManager:
    
    @pytest.fixture
    def test_db(self):
        """Yields a temporary in-memory database path."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except PermissionError:
            pass
        
    def test_encryption_and_decryption(self, test_db):
        am = AccountManager(db_path=test_db)
        
        password = "secret_password_123"
        enc = am.encrypt(password)
        
        assert enc != password
        assert type(enc) == bytes
        
        dec = am.decrypt(enc)
        assert dec == password
        
    def test_account_crud(self, test_db):
        am = AccountManager(db_path=test_db)
        
        # 1. Add Account
        acc = AccountCreate(
            name="Personal Live",
            server="MetaQuotes-Demo",
            login=1234567,
            password="mypassword",
            is_live=True
        )
        
        acc_id = am.add_account(acc)
        assert acc_id > 0
        
        # 2. Get Accounts (List)
        accounts = am.get_accounts()
        assert len(accounts) == 1
        assert accounts[0].login == 1234567
        assert accounts[0].is_live is True
        
        # 3. Get Credentials (includes decrypted password)
        creds = am.get_credentials(acc_id)
        assert creds is not None
        assert creds["login"] == 1234567
        assert creds["server"] == "MetaQuotes-Demo"
        assert creds["password"] == "mypassword"
        
        # 4. Duplicate Login should raise ValueError
        dup = AccountCreate(
            name="Duplicate",
            server="xyz",
            login=1234567,
            password="pwd"
        )
        with pytest.raises(ValueError):
            am.add_account(dup)
            
        # 5. Delete Account
        success = am.delete_account(acc_id)
        assert success is True
        
        # Verify deleted
        assert len(am.get_accounts()) == 0
        assert am.get_credentials(acc_id) is None
