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
from modules.auth import require_auth
from modules.ui_helpers import (sidebar_nav,inject_css, page_header, section_label,
                                 status_badge, stat_box, link_html, DARK)
from config import STATUS_OPTIONS, DARK as D

st.set_page_config(page_title="Dashboard — Octa Proposals",
                   page_icon="📊", layout="wide")
inject_css()
sidebar_nav()
require_auth()

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

# Pre-compute totals — only Submitted + Funded count toward budget KPIs
ACTIVE_STATUSES = {"Submitted", "Funded"}
active_df         = df[df["status"].isin(ACTIVE_STATUSES)]
total_portfolio   = active_df["total_budget"].sum()
total_octa        = active_df["octa_budget"].sum()
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
        dl_df["start_date"] = pd.Timestamp.today()

        # ── Use acronym if available, else proposal_id ──────────────────────
        dl_df["display_label"] = dl_df.apply(
            lambda r: r["acronym"].strip()
                      if str(r.get("acronym", "")).strip()
                      else str(r.get("proposal_id", "")),
            axis=1
        )

        # ── PES fund flag ────────────────────────────────────────────────────
        PES_ENTITLED = "Entitled to PES fund"
        dl_df["pes_flag"] = dl_df["pes_fund_request"].apply(
            lambda v: "Entitled to PES fund" if str(v).strip() == PES_ENTITLED
                      else "Standard"
        )

        # ── Bar colour: PES = orange, Standard = use status colour ──────────
        def _bar_color(row):
            if row["pes_flag"] == "Entitled to PES fund":
                return D["accent2"]          # orange for PES
            return status_colors.get(row["status"], D["muted"])

        dl_df["bar_color"] = dl_df.apply(_bar_color, axis=1)

        # ── Build figure manually (px.timeline doesn't support per-bar color)─
        fig_dl = go.Figure()

        today = pd.Timestamp.today()

        for _, r in dl_df.iterrows():
            days_left = (r["deadline_dt"] - today).days
            is_pes    = r["pes_flag"] == "Entitled to PES fund"
            hover_txt = (
                f"<b>{r['display_label']}</b><br>"
                f"Title: {r.get('proposal_title','')[:50]}<br>"
                f"Deadline: {str(r['deadline_dt'])[:10]}<br>"
                f"Days left: {days_left}<br>"
                f"Responsible: {r.get('responsible_person','—')}<br>"
                + ("⭐ Entitled to PES fund" if is_pes else "")
            )
            fig_dl.add_trace(go.Bar(
                name      = r["pes_flag"],
                x         = [days_left],
                y         = [r["display_label"]],
                orientation = "h",
                marker_color = r["bar_color"],
                marker_line_width = 0,
                opacity   = 0.9,
                text      = "⭐ PES fund" if is_pes else "",
                textposition = "inside",
                textfont  = dict(color="white", size=11),
                hovertemplate = hover_txt + "<extra></extra>",
                showlegend = is_pes,   # only PES entries appear in legend
                legendgroup = r["pes_flag"],
            ))

        fig_dl.update_layout(
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "rgba(0,0,0,0)",
            height        = max(200, len(dl_df) * 40),
            margin        = dict(l=0, r=0, t=10, b=0),
            font_color    = D["text"],
            barmode       = "overlay",
            showlegend    = True,
            legend        = dict(
                orientation = "h", yanchor = "bottom", y = 1.02,
                xanchor = "right", x = 1,
                font = dict(color=D["text"], size=11),
                bgcolor = "rgba(0,0,0,0)",
            ),
            xaxis = dict(
                title     = "Days until deadline",
                gridcolor = "rgba(255,255,255,0.05)",
                ticksuffix = "d",
            ),
            yaxis = dict(showgrid=False),
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

# ── Numeric sort on proposal_id (extract trailing number) ────────────────────
def _pid_num(pid):
    """Extract trailing integer from 'Octa_Proposal_27' → 27."""
    try:
        return int(str(pid).split("_")[-1])
    except Exception:
        return 0

if sort_col == "proposal_id":
    filtered = filtered.copy()
    filtered["_sort_num"] = filtered["proposal_id"].apply(_pid_num)
    filtered = filtered.sort_values("_sort_num", ascending=False, na_position="last")
    filtered = filtered.drop(columns=["_sort_num"])
else:
    filtered = filtered.sort_values(sort_col, ascending=True, na_position="last")

# ── Status colour palette ─────────────────────────────────────────────────────
STATUS_CARD = {
    "Funded":         ("#28a745", "rgba(40,167,69,0.15)",    "#1a3d22", "🏆"),
    "Submitted":      ("#00BCD4", "rgba(0,188,212,0.13)",    "#0a2a30", "📤"),
    "In preparation": ("#f6cc52", "rgba(246,204,82,0.13)",   "#2e2a10", "✍️"),
    "Planned":        ("#8899b0", "rgba(136,153,176,0.11)",  "#1e2535", "📅"),
    "Missed":         ("#f6ad55", "rgba(246,173,85,0.14)",   "#2e2010", "⏭️"),
    "Rejected":       ("#fc8181", "rgba(252,129,129,0.14)",  "#301515", "❌"),
    "Ended":          ("#6b7280", "rgba(107,114,128,0.13)",  "#1c1f25", "🏁"),
}
DEFAULT_CARD = ("#8899b0", "rgba(136,153,176,0.10)", "#1e2535", "📋")

# ── Filtered totals (only Submitted + Funded) ────────────────────────────────
f_active = filtered[filtered["status"].isin(ACTIVE_STATUSES)]
f_octa   = f_active["octa_budget"].sum()
f_total  = f_active["total_budget"].sum()
st.markdown(
    f"<p style='color:{D['muted']};font-size:0.85rem;margin-bottom:0.8rem'>"
    f"Showing <strong style='color:{D['text']}'>{len(filtered)}</strong> of {len(df)} proposals"
    f"&nbsp;&nbsp;·&nbsp;&nbsp;"
    f"Submitted+Funded Octa: <strong style='color:{D['accent2']}'>{fmt_eur(f_octa)}</strong>"
    f"&nbsp;&nbsp;·&nbsp;&nbsp;"
    f"Submitted+Funded Total: <strong style='color:{D['accent']}'>{fmt_eur(f_total)}</strong>"
    f"</p>",
    unsafe_allow_html=True
)

# ── Proposal cards — pure Streamlit, colored stripe + native expander ─────────
for _, row in filtered.iterrows():
    pid         = row.get("proposal_id", "")
    title       = row.get("proposal_title", "") or row.get("acronym", "") or pid
    acronym     = row.get("acronym", "")      or "—"
    status      = row.get("status", "")
    ddl         = str(row.get("deadline")         or "—")
    octa_b      = float(row.get("octa_budget")    or 0)
    tot_b       = float(row.get("total_budget")   or 0)
    octa_pct    = (octa_b / tot_b * 100) if tot_b > 0 else 0
    responsible = row.get("responsible_person",   "") or "—"
    writer      = row.get("main_writer",          "") or "—"
    sr          = float(row.get("success_rate",    0) or 0)
    duration    = int(row.get("duration_months",   0) or 0)
    coordinator = row.get("coordinator",          "") or ""
    call_link   = row.get("link_to_call",         "") or ""
    drive_link  = row.get("google_drive_link",    "") or ""
    comment     = row.get("comment",              "") or ""
    partners_list   = row.get("partners_list")   or []
    associates_list = row.get("associates_list") or []
    if isinstance(partners_list,   str): partners_list   = []
    if isinstance(associates_list, str): associates_list = []
    actions = {p: row.get(f"action_{p.lower()}", "") or ""
               for p in ["Tamer", "Yasin", "Haseeb", "Other"]}

    s_border, s_bg, s_dark, s_icon = STATUS_CARD.get(status, DEFAULT_CARD)
    sr_str  = f"{sr:.1f}%" if sr else "—"
    share_w = f"{min(octa_pct, 100):.0f}"

    # ── Colored stripe (one tiny HTML line — no indentation, no comments) ───
    st.markdown(
        f"<div style='height:5px;background:{s_border};"
        f"border-radius:4px 4px 0 0;margin-bottom:2px'></div>",
        unsafe_allow_html=True,
    )

    # ── Native expander — collapsed by default ───────────────────────────────
    label = f"{s_icon}  {pid}  ·  {acronym}  |  {status}  |  ⏰ {ddl}  |  Octa: {fmt_eur(octa_b)}"
    with st.expander(label, expanded=False):

        # Data grid
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"**Acronym:** {acronym}")
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Duration:** {duration} months")
        with c2:
            st.markdown(f"**Deadline:** {ddl}")
            st.markdown(f"**Submission Date:** {str(row.get('submission_date') or '—')}")
            st.markdown(f"**Announcement:** {str(row.get('announcement_date') or '—')}")
        with c3:
            st.markdown(f"**Octa Budget:** {fmt_eur(octa_b)}")
            st.markdown(f"**Total Budget:** {fmt_eur(tot_b)}")
            st.markdown(f"**Octa Share:** {octa_pct:.1f}%")
            st.markdown(f"**Success Rate:** {sr_str}")
        with c4:
            st.markdown(f"**Responsible:** {responsible}")
            st.markdown(f"**Main Writer:** {writer}")
            st.markdown(f"**Form ID:** {row.get('form_id','—') or '—'}")
            st.markdown(f"**Submission ID:** {row.get('submission_id','—') or '—'}")

        # Octa share bar (single short HTML line)
        st.markdown(
            f"<div style='background:rgba(255,255,255,0.1);border-radius:3px;"
            f"height:6px;margin:0.5rem 0'><div style='background:{s_border};"
            f"border-radius:3px;height:6px;width:{share_w}%'></div></div>",
            unsafe_allow_html=True,
        )

        # Links
        if call_link or drive_link:
            lc1, lc2, lc3 = st.columns([1, 1, 4])
            if call_link:
                lc1.link_button("🔗 Call Page", call_link)
            if drive_link:
                lc2.link_button("📁 Drive", drive_link)

        # Consortium
        if coordinator or partners_list or associates_list:
            st.markdown("---")
            if coordinator:
                st.markdown(f"**🏛 Coordinator:** {coordinator}")
            if partners_list:
                st.markdown("**Partners:** " + "  ·  ".join(partners_list))
            if associates_list:
                st.markdown("**Associates:** " + "  ·  ".join(associates_list))

        # Actions
        any_action = any(v for v in actions.values())
        if any_action:
            st.markdown("---")
            ac1, ac2 = st.columns(2)
            for i, (person, val) in enumerate(actions.items()):
                if val:
                    (ac1 if i % 2 == 0 else ac2).markdown(
                        f"**⚡ {person}:** {val}"
                    )

        # Comment
        if comment:
            st.markdown("---")
            st.markdown(f"**💬 Comment:** {comment}")

        # Edit button
        st.markdown("---")
        if st.button(f"✏️ Edit {pid}", key=f"edit_{pid}", type="primary"):
            st.session_state["edit_proposal_id"] = pid
            st.switch_page("pages/proposal_form.py")

    st.markdown("<div style='margin-bottom:4px'></div>", unsafe_allow_html=True)



