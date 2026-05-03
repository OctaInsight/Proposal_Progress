"""
Octa Platform — Email Utilities
Sends auth emails via Gmail SMTP using an App Password.
All email content is plain text — no HTML dependencies.
"""
import smtplib
import secrets
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone


def _smtp_config() -> tuple:
    """Return (sender_email, app_password) from st.secrets."""
    try:
        return (
            st.secrets["email"]["sender"],
            st.secrets["email"]["password"],
        )
    except Exception:
        return None, None


def _send(to: str, subject: str, body: str) -> tuple:
    """
    Send a plain-text email via Gmail SMTP.
    Returns (ok: bool, error_message: str).
    """
    sender, password = _smtp_config()
    if not sender or not password:
        return False, "Email not configured in secrets.toml."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Octa Insight <{sender}>"
    msg["To"]      = to
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to, msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)


# ── Auth emails ───────────────────────────────────────────────────────────────

ADMIN_EMAIL = "octainsight@gmail.com"


def send_registration_emails(user: dict) -> tuple:
    """
    Send two emails on new registration:
    1. To admin — approval request
    2. To user  — confirmation that request is pending
    Returns (ok, error).
    """
    full_name = f"{user.get('first_name','')} {user.get('last_name','')}".strip()
    email     = user.get("email", "")
    username  = user.get("username", "")

    # ── Email 1: to admin ─────────────────────────────────────────────────────
    admin_body = f"""
New user registration — Octa Platform

Name:     {full_name}
Username: {username}
Email:    {email}
Time:     {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

To approve this account, go to:
  Octa Proposals → Admin Panel → Pending Users

Or approve directly in Supabase:
  UPDATE octa_users
  SET status = 'approved',
      approved_at = NOW(),
      approved_by = 'admin',
      apps_access = '["octa_proposals"]'
  WHERE email = '{email}';

—
Octa Platform · Automated Notification
""".strip()

    ok1, err1 = _send(ADMIN_EMAIL,
                      f"[Octa] New registration: {full_name} ({username})",
                      admin_body)

    # ── Email 2: to user ──────────────────────────────────────────────────────
    user_body = f"""
Hello {full_name or username},

Thank you for registering with the Octa Platform.

Your account is currently pending administrator approval.
You will receive another email once your account has been activated.

Your registration details:
  Username: {username}
  Email:    {email}

If you did not make this request, please ignore this email.

—
Octa Insight Team
octainsight@gmail.com
""".strip()

    ok2, err2 = _send(email,
                      "[Octa] Your registration is pending approval",
                      user_body)

    if not ok1 and not ok2:
        return False, f"Admin email: {err1} | User email: {err2}"
    return True, ""


def send_approval_email(user: dict) -> tuple:
    """Notify user that their account has been approved."""
    full_name = f"{user.get('first_name','')} {user.get('last_name','')}".strip()
    email     = user.get("email", "")
    apps      = user.get("apps_access") or []
    if isinstance(apps, str):
        import json
        try:    apps = json.loads(apps)
        except: apps = []
    apps_str = ", ".join(apps) if apps else "No apps assigned yet"

    body = f"""
Hello {full_name or user.get('username','')},

Great news — your Octa Platform account has been approved!

You can now log in at the application link shared with you.

Apps you have access to:
  {apps_str}

Your username: {user.get('username','')}

—
Octa Insight Team
octainsight@gmail.com
""".strip()

    return _send(email, "[Octa] Your account has been approved!", body)


def generate_reset_token() -> tuple:
    """
    Generate a secure reset token and its expiry (1 hour from now).
    Returns (token: str, expires_at: datetime).
    """
    token      = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return token, expires_at


def send_password_reset_email(email: str, username: str, token: str,
                              app_url: str = "") -> tuple:
    """Send a password reset email with a token link."""
    reset_url = f"{app_url}?reset_token={token}" if app_url else f"Token: {token}"

    body = f"""
Hello {username},

You requested a password reset for your Octa Platform account.

Use the token below in the password reset form:

  {reset_url}

This link expires in 1 hour.

If you did not request a password reset, please ignore this email.
Your password will not change.

—
Octa Insight Team
octainsight@gmail.com
""".strip()

    return _send(email, "[Octa] Password Reset Request", body)
