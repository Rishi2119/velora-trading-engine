import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "mobile_api"))

from mt5_manager import mt5_manager
import json

MT5_CONFIG_PATH = os.path.join(BASE_DIR, "mobile_api", "mt5_config.json")

print("Reading config...")
with open(MT5_CONFIG_PATH) as f:
    cfg = json.load(f)

print(f"Connecting to account: {cfg.get('account')} on server: {cfg.get('server')}")
result = mt5_manager.connect(int(cfg.get('account')), cfg.get('password'), cfg.get('server'))
print("Result:", result)
