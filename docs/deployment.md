# Velora Deployment Guide

This guide covers the deployment of the Velora Trading Engine on a Windows environment (required for MetaTrader 5 terminal interaction).

## Prerequisites

- **Python 3.10+**
- **MetaTrader 5 Terminal** (Logged into your broker)
- **Supabase Account** (For remote journaling)
- **Telegram Bot** (For alerts)

## Environment Setup

Create a `.env` file in the root directory:

```env
# MT5 Credentials (Fallback)
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=MetaQuotes-Demo

# Encryption key (Generate with: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode()))
FERNET_KEY=your_base64_key

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id

# Engine Config
ENGINE_MODE=paper  # change to 'live' for real trading
LOG_LEVEL=INFO
```

## Running the Engine

### 1. Manual Start
```bash
# Install dependencies
pip install -r requirements.txt

# Start the Fast API backend
cd backend
python main.py

# In a separate terminal, start the Autonomous Engine
python main.py --engine
```

### 2. Production Watchdog
On Windows, use the provided `watchdog.bat` to ensure the engine restarts automatically if it crashes:

```batch
@echo off
:loop
python main.py --engine
timeout /t 10
goto loop
```

## Frontend Access

- **Web Dashboard**: `cd web_frontend && npm run dev` -> http://localhost:3000
- **Mobile App**: `cd velora_flutter && flutter run`

## Production Security Checklist

1. [ ] Ensure `ENGINE_MODE=live` only when ready.
2. [ ] Verify `FERNET_KEY` is backed up (losing it makes `accounts.db` unreadable).
3. [ ] Check that `logs/` directory exists and has write permissions.
4. [ ] Ensure MT5 Terminal has "Allow Algo Trading" enabled in Options -> Expert Advisors.
