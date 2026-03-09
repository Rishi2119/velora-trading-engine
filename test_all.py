"""
Velora Trading Platform - Automated Test Suite
Tests all API endpoints and system functionality
"""

import sys
import time
import requests
import json
from datetime import datetime

# Configuration
FASTAPI_BASE = "http://localhost:8000"
MOBILE_API_BASE = "http://localhost:5050"
WEB_FRONTEND = "http://localhost:3000"

# Test credentials
TEST_EMAIL = "test@velora.com"
TEST_PASSWORD = "test123456"
TEST_NAME = "Test User"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(msg, color=None):
    if color:
        print(f"{color}{msg}{Colors.END}")
    else:
        print(msg)

def test_result(name, success, details=""):
    if success:
        log(f"  ✓ {name}", Colors.GREEN)
    else:
        log(f"  ✗ {name}: {details}", Colors.RED)
    return success

class VeloraTestSuite:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.results = {"passed": 0, "failed": 0, "skipped": 0}
    
    def run_all_tests(self):
        log("\n" + "="*60, Colors.BLUE)
        log("     VELORA TRADING PLATFORM - AUTOMATED TEST SUITE", Colors.BLUE)
        log("="*60 + "\n", Colors.BLUE)
        
        # Test 1: Service Health Checks
        log("[1] SERVICE HEALTH CHECKS", Colors.YELLOW)
        self.test_fastapi_health()
        self.test_mobile_api_health()
        self.test_web_frontend()
        
        # Test 2: Authentication
        log("\n[2] AUTHENTICATION TESTS", Colors.YELLOW)
        self.test_register()
        self.test_login()
        self.test_me()
        
        # Test 3: Trading Endpoints
        log("\n[3] TRADING API TESTS", Colors.YELLOW)
        self.test_trading_stats()
        self.test_open_positions()
        self.test_trade_history()
        self.test_performance()
        self.test_kill_switch()
        self.test_mt5_status()
        
        # Test 4: Mobile API Endpoints
        log("\n[4] MOBILE API TESTS", Colors.YELLOW)
        self.test_mobile_stats()
        self.test_mobile_trades()
        self.test_mobile_performance()
        
        # Test 5: AI Agent Endpoints
        log("\n[5] AI AGENT TESTS", Colors.YELLOW)
        self.test_ai_status()
        
        # Summary
        self.print_summary()
        
        return self.results["failed"] == 0
    
    # ─── Health Checks ────────────────────────────────────────────────────
    
    def test_fastapi_health(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/health", timeout=5)
            success = r.status_code == 200 and r.json().get("status") == "ok"
            if test_result("FastAPI Backend Health", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("FastAPI Backend Health", False, str(e))
            self.results["failed"] += 1
    
    def test_mobile_api_health(self):
        try:
            r = requests.get(f"{MOBILE_API_BASE}/api/health", timeout=5)
            success = r.status_code == 200 and r.json().get("status") == "ok"
            if test_result("Mobile API Health", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Mobile API Health", False, str(e))
            self.results["failed"] += 1
    
    def test_web_frontend(self):
        try:
            r = requests.get(WEB_FRONTEND, timeout=5)
            success = r.status_code == 200
            if test_result("Web Frontend", success, f"Status {r.status_code}"):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Web Frontend", False, str(e))
            self.results["failed"] += 1
    
    # ─── Authentication ───────────────────────────────────────────────────
    
    def test_register(self):
        try:
            r = requests.post(f"{FASTAPI_BASE}/api/v1/auth/register", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": TEST_NAME
            }, timeout=10)
            # 201 = new user, 409 = already exists (both acceptable)
            success = r.status_code in [201, 409]
            if r.status_code == 201:
                data = r.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
            if test_result("User Registration", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("User Registration", False, str(e))
            self.results["failed"] += 1
    
    def test_login(self):
        try:
            r = requests.post(f"{FASTAPI_BASE}/api/v1/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }, timeout=10)
            success = r.status_code == 200
            if success:
                data = r.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user_id")
            if test_result("User Login", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("User Login", False, str(e))
            self.results["failed"] += 1
    
    def test_me(self):
        if not self.token:
            test_result("Get User Profile", False, "No token available")
            self.results["skipped"] += 1
            return
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/auth/me", 
                           headers={"Authorization": f"Bearer {self.token}"}, timeout=10)
            success = r.status_code == 200 and "email" in r.json()
            if test_result("Get User Profile", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Get User Profile", False, str(e))
            self.results["failed"] += 1
    
    # ─── Trading Endpoints ────────────────────────────────────────────────
    
    def test_trading_stats(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/trading/stats", timeout=10)
            success = r.status_code == 200 and "account_balance" in r.json()
            if test_result("Trading Stats", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Trading Stats", False, str(e))
            self.results["failed"] += 1
    
    def test_open_positions(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/trading/open-positions", timeout=10)
            success = r.status_code == 200 and "trades" in r.json()
            if test_result("Open Positions", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Open Positions", False, str(e))
            self.results["failed"] += 1
    
    def test_trade_history(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/trading/history", timeout=10)
            success = r.status_code == 200 and "trades" in r.json()
            if test_result("Trade History", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Trade History", False, str(e))
            self.results["failed"] += 1
    
    def test_performance(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/trading/performance", timeout=10)
            success = r.status_code == 200
            if test_result("Performance Data", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Performance Data", False, str(e))
            self.results["failed"] += 1
    
    def test_kill_switch(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/trading/kill-switch", timeout=10)
            success = r.status_code == 200 and "active" in r.json()
            if test_result("Kill Switch Status", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Kill Switch Status", False, str(e))
            self.results["failed"] += 1
    
    def test_mt5_status(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/trading/mt5/status", timeout=10)
            success = r.status_code == 200 and "connected" in r.json()
            if test_result("MT5 Status", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("MT5 Status", False, str(e))
            self.results["failed"] += 1
    
    # ─── Mobile API Endpoints ─────────────────────────────────────────────
    
    def test_mobile_stats(self):
        try:
            r = requests.get(f"{MOBILE_API_BASE}/api/stats", timeout=10)
            success = r.status_code == 200 and "account_balance" in r.json()
            if test_result("Mobile API Stats", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Mobile API Stats", False, str(e))
            self.results["failed"] += 1
    
    def test_mobile_trades(self):
        try:
            r = requests.get(f"{MOBILE_API_BASE}/api/trades", timeout=10)
            success = r.status_code == 200 and "trades" in r.json()
            if test_result("Mobile API Trades", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Mobile API Trades", False, str(e))
            self.results["failed"] += 1
    
    def test_mobile_performance(self):
        try:
            r = requests.get(f"{MOBILE_API_BASE}/api/performance", timeout=10)
            success = r.status_code == 200
            if test_result("Mobile API Performance", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("Mobile API Performance", False, str(e))
            self.results["failed"] += 1
    
    # ─── AI Agent Endpoints ───────────────────────────────────────────────
    
    def test_ai_status(self):
        try:
            r = requests.get(f"{FASTAPI_BASE}/api/v1/ai/status", timeout=10)
            success = r.status_code == 200
            if test_result("AI Agent Status", success, r.text[:100] if not success else ""):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
        except Exception as e:
            test_result("AI Agent Status", False, str(e))
            self.results["failed"] += 1
    
    # ─── Summary ──────────────────────────────────────────────────────────
    
    def print_summary(self):
        log("\n" + "="*60, Colors.BLUE)
        log("                      TEST SUMMARY", Colors.BLUE)
        log("="*60, Colors.BLUE)
        
        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        
        log(f"\n  Total Tests:  {total}")
        log(f"  Passed:       {self.results['passed']}", Colors.GREEN)
        log(f"  Failed:       {self.results['failed']}", Colors.RED if self.results['failed'] > 0 else None)
        log(f"  Skipped:      {self.results['skipped']}", Colors.YELLOW if self.results['skipped'] > 0 else None)
        
        if self.results["failed"] == 0:
            log(f"\n  ✓ ALL TESTS PASSED!", Colors.GREEN)
        else:
            log(f"\n  ✗ SOME TESTS FAILED", Colors.RED)
        
        log("\n" + "="*60 + "\n", Colors.BLUE)


if __name__ == "__main__":
    suite = VeloraTestSuite()
    success = suite.run_all_tests()
    sys.exit(0 if success else 1)
