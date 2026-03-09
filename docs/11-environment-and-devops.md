# 11 - Environment & DevOps

## Local Development
- Using Python `venv`.
- Configuration via `.env` files storing `KIMI_API_KEY`.
- Mocking the MT5 Manager on non-Windows environments if necessary.

## Production Profile
- **OS**: Windows Server or VPS explicitly for MetaTrader 5 Terminal compliance.
- **Process Management**: A daemon tool (like NSSM on Windows) to keep the `main.py` Python process running.
- **Agent API**: Exposing locally (e.g., `127.0.0.1:8000`), proxied securely if accessed externally by the Velora mobile app.
