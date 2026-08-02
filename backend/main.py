from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header
)
from google_auth import verify_google_token
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

from email_service import (
    send_test_email,
    generate_verification_token,
    send_verification_email,
    generate_reset_token,
    send_reset_email
)
from google_auth import verify_google_token

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:5501",
        "http://localhost:5501"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str

class GoogleLoginRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    password: str


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@app.get("/")
def home():

    return {
        "message": "Auth System Running Successfully"
    }


@app.post("/signup")
def signup(
    user: SignupRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    verification_token = (
        generate_verification_token()
    )

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(
            user.password
        ),
        is_verified=False,
        verification_token=verification_token
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    try:
        send_verification_email(
            user.email,
            verification_token
        )
    except Exception as e:
        print("Email Error:", e)

    new_user.is_verified = True

    db.commit()

    return {
        "message":
        "Account created successfully"
    }


@app.get("/verify/{token}")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.verification_token == token
    ).first()

    if not user:

        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )

    user.is_verified = True
    user.verification_token = None

    db.commit()

    return {
        "message":
        "Email verified successfully"
    }


@app.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    reset_token = generate_reset_token()

    user.reset_token = reset_token

    db.commit()

    send_reset_email(
        user.email,
        reset_token
    )

    return {
        "message":
        "Password reset email sent"
    }


@app.post("/reset-password/{token}")
def reset_password(
    token: str,
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.reset_token == token
    ).first()

    if not user:

        raise HTTPException(
            status_code=400,
            detail="Invalid reset token"
        )

    user.password = hash_password(
        request.password
    )

    user.reset_token = None

    db.commit()

    return {
        "message":
        "Password reset successful"
    }

@app.post("/google-login")
def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db)
):

    google_user = verify_google_token(
        request.token
    )

    if not google_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid Google token"
        )

    user = db.query(User).filter(
        User.email == google_user["email"]
    ).first()

    if not user:

        user = User(
            name=google_user["name"],
            email=google_user["email"],
            password=None,
            is_verified=True,
            google_id=google_user["google_id"],
            auth_provider="google"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(
        {
            "sub": user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/login")
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not existing_user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        user.password,
        existing_user.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not existing_user.is_verified:

        raise HTTPException(
            status_code=401,
            detail="Please verify your email first"
        )

    token = create_access_token(
        {
            "sub": existing_user.email
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/me")
def me(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Token missing"
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    email = verify_token(token)

    if not email:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.email == email
    ).first()

    return {
    "id": user.id,
    "name": user.name,
    "email": user.email,
    "verified": user.is_verified,
    "provider": user.auth_provider
    }

@app.get("/dashboard")
def dashboard(
    authorization: str = Header(None)
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Token missing"
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    email = verify_token(token)

    if not email:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return {
        "message": "Welcome to Dashboard",
        "email": email
    }


@app.get("/test-email")
def test_email():

    response = send_test_email(
        "vinayaka2103sy@gmail.com"
    )

    return response