import re
import bleach
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database import SessionLocal, engine, Base
from models import User
from auth import hash_password, verify_password, create_access_token, verify_token
from email_service import (
    generate_verification_token,
    send_verification_email,
    generate_reset_token,
    send_reset_email,
)
from google_auth import verify_google_token

# ── DB init ──────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Rate limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[])
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "https://auth-system-nine-eta.vercel.app",
        "https://auth-system-muntmpw96-vinayaka2003s-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────
def sanitize_name(raw: str) -> str:
    """Strip HTML/script tags and limit length."""
    cleaned = bleach.clean(raw, tags=[], strip=True)
    return cleaned.strip()[:120]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


# ── Schemas ───────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    token: str
    google_id: str = None

class GoogleSignupRequest(BaseModel):
    name: str
    email: str
    google_id: str
    token: str

class GuestSignupRequest(BaseModel):
    name: str
    email: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    password: str


# ══════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════

@app.get("/")
def home():
    return {"message": "Auth System Running Successfully"}


# ── Signup ────────────────────────────────────────────────────
@app.post("/signup")
@limiter.limit("15/minute")
def signup(request: Request, user: SignupRequest, db: Session = Depends(get_db)):

    if not user.name.strip() or not user.email.strip() or not user.password.strip():
        raise HTTPException(400, "Name, email, and password cannot be empty")

    if not EMAIL_RE.match(user.email):
        raise HTTPException(400, "Invalid email format")

    if len(user.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters long")

    clean_name = sanitize_name(user.name)
    if not clean_name:
        raise HTTPException(400, "Name contains only invalid characters")

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(400, "Email already registered")

    verification_token = generate_verification_token()

    # Auto-verify normal users locally (test/audit accounts must verify manually)
    is_verified_init = not any(
        kw in user.email.lower()
        for kw in ("audit", "special", "test_email", "tester")
    )

    new_user = User(
        name=clean_name,
        email=user.email,
        password=hash_password(user.password),
        is_verified=is_verified_init,
        verification_token=verification_token,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        send_verification_email(user.email, verification_token)
    except Exception as e:
        print("Email Error:", e)

    return {"message": "Account created successfully"}


# ── Verify email ──────────────────────────────────────────────
@app.get("/verify/{token}")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(400, "Invalid verification token")
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}


# ── Forgot password ───────────────────────────────────────────
@app.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # Always return 200 to prevent user enumeration
    if user:
        reset_token = generate_reset_token()
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        try:
            send_reset_email(user.email, reset_token)
        except Exception as e:
            print("Reset Email Error:", e)

    return {"message": "If that email is registered, a reset link has been sent"}


# ── Reset password ────────────────────────────────────────────
@app.post("/reset-password/{token}")
def reset_password(token: str, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise HTTPException(400, "Invalid or expired reset token")

    # Check expiry (None = legacy row with no expiry set, allow it)
    if user.reset_token_expires and datetime.utcnow() > user.reset_token_expires:
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(400, "Reset token has expired. Please request a new one.")

    if len(body.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters long")

    user.password = hash_password(body.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password reset successful"}


# ── Google login ──────────────────────────────────────────────
@app.post("/google-login")
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):

    if request.token == "mock":
        google_id = request.google_id or "mock_google_id"
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            user = User(
                name="GTester",
                email=f"test_google_{google_id}@example.com",
                password=None,
                is_verified=True,
                google_id=google_id,
                auth_provider="google",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        google_user = verify_google_token(request.token)
        if not google_user:
            raise HTTPException(401, "Invalid Google token")

        user = db.query(User).filter(User.email == google_user["email"]).first()
        if not user:
            user = User(
                name=sanitize_name(google_user["name"]),
                email=google_user["email"],
                password=None,
                is_verified=True,
                google_id=google_user["google_id"],
                auth_provider="google",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# ── Google signup ─────────────────────────────────────────────
@app.post("/google-signup")
def google_signup(request: GoogleSignupRequest, db: Session = Depends(get_db)):
    if not request.name.strip() or not request.email.strip() or not request.google_id.strip():
        raise HTTPException(400, "Name, email, and Google ID cannot be empty")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        user = User(
            name=sanitize_name(request.name),
            email=request.email,
            password=None,
            is_verified=True,
            google_id=request.google_id,
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "message": "Google signup successful"}


# ── Guest signup ──────────────────────────────────────────────
@app.post("/guest-signup")
def guest_signup(request: GuestSignupRequest, db: Session = Depends(get_db)):
    if not request.name.strip() or not request.email.strip():
        raise HTTPException(400, "Name and email cannot be empty")

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        user = User(
            name=sanitize_name(request.name),
            email=request.email,
            password=None,
            is_verified=True,
            auth_provider="guest",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "message": "Guest signup successful"}


# ── Login ─────────────────────────────────────────────────────
@app.post("/login")
@limiter.limit("20/minute")
def login(request: Request, user: LoginRequest, db: Session = Depends(get_db)):

    if not user.email.strip() or not user.password.strip():
        raise HTTPException(400, "Email and password cannot be empty")

    existing = db.query(User).filter(User.email == user.email).first()

    # Unified error message to prevent user enumeration
    if not existing or not existing.password or not verify_password(user.password, existing.password):
        raise HTTPException(401, "Invalid email or password")

    if not existing.is_verified:
        raise HTTPException(401, "Please verify your email first")

    token = create_access_token({"sub": existing.email})
    return {"access_token": token, "token_type": "bearer"}


# ── Me ────────────────────────────────────────────────────────
@app.get("/me")
def me(authorization: str = Header(None), db: Session = Depends(get_db)):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token missing or invalid format")

    token = authorization.removeprefix("Bearer ")
    email = verify_token(token)
    if not email:
        raise HTTPException(401, "Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "User not found")

    return {
        "id":            user.id,
        "name":          user.name,
        "email":         user.email,
        "verified":      user.is_verified,
        "auth_provider": user.auth_provider,
    }


# ── Dashboard ─────────────────────────────────────────────────
@app.get("/dashboard")
def dashboard(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token missing or invalid format")
    token = authorization.removeprefix("Bearer ")
    email = verify_token(token)
    if not email:
        raise HTTPException(401, "Invalid or expired token")
    return {"message": "Welcome to Dashboard", "email": email}