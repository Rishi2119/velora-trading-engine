import { createClient } from '@/lib/supabase/client';

export async function signInWithGoogle() {
  const supabase = createClient();
  const redirectTo = `${window.location.origin}/auth/callback`;

  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo,
    },
  });

  return { error };
}

export async function signOut() {
  const supabase = createClient();
  return supabase.auth.signOut();
}
