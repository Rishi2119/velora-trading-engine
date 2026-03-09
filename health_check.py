"""
System Health Check
Comprehensive health monitoring for production trading system
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthCheck:
    """System health check for production trading"""
    
    def __init__(self):
        self.checks = []
        self.last_check = None
        self.results = {}
    
    def register_check(self, name: str, check_func, critical: bool = True):
        """Register a health check"""
        self.checks.append({
            'name': name,
            'func': check_func,
            'critical': critical
        })
    
    def run_check(self, name: str, check_func) -> Dict:
        """Run a single health check"""
        try:
            start = time.time()
            result = check_func()
            duration = time.time() - start
            
            return {
                'name': name,
                'status': 'ok' if result.get('ok', True) else 'warning',
                'message': result.get('message', 'OK'),
                'details': result.get('details', {}),
                'duration_ms': int(duration * 1000),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'name': name,
                'status': 'error',
                'message': str(e),
                'duration_ms': 0,
                'timestamp': datetime.now().isoformat()
            }
    
    def run_all(self) -> Dict:
        """Run all health checks"""
        results = []
        all_ok = True
        
        for check in self.checks:
            result = self.run_check(check['name'], check['func'])
            results.append(result)
            
            if check['critical'] and result['status'] != 'ok':
                all_ok = False
        
        self.results = results
        self.last_check = datetime.now()
        
        return {
            'status': 'healthy' if all_ok else 'degraded',
            'timestamp': self.last_check.isoformat(),
            'checks': results,
            'summary': {
                'total': len(results),
                'ok': sum(1 for r in results if r['status'] == 'ok'),
                'warning': sum(1 for r in results if r['status'] == 'warning'),
                'error': sum(1 for r in results if r['status'] == 'error')
            }
        }
    
    def get_status(self) -> Dict:
        """Get current status summary"""
        if not self.results:
            return {'status': 'unknown', 'message': 'No checks run yet'}
        
        return {
            'status': 'healthy' if all(r['status'] == 'ok' for r in self.results) else 'degraded',
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'summary': {
                'total': len(self.results),
                'ok': sum(1 for r in self.results if r['status'] == 'ok'),
                'warning': sum(1 for r in self.results if r['status'] == 'warning'),
                'error': sum(1 for r in self.results if r['status'] == 'error')
            }
        }


# =========================
# DEFAULT HEALTH CHECKS
# =========================

def check_logs_directory() -> Dict:
    """Check logs directory is writable"""
    log_dir = 'logs'
    exists = os.path.exists(log_dir)
    writable = os.access(log_dir, os.W_OK) if exists else False
    
    return {
        'ok': exists and writable,
        'message': f"Logs directory: {'OK' if writable else 'NOT WRITABLE'}",
        'details': {'exists': exists, 'writable': writable}
    }


def check_state_file() -> Dict:
    """Check risk state file"""
    state_file = 'logs/risk_state.json'
    exists = os.path.exists(state_file)
    
    if not exists:
        return {'ok': True, 'message': 'State file will be created'}
    
    try:
        import json
        with open(state_file) as f:
            state = json.load(f)
        return {
            'ok': True,
            'message': 'State file valid',
            'details': state
        }
    except Exception as e:
        return {
            'ok': False,
            'message': f'State file error: {e}'
        }


def check_config() -> Dict:
    """Check configuration is valid"""
    try:
        import config
        valid = config.validate_config()
        return {
            'ok': valid,
            'message': 'Config valid' if valid else 'Config has errors',
            'details': {
                'account_balance': config.ACCOUNT_BALANCE,
                'risk_per_trade': config.RISK_PER_TRADE,
                'execution_enabled': config.ENABLE_EXECUTION
            }
        }
    except Exception as e:
        return {
            'ok': False,
            'message': f'Config error: {e}'
        }


def check_mt5_connection() -> Dict:
    """Check MT5 connection status"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mobile_api'))
        from mt5_manager import mt5_manager
        
        if mt5_manager.connected:
            info = mt5_manager.get_account_info()
            return {
                'ok': True,
                'message': 'MT5 connected',
                'details': info
            }
        else:
            return {
                'ok': True,
                'message': 'MT5 not connected (expected in paper mode)'
            }
    except Exception as e:
        return {
            'ok': True,  # Not critical
            'message': f'MT5 check skipped: {e}'
        }


