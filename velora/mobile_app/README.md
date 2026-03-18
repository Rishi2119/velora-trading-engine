# Mobile App (Flutter)

## Architecture
- Presentation: screens + widgets
- Domain: entities + repository contracts
- Data: Supabase repository implementations
- State: Riverpod

## Core Features
- Google OAuth via Supabase
- Session-aware auth gate
- Trader dashboard with streak, discipline score, analytics chart
- Markets, Journal, Profile, Subscription screens

## Run

```bash
flutter pub get
flutter run --dart-define-from-file=.env
```

## Build AAB

```bash
flutter build appbundle --release --dart-define-from-file=.env
```
