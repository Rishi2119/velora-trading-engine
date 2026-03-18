# Supabase Setup

1. Create a Supabase project.
2. Enable Google provider in Authentication -> Providers.
3. Run `schema.sql` in SQL Editor.
4. Set redirect URLs:
   - `https://<your-vercel-domain>/auth/callback`
   - `io.velora.trade://login-callback`
5. Copy URL + anon key into `mobile_app/.env` and `web_app/.env.local`.
6. Keep service role key server-side only.

## RLS Notes
- All tables have strict RLS enabled.
- Policies only allow each authenticated user to access rows with their own `user_id` / `id`.
- No broad anonymous access policies are included.
