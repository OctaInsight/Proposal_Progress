"""
Octa Platform — Login Page
Sign In · Register · Forgot Password
"""
import streamlit as st
from modules.ui_helpers import inject_css, DARK
from modules.auth import (
    login_user, register_user, set_session,
    request_password_reset, reset_password_with_token, is_authenticated
)
from modules.email_utils import send_registration_emails

st.set_page_config(
    page_title="Login — Octa Platform",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="collapsed",
)
inject_css()

# Redirect if already logged in
if is_authenticated():
    st.switch_page("app.py")

# Check for password reset token in URL
params = st.query_params
reset_token = params.get("reset_token", "")

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:2rem 0 1.5rem">
    <div style="font-size:3rem">📋</div>
    <h1 style="color:white;font-size:2rem;font-weight:800;
               margin:0.4rem 0 0.2rem;letter-spacing:-1px">
        Octa Platform
    </h1>
    <p style="color:{DARK['muted']};font-size:0.95rem;margin:0">
        Proposal tracking &amp; partner management
    </p>
</div>
""", unsafe_allow_html=True)

# ── Password reset flow (token in URL) ───────────────────────────────────────
if reset_token:
    st.markdown(f"""
    <div style="background:{DARK['bg2']};border:1px solid {DARK['border']};
                border-left:4px solid {DARK['accent']};border-radius:12px;
                padding:1.5rem;margin-bottom:1rem">
        <h3 style="color:white;margin:0 0 1rem">🔑 Reset Your Password</h3>
    </div>
    """, unsafe_allow_html=True)
    new_pw  = st.text_input("New password",     type="password",
                             placeholder="At least 8 characters")
    new_pw2 = st.text_input("Confirm password", type="password",
                             placeholder="Repeat new password")
    if st.button("✅ Set New Password", type="primary", use_container_width=True):
        if new_pw != new_pw2:
            st.error("Passwords do not match.")
        else:
            ok, msg = reset_password_with_token(reset_token, new_pw)
            if ok:
                st.success(msg)
                st.query_params.clear()
                st.info("You can now sign in with your new password.")
            else:
                st.error(msg)
    st.stop()

# ── Auth tabs ─────────────────────────────────────────────────────────────────
tab_login, tab_register, tab_forgot = st.tabs(
    ["🔑  Sign In", "✨  Register", "🔓  Forgot Password"]
)

# ────────────────────────────────────────────────────────────────────────────
# SIGN IN
# ────────────────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    login_email = st.text_input("Email address", key="li_email",
                                placeholder="you@example.com")
    login_pass  = st.text_input("Password", type="password", key="li_pass",
                                placeholder="Your password")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Sign In →", type="primary", use_container_width=True,
                 key="btn_login"):
        if not login_email or not login_pass:
            st.warning("Please fill in both fields.")
        else:
            ok, msg, user = login_user(login_email, login_pass)
            if ok:
                set_session(user)
                st.success(msg)
                st.switch_page("app.py")
            else:
                st.error(f"❌ {msg}")

# ────────────────────────────────────────────────────────────────────────────
# REGISTER
# ────────────────────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("📋 After registration, an admin will review and activate your account. "
            "You'll receive an email confirmation.")

    rc1, rc2 = st.columns(2)
    with rc1:
        reg_first = st.text_input("First name *", key="reg_first",
                                  placeholder="Maria")
    with rc2:
        reg_last  = st.text_input("Last name *",  key="reg_last",
                                  placeholder="Rossi")

    reg_username = st.text_input("Username *", key="reg_uname",
                                 placeholder="mariarossi")
    reg_email    = st.text_input("Email address *", key="reg_email",
                                 placeholder="you@example.com")

    rc3, rc4 = st.columns(2)
    with rc3:
        reg_pass  = st.text_input("Password *",         type="password",
                                  key="reg_pass",  placeholder="Min 8 characters")
    with rc4:
        reg_pass2 = st.text_input("Confirm password *", type="password",
                                  key="reg_pass2", placeholder="Repeat password")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Submit Registration →", type="primary",
                 use_container_width=True, key="btn_register"):
        if reg_pass != reg_pass2:
            st.error("❌ Passwords do not match.")
        elif not all([reg_first, reg_last, reg_username, reg_email, reg_pass]):
            st.warning("Please fill in all required fields.")
        else:
            ok, msg, user = register_user(
                reg_email, reg_username,
                reg_first, reg_last, reg_pass
            )
            if ok and user:
                # Send notification emails
                email_ok, email_err = send_registration_emails(user)
                st.success("✅ Registration submitted! You will receive a confirmation email.")
                if not email_ok:
                    st.warning(f"⚠️ Could not send notification emails: {email_err}")
            elif ok:
                st.success("✅ Registration submitted!")
            else:
                st.error(f"❌ {msg}")

# ────────────────────────────────────────────────────────────────────────────
# FORGOT PASSWORD
# ────────────────────────────────────────────────────────────────────────────
with tab_forgot:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{DARK['muted']};font-size:0.9rem'>"
                f"Enter your registered email address and we'll send you "
                f"a link to reset your password.</p>",
                unsafe_allow_html=True)

    forgot_email = st.text_input("Email address", key="fp_email",
                                  placeholder="you@example.com")
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Send Reset Link →", type="primary",
                 use_container_width=True, key="btn_forgot"):
        if not forgot_email:
            st.warning("Please enter your email address.")
        else:
            ok, msg = request_password_reset(forgot_email)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

# Footer
st.markdown(f"""
<div style="text-align:center;margin-top:2rem;color:{DARK['muted']};
            font-size:0.72rem">
    Octa Platform · v1.0.0 · Questions? octainsight@gmail.com
</div>
""", unsafe_allow_html=True)
