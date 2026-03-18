import { type NextRequest } from 'next/server';
import { updateSession } from '@/lib/supabase/middleware';

// Keep middleware only for keeping the Supabase session in sync with cookies.
// Route protection is handled inside pages/layouts instead of here to avoid
// redirect loops during the OAuth callback flow.
export async function middleware(request: NextRequest) {
  const response = await updateSession(request);
  return response;
}

export const config = {
  matcher: ['/dashboard/:path*', '/profile/:path*', '/auth/:path*'],
};
