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
        dl_df["start_date"] = pd.Timestamp.today()   # scalar → column
        fig_dl = px.timeline(
            dl_df,
            x_start="start_date",
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

# ── Proposal cards — full HTML, guaranteed colours ────────────────────────────
for _, row in filtered.iterrows():
    pid    = row.get("proposal_id", "")
    title  = row.get("proposal_title", "") or row.get("acronym", "") or pid
    acronym = row.get("acronym", "") or "—"
    status  = row.get("status", "")
    ddl     = str(row.get("deadline") or "—")
    sub_dt  = str(row.get("submission_date") or "—")
    octa_b  = float(row.get("octa_budget")  or 0)
    tot_b   = float(row.get("total_budget") or 0)
    octa_pct = (octa_b / tot_b * 100) if tot_b > 0 else 0
    responsible = row.get("responsible_person", "—") or "—"
    writer      = row.get("main_writer", "—") or "—"
    sr          = row.get("success_rate", 0) or 0
    duration    = int(row.get("duration_months", 0) or 0)
    coordinator = row.get("coordinator", "") or ""
    call_link   = row.get("link_to_call", "") or ""
    drive_link  = row.get("google_drive_link", "") or ""
    comment     = row.get("comment", "") or ""

    partners_list   = row.get("partners_list")   or []
    associates_list = row.get("associates_list") or []
    if isinstance(partners_list,   str): partners_list   = []
    if isinstance(associates_list, str): associates_list = []

    # Resolve status colours first — needed by actions_html below
    s_border, s_bg, s_dark, s_icon = STATUS_CARD.get(status, DEFAULT_CARD)

    # Actions
    actions = {p: row.get(f"action_{p.lower()}", "") or ""
               for p in ["Tamer","Yasin","Haseeb","Other"]}
    actions_html = ""
    text_col = D["text"]
    for person, val in actions.items():
        if val:
            actions_html += (
                f"<div style='margin-bottom:3px'>"
                f"<span style='color:{s_border};font-weight:600'>{person}:</span> "
                f"<span style='color:{text_col}'>{val}</span></div>"
            )

    # Pre-compute HTML fragments that would cause quote conflicts inside f-strings
    comment_html = (
        f"<div style='margin-top:0.6rem;font-size:0.84rem;color:{D['muted']}'>"
        f"<b style='color:{D['text']}'>💬 Comment:</b> {comment}</div>"
        if comment else ""
    )
    actions_div = (
        f"<div style='border-top:1px solid {s_border}33;margin-top:0.8rem;"
        f"padding-top:0.7rem;font-size:0.84rem'>{actions_html}</div>"
        if actions_html else ""
    )

    # Links HTML
    link_parts = []
    if call_link:
        link_parts.append(
            f"<a href='{call_link}' target='_blank' style='color:{D['accent']};"
            f"text-decoration:none;font-size:0.82rem;margin-right:1rem'>"
            f"🔗 Call Page</a>")
    if drive_link:
        link_parts.append(
            f"<a href='{drive_link}' target='_blank' style='color:{D['accent']};"
            f"text-decoration:none;font-size:0.82rem'>"
            f"📁 Google Drive</a>")

    # Consortium
    cons_parts = []
    if coordinator:
        cons_parts.append(f"<b>🏛 Coord:</b> {coordinator}")
    if partners_list:
        cons_parts.append("<b>Partners:</b> " + " · ".join(partners_list))
    if associates_list:
        cons_parts.append("<b>Associates:</b> " + " · ".join(associates_list))

    consortium_html = ""
    if cons_parts:
        consortium_html = f"""
        <div style='border-top:1px solid {s_border}33;margin-top:0.8rem;
                    padding-top:0.7rem;font-size:0.84rem;color:{D["text"]};
                    line-height:1.7'>
            {"<br>".join(cons_parts)}
        </div>"""

    # Render full card as one HTML block
    st.markdown(f"""
    <div style="
        background:{s_bg};
        border:1px solid {s_border}66;
        border-left:6px solid {s_border};
        border-radius:12px;
        padding:1rem 1.3rem 1.1rem;
        margin:0.45rem 0 0.1rem;
    ">
        <!-- Header row -->
        <div style="display:flex;align-items:center;gap:0.6rem;
                    flex-wrap:wrap;margin-bottom:0.75rem">
            <span style="font-size:1.2rem">{s_icon}</span>
            <span style="background:{s_border}30;color:{s_border};
                         font-weight:700;font-size:0.7rem;
                         text-transform:uppercase;letter-spacing:0.08em;
                         padding:2px 9px;border-radius:20px;
                         border:1px solid {s_border}66">{status}</span>
            <span style="color:{s_border};font-weight:700;font-size:0.95rem;
                         font-family:monospace">{pid}</span>
            <span style="color:{D['muted']}">·</span>
            <span style="color:{D['text']};font-size:0.9rem;font-weight:600;
                         flex:1;min-width:0">
                {title[:70]}{'…' if len(title)>70 else ''}
            </span>
        </div>

        <!-- Data grid -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);
                    gap:0.6rem 1.2rem;font-size:0.84rem">
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    ACRONYM</div>
                <div style="color:{D['text']};font-weight:600">{acronym}</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    DEADLINE</div>
                <div style="color:{D['text']}">{ddl}</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    RESPONSIBLE</div>
                <div style="color:{D['text']}">{responsible}</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    MAIN WRITER</div>
                <div style="color:{D['text']}">{writer}</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    OCTA BUDGET</div>
                <div style="color:{D['accent2']};font-weight:700">{fmt_eur(octa_b)}</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    TOTAL BUDGET</div>
                <div style="color:{D['accent']};font-weight:700">{fmt_eur(tot_b)}</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    DURATION</div>
                <div style="color:{D['text']}">{duration} months</div>
            </div>
            <div>
                <div style="color:{D['muted']};font-size:0.72rem;margin-bottom:2px">
                    SUCCESS RATE</div>
                <div style="color:{D['text']}">{f'{float(sr):.1f}%' if sr else '—'}</div>
            </div>
        </div>

        <!-- Octa share bar -->
        <div style="margin:0.8rem 0 0.5rem">
            <div style="display:flex;justify-content:space-between;
                        font-size:0.72rem;color:{D['muted']};margin-bottom:4px">
                <span>Octa share of total budget</span>
                <span style="color:{s_border}">{octa_pct:.1f}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.1);border-radius:4px;height:6px">
                <div style="background:{s_border};border-radius:4px;height:6px;
                            width:{min(octa_pct,100):.1f}%"></div>
            </div>
        </div>

        <!-- Links -->
        {"<div style='margin-bottom:0.6rem'>" + " ".join(link_parts) + "</div>"
          if link_parts else ""}

        <!-- Consortium -->
        {consortium_html}

        <!-- Actions -->
        {actions_div}

        <!-- Comment -->
        {comment_html}
    </div>
    """, unsafe_allow_html=True)

    # Edit button sits flush below each card
    if st.button(f"✏️ Edit {pid}", key=f"edit_{pid}"):
        st.session_state["edit_proposal_id"] = pid
        st.switch_page("pages/proposal_form.py")


