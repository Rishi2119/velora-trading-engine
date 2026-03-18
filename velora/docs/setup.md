# Setup Guide

## 1. Supabase Project

1. Create project in Supabase.
2. Authentication -> Providers -> enable Google.
3. SQL Editor -> run `../supabase/schema.sql`.
4. Add redirect URLs:
   - Web: `http://localhost:3000/dashboard`
   - Mobile deep link: `io.velora.trade://login-callback`

## 2. Web Environment

1. Copy `web_app/.env.example` -> `web_app/.env.local`
2. Fill:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY` (server-only)

## 3. Mobile Environment

1. Copy `mobile_app/.env.example` -> `mobile_app/.env`
2. Fill:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`

## 4. Run Locally

Web:
```bash
cd web_app
npm install
npm run dev
```

Mobile:
```bash
cd mobile_app
flutter pub get
flutter run --dart-define-from-file=.env
```

## 5. Security Validation Checklist

- Verify RLS enabled on all tables.
- Confirm each policy is `auth.uid()` scoped.
- Confirm no service role key in mobile/web bundles.
- Confirm Google OAuth redirect URLs are exact.
