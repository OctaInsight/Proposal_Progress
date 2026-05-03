"""
Octa Platform — Admin Panel
Approve pending users, manage app access, disable accounts.
Only accessible to users with role='admin'.
"""
import streamlit as st
import json
from datetime import datetime, timezone

from modules.auth import require_auth, is_admin
from modules.database import db
from modules.email_utils import send_approval_email
from modules.ui_helpers import inject_css, page_header, section_label, DARK

st.set_page_config(page_title="Admin — Octa Platform",
                   page_icon="🛡️", layout="wide")
inject_css()
require_auth()

if not is_admin():
    st.error("🚫 Access denied. Admin role required.")
    st.stop()

# Back button
if st.button("← Back to App"):
    st.switch_page("app.py")

page_header("Admin Panel", "User management for all Octa applications", "🛡️")

# All known apps for access assignment
ALL_APPS = ["octa_proposals", "octa_insight", "octa_partners"]

# ── Load all users ────────────────────────────────────────────────────────────
def load_users(status_filter=None):
    q = db().table("octa_users").select("*").order("created_at", desc=True)
    if status_filter:
        q = q.eq("status", status_filter)
    return q.execute().data or []


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_pending, tab_approved, tab_all = st.tabs(
    ["⏳ Pending Approval", "✅ Approved Users", "👥 All Users"]
)

# ────────────────────────────────────────────────────────────────────────────
# PENDING USERS
# ────────────────────────────────────────────────────────────────────────────
with tab_pending:
    pending = load_users("pending")
    if not pending:
        st.success("No pending registrations.")
    else:
        st.markdown(f"**{len(pending)} user(s) awaiting approval**")
        for u in pending:
            apps_val = u.get("apps_access") or []
            if isinstance(apps_val, str):
                try:    apps_val = json.loads(apps_val)
                except: apps_val = []

            with st.expander(
                f"👤 {u.get('first_name','')} {u.get('last_name','')} "
                f"({u.get('username','')}) — {u.get('email','')}",
                expanded=True
            ):
                ic1, ic2, ic3 = st.columns(3)
                ic1.markdown(f"**Email:** {u.get('email','')}")
                ic2.markdown(f"**Username:** {u.get('username','')}")
                ic3.markdown(f"**Registered:** {str(u.get('created_at',''))[:10]}")

                # App access assignment
                selected_apps = st.multiselect(
                    "Grant access to:",
                    ALL_APPS,
                    default=apps_val,
                    key=f"apps_{u['id']}"
                )

                bc1, bc2, bc3 = st.columns([1, 1, 2])
                with bc1:
                    if st.button("✅ Approve", key=f"approve_{u['id']}",
                                 type="primary"):
                        db().table("octa_users").update({
                            "status":      "approved",
                            "apps_access": selected_apps,
                            "approved_at": datetime.now(timezone.utc).isoformat(),
                            "approved_by": st.session_state.get("username","admin"),
                        }).eq("id", u["id"]).execute()
                        u["apps_access"] = selected_apps
                        email_ok, email_err = send_approval_email(u)
                        st.success(f"✅ Approved {u.get('username','')}!")
                        if not email_ok:
                            st.warning(f"Approval email failed: {email_err}")
                        st.rerun()
                with bc2:
                    if st.button("🚫 Reject", key=f"reject_{u['id']}"):
                        db().table("octa_users").update({
                            "status": "disabled",
                        }).eq("id", u["id"]).execute()
                        st.warning(f"Rejected {u.get('username','')}.")
                        st.rerun()

# ────────────────────────────────────────────────────────────────────────────
# APPROVED USERS
# ────────────────────────────────────────────────────────────────────────────
with tab_approved:
    approved = load_users("approved")
    if not approved:
        st.info("No approved users yet.")
    else:
        for u in approved:
            apps_val = u.get("apps_access") or []
            if isinstance(apps_val, str):
                try:    apps_val = json.loads(apps_val)
                except: apps_val = []

            with st.expander(
                f"✅ {u.get('first_name','')} {u.get('last_name','')} "
                f"({u.get('username','')}) — {', '.join(apps_val) or 'no apps'}"
            ):
                ec1, ec2 = st.columns(2)
                ec1.markdown(f"**Email:** {u.get('email','')}")
                ec2.markdown(f"**Role:** {u.get('role','user')}")
                ec1.markdown(f"**Last login:** {str(u.get('last_login','—'))[:16]}")
                ec2.markdown(f"**Approved:** {str(u.get('approved_at','—'))[:10]}")

                new_apps = st.multiselect(
                    "App access:",
                    ALL_APPS,
                    default=apps_val,
                    key=f"edit_apps_{u['id']}"
                )
                new_role = st.selectbox(
                    "Role:", ["user", "admin"],
                    index=0 if u.get("role") != "admin" else 1,
                    key=f"role_{u['id']}"
                )

                uc1, uc2, uc3 = st.columns([1, 1, 2])
                with uc1:
                    if st.button("💾 Save", key=f"save_{u['id']}"):
                        db().table("octa_users").update({
                            "apps_access": new_apps,
                            "role":        new_role,
                        }).eq("id", u["id"]).execute()
                        st.success("Saved!")
                        st.rerun()
                with uc2:
                    if st.button("🚫 Disable", key=f"disable_{u['id']}"):
                        db().table("octa_users").update({
                            "status": "disabled"
                        }).eq("id", u["id"]).execute()
                        st.warning("Account disabled.")
                        st.rerun()

# ────────────────────────────────────────────────────────────────────────────
# ALL USERS (summary table)
# ────────────────────────────────────────────────────────────────────────────
with tab_all:
    import pandas as pd
    all_users = load_users()
    if all_users:
        df_u = pd.DataFrame([{
            "Name":       f"{u.get('first_name','')} {u.get('last_name','')}".strip(),
            "Username":   u.get("username",""),
            "Email":      u.get("email",""),
            "Status":     u.get("status",""),
            "Role":       u.get("role",""),
            "Apps":       ", ".join(u.get("apps_access") or []),
            "Registered": str(u.get("created_at",""))[:10],
            "Last Login":  str(u.get("last_login","—"))[:16],
        } for u in all_users])
        st.dataframe(df_u, use_container_width=True, hide_index=True)
    else:
        st.info("No users found.")
