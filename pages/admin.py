"""
Octa Platform — Admin Panel
Approve pending users, manage app access, disable accounts.
No email — all actions are in-app.
"""
import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone

from modules.auth import require_auth, is_admin
from modules.database import db
from modules.ui_helpers import sidebar_nav, inject_css, page_header, section_label, DARK

st.set_page_config(page_title="Admin — Octa Platform",
                   page_icon="🛡️", layout="wide")
inject_css()
sidebar_nav()
require_auth()

if not is_admin():
    st.error("🚫 Access denied. Admin role required.")
    st.stop()

if st.button("← Back to App"):
    st.switch_page("app.py")

page_header("Admin Panel", "User management for all Octa applications", "🛡️")

ALL_APPS = ["octa_proposals", "octa_insight", "octa_partners"]


def load_users(status_filter=None) -> list:
    q = db().table("octa_users").select("*").order("created_at", desc=True)
    if status_filter:
        q = q.eq("status", status_filter)
    return q.execute().data or []


def parse_apps(u: dict) -> list:
    apps = u.get("apps_access") or []
    if isinstance(apps, str):
        try:    return json.loads(apps)
        except: return []
    return list(apps)


# ── Pending badge in page ─────────────────────────────────────────────────────
pending_count = len(load_users("pending"))
if pending_count > 0:
    st.markdown(f"""
    <div style="background:rgba(246,204,82,0.15);
                border:1px solid rgba(246,204,82,0.4);
                border-left:5px solid {DARK['warning']};
                border-radius:10px;padding:0.9rem 1.2rem;margin-bottom:1rem">
        <span style="font-size:1.3rem">⏳</span>
        <strong style="color:{DARK['warning']};font-size:1rem">
            {pending_count} user{'s' if pending_count > 1 else ''} waiting for approval
        </strong>
    </div>
    """, unsafe_allow_html=True)

tab_pending, tab_approved, tab_all = st.tabs(
    [f"⏳ Pending ({pending_count})", "✅ Approved", "👥 All Users"]
)

# ─── PENDING ──────────────────────────────────────────────────────────────────
with tab_pending:
    pending = load_users("pending")
    if not pending:
        st.success("✅ No pending registrations — all clear.")
    else:
        for u in pending:
            full_name = f"{u.get('first_name','')} {u.get('last_name','')}".strip()
            with st.expander(
                f"⏳ {full_name}  ·  {u.get('username','')}  ·  {u.get('email','')}",
                expanded=True
            ):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Name:** {full_name}")
                c2.markdown(f"**Username:** {u.get('username','')}")
                c3.markdown(f"**Email:** {u.get('email','')}")
                c1.markdown(f"**Registered:** {str(u.get('created_at',''))[:16]}")

                st.markdown("<br>", unsafe_allow_html=True)
                selected_apps = st.multiselect(
                    "Grant access to these apps:",
                    ALL_APPS,
                    default=["octa_proposals"],
                    key=f"apps_{u['id']}"
                )

                bc1, bc2, _ = st.columns([1, 1, 3])
                with bc1:
                    if st.button("✅ Approve", key=f"approve_{u['id']}",
                                 type="primary", use_container_width=True):
                        db().table("octa_users").update({
                            "status":      "approved",
                            "apps_access": selected_apps,
                            "approved_at": datetime.now(timezone.utc).isoformat(),
                            "approved_by": st.session_state.get("username", "admin"),
                        }).eq("id", u["id"]).execute()
                        st.success(f"✅ {full_name} approved!")
                        st.rerun()
                with bc2:
                    if st.button("🚫 Reject", key=f"reject_{u['id']}",
                                 use_container_width=True):
                        db().table("octa_users").update({
                            "status": "disabled"
                        }).eq("id", u["id"]).execute()
                        st.warning(f"Rejected {full_name}.")
                        st.rerun()

# ─── APPROVED ─────────────────────────────────────────────────────────────────
with tab_approved:
    approved = load_users("approved")
    if not approved:
        st.info("No approved users yet.")
    else:
        for u in approved:
            apps_val  = parse_apps(u)
            full_name = f"{u.get('first_name','')} {u.get('last_name','')}".strip()
            with st.expander(
                f"✅ {full_name}  ·  {u.get('username','')}  ·  "
                f"{', '.join(apps_val) or 'no apps assigned'}"
            ):
                ec1, ec2 = st.columns(2)
                ec1.markdown(f"**Email:** {u.get('email','')}")
                ec2.markdown(f"**Role:** {u.get('role','user')}")
                ec1.markdown(f"**Last login:** {str(u.get('last_login','—'))[:16]}")
                ec2.markdown(f"**Approved:** {str(u.get('approved_at','—'))[:10]}")

                new_apps = st.multiselect(
                    "App access:", ALL_APPS, default=apps_val,
                    key=f"edit_apps_{u['id']}"
                )
                new_role = st.selectbox(
                    "Role:", ["user", "admin"],
                    index=1 if u.get("role") == "admin" else 0,
                    key=f"role_{u['id']}"
                )

                sc1, sc2, _ = st.columns([1, 1, 3])
                with sc1:
                    if st.button("💾 Save", key=f"save_{u['id']}",
                                 use_container_width=True):
                        db().table("octa_users").update({
                            "apps_access": new_apps,
                            "role":        new_role,
                        }).eq("id", u["id"]).execute()
                        st.success("Saved!")
                        st.rerun()
                with sc2:
                    if st.button("🚫 Disable", key=f"disable_{u['id']}",
                                 use_container_width=True):
                        db().table("octa_users").update({
                            "status": "disabled"
                        }).eq("id", u["id"]).execute()
                        st.warning("Account disabled.")
                        st.rerun()

# ─── ALL USERS TABLE ──────────────────────────────────────────────────────────
with tab_all:
    all_users = load_users()
    if all_users:
        df_u = pd.DataFrame([{
            "Name":       f"{u.get('first_name','')} {u.get('last_name','')}".strip(),
            "Username":   u.get("username", ""),
            "Email":      u.get("email", ""),
            "Status":     u.get("status", ""),
            "Role":       u.get("role", ""),
            "Apps":       ", ".join(parse_apps(u)) or "—",
            "Registered": str(u.get("created_at", ""))[:10],
            "Last Login":  str(u.get("last_login", "—"))[:16],
        } for u in all_users])
        st.dataframe(df_u, use_container_width=True, hide_index=True)
    else:
        st.info("No users found.")
