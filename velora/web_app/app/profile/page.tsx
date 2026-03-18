'use client';

import { signOut } from '@/lib/services/auth-service';

export default function ProfilePage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <section className="velora-card p-6">
        <h1 className="font-display text-3xl">Profile</h1>
        <p className="mt-2 text-slate-300">Manage account, behavior metrics, and security settings.</p>
        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl bg-white/5 p-4">
            <p className="text-slate-400">Current Tier</p>
            <p className="mt-1 text-xl text-premium">Pro</p>
          </div>
          <div className="rounded-xl bg-white/5 p-4">
            <p className="text-slate-400">Risk Style</p>
            <p className="mt-1 text-xl">Moderate</p>
          </div>
        </div>
        <button onClick={() => signOut()} className="mt-6 rounded-xl border border-white/30 px-4 py-2">
          Sign Out
        </button>
      </section>
    </main>
  );
}
