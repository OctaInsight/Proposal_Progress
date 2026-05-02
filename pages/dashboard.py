"""
Octa Proposals — Dashboard Page
Interactive proposal pipeline with charts, filters, and per-proposal edit.
Includes Octa-specific budget KPIs and per-project Octa budget chart.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from modules.database import get_all_proposals
from modules.ui_helpers import (inject_css, page_header, section_label,
                                 status_badge, stat_box, link_html, DARK)
from config import STATUS_OPTIONS, DARK as D

st.set_page_config(page_title="Dashboard — Octa Proposals",
                   page_icon="📊", layout="wide")
inject_css()

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

def _to_num(series):
    """Strip €, £, $, %, commas then coerce to float — handles any format."""
    return (
        series.astype(str)
              .str.replace(r"[€£$%,\s]", "", regex=True)
              .str.strip()
              .pipe(pd.to_numeric, errors="coerce")
              .fillna(0)
    )

for col in ["octa_budget", "total_budget", "success_rate", "duration_months"]:
    if col in df.columns:
        df[col] = _to_num(df[col])

# Pre-compute totals
total_portfolio   = df["total_budget"].sum()
total_octa        = df["octa_budget"].sum()
octa_share_pct    = (total_octa / total_portfolio * 100) if total_portfolio > 0 else 0

status_colors = {
    "Funded":         D["success"],
    "Submitted":      D["accent"],
    "In preparation": D["warning"],
    "Planned":        D["muted"],
    "Missed":         D["danger"],
    "Rejected":       "#718096",
}

def fmt_eur(v):
    try:
        v = float(v)
    except Exception:
        return "€0"
    if v >= 1_000_000:
        return f"€{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"€{v/1_000:.1f}K"
    return f"€{v:,.0f}"

# ── KPI strip — 6 boxes ───────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
stat_box(k1, "Total Proposals",    len(df))
stat_box(k2, "Funded",             int((df["status"] == "Funded").sum()))
stat_box(k3, "Submitted",          int((df["status"] == "Submitted").sum()))
stat_box(k4, "In Preparation",     int((df["status"] == "In preparation").sum()))
stat_box(k5, "Total Portfolio",    fmt_eur(total_portfolio))
stat_box(k6, "Octa Total Budget",  fmt_eur(total_octa))

st.markdown("<br>", unsafe_allow_html=True)

# ── Octa budget summary banner ────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,{D['sidebar']} 0%,#2d4a7a 100%);
            border-radius:12px; padding:1.1rem 1.6rem; margin-bottom:1.2rem;
            border-left:4px solid {D['accent2']};
            display:flex; flex-wrap:wrap; gap:2rem; align-items:center">
    <div>
        <div style="color:rgba(255,255,255,0.65);font-size:0.78rem;
                    text-transform:uppercase;letter-spacing:0.08em">
            Octa Total Budget (all projects)
        </div>
        <div style="color:white;font-size:2rem;font-weight:800;
                    letter-spacing:-0.5px;margin-top:2px">
            {fmt_eur(total_octa)}
        </div>
    </div>
    <div style="border-left:1px solid rgba(255,255,255,0.2);
                padding-left:2rem">
        <div style="color:rgba(255,255,255,0.65);font-size:0.78rem;
                    text-transform:uppercase;letter-spacing:0.08em">
            Share of Total Portfolio
        </div>
        <div style="color:{D['accent2']};font-size:2rem;font-weight:800;
                    margin-top:2px">
            {octa_share_pct:.1f}%
        </div>
    </div>
    <div style="border-left:1px solid rgba(255,255,255,0.2);
                padding-left:2rem">
        <div style="color:rgba(255,255,255,0.65);font-size:0.78rem;
                    text-transform:uppercase;letter-spacing:0.08em">
            Total Portfolio
        </div>
        <div style="color:white;font-size:2rem;font-weight:800;
                    margin-top:2px">
            {fmt_eur(total_portfolio)}
        </div>
    </div>
    <div style="border-left:1px solid rgba(255,255,255,0.2);
                padding-left:2rem">
        <div style="color:rgba(255,255,255,0.65);font-size:0.78rem;
                    text-transform:uppercase;letter-spacing:0.08em">
            Avg Octa Budget / Project
        </div>
        <div style="color:{D['accent']};font-size:2rem;font-weight:800;
                    margin-top:2px">
            {fmt_eur(total_octa / len(df)) if len(df) > 0 else "—"}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Charts — Status + Budget comparison side by side ─────────────────────────
ch1, ch2 = st.columns(2)

CHART_H = 280   # shared fixed height for both charts

with ch1:
    section_label("Proposals by Status")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig_status = px.bar(
        status_counts, x="Status", y="Count",
        color="Status", color_discrete_map=status_colors,
        template="plotly_dark",
    )
    fig_status.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, height=CHART_H,
        margin=dict(l=0, r=10, t=10, b=0),
        font_color=D["text"],
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    fig_status.update_traces(marker_line_width=0)
    st.plotly_chart(fig_status, use_container_width=True)

with ch2:
    section_label("Total Budget vs Octa Budget (€)")
    # Use ALL proposals - fall back to proposal_id label if acronym empty
    cmp_df = df.copy()
    cmp_df["label"] = cmp_df.apply(
        lambda r: (r["acronym"].strip()
                   if str(r.get("acronym","")).strip()
                   else str(r.get("proposal_id",""))[:18]),
        axis=1
    )
    cmp_df = cmp_df.sort_values("total_budget", ascending=True)

    has_budget = (cmp_df["total_budget"] > 0).any()

    if not has_budget:
        st.markdown(
            f"<div style='color:{D['muted']};padding:2rem;text-align:center;"
            f"background:{D['bg2']};border-radius:10px;height:{CHART_H}px;"
            f"display:flex;align-items:center;justify-content:center'>"
            f"Budget data not yet synced. Open each proposal and save to populate.</div>",
            unsafe_allow_html=True
        )
    else:
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Bar(
            name="Total Budget",
            x=cmp_df["total_budget"],
            y=cmp_df["label"],
            orientation="h",
            marker=dict(color=D["accent"], opacity=0.85, line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>Total: €%{x:,.0f}<extra></extra>",
        ))
        fig_cmp.add_trace(go.Bar(
            name="Octa Budget",
            x=cmp_df["octa_budget"],
            y=cmp_df["label"],
            orientation="h",
            marker=dict(color=D["accent2"], opacity=0.95, line=dict(width=0)),
            hovertemplate="<b>%{y}</b><br>Octa: €%{x:,.0f}<extra></extra>",
        ))
        fig_cmp.update_layout(
            barmode="overlay",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=CHART_H,
            margin=dict(l=0, r=10, t=28, b=0),
            font_color=D["text"],
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01,
                xanchor="right", x=1,
                font=dict(color=D["text"], size=11),
                bgcolor="rgba(0,0,0,0)",
            ),
            xaxis=dict(
                showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                tickprefix="€", tickformat=",.0f",
            ),
            yaxis=dict(showgrid=False, tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

# ── Deadline timeline ─────────────────────────────────────────────────────────
section_label("Upcoming Deadlines")
dl_df = df[df["deadline"].notna() & (df["deadline"] != "")].copy()
if not dl_df.empty:
    dl_df["deadline_dt"] = pd.to_datetime(dl_df["deadline"], errors="coerce")
    dl_df = dl_df.dropna(subset=["deadline_dt"])
    dl_df = dl_df[dl_df["deadline_dt"] >= pd.Timestamp.today()]
    dl_df = dl_df.sort_values("deadline_dt").head(12)
    if not dl_df.empty:
        fig_dl = px.timeline(
            dl_df,
            x_start=pd.Timestamp.today(),
            x_end="deadline_dt",
            y="proposal_id",
            color="status",
            color_discrete_map=status_colors,
            template="plotly_dark",
            labels={"proposal_id": ""},
            hover_data=["proposal_title", "acronym", "responsible_person"],
        )
        fig_dl.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=max(180, len(dl_df) * 38),
            margin=dict(l=0, r=0, t=10, b=0),
            font_color=D["text"],
        )
        st.plotly_chart(fig_dl, use_container_width=True)
    else:
        st.info("No upcoming deadlines.")
else:
    st.info("No deadline data available.")

# ── Filters + proposal list ───────────────────────────────────────────────────
section_label("Proposal List")
fc1, fc2, fc3 = st.columns([2, 2, 2])
with fc1:
    f_status = st.multiselect("Filter by Status", STATUS_OPTIONS,
                               default=[], key="f_status")
with fc2:
    f_search = st.text_input("Search (title / acronym / ID)",
                              placeholder="Type to filter…", key="f_search")
with fc3:
    sort_col = st.selectbox("Sort by",
        ["proposal_id", "deadline", "total_budget", "octa_budget",
         "status", "acronym"])

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

# Filtered totals
f_octa  = filtered["octa_budget"].sum()
f_total = filtered["total_budget"].sum()
st.markdown(
    f"<p style='color:{D['muted']};font-size:0.85rem;margin-bottom:0.8rem'>"
    f"Showing <strong style='color:{D['text']}'>{len(filtered)}</strong> of {len(df)} proposals"
    f"&nbsp;&nbsp;·&nbsp;&nbsp;"
    f"Octa budget in view: <strong style='color:{D['accent2']}'>{fmt_eur(f_octa)}</strong>"
    f"&nbsp;&nbsp;·&nbsp;&nbsp;"
    f"Total budget in view: <strong style='color:{D['accent']}'>{fmt_eur(f_total)}</strong>"
    f"</p>",
    unsafe_allow_html=True
)

# ── Proposal cards ────────────────────────────────────────────────────────────
for _, row in filtered.iterrows():
    pid    = row.get("proposal_id", "")
    title  = row.get("proposal_title", "") or row.get("acronym", "") or pid
    status = row.get("status", "")
    ddl    = str(row.get("deadline") or "")
    octa_b = float(row.get("octa_budget")  or 0)
    tot_b  = float(row.get("total_budget") or 0)
    # Octa share for this proposal
    octa_pct = (octa_b / tot_b * 100) if tot_b > 0 else 0

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

    with st.expander(
        f"**{pid}** — {title}  {status_badge(status)}  "
        f"<span style='color:{D['accent2']};font-size:0.8rem'>"
        f"Octa: {fmt_eur(octa_b)}</span>",
        expanded=False
    ):
        oc1, oc2, oc3, oc4 = st.columns(4)
        with oc1:
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Acronym:** {row.get('acronym','—')}")
        with oc2:
            st.markdown(f"**Deadline:** {ddl or '—'}")
            st.markdown(f"**Duration:** {int(row.get('duration_months', 0))} months")
        with oc3:
            st.markdown(f"**Octa Budget:** {fmt_eur(octa_b)}")
            st.markdown(f"**Total Budget:** {fmt_eur(tot_b)}")
            st.markdown(
                f"<span style='color:{D['muted']};font-size:0.8rem'>"
                f"Octa share: {octa_pct:.1f}%</span>",
                unsafe_allow_html=True
            )
        with oc4:
            st.markdown(f"**Responsible:** {row.get('responsible_person','—')}")
            st.markdown(f"**Main Writer:** {row.get('main_writer','—')}")
            sr = row.get("success_rate", 0)
            if sr:
                st.markdown(f"**Success Rate:** {float(sr or 0):.2f}%")

        # Mini Octa share bar
        st.markdown(f"""
        <div style="margin:0.6rem 0 0.2rem">
            <div style="font-size:0.75rem;color:{D['muted']};margin-bottom:3px">
                Octa budget share of total
            </div>
            <div style="background:{D['bg3']};border-radius:4px;height:8px;width:100%">
                <div style="background:{D['accent2']};border-radius:4px;
                            height:8px;width:{min(octa_pct,100):.1f}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
            st.markdown("<div class='section-label' style='margin-top:0.8rem'>"
                        "Consortium</div>", unsafe_allow_html=True)
            if row.get("coordinator"):
                st.markdown(f"**🏛 Coord:** {row['coordinator']}")
            if partners_list:
                st.markdown("**Partners:** " + " · ".join(partners_list))
            if associates_list:
                st.markdown("**Associates:** " + " · ".join(associates_list))

        # Actions
        if any(row.get(f"action_{k}", "") for k in ["tamer","yasin","haseeb","other"]):
            st.markdown("<div class='section-label' style='margin-top:0.8rem'>"
                        "Actions</div>", unsafe_allow_html=True)
            for person in ["Tamer","Yasin","Haseeb","Other"]:
                val = row.get(f"action_{person.lower()}", "")
                if val:
                    st.markdown(f"**{person}:** {val}")

        if row.get("comment"):
            st.markdown(f"**💬 Comment:** {row['comment']}")

        st.markdown("<hr style='margin:1rem 0'>", unsafe_allow_html=True)

        if st.button("✏️ Edit Proposal", key=f"edit_{pid}", type="primary"):
            st.session_state["edit_proposal_id"] = pid
            st.switch_page("pages/proposal_form.py")
