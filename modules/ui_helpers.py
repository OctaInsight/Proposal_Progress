"""Octa Proposals — Shared UI helpers and dark-mode CSS."""
import streamlit as st
from config import DARK, APP_NAME, APP_VERSION

GLOBAL_CSS = f"""
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="block-container"] {{
    background-color: {DARK['bg']} !important;
    color: {DARK['text']} !important;
}}
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="column"],
.element-container, .stMarkdown {{
    background: transparent !important;
}}
h1,h2,h3,h4 {{ color: {DARK['text']} !important; }}
p, li {{ color: {DARK['text']}; }}
label, .stTextInput label, .stSelectbox label,
.stMultiselect label, .stTextArea label,
.stNumberInput label, .stDateInput label {{
    color: {DARK['muted']} !important;
    font-size: 0.85rem !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {DARK['sidebar']} !important;
    border-right: 3px solid {DARK['accent']} !important;
    box-shadow: 4px 0 20px rgba(0,188,212,0.1) !important;
}}
[data-testid="stSidebar"] * {{ color: {DARK['text']} !important; }}

/* Hide Streamlit's auto-generated page navigation completely */
[data-testid="stSidebarNav"] {{
    display: none !important;
}}

/* Style st.page_link as nav buttons */
[data-testid="stSidebar"] [data-testid="stPageLink"] {{
    width: 100% !important;
    display: block !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a {{
    display: block !important;
    width: 100% !important;
    padding: 0.45rem 0.8rem !important;
    border-radius: 8px !important;
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: {DARK['text']} !important;
    text-decoration: none !important;
    font-size: 0.88rem !important;
    margin-bottom: 3px !important;
    transition: all 0.18s !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {{
    background: {DARK['accent']}22 !important;
    border-color: {DARK['accent']}66 !important;
    color: {DARK['accent']} !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink-active"] a {{
    background: {DARK['accent']}30 !important;
    border-color: {DARK['accent']} !important;
    color: {DARK['accent']} !important;
    font-weight: 600 !important;
}}

/* Sign out button in sidebar */
[data-testid="stSidebar"] .stButton > button {{
    background: rgba(252,129,129,0.12) !important;
    border: 1px solid rgba(252,129,129,0.3) !important;
    border-radius: 8px !important;
    width: 100% !important;
    color: {DARK['danger']} !important;
    font-size: 0.85rem !important;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(252,129,129,0.25) !important;
    border-color: {DARK['danger']} !important;
}}

/* Inputs */
input, textarea, input[type="text"],
input[type="number"], input[type="email"] {{
    background: {DARK['bg3']} !important;
    border: 1px solid {DARK['border']} !important;
    border-radius: 8px !important;
    color: {DARK['text']} !important;
}}
input::placeholder, textarea::placeholder {{
    color: {DARK['muted']} !important;
}}
div[data-baseweb="select"] > div {{
    background: {DARK['bg3']} !important;
    border-color: {DARK['border']} !important;
    color: {DARK['text']} !important;
}}
div[data-baseweb="select"] * {{ color: {DARK['text']} !important; }}
div[data-baseweb="popover"] {{
    background: {DARK['bg2']} !important;
    border: 1px solid {DARK['border']} !important;
}}
div[data-baseweb="popover"] li:hover {{
    background: {DARK['bg3']} !important;
}}
/* Date picker */
div[data-baseweb="calendar"],
div[data-baseweb="datepicker"] > div {{
    background: {DARK['bg2']} !important;
    color: {DARK['text']} !important;
}}

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {{
    background: {DARK['bg2']};
    border-radius: 10px; padding: 4px;
    border: 1px solid {DARK['border']};
}}
[data-testid="stTabs"] [role="tab"] {{
    color: {DARK['muted']} !important;
    border-radius: 8px;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    background: {DARK['accent']} !important;
    color: white !important;
}}

/* Buttons */
[data-testid="stButton"] > button {{
    background: {DARK['bg3']} !important;
    border: 1px solid {DARK['border']} !important;
    color: {DARK['text']} !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}}
[data-testid="stButton"] > button:hover {{
    border-color: {DARK['accent']} !important;
    color: {DARK['accent']} !important;
}}
[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg,{DARK['accent']},#0097A7) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
}}

/* Expanders */
[data-testid="stExpander"] {{
    background: {DARK['bg2']} !important;
    border: 1px solid {DARK['border']} !important;
    border-radius: 10px !important;
}}
[data-testid="stExpander"] summary {{ color: {DARK['text']} !important; }}

/* Alerts */
[data-testid="stAlert"] {{ border-radius: 10px !important; }}
[data-testid="stAlert"][kind="info"]    {{ background: rgba(0,188,212,0.12) !important; }}
[data-testid="stAlert"][kind="success"] {{ background: rgba(40,167,69,0.12) !important; }}
[data-testid="stAlert"][kind="warning"] {{ background: rgba(255,193,7,0.12) !important; }}
[data-testid="stAlert"][kind="error"]   {{ background: rgba(220,53,69,0.12) !important; }}

/* DataFrames */
[data-testid="stDataFrame"] {{ background: {DARK['bg2']} !important; }}
.dvn-scroller {{ background: {DARK['bg2']} !important; }}

hr {{ border-color: {DARK['border']} !important; }}
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: {DARK['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {DARK['bg3']}; border-radius: 3px; }}

/* ── Octa custom components ── */
.page-header {{
    background: linear-gradient(135deg,{DARK['sidebar']} 0%,#2d4a7a 100%);
    padding: 1.4rem 2rem;
    border-radius: 12px;
    border-left: 4px solid {DARK['accent']};
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.page-header h1 {{
    margin: 0; font-size: 1.7rem; font-weight: 700;
    color: white !important;
}}
.page-header p {{
    margin: 0.25rem 0 0; color: rgba(255,255,255,0.7) !important;
    font-size: 0.92rem;
}}
.card {{
    background: {DARK['bg2']};
    border: 1px solid {DARK['border']};
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: box-shadow 0.2s;
}}
.card:hover {{
    box-shadow: 0 4px 20px rgba(0,188,212,0.1);
    border-color: rgba(0,188,212,0.25);
}}
.card h3 {{
    margin: 0 0 0.3rem;
    color: {DARK['text']} !important;
    font-size: 1rem; font-weight: 600;
}}
.section-label {{
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: {DARK['accent']};
    margin: 1.4rem 0 0.6rem; padding-bottom: 0.3rem;
    border-bottom: 1px solid {DARK['border']};
}}
.stat-box {{
    background: {DARK['bg2']};
    border: 1px solid {DARK['border']};
    border-top: 3px solid {DARK['accent']};
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}}
.stat-val  {{ font-size: 2rem; font-weight: 700; color: {DARK['text']}; line-height:1; }}
.stat-lbl  {{ font-size: 0.8rem; color: {DARK['muted']}; margin-top: 0.3rem; }}
.badge {{
    display: inline-block; padding: 2px 10px;
    border-radius: 20px; font-size: 0.74rem; font-weight: 500;
    background: rgba(255,255,255,0.08); color: {DARK['text']};
    border: 1px solid {DARK['border']};
}}
.badge-funded   {{ background:rgba(40,167,69,0.2);  color:{DARK['success']}; border-color:rgba(40,167,69,0.35); }}
.badge-submitted {{ background:rgba(0,188,212,0.15); color:{DARK['accent']};  border-color:rgba(0,188,212,0.3); }}
.badge-prep     {{ background:rgba(255,193,7,0.15); color:{DARK['warning']}; border-color:rgba(255,193,7,0.3); }}
.badge-missed   {{ background:rgba(220,53,69,0.15); color:{DARK['danger']};  border-color:rgba(220,53,69,0.3); }}
.badge-rejected {{ background:rgba(108,117,125,0.2);color:#a0aec0;           border-color:rgba(108,117,125,0.3); }}
.badge-planned  {{ background:rgba(255,255,255,0.07);color:{DARK['muted']};  border-color:{DARK['border']}; }}
.divider {{ border:none; border-top:1px solid {DARK['border']}; margin:1.2rem 0; }}
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon + ' ' if icon else ''}{title}</h1>
        {'<p>' + subtitle + '</p>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f'<div class="section-label">{text}</div>',
                unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {
        "Funded":         "badge-funded",
        "Submitted":      "badge-submitted",
        "In preparation": "badge-prep",
        "Missed":         "badge-missed",
        "Rejected":       "badge-rejected",
        "Planned":        "badge-planned",
    }.get(status, "badge-planned")
    return f'<span class="badge {cls}">{status}</span>'


def stat_box(col, label: str, value):
    with col:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-val">{value}</div>
            <div class="stat-lbl">{label}</div>
        </div>
        """, unsafe_allow_html=True)


