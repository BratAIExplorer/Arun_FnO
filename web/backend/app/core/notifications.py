"""
Notification Core - Sends emails for auth (signup, reset) and trading alerts
"""
import os
import logging
from email.message import EmailMessage
import aiosmtplib

logger = logging.getLogger(__name__)

async def send_email(subject: str, recipient: str, body: str, html_body: str = None):
    """
    Sends an email using system SMTP settings or user-provided SMTP settings.
    Defaulting to system settings for auth emails.
    """
    host = os.getenv("SYSTEM_SMTP_HOST")
    port = int(os.getenv("SYSTEM_SMTP_PORT", 587))
    user = os.getenv("SYSTEM_SMTP_USER")
    password = os.getenv("SYSTEM_SMTP_PASS")

    if not all([host, user, password]):
        logger.warning(f"⚠️ SMTP settings not configured. Cannot send email to {recipient}.")
        # For development debugging, we log the "email" content
        logger.info(f"--- [MOCK EMAIL] ---\nTo: {recipient}\nSubject: {subject}\nBody: {body}\n-------------------")
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = recipient
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        await aiosmtplib.send(
            msg,
            hostname=host,
            port=port,
            username=user,
            password=password,
            use_tls=(port == 465),
            start_tls=(port == 587),
        )
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send email to {recipient}: {e}")
        return False


async def send_confirmation_email(email: str, token: str, domain: str):
    """Send email confirmation link to new user"""
    link = f"{domain}/api/auth/confirm-email?token={token}"
    subject = "Confirm your F&O Sentinel account"
    body = f"Please confirm your account by clicking this link: {link}"
    html = f"""
    <html>
        <body style="font-family: sans-serif; background: #f4f4f4; padding: 20px;">
            <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto;">
                <h2 style="color: #0A84FF;">Welcome to F&O Sentinel 🍏</h2>
                <p>Please click the button below to confirm your account and start trading.</p>
                <a href="{link}" style="display: inline-block; background: #0A84FF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;">Confirm Email</a>
                <p style="font-size: 0.8rem; color: #888; margin-top: 20px;">If you didn't sign up for an account, you can safely ignore this email.</p>
            </div>
        </body>
    </html>
    """
    return await send_email(subject, email, body, html)


async def send_reset_email(email: str, token: str, domain: str):
    """Send password reset link"""
    link = f"{domain}/reset-password?token={token}"
    subject = "Reset your F&O Sentinel password"
    body = f"Click here to reset your password: {link}"
    html = f"""
    <html>
        <body style="font-family: sans-serif; background: #f4f4f4; padding: 20px;">
            <div style="background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto;">
                <h2 style="color: #FF453A;">Reset Password 🔑</h2>
                <p>We received a request to reset your password. If this was you, click the button below:</p>
                <a href="{link}" style="display: inline-block; background: #FF453A; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin-top: 10px;">Reset Password</a>
                <p style="font-size: 0.8rem; color: #888; margin-top: 20px;">This link will expire in 1 hour. If you didn't request a reset, you can ignore this.</p>
            </div>
        </body>
    </html>
    """
    return await send_email(subject, email, body, html)
