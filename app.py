"""
Octa Proposals — Main Entry Point
Landing page with sync-on-load + 3 navigation buttons.
"""
import streamlit as st
from config import APP_NAME, APP_ICON, DARK
from modules.ui_helpers import inject_css

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Google Sheet → DB sync (once per session) ─────────────────────────────────
if "synced" not in st.session_state:
    st.session_state.synced       = False
    st.session_state.sync_message = ""
    st.session_state.sync_count   = 0

if not st.session_state.synced:
    with st.spinner("🔄 Syncing with Google Sheet…"):
        try:
            from modules.sheets import sync_sheet_to_db
            count, msg = sync_sheet_to_db()
            st.session_state.sync_count   = count
            st.session_state.sync_message = msg
        except Exception as e:
            st.session_state.sync_message = f"⚠️ Sheet sync skipped: {e}"
        st.session_state.synced = True

# ── Landing page ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding: 2.5rem 0 1rem;">
    <div style="font-size:3.5rem">📋</div>
    <h1 style="color:white; font-size:2.4rem; font-weight:800;
               margin:0.4rem 0 0.2rem; letter-spacing:-1px">
        Octa Proposals
    </h1>
    <p style="color:{DARK['muted']}; font-size:1rem; margin:0">
        Proposal tracking &amp; partner management
    </p>
</div>
""", unsafe_allow_html=True)

# Sync status banner
msg = st.session_state.sync_message
if msg:
    if "✅" in msg:
        st.success(msg)
    elif "⚠️" in msg or "skipped" in msg.lower():
        st.warning(msg)
    else:
        st.info(msg)

st.markdown("<br>", unsafe_allow_html=True)

# ── Three big navigation buttons ──────────────────────────────────────────────
btn_style = f"""
<style>
div[data-testid="stButton"].big-btn > button {{
    height: 180px !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    border-radius: 16px !important;
    border: 2px solid {DARK['border']} !important;
    background: {DARK['bg2']} !important;
    color: {DARK['text']} !important;
    transition: all 0.25s !important;
    line-height: 1.5 !important;
    white-space: pre-line !important;
}}
div[data-testid="stButton"].big-btn > button:hover {{
    border-color: {DARK['accent']} !important;
    background: {DARK['bg3']} !important;
    box-shadow: 0 0 24px rgba(0,188,212,0.2) !important;
    color: {DARK['accent']} !important;
    transform: translateY(-2px) !important;
}}
</style>
"""
st.markdown(btn_style, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button(
        "📊\n\nProposals Progress\nDashboard",
        key="btn_dashboard",
        use_container_width=True,
    ):
        st.switch_page("pages/dashboard.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button(
        "➕\n\nAdd New\nProposal",
        key="btn_add_proposal",
        use_container_width=True,
    ):
        st.session_state.pop("edit_proposal_id", None)   # fresh form
        st.switch_page("pages/proposal_form.py")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="big-btn">', unsafe_allow_html=True)
    if st.button(
        "🤝\n\nAdd New\nPartner",
        key="btn_add_partner",
        use_container_width=True,
    ):
        st.switch_page("pages/partners.py")
    st.markdown('</div>', unsafe_allow_html=True)

# ── Quick stats footer ────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
try:
    from modules.database import get_all_proposals
    from config import STATUS_OPTIONS
    proposals = get_all_proposals()
    if proposals:
        total    = len(proposals)
        funded   = sum(1 for p in proposals if p.get("status") == "Funded")
        active   = sum(1 for p in proposals
                       if p.get("status") in ("In preparation","Submitted","Planned"))
        budgets  = [float(p.get("total_budget") or 0) for p in proposals]
        total_eur = sum(budgets)

        st.markdown(f"""
        <div style="display:grid; grid-template-columns:repeat(4,1fr);
                    gap:1rem; max-width:900px; margin:0 auto">
            <div style="background:{DARK['bg2']}; border:1px solid {DARK['border']};
                        border-top:3px solid {DARK['accent']}; border-radius:12px;
                        padding:1.2rem; text-align:center">
                <div style="font-size:2rem;font-weight:700;color:{DARK['text']}">{total}</div>
                <div style="font-size:0.8rem;color:{DARK['muted']}">Total Proposals</div>
            </div>
            <div style="background:{DARK['bg2']}; border:1px solid {DARK['border']};
                        border-top:3px solid {DARK['success']}; border-radius:12px;
                        padding:1.2rem; text-align:center">
                <div style="font-size:2rem;font-weight:700;color:{DARK['success']}">{funded}</div>
                <div style="font-size:0.8rem;color:{DARK['muted']}">Funded</div>
            </div>
            <div style="background:{DARK['bg2']}; border:1px solid {DARK['border']};
                        border-top:3px solid {DARK['warning']}; border-radius:12px;
                        padding:1.2rem; text-align:center">
                <div style="font-size:2rem;font-weight:700;color:{DARK['warning']}">{active}</div>
                <div style="font-size:0.8rem;color:{DARK['muted']}">Active</div>
            </div>
            <div style="background:{DARK['bg2']}; border:1px solid {DARK['border']};
                        border-top:3px solid {DARK['accent2']}; border-radius:12px;
                        padding:1.2rem; text-align:center">
                <div style="font-size:1.5rem;font-weight:700;color:{DARK['accent2']}">
                    €{total_eur/1e6:.1f}M
                </div>
                <div style="font-size:0.8rem;color:{DARK['muted']}">Total Budget</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
except Exception:
    pass

st.markdown(f"""
<div style="text-align:center; margin-top:2.5rem; color:{DARK['muted']};
            font-size:0.72rem">
    Octa Proposals · v1.0.0
</div>
""", unsafe_allow_html=True)
