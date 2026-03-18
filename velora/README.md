# VELORA TRADE TERMINAL

Production-ready full-stack trading platform scaffold with Flutter mobile, Next.js web, and Supabase backend.

## Monorepo Structure

```text
velora/
├── mobile_app/          # Flutter Android-first app
├── web_app/             # Next.js 14 web platform
├── supabase/            # SQL schema + backend setup docs
├── backend/             # Optional BFF / worker service boundary
└── docs/                # Setup + deployment runbooks
```

## Quick Start

1. Configure Supabase and run `supabase/schema.sql`.
2. Create `mobile_app/.env` and `web_app/.env.local` from examples.
3. Start mobile app:
   - `cd mobile_app`
   - `flutter pub get`
   - `flutter run --dart-define-from-file=.env`
4. Start web app:
   - `cd web_app`
   - `npm install`
   - `npm run dev`

See `docs/setup.md` and `docs/deployment.md` for full production instructions.
