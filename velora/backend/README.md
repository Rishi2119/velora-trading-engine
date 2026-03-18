# Backend Boundary (Optional)

Supabase is the primary backend for auth + database + RLS.

Use this folder for optional services:
- Broker adapters (FIX, REST)
- Risk engine workers
- AI scoring microservices
- Stripe webhook handlers

Keep all service credentials server-side and never expose private keys to client apps.
