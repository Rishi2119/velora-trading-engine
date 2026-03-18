# Deployment Guide

## Web (Vercel)

1. Push `velora/web_app` to Git repository.
2. Import into Vercel.
3. Set environment variables from `web_app/.env.example`.
4. Build command: `npm run build`
5. Output: `.next`
6. Add production Supabase OAuth redirect URL to Google and Supabase.

## Backend (Supabase)

1. Run `supabase/schema.sql` in production project.
2. Verify table RLS + policies in Table Editor.
3. Rotate anon and service keys if exposed.
4. Enable backups and PITR (paid tier recommended for production).

## Mobile (Android Play Store)

1. Create keystore:
```bash
keytool -genkey -v -keystore velora-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias velora
```
2. Configure `android/key.properties` and `build.gradle` signing config.
3. Build signed AAB:
```bash
flutter build appbundle --release --dart-define-from-file=.env
```
4. Upload `.aab` to Google Play Console.
5. Complete content rating, privacy policy, and production rollout.

## Play Store Checklist

- App signing configured
- Privacy policy URL live
- Crash reporting enabled
- Screenshots + feature graphic prepared
- Test track validated before production
