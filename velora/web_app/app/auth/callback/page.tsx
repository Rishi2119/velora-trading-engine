import { redirect } from 'next/navigation';

// After Supabase completes OAuth, just send the user to the dashboard.
// Our middleware will check the session and, if missing, redirect back to /auth/login.
export default function AuthCallbackPage() {
  redirect('/dashboard');
}
