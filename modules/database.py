"""Octa Proposals — Supabase database layer."""
import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
from config import MAX_PARTNERS, MAX_ASSOCIATES


@st.cache_resource
def _client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


def db() -> Client:
    return _client()


# ── Proposal ID generation ────────────────────────────────────────────────────

def next_proposal_id() -> str:
    """Return next Octa_Proposal_XXX id based on highest number in DB."""
    try:
        resp = db().table("proposals").select("proposal_id").execute()
        nums = []
        for r in (resp.data or []):
            try:
                nums.append(int(r["proposal_id"].split("_")[-1]))
            except Exception:
                pass
        return f"Octa_Proposal_{(max(nums) + 1) if nums else 1:03d}"
    except Exception:
        return "Octa_Proposal_001"


# ── Proposals ─────────────────────────────────────────────────────────────────

def get_all_proposals() -> list:
    resp = db().table("proposals").select("*").order("proposal_id").execute()
    return resp.data or []


def get_proposal_ids() -> set:
    resp = db().table("proposals").select("proposal_id").execute()
    return {r["proposal_id"] for r in (resp.data or [])}


def get_proposal_by_pid(proposal_id: str) -> dict | None:
    resp = (db().table("proposals").select("*")
            .eq("proposal_id", proposal_id).execute())
    return resp.data[0] if resp.data else None


def upsert_proposal(data: dict) -> tuple:
    """Upsert by proposal_id. Returns (ok: bool, message: str)."""
    try:
        data["updated_at"] = datetime.now().isoformat()
        db().table("proposals").upsert(
            data, on_conflict="proposal_id"
        ).execute()
        return True, "Saved successfully."
    except Exception as e:
        return False, f"Database error: {e}"


def _safe_num(v, default=0):
    try:
        return float(str(v).replace(",", "").strip())
    except Exception:
        return default


def _safe_date(v):
    if not v:
        return None
    if isinstance(v, date):
        return v.isoformat()
    s = str(v).strip()
    return s or None


def row_to_db(row: dict) -> dict:
    """Convert flat Google Sheet row → DB-shaped dict."""
    partners   = [row.get(f"Partner {i}",   "") for i in range(1, MAX_PARTNERS   + 1)]
    associates = [row.get(f"Associated {i}", "") for i in range(1, MAX_ASSOCIATES + 1)]
    return {
        "proposal_id":        str(row.get("Proposal ID", "")).strip(),
        "action_tamer":       row.get("Action: Tamer",          ""),
        "action_yasin":       row.get("Action: Yasin",          ""),
        "action_haseeb":      row.get("Action: Haseeb",         ""),
        "action_other":       row.get("Action: Other",          ""),
        "comment":            row.get("Comment",                 ""),
        "pes_fund_request":   row.get("PES Fund Request",       ""),
        "status":             row.get("Status",            "Planned"),
        "octa_budget":        _safe_num(row.get("Octa Budget (EUR)",   0)),
        "total_budget":       _safe_num(row.get("Total Budget (EUR)",  0)),
        "link_cloudearti":    row.get("Link to CloudEARTHi",    ""),
        "success_rate":       _safe_num(row.get("Success Rate (%)",    0)),
        "duration_months":    int(_safe_num(row.get("Duration (months)", 0))),
        "mandate_letter":     row.get("Mandate/Support Letter", ""),
        "responsible_person": row.get("Responsible Person",     ""),
        "main_writer":        row.get("Main Writer",            ""),
        "form_id":            row.get("Form ID",                ""),
        "submission_id":      row.get("Submission ID",          ""),
        "acronym":            row.get("Acronym",                ""),
        "proposal_title":     row.get("Proposal Title",         ""),
        "call":               row.get("Call",                   ""),
        "topic":              row.get("Topic",                  ""),
        "type_of_action":     row.get("Type of Action",         ""),
        "link_to_call":       row.get("Link to Call",           ""),
        "google_drive_link":  row.get("Google Drive Link",      ""),
        "deadline":           _safe_date(row.get("Deadline")),
        "submission_date":    _safe_date(row.get("Submission Date")),
        "announcement_date":  _safe_date(row.get("Announcement Date")),
        "coordinator":        row.get("Coordinator",            ""),
        "partners_list":      [p for p in partners   if p],
        "associates_list":    [a for a in associates if a],
    }


def db_to_sheet_row(p: dict, sheet_columns: list) -> list:
    """Flatten DB row → ordered list matching SHEET_COLUMNS."""
    partners_list   = p.get("partners_list")   or []
    associates_list = p.get("associates_list") or []
    if isinstance(partners_list,   str): partners_list   = []
    if isinstance(associates_list, str): associates_list = []

    flat = {
        "Proposal ID":          p.get("proposal_id",        ""),
        "Action: Tamer":        p.get("action_tamer",        ""),
        "Action: Yasin":        p.get("action_yasin",        ""),
        "Action: Haseeb":       p.get("action_haseeb",       ""),
        "Action: Other":        p.get("action_other",        ""),
        "Comment":              p.get("comment",             ""),
        "PES Fund Request":     p.get("pes_fund_request",    ""),
        "Status":               p.get("status",              ""),
        "Octa Budget (EUR)":    p.get("octa_budget",          0),
        "Total Budget (EUR)":   p.get("total_budget",         0),
        "Link to CloudEARTHi":  p.get("link_cloudearti",     ""),
        "Success Rate (%)":     p.get("success_rate",         0),
        "Duration (months)":    p.get("duration_months",      0),
        "Mandate/Support Letter": p.get("mandate_letter",    ""),
        "Responsible Person":   p.get("responsible_person",  ""),
        "Main Writer":          p.get("main_writer",         ""),
        "Form ID":              p.get("form_id",             ""),
        "Submission ID":        p.get("submission_id",       ""),
        "Acronym":              p.get("acronym",             ""),
        "Proposal Title":       p.get("proposal_title",      ""),
        "Call":                 p.get("call",                ""),
        "Topic":                p.get("topic",               ""),
        "Type of Action":       p.get("type_of_action",      ""),
        "Link to Call":         p.get("link_to_call",        ""),
        "Google Drive Link":    p.get("google_drive_link",   ""),
        "Deadline":             str(p.get("deadline")    or ""),
        "Submission Date":      str(p.get("submission_date") or ""),
        "Announcement Date":    str(p.get("announcement_date") or ""),
        "Coordinator":          p.get("coordinator",         ""),
    }
    from config import MAX_PARTNERS, MAX_ASSOCIATES
    for i in range(1, MAX_PARTNERS + 1):
        flat[f"Partner {i}"] = partners_list[i-1] if i-1 < len(partners_list) else ""
    for i in range(1, MAX_ASSOCIATES + 1):
        flat[f"Associated {i}"] = associates_list[i-1] if i-1 < len(associates_list) else ""

    return [str(flat.get(col, "")) for col in sheet_columns]


# ── Partners ──────────────────────────────────────────────────────────────────

def get_all_partners() -> list:
    resp = db().table("partners").select("*").order("full_name").execute()
    return resp.data or []


def upsert_partner(data: dict) -> tuple:
    try:
        data["updated_at"] = datetime.now().isoformat()
        if data.get("id"):
            pid = data.pop("id")
            db().table("partners").update(data).eq("id", pid).execute()
        else:
            db().table("partners").insert(data).execute()
        return True, "Partner saved."
    except Exception as e:
        return False, f"Error: {e}"


def delete_partner(partner_id: int) -> bool:
    try:
        db().table("partners").delete().eq("id", partner_id).execute()
        return True
    except Exception:
        return False
