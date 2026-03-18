import firebase_admin
from firebase_admin import auth, credentials
import os
import logging

from backend.config.settings import settings
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not settings.ENABLE_FIREBASE:
        logger.info("Firebase is disabled via settings. Skipping initialization.")
        return False
        
    if firebase_admin._apps:
        return True
        
    try:
        # Check multiple possible locations for service account
        possible_paths = [
            os.path.join(os.getcwd(), "firebase-service-account.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "firebase-service-account.json"),
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        ]
        
        for path in filter(None, possible_paths):
            if os.path.exists(path):
                try:
                    cred = credentials.Certificate(path)
                    firebase_admin.initialize_app(cred)
                    logger.info(f"Firebase Admin initialized from {path}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to initialize Firebase from {path}: {e}")
        
        # Fallback to project_id from settings
        project_id = settings.FIREBASE_PROJECT_ID
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
            firebase_admin.initialize_app(options={'projectId': project_id})
            logger.info(f"Firebase initialized with Project ID: {project_id}")
        else:
            firebase_admin.initialize_app()
            logger.warning("Firebase initialized with default credentials (no service account or project ID found).")
        return True
    except Exception as e:
        logger.error(f"Critical: Firebase Admin initialization failed: {e}")
        return False


# Trigger initialization
initialize_firebase()



def verify_firebase_token(id_token: str):
    """
    Verifies a Firebase ID token.
    Returns the decoded token (claims) if valid, or raises an exception.
    """
    if not settings.ENABLE_FIREBASE:
        raise ValueError("Firebase authentication is currently disabled.")

    try:
        # Check if initialized
        if not firebase_admin._apps:
            if not initialize_firebase():
                raise ValueError("Firebase Admin SDK failed to initialize.")
            
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token

    except Exception as e:
        logger.error(f"Error verifying Firebase token: {str(e)}", exc_info=True)
        raise ValueError(f"Invalid Firebase token: {str(e)}")

def get_or_create_user_from_firebase(decoded_token: dict):
    """
    Business logic to extract user info from the verified token.
    You can use this to sync with your local database if needed.
    """
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    name = decoded_token.get("name")
    picture = decoded_token.get("picture")
    
    return {
        "uid": uid,
        "email": email,
        "name": name,
        "picture": picture
    }
