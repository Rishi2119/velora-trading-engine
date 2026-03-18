# 07 - Monorepo Structure

```text
trading_engins/
├── autonomous_agent/       # Python Autonomous AI Backend
│   ├── agent/
│   │   ├── core/           # Loop, Reasoning, Decision frameworks
│   │   ├── execution/      # Risk guards, MT5 caller
│   │   └── memory/         # JSON memory handlers
│   ├── data/
│   ├── main.py
│   └── requirements.txt
├── mobile_app/             # Velora React Native / Expo App
│   ├── App.js
│   └── eas.json
├── docs/                   # Full Documentation Hub (Here)
└── find_expo_session.py    # Session Management script
```
