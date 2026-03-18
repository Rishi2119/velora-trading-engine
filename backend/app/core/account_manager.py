import os
import sqlite3
import logging
from typing import List, Dict, Optional
from cryptography.fernet import Fernet
from pydantic import BaseModel

from backend.app.core.config import config

logger = logging.getLogger(__name__)


class AccountCreate(BaseModel):
    name: str
    server: str
    login: int
    password: str
    is_live: bool = False

class AccountResponse(BaseModel):
    id: int
    name: str
    server: str
    login: int
    is_live: bool


class AccountManager:
    """Manages MT5 user accounts with Fernet-encrypted passwords stored in SQLite."""
    
    def __init__(self, db_path: str = "logs/accounts.db", encryption_key: str = None):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # In a real system, the encryption key must be in .env. We fallback to a temporary one for safety.
        # But a temp one means passwords are lost on restart.
        key = encryption_key or os.getenv("FERNET_KEY")
        if not key:
            logger.warning("No FERNET_KEY found in env! Generating a temporary key.")
            key = Fernet.generate_key().decode()
            
        self.cipher = Fernet(key.encode())
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    server TEXT NOT NULL,
                    login INTEGER UNIQUE NOT NULL,
                    password_encrypted BLOB NOT NULL,
                    is_live BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            
    def encrypt(self, password: str) -> bytes:
        return self.cipher.encrypt(password.encode())
        
    def decrypt(self, encrypted_password: bytes) -> str:
        return self.cipher.decrypt(encrypted_password).decode()
        
    def add_account(self, acc: AccountCreate) -> int:
        enc_pass = self.encrypt(acc.password)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO accounts (name, server, login, password_encrypted, is_live) VALUES (?, ?, ?, ?, ?)",
                    (acc.name, acc.server, acc.login, enc_pass, acc.is_live)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Account with login {acc.login} already exists.")
            
    def get_accounts(self) -> List[AccountResponse]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id, name, server, login, is_live FROM accounts").fetchall()
            return [
                AccountResponse(id=r["id"], name=r["name"], server=r["server"], login=r["login"], is_live=bool(r["is_live"]))
                for r in rows
            ]
            
    def delete_account(self, account_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            return cursor.rowcount > 0
            
    def get_credentials(self, account_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
            if not row:
                return None
                
            return {
                "server": row["server"],
                "login": row["login"],
                "password": self.decrypt(row["password_encrypted"])
            }

# Singleton
account_manager = AccountManager()
