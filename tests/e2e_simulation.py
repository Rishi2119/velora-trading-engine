import requests
import time
import os

AI_API_URL = "http://localhost:8080"
JOURNAL_PATH = "logs/journal.csv"

def run_e2e_simulation():
    print("🚀 Starting End-to-End Signal Simulation...")
    
    # 1. Check AI Engine Health
    try:
        health = requests.get(f"{AI_API_URL}/health", timeout=5).json()
        print(f"[INIT] AI Engine Status: {health.get('status')} (Running: {health.get('running')})")
    except Exception as e:
        print(f"[ERROR] AI Engine not reachable: {e}")
        return

    # 2. Trigger Signal
    print("[ACTION] Triggering manual inference cycle...")
    try:
        signal_resp = requests.post(f"{AI_API_URL}/signal", timeout=30).json()
        print(f"[RESULT] Signal Action: {signal_resp.get('action')} (Confidence: {signal_resp.get('confidence')})")
        print(f"[DEBUG] Reason: {signal_resp.get('reason')}")
    except Exception as e:
        print(f"[ERROR] Signal trigger failed: {e}")
        return

    # 3. Verify Journal (if trade was executed)
    if signal_resp.get("ticket"):
        print(f"[SUCCESS] Trade executed! Ticket: {signal_resp.get('ticket')}")
        if os.path.exists(JOURNAL_PATH):
            with open(JOURNAL_PATH, 'r') as f:
                last_line = f.readlines()[-1]
                print(f"[JOURNAL] Last Entry: {last_line.strip()}")
        else:
            print("[WARNING] Journal file not found despite trade execution.")
    else:
        print("[INFO] No trade executed (Risk or Model filtered it). This is normal behavior.")

if __name__ == "__main__":
    run_e2e_simulation()
