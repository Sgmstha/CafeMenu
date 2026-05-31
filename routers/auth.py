"""
Campus Café - Authentication Router
------------------------------------
This router defines endpoints for user registration, user logins, cookie-based sessions,
profile retrieval, and simulated SMS OTP verification.

TODO:
    1. Implement rate limiting on login/OTP endpoints to protect against brute-force attacks.
    2. Add standard telephone number verification validation.
    3. Replace mock console prints of OTP codes with a live SMS API client (e.g. Twilio).
    4. Implement secure CSRF tokens for the authentication cookies.
"""

from fastapi import APIRouter, HTTPException, Response, Depends
from datetime import datetime, timedelta
import uuid

# Import schemas and database models
from models.database import db, UserCreate, UserLogin, OTPRequest, OTPVerify
from models.auth import hash_password, verify_password, create_token, generate_otp, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(user: UserCreate):
    """
    Registers a new student user.
    Creates a password hash and initializes a wallet with 0 NPR coins.
    """
    # Enforce uniqueness of phone number
    if user.phone in db.users:
        raise HTTPException(400, "Phone number is already registered")
        
    db.users[user.phone] = {
        "id": str(uuid.uuid4()),
        "name": user.name,
        "phone": user.phone,
        "password_hash": hash_password(user.password),
        "coins": 0.0,
        "role": "user",  # Default role is always user. Admins must be seeded.
        "points": 0,
    }
    return {"message": "Registered successfully"}


@router.post("/login")
def login(creds: UserLogin, response: Response):
    """
    Logs in a user, generates a JWT token, and writes it to an HTTP-only session cookie.
    """
    user = db.users.get(creds.phone)
    if not user or not verify_password(creds.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
        
    # Generate token containing basic user identifiers
    token = create_token({"phone": user["phone"], "name": user["name"], "role": user["role"]})
    
    # Store token in a secure, HTTP-only cookie to prevent XSS-based theft
    # TODO: In production, enable 'secure=True' to restrict cookies to HTTPS only
    response.set_cookie(
        "access_token", 
        token, 
        httponly=True, 
        max_age=86400,  # 24 hours expiry
        samesite="lax"
    )
    return {"message": "Login successful", "name": user["name"], "role": user["role"]}


@router.post("/logout")
def logout(response: Response):
    """
    Logs out the user by deleting their access token cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me")
def me(user=Depends(get_current_user)):
    """
    Returns authentication details and the wallet coin balance of the currently logged-in user.
    If the requester is a guest, returns authenticated: False.
    """
    if not user:
        return {"authenticated": False}
        
    u = db.users.get(user["phone"], {})
    return {
        "authenticated": True,
        "name": user["name"],
        "phone": user["phone"],
        "role": user["role"],
        "coins": u.get("coins", 0),  # Fetched dynamically from database
        "roll": u.get("roll"),
        "section": u.get("section"),
        "counter": u.get("counter"),
    }


# ── OTP Flow for Order Verification ──────────────────────────────────────────

@router.post("/send-otp")
def send_otp(req: OTPRequest):
    """
    Generates and registers an OTP code before allowing a customer to finalize an order.
    
    NOTE: Currently mocks SMS delivery by printing to console.
    """
    otp = generate_otp()
    
    # Register OTP code with a 5-minute expiration timestamp
    db.otp_store[req.phone] = {
        "otp": otp,
        "name": req.name,
        "expires": datetime.utcnow() + timedelta(minutes=5),
    }
    
    # Log code directly to console for testing/development
    print(f"[DEMO OTP] Phone: {req.phone}  OTP: {otp}")
    
    # Exposing the OTP directly in the API response is done only for demonstration convenience.
    # TODO: Remove "demo_otp" from return payload and integrate actual SMS API.
    return {"message": "OTP sent", "demo_otp": otp}


@router.post("/verify-otp")
def verify_otp(req: OTPVerify):
    """
    Validates the user's submitted OTP code.
    Wipes the OTP record upon successful verification.
    """
    record = db.otp_store.get(req.phone)
    if not record:
        raise HTTPException(400, "No active OTP request found for this number")
        
    # Check if the code has expired
    if datetime.utcnow() > record["expires"]:
        del db.otp_store[req.phone]
        raise HTTPException(400, "OTP has expired. Please request a new one.")
        
    # Check code match
    if record["otp"] != req.otp:
        raise HTTPException(400, "Invalid OTP code entered")
        
    # Clean up OTP record from store on success (single-use validation)
    del db.otp_store[req.phone]
    return {"verified": True, "name": record["name"]}
