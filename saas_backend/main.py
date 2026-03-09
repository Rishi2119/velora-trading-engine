from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from supabase import create_client, Client
import stripe
import logging

app = FastAPI(title="Velora SaaS API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Basic Supabase Auth Dependency Example
def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    
    # Verify via Supabase
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_response.user
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# ----- API Endpoint Placeholders -----

@app.get("/api/dashboard")
def get_dashboard_stats(user: dict = Depends(get_current_user)):
    # Retrieve user stats from Supabase DB via RPC or direct query
    # Placeholder response
    return {
        "balance": 10500.0,
        "win_rate": 65.5,
        "equity_curve": [],
        "ai_commentary": "Market is showing bullish divergence on H4..."
    }

@app.post("/api/checkout")
def create_checkout_session(plan: str):
    # Stripe checkout session logic based on Starter/Pro/Elite
    plan_prices = {
        "starter": "price_starter_dummy",
        "pro": "price_pro_dummy",
        "elite": "price_elite_dummy",
    }
    # Return checkout url
    return {"url": f"https://checkout.stripe.com/c/pay/{plan_prices.get(plan, 'starter')}"}

@app.post("/api/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Fulfill the purchase (update Supabase profiles table)
        # customer_id = session.get("customer")
        # Update user's subscription tier
        pass

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
