"""
Octa Proposals — Dashboard Page
Interactive proposal pipeline with charts, filters, and per-proposal edit.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date

from modules.database import get_all_proposals
from modules.ui_helpers import (inject_css, page_header, section_label,
                                 status_badge, stat_box, link_html, DARK)
from config import STATUS_OPTIONS, DARK as D

st.set_page_config(page_title="Dashboard — Octa Proposals",
                   page_icon="📊", layout="wide")
inject_css()

# Back button
if st.button("← Back to Home", key="back_home"):
    st.switch_page("app.py")

page_header("Proposals Dashboard",
            "Live view of all proposals tracked in Octa", "📊")

# ── Load data ─────────────────────────────────────────────────────────────────
proposals = get_all_proposals()

if not proposals:
    st.info("No proposals in the database yet. Add your first proposal or "
            "sync from Google Sheet.")
    st.stop()

df = pd.DataFrame(proposals)

# Numeric safety
for col in ["octa_budget","total_budget","success_rate","duration_months"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5 = st.columns(5)
stat_box(k1, "Total Proposals",  len(df))
stat_box(k2, "Funded",           int((df["status"]=="Funded").sum()))
stat_box(k3, "Submitted",        int((df["status"]=="Submitted").sum()))
stat_box(k4, "In Preparation",   int((df["status"]=="In preparation").sum()))
total_eur = df["total_budget"].sum()
stat_box(k5, "Total Budget",
         f"€{total_eur/1e6:.1f}M" if total_eur >= 1e6 else f"€{total_eur:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    section_label("Proposals by Status")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status","Count"]
    colors = {
        "Funded":         D["success"],
        "Submitted":      D["accent"],
        "In preparation": D["warning"],
        "Planned":        D["muted"],
        "Missed":         D["danger"],
        "Rejected":       "#718096",
    }
    fig = px.bar(status_counts, x="Status", y="Count",
                 color="Status",
                 color_discrete_map=colors,
                 template="plotly_dark")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=280,
        margin=dict(l=0,r=0,t=10,b=0),
        font_color=D["text"],
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

with ch2:
    section_label("Budget Overview (€)")
    budget_df = df[df["total_budget"]>0].nlargest(10,"total_budget")[
        ["acronym","proposal_title","total_budget","status"]
    ].copy()
    budget_df["label"] = budget_df["acronym"].where(
        budget_df["acronym"] != "", budget_df["proposal_title"].str[:20])
    fig2 = px.bar(budget_df, x="total_budget", y="label",
                  orientation="h", template="plotly_dark",
                  color="status", color_discrete_map=colors,
                  labels={"total_budget":"Total Budget (€)","label":""})
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=280,
        margin=dict(l=0,r=0,t=10,b=0),
        font_color=D["text"],
    )
    st.plotly_chart(fig2, use_container_width=True)

# Deadline timeline
section_label("Upcoming Deadlines")
dl_df = df[df["deadline"].notna() & (df["deadline"] != "")].copy()
if not dl_df.empty:
    dl_df["deadline_dt"] = pd.to_datetime(dl_df["deadline"], errors="coerce")
    dl_df = dl_df.dropna(subset=["deadline_dt"])
    dl_df = dl_df[dl_df["deadline_dt"] >= pd.Timestamp.today()]
    dl_df = dl_df.sort_values("deadline_dt").head(10)
    if not dl_df.empty:
        fig3 = px.timeline(
            dl_df,
            x_start=pd.Timestamp.today(),
            x_end="deadline_dt",
            y="proposal_id",
            color="status",
            color_discrete_map=colors,
            template="plotly_dark",
            labels={"proposal_id":""},
            hover_data=["proposal_title","acronym","responsible_person"],
        )
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=max(180, len(dl_df)*38),
            margin=dict(l=0,r=0,t=10,b=0),
            font_color=D["text"],
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No upcoming deadlines.")
else:
    st.info("No deadline data available.")

# ── Filters ───────────────────────────────────────────────────────────────────
section_label("Proposal List")
fc1, fc2, fc3 = st.columns([2,2,2])
with fc1:
    f_status = st.multiselect("Filter by Status", STATUS_OPTIONS,
                               default=[], key="f_status")
with fc2:
    f_search = st.text_input("Search (title / acronym / ID)",
                              placeholder="Type to filter…", key="f_search")
with fc3:
    sort_col = st.selectbox("Sort by",
        ["proposal_id","deadline","total_budget","status","acronym"])

# Apply filters
filtered = df.copy()
if f_status:
    filtered = filtered[filtered["status"].isin(f_status)]
if f_search:
    mask = (
        filtered["proposal_title"].str.contains(f_search, case=False, na=False) |
        filtered["acronym"].str.contains(f_search, case=False, na=False) |
        filtered["proposal_id"].str.contains(f_search, case=False, na=False)
    )
    filtered = filtered[mask]
filtered = filtered.sort_values(sort_col, ascending=True, na_position="last")

st.markdown(f"<p style='color:{D['muted']};font-size:0.85rem'>"
            f"Showing <strong style='color:{D['text']}'>{len(filtered)}</strong>"
            f" of {len(df)} proposals</p>",
            unsafe_allow_html=True)

# ── Proposal cards ────────────────────────────────────────────────────────────
for _, row in filtered.iterrows():
    pid    = row.get("proposal_id","")
    title  = row.get("proposal_title","") or row.get("acronym","") or pid
    status = row.get("status","")
    ddl    = str(row.get("deadline") or "")
    budget = float(row.get("total_budget") or 0)

    # Urgency colour
    border_col = D["accent"]
    if ddl:
        try:
            days_left = (pd.Timestamp(ddl) - pd.Timestamp.today()).days
            if days_left < 0:    border_col = "#4a5568"
            elif days_left < 14: border_col = D["danger"]
            elif days_left < 30: border_col = D["warning"]
        except Exception:
            pass

    with st.expander(f"**{pid}** — {title}  {status_badge(status)}",
                     expanded=False):

        # Overview row
        oc1, oc2, oc3, oc4 = st.columns(4)
        with oc1:
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Acronym:** {row.get('acronym','—')}")
        with oc2:
            st.markdown(f"**Deadline:** {ddl or '—'}")
            st.markdown(f"**Duration:** {int(row.get('duration_months',0))} months")
        with oc3:
            st.markdown(f"**Octa Budget:** €{float(row.get('octa_budget',0) or 0):,.2f}")
            st.markdown(f"**Total Budget:** €{float(budget or 0):,.2f}")
        with oc4:
            st.markdown(f"**Responsible:** {row.get('responsible_person','—')}")
            st.markdown(f"**Main Writer:** {row.get('main_writer','—')}")
            sr = row.get('success_rate', 0)
            if sr:
                st.markdown(f"**Success Rate:** {float(sr or 0):.2f}%")

        # Links
        links_html = ""
        if row.get("link_to_call"):
            links_html += link_html(row["link_to_call"], "🔗 Call") + "&nbsp;&nbsp;"
        if row.get("google_drive_link"):
            links_html += link_html(row["google_drive_link"], "📁 Drive")
        if links_html:
            st.markdown(links_html, unsafe_allow_html=True)

        # Consortium
        partners_list   = row.get("partners_list")   or []
        associates_list = row.get("associates_list") or []
        if isinstance(partners_list,   str): partners_list   = []
        if isinstance(associates_list, str): associates_list = []

        if row.get("coordinator") or partners_list:
            st.markdown(f"<div class='section-label' style='margin-top:0.8rem'>"
                        f"Consortium</div>", unsafe_allow_html=True)
            cons_parts = []
            if row.get("coordinator"):
                cons_parts.append(f"**🏛 Coord:** {row['coordinator']}")
            if partners_list:
                cons_parts.append("**Partners:** " + " · ".join(partners_list))
            if associates_list:
                cons_parts.append("**Associates:** " + " · ".join(associates_list))
            for cp in cons_parts:
                st.markdown(cp)

        # Actions & comment
        if any(row.get(f"action_{k}","")
               for k in ["tamer","yasin","haseeb","other"]):
            st.markdown("<div class='section-label' style='margin-top:0.8rem'>"
                        "Actions</div>", unsafe_allow_html=True)
            for person in ["Tamer","Yasin","Haseeb","Other"]:
                val = row.get(f"action_{person.lower()}","")
                if val:
                    st.markdown(f"**{person}:** {val}")

        if row.get("comment"):
            st.markdown(f"**💬 Comment:** {row['comment']}")

        st.markdown("<hr style='margin:1rem 0'>", unsafe_allow_html=True)

        # Edit button
        if st.button(f"✏️ Edit Proposal", key=f"edit_{pid}", type="primary"):
            st.session_state["edit_proposal_id"] = pid
            st.switch_page("pages/proposal_form.py")
