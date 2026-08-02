import os
import secrets

from dotenv import load_dotenv
import resend

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def generate_verification_token():
    return secrets.token_urlsafe(32)


def generate_reset_token():
    return secrets.token_urlsafe(32)


def send_verification_email(
    to_email: str,
    verification_token: str
):

    verification_link = (
        f"http://127.0.0.1:8000/verify/{verification_token}"
    )

    params = {
        "from": "onboarding@resend.dev",
        "to": [to_email],
        "subject": "Verify Your Email",
        "html": f"""
        <h2>Welcome!</h2>

        <p>Please verify your email address.</p>

        <a href="{verification_link}">
            Verify Email
        </a>

        <p>{verification_link}</p>
        """
    }

    return resend.Emails.send(params)


def send_reset_email(
    to_email: str,
    reset_token: str
):

    reset_link = (
    f"http://127.0.0.1:5501/reset-password.html?token={reset_token}"
)

    params = {
        "from": "onboarding@resend.dev",
        "to": [to_email],
        "subject": "Reset Your Password",
        "html": f"""
        <h2>Password Reset</h2>

        <p>Click the link below to reset your password.</p>

        <a href="{reset_link}">
            Reset Password
        </a>

        <p>{reset_link}</p>
        """
    }

    return resend.Emails.send(params)


def send_test_email(
    to_email: str
):

    params = {
        "from": "onboarding@resend.dev",
        "to": [to_email],
        "subject": "Resend Test Email",
        "html": """
        <h1>Congratulations 🎉</h1>
        <p>Your Resend integration is working.</p>
        """
    }

    return resend.Emails.send(params)