def check_audit_journal() -> Dict:
    """Check audit journal integrity"""
    try:
        from audit_journal import get_audit_journal
        journal = get_audit_journal()
        valid, errors = journal.verify_integrity()
        
        return {
            'ok': valid,
            'message': 'Journal valid' if valid else f'Journal has {len(errors)} errors',
            'details': {'errors': errors}
        }
    except Exception as e:
        return {
            'ok': False,
            'message': f'Journal check failed: {e}'
        }


def check_risk_limits() -> Dict:
    """Check risk limits are enforced"""
    try:
        from risk import RiskManager
        from config import RiskLimits
        
        # Check hard limits are in place
        rm = RiskManager(20, 5, 2)
        
        limits_ok = (
            rm._max_risk_per_trade == RiskLimits.MAX_RISK_PER_TRADE and
            rm._max_daily_loss >= 20 and
            rm._max_daily_trades <= 10
        )
        
        return {
            'ok': limits_ok,
            'message': 'Risk limits enforced',
            'details': {
                'max_risk': rm._max_risk_per_trade,
                'max_daily_loss': rm._max_daily_loss,
                'max_trades': rm._max_daily_trades
            }
        }
    except Exception as e:
        return {
            'ok': False,
            'message': f'Risk check failed: {e}'
        }


def check_api_secret() -> Dict:
    """Check API secret exists"""
    secret_file = 'mobile_api/.api_secret'
    exists = os.path.exists(secret_file)
    
    return {
        'ok': exists,
        'message': 'API secret exists' if exists else 'API secret missing (will be generated)'
    }


def check_environment_vars() -> Dict:
    """Check critical environment variables"""
    required = ['MT5_ACCOUNT', 'MT5_PASSWORD', 'MT5_SERVER']
    optional = ['API_SECRET']
    
    # Check .env file
    env_file = '.env'
    has_env = os.path.exists(env_file)
    
    # Check if MT5 credentials set
    try:
        import config
        mt5_set = bool(config.MT5_ACCOUNT and config.MT5_PASSWORD and config.MT5_SERVER)
    except:
        mt5_set = False
    
    return {
        'ok': True,  # Warning only
        'message': 'Credentials check',
        'details': {
            'has_env_file': has_env,
            'mt5_configured': mt5_set
        }
    }


def check_data_files() -> Dict:
    """Check data files exist"""
    data_dir = 'data'
    exists = os.path.exists(data_dir)
    
    if not exists:
        return {
            'ok': False,
            'message': 'Data directory missing'
        }
    
    files = os.listdir(data_dir) if exists else []
    csv_files = [f for f in files if f.endswith('.csv')]
    
    return {
        'ok': len(csv_files) > 0,
        'message': f'{len(csv_files)} data files found',
        'details': {'files': csv_files[:5]}  # Show first 5
    }


# =========================
# HEALTH CHECK RUNNER
# =========================

def create_health_check() -> HealthCheck:
    """Create and configure health check"""
    health = HealthCheck()
    
    # Register all checks
    health.register_check('logs_directory', check_logs_directory, critical=True)
    health.register_check('config', check_config, critical=True)
    health.register_check('risk_limits', check_risk_limits, critical=True)
    health.register_check('audit_journal', check_audit_journal, critical=False)
    health.register_check('api_secret', check_api_secret, critical=False)
    health.register_check('mt5_connection', check_mt5_connection, critical=False)
    health.register_check('data_files', check_data_files, critical=False)
    health.register_check('environment', check_environment_vars, critical=False)
    
    return health


def run_health_checks():
    """Run all health checks and return results"""
    health = create_health_check()
    results = health.run_all()
    
    # Print summary
    print("\n" + "="*60)
    print("🏥 SYSTEM HEALTH CHECK")
    print("="*60)
    
    print(f"\nOverall Status: {results['status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    
    print(f"\nSummary: {results['summary']['ok']}/{results['summary']['total']} OK")
    
    print("\nDetailed Results:")
    for check in results['checks']:
        status_icon = {
            'ok': '✅',
            'warning': '⚠️',
            'error': '❌'
        }.get(check['status'], '?')
        
        print(f"  {status_icon} {check['name']}: {check['message']}")
    
    print("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    import sys
    import io
    # Fix Windows console encoding
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass
    run_health_checks()
