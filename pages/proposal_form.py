"""
Octa Proposals — Add / Edit Proposal Form
Unlimited partners and associated partners.
Dual-writes to Supabase + Google Sheets on save.
"""
import streamlit as st
from datetime import datetime

from modules.database import (
    next_proposal_id, get_proposal_by_pid,
    upsert_proposal, get_all_partners, _safe_date
)
from modules.sheets import write_proposal_to_sheet
from modules.ui_helpers import sidebar_nav, inject_css, page_header, section_label, DARK
from config import (
    PES_FUND_OPTIONS, STATUS_OPTIONS, MANDATE_OPTIONS, CLOUDEARTI_OPTIONS,
)

st.set_page_config(page_title="Proposal Form — Octa Proposals",
                   page_icon="📝", layout="wide")
inject_css()
sidebar_nav()

# ── Mode: new vs edit ─────────────────────────────────────────────────────────
edit_pid = st.session_state.get("edit_proposal_id")
is_edit  = bool(edit_pid)

if is_edit:
    existing = get_proposal_by_pid(edit_pid)
    if not existing:
        st.error(f"Proposal {edit_pid} not found.")
        st.stop()
    pid_display = edit_pid
    page_title  = f"Edit Proposal — {edit_pid}"
else:
    existing    = {}
    pid_display = next_proposal_id()
    page_title  = "Add New Proposal"


def _v(field, default=""):
    v = existing.get(field, default)
    return v if v is not None else default

def _vi(field, default=0):
    try:    return int(float(_v(field, default) or 0))
    except: return default

def _vf(field, default=0.0):
    try:    return float(_v(field, default) or 0)
    except: return default

def _vdate(field):
    v = existing.get(field)
    if not v: return None
    try:    return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except: return None


# ── Partner suggestions from DB ───────────────────────────────────────────────
all_partners  = get_all_partners()
partner_names = [""] + [p["full_name"] for p in all_partners]

# ── Initialise session state lists (once per form load) ───────────────────────
# Key: use proposal_id so switching between edit targets resets correctly
form_key = f"form_state_{pid_display}"
if form_key not in st.session_state:
    existing_p = existing.get("partners_list")   or []
    existing_a = existing.get("associates_list") or []
    if isinstance(existing_p, str): existing_p = []
    if isinstance(existing_a, str): existing_a = []
    st.session_state[form_key] = {
        "partners":   list(existing_p) if existing_p else [""],
        "associates": list(existing_a) if existing_a else [],
    }

form_state = st.session_state[form_key]

# ── Back button ───────────────────────────────────────────────────────────────
if st.button("← Back", key="back"):
    st.session_state.pop("edit_proposal_id", None)
    st.session_state.pop(form_key, None)
    st.switch_page("app.py")

page_header(page_title,
            "Changes are saved to both database and Google Sheet",
            "✏️" if is_edit else "➕")

