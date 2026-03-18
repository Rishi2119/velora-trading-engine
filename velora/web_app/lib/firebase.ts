export function initFirebaseIfEnabled() {
  if (process.env.NEXT_PUBLIC_ENABLE_FIREBASE !== 'true') return null;

  // Add Firebase app initialization + analytics setup here.
  // Keep optional to avoid forcing Firebase in every deployment.
  return true;
}
