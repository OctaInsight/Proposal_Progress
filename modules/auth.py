"""
Octa Platform — Authentication Module
Handles registration, login, password reset and session management.
Uses the shared `octa_users` table in Supabase.
"""
import bcrypt
import streamlit as st
from datetime import datetime, timezone
from modules.database import db

APP_NAME = "octa_proposals"   # this app's identifier in apps_access list


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ── User lookups ──────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    resp = db().table("octa_users").select("*") \
        .eq("email", email.strip().lower()).execute()
    return resp.data[0] if resp.data else None


def get_user_by_username(username: str) -> dict | None:
    resp = db().table("octa_users").select("*") \
        .eq("username", username.strip()).execute()
    return resp.data[0] if resp.data else None


def get_user_by_id(uid: int) -> dict | None:
    resp = db().table("octa_users").select("*").eq("id", uid).execute()
    return resp.data[0] if resp.data else None


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(email: str, username: str, first_name: str,
                  last_name: str, password: str) -> tuple:
    """
    Create a new pending user.
    Returns (ok: bool, message: str, user: dict | None).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters.", None
    if "@" not in email:
        return False, "Invalid email address.", None
    if len(username) < 3:
        return False, "Username must be at least 3 characters.", None

    # Check uniqueness
    if get_user_by_email(email):
        return False, "This email is already registered.", None
    if get_user_by_username(username):
        return False, "This username is already taken.", None

    hashed = hash_password(password)
    try:
        resp = db().table("octa_users").insert({
            "email":         email.strip().lower(),
            "username":      username.strip(),
            "first_name":    first_name.strip(),
            "last_name":     last_name.strip(),
            "password_hash": hashed,
            "status":        "pending",
            "apps_access":   [],
            "role":          "user",
        }).execute()
        user = resp.data[0] if resp.data else None
        return True, "Registration submitted successfully.", user
    except Exception as e:
        return False, f"Registration failed: {e}", None


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(email: str, password: str) -> tuple:
    """
    Authenticate a user.
    Returns (ok: bool, message: str, user: dict | None).
    """
    user = get_user_by_email(email)
    if not user:
        return False, "No account found with this email.", None

    if user.get("status") == "pending":
        return False, "Your account is pending admin approval. You will receive an email once approved.", None
    if user.get("status") == "disabled":
        return False, "Your account has been disabled. Contact octainsight@gmail.com.", None

    if not verify_password(password, user.get("password_hash", "")):
        return False, "Incorrect password.", None

    # Check app access
    apps = user.get("apps_access") or []
    if isinstance(apps, str):
        import json
        try:    apps = json.loads(apps)
        except: apps = []
    if APP_NAME not in apps and user.get("role") != "admin":
        return False, f"Your account does not have access to this application.", None

    # Update last login
    db().table("octa_users") \
        .update({"last_login": datetime.now(timezone.utc).isoformat()}) \
        .eq("id", user["id"]).execute()

    return True, f"Welcome back, {user.get('first_name') or user.get('username')}!", user


# ── Password Reset ────────────────────────────────────────────────────────────

def request_password_reset(email: str) -> tuple:
    """
    Generate a reset token, store it, and send the email.
    Returns (ok, message).
    """
    user = get_user_by_email(email)
    if not user:
        # Don't reveal whether email exists
        return True, "If that email is registered, you will receive a reset link."

    from modules.email_utils import generate_reset_token, send_password_reset_email
    token, expires = generate_reset_token()

    db().table("octa_users").update({
        "reset_token":   token,
        "reset_expires": expires.isoformat(),
    }).eq("id", user["id"]).execute()

    try:
        app_url = st.secrets.get("app_url", "")
    except Exception:
        app_url = ""

    ok, err = send_password_reset_email(
        email, user.get("username", ""), token, app_url
    )
    if not ok:
        return False, f"Could not send reset email: {err}"
    return True, "Password reset email sent. Check your inbox."


def reset_password_with_token(token: str, new_password: str) -> tuple:
    """
    Validate token and update password.
    Returns (ok, message).
    """
    if len(new_password) < 8:
        return False, "Password must be at least 8 characters."

    resp = db().table("octa_users").select("*") \
        .eq("reset_token", token).execute()
    if not resp.data:
        return False, "Invalid or expired reset token."

    user    = resp.data[0]
    expires = user.get("reset_expires")
    if expires:
        from datetime import datetime, timezone
        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > exp_dt:
            return False, "Reset token has expired. Please request a new one."

    hashed = hash_password(new_password)
    db().table("octa_users").update({
        "password_hash": hashed,
        "reset_token":   None,
        "reset_expires": None,
    }).eq("id", user["id"]).execute()

    return True, "Password updated successfully. You can now log in."


# ── Session ───────────────────────────────────────────────────────────────────

def set_session(user: dict):
    apps = user.get("apps_access") or []
    if isinstance(apps, str):
        import json
        try:    apps = json.loads(apps)
        except: apps = []
    st.session_state.authenticated  = True
    st.session_state.user_id        = user["id"]
    st.session_state.username       = user.get("username", "")
    st.session_state.first_name     = user.get("first_name", "")
    st.session_state.last_name      = user.get("last_name", "")
    st.session_state.email          = user.get("email", "")
    st.session_state.role           = user.get("role", "user")
    st.session_state.apps_access    = apps


def clear_session():
    for k in ["authenticated","user_id","username","first_name",
              "last_name","email","role","apps_access"]:
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated"))


def require_auth():
    """Call at top of every protected page. Redirects to login if not authed."""
    if not is_authenticated():
        st.switch_page("pages/login.py")


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"