# ═════════════════════════════════════════════════════════════════════════════
# FORM
# ═════════════════════════════════════════════════════════════════════════════
with st.form("proposal_form", clear_on_submit=False):

    # ── Proposal ID display ───────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{DARK['bg2']};border:1px solid {DARK['border']};
                border-left:4px solid {DARK['accent']};border-radius:10px;
                padding:0.9rem 1.2rem;margin-bottom:1rem">
        <span style="color:{DARK['muted']};font-size:0.8rem">PROPOSAL ID</span><br>
        <span style="font-size:1.4rem;font-weight:700;color:{DARK['accent']};
                     font-family:monospace">{pid_display}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Project Identification ────────────────────────────────────────────────
    section_label("📌 Project Identification")
    c1, c2 = st.columns(2)
    with c1:
        acronym        = st.text_input("Acronym", value=_v("acronym"),
                                       placeholder="e.g. GreenAI")
    with c2:
        proposal_title = st.text_input("Proposal Title *", value=_v("proposal_title"),
                                       placeholder="Full title of the proposal")
    c3, c4, c5 = st.columns(3)
    with c3:
        call           = st.text_input("Call",           value=_v("call"))
    with c4:
        topic          = st.text_input("Topic",          value=_v("topic"))
    with c5:
        type_of_action = st.text_input("Type of Action", value=_v("type_of_action"),
                                       placeholder="RIA, IA, CSA…")
    lc1, lc2 = st.columns(2)
    with lc1:
        link_to_call      = st.text_input("🔗 Link to the Call",
                                          value=_v("link_to_call"),
                                          placeholder="https://…")
    with lc2:
        google_drive_link = st.text_input("📁 Google Drive Link",
                                          value=_v("google_drive_link"),
                                          placeholder="https://drive.google.com/…")

    # ── Status & Funding ──────────────────────────────────────────────────────
    section_label("📊 Status & Funding")
    sf1, sf2, sf3 = st.columns(3)
    with sf1:
        status = st.selectbox("Status *", STATUS_OPTIONS,
                              index=STATUS_OPTIONS.index(_v("status","Planned"))
                              if _v("status","Planned") in STATUS_OPTIONS else 0)
    with sf2:
        pes_fund_request = st.selectbox(
            "PES Fund Request", PES_FUND_OPTIONS,
            index=PES_FUND_OPTIONS.index(_v("pes_fund_request",""))
                  if _v("pes_fund_request","") in PES_FUND_OPTIONS else 0)
    with sf3:
        mandate_letter = st.selectbox(
            "Mandate/Support Letter", MANDATE_OPTIONS,
            index=MANDATE_OPTIONS.index(_v("mandate_letter","Not required"))
                  if _v("mandate_letter","") in MANDATE_OPTIONS else 0)

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1:
        octa_budget  = st.number_input("Octa Budget (€)", min_value=0.0,
                                       value=_vf("octa_budget"), step=1000.0,
                                       format="%.0f")
    with bc2:
        total_budget = st.number_input("Total Budget (€)", min_value=0.0,
                                       value=_vf("total_budget"), step=10000.0,
                                       format="%.0f")
    with bc3:
        success_rate = st.number_input("Success Rate (%)", min_value=0.0,
                                       max_value=100.0,
                                       value=_vf("success_rate"), step=1.0)
    with bc4:
        duration_months = st.number_input("Duration (months)", min_value=0,
                                          value=_vi("duration_months"), step=1)

    link_cloudearti = st.selectbox(
        "Link to CloudEARTHi", CLOUDEARTI_OPTIONS,
        index=CLOUDEARTI_OPTIONS.index(_v("link_cloudearti",""))
              if _v("link_cloudearti","") in CLOUDEARTI_OPTIONS else 0)

    # ── Dates ─────────────────────────────────────────────────────────────────
    section_label("📅 Dates")
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        deadline          = st.date_input("Submission Deadline",
                                          value=_vdate("deadline"),
                                          format="YYYY-MM-DD")
    with dc2:
        submission_date   = st.date_input("Actual Submission Date",
                                          value=_vdate("submission_date"),
                                          format="YYYY-MM-DD")
    with dc3:
        announcement_date = st.date_input("Announcement Date",
                                          value=_vdate("announcement_date"),
                                          format="YYYY-MM-DD")

    # ── Reference IDs ─────────────────────────────────────────────────────────
    section_label("🔢 Reference Numbers")
    id1, id2 = st.columns(2)
    with id1:
        form_id       = st.text_input("Form ID",       value=_v("form_id"))
    with id2:
        submission_id = st.text_input("Submission ID", value=_v("submission_id"))

    # ── Responsible People ────────────────────────────────────────────────────
    section_label("👥 Responsible People")
    pp1, pp2 = st.columns(2)
    with pp1:
        responsible_person = st.text_input("Responsible Person",
                                           value=_v("responsible_person"))
    with pp2:
        main_writer = st.text_input("Main Writer", value=_v("main_writer"))

    # ── Actions ───────────────────────────────────────────────────────────────
    section_label("⚡ Actions Required")
    aa1, aa2 = st.columns(2)
    with aa1:
        action_tamer  = st.text_area("Action: Tamer",  value=_v("action_tamer"),  height=80)
        action_haseeb = st.text_area("Action: Haseeb", value=_v("action_haseeb"), height=80)
    with aa2:
        action_yasin  = st.text_area("Action: Yasin",  value=_v("action_yasin"),  height=80)
        action_other  = st.text_area("Action: Other",  value=_v("action_other"),  height=80)
    comment = st.text_area("💬 General Comment", value=_v("comment"), height=80)

    # ── Consortium: Coordinator ───────────────────────────────────────────────
    section_label("🌍 Consortium")
    coordinator = st.text_input("🏛 Coordinator (Lead Partner)",
                                value=_v("coordinator"),
                                placeholder="Organisation name")

    # ── Partners (unlimited, rendered from session state) ─────────────────────
    st.markdown(
        f"<p style='color:{DARK['text']};font-weight:600;margin-top:1rem'>"
        f"Partners <span style='color:{DARK['muted']};font-weight:400;font-size:0.82rem'>"
        f"({len(form_state['partners'])} added — unlimited)</span></p>",
        unsafe_allow_html=True
    )

    partner_values = []
    for i, pval in enumerate(form_state["partners"]):
        row_c1, row_c2, row_c3 = st.columns([3, 2, 1])
        with row_c1:
            typed = st.text_input(
                f"Partner {i+1}", value=pval,
                key=f"p_text_{i}",
                placeholder=f"Partner {i+1} name",
                label_visibility="visible",
            )
        with row_c2:
            picked = st.selectbox(
                "Pick from DB", partner_names,
                key=f"p_pick_{i}",
                label_visibility="visible",
            )
        with row_c3:
            # Placeholder — remove buttons are outside the form
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<span style='color:{DARK['muted']};font-size:0.75rem'>"
                f"#{i+1}</span>",
                unsafe_allow_html=True
            )
        partner_values.append(typed if typed.strip() else picked)

    # ── Associates (unlimited) ────────────────────────────────────────────────
    st.markdown(
        f"<p style='color:{DARK['text']};font-weight:600;margin-top:1.2rem'>"
        f"Associated Partners <span style='color:{DARK['muted']};font-weight:400;"
        f"font-size:0.82rem'>({len(form_state['associates'])} added — unlimited)"
        f"</span></p>",
        unsafe_allow_html=True
    )

    associate_values = []
    for i, aval in enumerate(form_state["associates"]):
        ar1, ar2, ar3 = st.columns([3, 2, 1])
        with ar1:
            typed_a = st.text_input(
                f"Associated {i+1}", value=aval,
                key=f"a_text_{i}",
                placeholder=f"Associated partner {i+1}",
                label_visibility="visible",
            )
        with ar2:
            picked_a = st.selectbox(
                "Pick from DB", partner_names,
                key=f"a_pick_{i}",
                label_visibility="visible",
            )
        with ar3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<span style='color:{DARK['muted']};font-size:0.75rem'>"
                f"#{i+1}</span>",
                unsafe_allow_html=True
            )
        associate_values.append(typed_a if typed_a.strip() else picked_a)

    # ── Save button (inside form) ─────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button(
        "💾 Save Proposal", type="primary", use_container_width=True
    )

