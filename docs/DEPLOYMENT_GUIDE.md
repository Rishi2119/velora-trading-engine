# Velora Trading Platform - Deployment Guide

## 📋 Overview

Velora is an AI-powered trading platform with:
- **Backend**: FastAPI (Python) - Main API on port 8000
- **Mobile API**: Flask (Python) - Mobile support on port 5050
- **Web Frontend**: Next.js - Dashboard on port 3000
- **Mobile App**: Flutter - Android/iOS app
- **Trading Engine**: MT5 integration for live trading

## 🚀 Quick Start

### Option 1: Local Development

**Windows:**
```batch
start_production.bat
```

**Linux/Mac:**
```bash
chmod +x start_production.sh
./start_production.sh
```

### Option 2: Docker Compose

```bash
docker-compose up --build
```

## 📦 Manual Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Flutter SDK 3.11+
- MetaTrader 5 (for live trading)

### Backend Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r backend/requirements.txt
pip install flask flask-cors
```

4. Start FastAPI Backend:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

5. Start Flask Mobile API:
```bash
python mobile_api/app.py
```

### Web Frontend Setup

```bash
cd web_frontend
npm install
npm run dev
```

### Mobile App (Flutter) Build

1. Navigate to Flutter directory:
```bash
cd velora_flutter
```

2. Get dependencies:
```bash
flutter pub get
```

3. Build APK:
```bash
flutter build apk --release
```

APK will be at: `velora_flutter/build/app/outputs/flutter-apk/app-release.apk`

Or use the build script:
```batch
build_apk.bat
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# MT5 Credentials (REQUIRED for live trading)
MT5_ACCOUNT=10009891274
MT5_PASSWORD=yourpassword
MT5_SERVER=MetaQuotes-Demo

# Optional settings
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:///./velora.db
```

### Flutter App Configuration

Edit `velora_flutter/.env`:
```env
# For physical device testing on same WiFi
LOCAL_NETWORK_IP=192.168.1.xxx

# Production API URL
API_BASE_URL=https://api.velora.com/api/v1
```

## 🌐 API Endpoints

### FastAPI Backend (Port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger documentation |
| `/api/v1/auth/register` | POST | User registration |
| `/api/v1/auth/login` | POST | User login |
| `/api/v1/auth/me` | GET | Current user profile |
| `/api/v1/trading/stats` | GET | Account statistics |
| `/api/v1/trading/open-positions` | GET | Open trades |
| `/api/v1/trading/history` | GET | Trade history |
| `/api/v1/trading/mt5/status` | GET | MT5 connection status |
| `/api/v1/ai/status` | GET | AI Agent status |

### Flask Mobile API (Port 5050)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/stats` | GET | Account statistics |
| `/api/trades` | GET | All trades |
| `/api/open-trades` | GET | Open positions |
| `/api/performance` | GET | Performance metrics |
| `/api/mt5/status` | GET | MT5 connection |

## 🧪 Testing

Run automated tests:
```bash
python test_all.py
```

Tests verify:
- Backend health
- Mobile API health
- Web frontend
- User authentication
- Trading endpoints
- AI Agent status

## 🐳 Docker Deployment

### Build and Run
```bash
docker-compose up --build -d
```

### Services
- `backend` - FastAPI on port 8000
- `mobile_api` - Flask on port 5050
- `frontend` - Next.js on port 3000

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

## 📱 Mobile App Installation

1. Build the APK using `build_apk.bat`
2. Transfer `velora-release.apk` to your Android device
3. Enable "Install from unknown sources" in settings
4. Install and run

### Physical Device Testing

1. Find your computer's local IP (ipconfig / ifconfig)
2. Update `velora_flutter/.env`:
   ```
   LOCAL_NETWORK_IP=192.168.1.xxx
   ```
3. Rebuild APK and install

## 🔐 Security Notes

- Default JWT secret should be changed in production
- MT5 credentials stored in .env (never commit to git)
- API tokens auto-generated on first run
- Rate limiting enabled (100 req/min)

## 📂 Project Structure

```
trading_engins/
├── backend/              # FastAPI backend
│   ├── api/             # API routes
│   ├── config/          # Settings
│   ├── database/        # Models & migrations
│   └── utils/           # MT5 manager, security
├── mobile_api/          # Flask mobile API
├── web_frontend/        # Next.js dashboard
├── velora_flutter/      # Flutter mobile app
│   ├── lib/
│   │   ├── screens/    # UI screens
│   │   └── services/   # API clients
│   └── android/        # Android config
├── docker-compose.yml   # Docker orchestration
├── Dockerfile.backend   # Backend Docker image
├── Dockerfile.frontend  # Frontend Docker image
├── start_production.bat # Windows startup
├── start_production.sh  # Unix startup
├── build_apk.bat       # APK build script
└── test_all.py         # Automated tests
```

## 🆘 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.11+)
- Verify venv activated: should see `(venv)` in prompt
- Check port 8000 not in use

### Mobile app can't connect
- Ensure backend is running on port 8000
- Check LOCAL_NETWORK_IP in .env
- Verify both devices on same network

### MT5 not connecting
- MetaTrader 5 must be running
- Check credentials in .env
- Server name must match exactly

### Flutter build fails
- Run `flutter doctor` to check setup
- Ensure Flutter 3.11+ installed
- Run `flutter clean` then rebuild

## 📞 Support

For issues:
1. Check logs in `/logs` directory
2. Run `python test_all.py` to identify failing components
3. Review error messages in console output