def link_html(url: str, label: str = "🔗 Open") -> str:
    if not url:
        return ""
    return (f'<a href="{url}" target="_blank" rel="noopener"'
            f' style="color:{DARK["accent"]};text-decoration:none;'
            f'font-size:0.85rem">{label}</a>')


def sidebar_nav():
    """
    Sidebar navigation using st.page_link() — the correct Streamlit API.
    Groups items with dividers and boxes.
    """
    is_auth  = st.session_state.get("authenticated", False)
    is_admin_user = st.session_state.get("role") == "admin"
    uname    = (st.session_state.get("first_name") or
                st.session_state.get("username", ""))

    with st.sidebar:

        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown(f"""<div style="text-align:center;padding:1rem 0 0.8rem">
<div style="font-size:2.2rem">📋</div>
<div style="font-weight:700;font-size:1.05rem;color:{DARK['text']}">
{APP_NAME}</div>
<div style="color:{DARK['muted']};font-size:0.68rem">v{APP_VERSION}</div>
</div>""", unsafe_allow_html=True)

        # ── User badge ────────────────────────────────────────────────────────
        if is_auth and uname:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.07);"
                f"border:1px solid rgba(255,255,255,0.12);border-radius:8px;"
                f"padding:0.4rem 0.8rem;font-size:0.82rem;margin-bottom:0.4rem'>"
                f"👤 <strong style='color:{DARK["text"]}'>{uname}</strong>"
                f"</div>",
                unsafe_allow_html=True
            )

        # ── Divider ───────────────────────────────────────────────────────────
        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);"
            "margin:0.3rem 0 0.5rem'>",
            unsafe_allow_html=True
        )

        # ── Main navigation ───────────────────────────────────────────────────
        st.markdown(
            f"<div style='font-size:0.68rem;font-weight:600;letter-spacing:0.1em;"
            f"text-transform:uppercase;color:{DARK['muted']};margin-bottom:0.3rem'>"
            f"Navigation</div>",
            unsafe_allow_html=True
        )

        st.page_link("app.py",                    label="🏠  Home")
        st.page_link("pages/dashboard.py",         label="📊  Dashboard")
        st.page_link("pages/partners.py",          label="🤝  Partners")
        st.page_link("pages/proposal_form.py",     label="📝  New Proposal")

        st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);margin:0.5rem 0'>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:{DARK["muted"]};margin-bottom:0.3rem'>Tasks</div>", unsafe_allow_html=True)
        st.page_link("pages/assign_task.py", label="📌  Assign Task")
        st.page_link("pages/my_tasks.py",    label="✅  My Tasks")

        # ── Admin section (admin only) ────────────────────────────────────────
        if is_admin_user:
            st.markdown(
                "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);"
                "margin:0.5rem 0'>",
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div style='font-size:0.68rem;font-weight:600;letter-spacing:0.1em;"
                f"text-transform:uppercase;color:{DARK['muted']};margin-bottom:0.3rem'>"
                f"Administration</div>",
                unsafe_allow_html=True
            )
            st.page_link("pages/admin.py", label="🛡️  Admin Panel")

        # ── Account section ───────────────────────────────────────────────────
        st.markdown(
            "<hr style='border:none;border-top:1px solid rgba(255,255,255,0.12);"
            "margin:0.5rem 0'>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='font-size:0.68rem;font-weight:600;letter-spacing:0.1em;"
            f"text-transform:uppercase;color:{DARK['muted']};margin-bottom:0.3rem'>"
            f"Account</div>",
            unsafe_allow_html=True
        )

        if is_auth:
            st.page_link("pages/login.py", label="🚪  Logout")
            # The logout actually needs a button since it clears session
            # page_link just navigates; use a small button for real logout
            if st.button("Sign out", use_container_width=True,
                         key="sidebar_signout"):
                from modules.auth import clear_session
                clear_session()
                st.switch_page("pages/login.py")
        else:
            st.page_link("pages/login.py", label="🔑  Login / Register")

        # ── Footer ────────────────────────────────────────────────────────────
        st.markdown(
            f"<div style='color:{DARK['muted']};font-size:0.65rem;"
            f"text-align:center;margin-top:1.5rem'>Octa Platform</div>",
            unsafe_allow_html=True
        )
