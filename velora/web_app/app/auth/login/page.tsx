'use client';

import { signInWithGoogle } from '@/lib/services/auth-service';
import { toast } from 'sonner';

export default function LoginPage() {
  const onGoogleLogin = async () => {
    const { error } = await signInWithGoogle();
    if (error) {
      toast.error(error.message || 'Failed to start Google login flow.');
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <section className="velora-card w-full max-w-md p-6">
        <h1 className="font-display text-3xl">Welcome to Velora</h1>
        <p className="mt-2 text-slate-300">Continue with Google to secure your trading workspace.</p>
        <button
          onClick={onGoogleLogin}
          className="mt-6 w-full rounded-xl bg-electric px-4 py-3 font-semibold text-white"
        >
          Continue with Google
        </button>
      </section>
    </main>
  );
}
