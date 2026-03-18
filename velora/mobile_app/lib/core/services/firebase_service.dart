class FirebaseService {
  static Future<void> initializeIfEnabled() async {
    const enableFirebase = bool.fromEnvironment('ENABLE_FIREBASE', defaultValue: false);
    if (!enableFirebase) return;

    // Add Firebase.initializeApp() and notification handlers here.
    // Keep initialization behind env flag for controlled rollout.
  }
}
