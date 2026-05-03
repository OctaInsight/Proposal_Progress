"""
Octa Proposals — Partner Management Page
View all partners, add new ones, edit existing with multiple contacts.
"""
import streamlit as st
import json

from modules.auth import require_auth
from modules.database import get_all_partners, upsert_partner, delete_partner
from modules.ui_helpers import sidebar_nav, inject_css, page_header, section_label, DARK
from config import PARTNER_TYPES, COUNTRIES

st.set_page_config(page_title="Partners — Octa Proposals",
                   page_icon="🤝", layout="wide")
inject_css()
sidebar_nav()
require_auth()

if st.button("← Back to Home", key="back"):
    st.switch_page("app.py")

page_header("Partner Management",
            "View, add, and manage consortium partners", "🤝")

# ── Load partners ─────────────────────────────────────────────────────────────
partners = get_all_partners()

# ── Layout: left = list, right = form ─────────────────────────────────────────
list_col, form_col = st.columns([2, 3], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
# LEFT — Partner list
# ─────────────────────────────────────────────────────────────────────────────
with list_col:
    section_label(f"All Partners ({len(partners)})")

    search = st.text_input("🔍 Search", placeholder="Name, country, type…",
                           key="partner_search")
    filtered = [
        p for p in partners
        if not search or search.lower() in (
            p.get("full_name","") + p.get("country","") +
            p.get("partner_type","")
        ).lower()
    ]

    if not filtered:
        st.info("No partners found." if search else
                "No partners yet. Use the form to add your first partner.")

    for p in filtered:
        pid       = p.get("id")
        name      = p.get("full_name","—")
        short     = p.get("short_name","")
        ptype     = p.get("partner_type","")
        country   = p.get("country","")
        contacts  = p.get("contacts") or []
        if isinstance(contacts, str):
            try:    contacts = json.loads(contacts)
            except: contacts = []

        with st.expander(
            f"**{name}**" + (f" ({short})" if short else "") +
            f"  `{ptype}` · {country}",
            expanded=False
        ):
            # Contact list
            if contacts:
                st.markdown(f"<div style='color:{DARK['muted']};font-size:0.8rem;"
                            f"margin-bottom:0.5rem'>Contacts</div>",
                            unsafe_allow_html=True)
                for c in contacts:
                    st.markdown(
                        f"👤 **{c.get('name','—')}** · "
                        f"📞 {c.get('phone','—')} · "
                        f"✉️ {c.get('email','—')}"
                    )
            else:
                st.markdown(f"<span style='color:{DARK['muted']}'>No contacts</span>",
                            unsafe_allow_html=True)

            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("✏️ Edit", key=f"edit_{pid}", use_container_width=True):
                    st.session_state["editing_partner"] = p
                    st.session_state["edit_contacts"]   = list(contacts)
                    st.rerun()
            with btn2:
                if st.button("🗑 Delete", key=f"del_{pid}", use_container_width=True):
                    if delete_partner(pid):
                        st.success(f"Deleted {name}")
                        st.rerun()
                    else:
                        st.error("Delete failed.")


# ─────────────────────────────────────────────────────────────────────────────
# RIGHT — Add / Edit form
# ─────────────────────────────────────────────────────────────────────────────
with form_col:

    editing = st.session_state.get("editing_partner")
    is_edit = editing is not None

    if is_edit:
        section_label(f"✏️ Edit Partner — {editing.get('full_name','')}")
        if st.button("✚ Switch to New Partner", key="switch_new"):
            st.session_state.pop("editing_partner", None)
            st.session_state.pop("edit_contacts", None)
            st.rerun()
    else:
        section_label("➕ Add New Partner")

    def _v(field, default=""):
        return editing.get(field, default) if editing else default

    # Contacts session state
    if "edit_contacts" not in st.session_state:
        st.session_state.edit_contacts = [{"name":"","phone":"","email":""}]

    contacts_state = st.session_state.edit_contacts

    with st.form("partner_form", clear_on_submit=False):

        # Basic info
        r1, r2 = st.columns(2)
        with r1:
            full_name  = st.text_input("Partner Full Name *",
                                        value=_v("full_name"),
                                        placeholder="University of Example")
        with r2:
            short_name = st.text_input("Short Name / Acronym",
                                        value=_v("short_name"),
                                        placeholder="UoE")

        r2a, r2b = st.columns(2)
        with r2a:
            type_idx = PARTNER_TYPES.index(_v("partner_type","HEI")) \
                       if _v("partner_type","") in PARTNER_TYPES else 0
            partner_type = st.selectbox("Partner Type", PARTNER_TYPES,
                                         index=type_idx)
        with r2b:
            country_idx = (COUNTRIES.index(_v("country",""))
                           if _v("country","") in COUNTRIES else 0)
            country = st.selectbox("Country", COUNTRIES, index=country_idx)

        # Contacts section (rendered from session state)
        st.markdown(f"<div class='section-label' style='margin-top:1rem'>"
                    f"Contacts</div>", unsafe_allow_html=True)

        updated_contacts = []
        for i, contact in enumerate(contacts_state):
            st.markdown(
                f"<p style='color:{DARK['muted']};font-size:0.82rem;"
                f"margin:0.5rem 0 0.2rem'>Contact {i+1}</p>",
                unsafe_allow_html=True
            )
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                cname = st.text_input("Name", value=contact.get("name",""),
                                       key=f"cname_{i}", placeholder="Full name")
            with cc2:
                cphone = st.text_input("Phone", value=contact.get("phone",""),
                                        key=f"cphone_{i}",
                                        placeholder="+47 000 00 000")
            with cc3:
                cemail = st.text_input("Email", value=contact.get("email",""),
                                        key=f"cemail_{i}",
                                        placeholder="name@org.eu")
            updated_contacts.append({"name": cname, "phone": cphone,
                                      "email": cemail})

        # Save button
        st.markdown("<br>", unsafe_allow_html=True)
        save_clicked = st.form_submit_button(
            "💾 Save Partner", type="primary", use_container_width=True
        )

    # Dynamic contact buttons (outside form)
    add_col, rem_col, _ = st.columns([1, 1, 3])
    with add_col:
        if st.button("➕ Add Contact", key="add_contact"):
            st.session_state.edit_contacts.append(
                {"name":"","phone":"","email":""}
            )
            st.rerun()
    with rem_col:
        if st.button("➖ Remove Last",
                     disabled=len(contacts_state) <= 1,
                     key="rem_contact"):
            st.session_state.edit_contacts.pop()
            st.rerun()

    # Save logic
    if save_clicked:
        if not full_name.strip():
            st.error("❌ Partner Full Name is required.")
        else:
            clean_contacts = [c for c in updated_contacts
                              if c["name"] or c["phone"] or c["email"]]
            data = {
                "full_name":    full_name.strip(),
                "short_name":   short_name.strip(),
                "partner_type": partner_type,
                "country":      country,
                "contacts":     clean_contacts,
            }
            if is_edit and editing.get("id"):
                data["id"] = editing["id"]

            ok, msg = upsert_partner(data)
            if ok:
                st.success(f"✅ {msg}")
                st.session_state.pop("editing_partner", None)
                st.session_state.edit_contacts = [{"name":"","phone":"","email":""}]
                st.rerun()
            else:
                st.error(f"❌ {msg}")