# ═════════════════════════════════════════════════════════════════════════════
# DYNAMIC BUTTONS — outside form so they don't trigger submit
# ═════════════════════════════════════════════════════════════════════════════
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{DARK['muted']};font-size:0.82rem'>"
    f"Use buttons below to add or remove rows, then fill in the form above.</p>",
    unsafe_allow_html=True
)

# Partners row management
pa1, pa2, pa3 = st.columns([1, 1, 4])
with pa1:
    if st.button("➕ Add Partner", use_container_width=True, key="add_p"):
        form_state["partners"].append("")
        st.rerun()
with pa2:
    if st.button("➖ Remove Last Partner",
                 use_container_width=True, key="rem_p",
                 disabled=len(form_state["partners"]) <= 1):
        form_state["partners"].pop()
        st.rerun()

# Associates row management
aa1b, aa2b, aa3b = st.columns([1, 1, 4])
with aa1b:
    if st.button("➕ Add Associate", use_container_width=True, key="add_a"):
        form_state["associates"].append("")
        st.rerun()
with aa2b:
    if st.button("➖ Remove Last Associate",
                 use_container_width=True, key="rem_a",
                 disabled=len(form_state["associates"]) == 0):
        form_state["associates"].pop()
        st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# SAVE LOGIC
# ═════════════════════════════════════════════════════════════════════════════
if submitted:
    if not proposal_title.strip():
        st.error("❌ Proposal Title is required.")
        st.stop()

    clean_partners   = [p for p in partner_values   if p and p.strip()]
    clean_associates = [a for a in associate_values if a and a.strip()]

    db_row = {
        "proposal_id":        pid_display,
        "action_tamer":       action_tamer,
        "action_yasin":       action_yasin,
        "action_haseeb":      action_haseeb,
        "action_other":       action_other,
        "comment":            comment,
        "pes_fund_request":   pes_fund_request,
        "status":             status,
        "octa_budget":        octa_budget,
        "total_budget":       total_budget,
        "link_cloudearti":    link_cloudearti,
        "success_rate":       success_rate,
        "duration_months":    int(duration_months),
        "mandate_letter":     mandate_letter,
        "responsible_person": responsible_person,
        "main_writer":        main_writer,
        "form_id":            form_id,
        "submission_id":      submission_id,
        "acronym":            acronym,
        "proposal_title":     proposal_title,
        "call":               call,
        "topic":              topic,
        "type_of_action":     type_of_action,
        "link_to_call":       link_to_call,
        "google_drive_link":  google_drive_link,
        "deadline":           _safe_date(deadline),
        "submission_date":    _safe_date(submission_date),
        "announcement_date":  _safe_date(announcement_date),
        "coordinator":        coordinator,
        "partners_list":      clean_partners,
        "associates_list":    clean_associates,
    }

    # 1. Save to Supabase
    with st.spinner("Saving to database…"):
        from modules.database import upsert_proposal
        ok_db, msg_db = upsert_proposal(db_row)

    # 2. Mirror to Google Sheet
    with st.spinner("Syncing to Google Sheet…"):
        ok_sheet, msg_sheet = write_proposal_to_sheet(db_row)

    if ok_db:
        st.success(f"✅ {msg_db}")
        if ok_sheet:
            st.success(f"✅ {msg_sheet}")
        else:
            st.warning(f"⚠️ Database saved, but Sheet sync failed: {msg_sheet}")

        # Update session state with saved values so re-renders stay correct
        form_state["partners"]   = clean_partners   if clean_partners   else [""]
        form_state["associates"] = clean_associates if clean_associates else []

        st.balloons()
        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem;background:{DARK['bg2']};
                    border-radius:12px;border:1px solid {DARK['border']};margin-top:1rem">
            <h3 style="color:{DARK['success']}">
                ✅ Proposal <code>{pid_display}</code> saved!
            </h3>
            <p style="color:{DARK['muted']}">
                {len(clean_partners)} partner(s) · {len(clean_associates)} associate(s)
            </p>
        </div>
        """, unsafe_allow_html=True)

        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("📊 Go to Dashboard", use_container_width=True):
                st.session_state.pop("edit_proposal_id", None)
                st.session_state.pop(form_key, None)
                st.switch_page("pages/dashboard.py")
        with nav2:
            if st.button("➕ Add Another Proposal", use_container_width=True):
                st.session_state.pop("edit_proposal_id", None)
                st.session_state.pop(form_key, None)
                st.rerun()
    else:
        st.error(f"❌ {msg_db}")
