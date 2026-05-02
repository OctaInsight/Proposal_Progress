"""
Octa Proposals — Google Sheets integration via Apps Script Web App.
No service account keys required.
Read  → published CSV URL (no auth)
Write → Apps Script Web App endpoint (no auth, just the URL)
"""
import streamlit as st
import requests
import pandas as pd
import json
import io
from config import SHEET_COLUMNS, MAX_PARTNERS, MAX_ASSOCIATES


def _csv_url() -> str:
    try:
        return st.secrets["sheets"]["csv_url"]
    except Exception:
        return ""


def _script_url() -> str:
    try:
        return st.secrets["sheets"]["script_url"]
    except Exception:
        return ""


# ── Read ──────────────────────────────────────────────────────────────────────

def read_all_from_sheet() -> list:
    """
    Read all rows from the published CSV.
    Returns list of dicts keyed by header row.
    """
    url = _csv_url()
    if not url:
        return []
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text), dtype=str).fillna("")
        # Keep only rows with a non-empty Proposal ID
        if "Proposal ID" not in df.columns:
            return []
        df = df[df["Proposal ID"].str.strip() != ""]
        return df.to_dict(orient="records")
    except Exception as e:
        return []


def get_sheet_proposal_ids() -> set:
    rows = read_all_from_sheet()
    return {r.get("Proposal ID","").strip() for r in rows
            if r.get("Proposal ID","").strip()}


# ── Write ─────────────────────────────────────────────────────────────────────

def _post(payload: dict) -> tuple:
    """POST JSON to Apps Script web app. Returns (ok, message)."""
    url = _script_url()
    if not url:
        return False, "Apps Script URL not configured in secrets.toml."
    try:
        resp = requests.post(
            url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=20,
            # Apps Script redirects — follow them
            allow_redirects=True,
        )
        result = resp.json()
        if result.get("status") == "ok":
            return True, "Synced to Google Sheet."
        return False, f"Script error: {result.get('message', resp.text)}"
    except Exception as e:
        return False, f"Sheet write error: {e}"


def ensure_header() -> tuple:
    """Make sure the header row exists in the Sheet."""
    return _post({
        "action":  "ensure_header",
        "headers": SHEET_COLUMNS,
    })


def write_proposal_to_sheet(proposal_db_row: dict) -> tuple:
    """
    Write (or overwrite) one proposal to the Sheet.
    Matches by Proposal ID in column A.
    """
    row_values = _db_to_sheet_row(proposal_db_row)
    return _post({
        "action":      "write_row",
        "proposal_id": proposal_db_row.get("proposal_id",""),
        "headers":     SHEET_COLUMNS,
        "row":         row_values,
    })


# ── Sync Sheet → DB ───────────────────────────────────────────────────────────

def sync_sheet_to_db() -> tuple:
    """
    Read Sheet → find Proposal IDs not in DB → insert them.
    Returns (new_count: int, message: str).
    Called once per session on app load.
    """
    from modules.database import get_proposal_ids, row_to_db, upsert_proposal

    csv = _csv_url()
    if not csv:
        return 0, "ℹ️ Google Sheet not configured — skipping sync."

    sheet_rows = read_all_from_sheet()
    if not sheet_rows:
        return 0, "ℹ️ Google Sheet is empty or unreachable — skipping sync."

    db_ids    = get_proposal_ids()
    new_count = 0
    errors    = []

    for row in sheet_rows:
        pid = row.get("Proposal ID","").strip()
        if not pid or pid in db_ids:
            continue
        db_row = row_to_db(row)
        ok, msg = upsert_proposal(db_row)
        if ok:
            new_count += 1
        else:
            errors.append(f"{pid}: {msg}")

    if errors:
        return new_count, (f"⚠️ Sync done with errors: {'; '.join(errors[:3])}")
    if new_count > 0:
        return new_count, (f"✅ {new_count} new proposal(s) imported from Google Sheet.")
    return 0, "✅ Database is up to date with Google Sheet."


# ── Internal helper ───────────────────────────────────────────────────────────

def _db_to_sheet_row(p: dict) -> list:
    """Flatten DB dict → ordered list matching SHEET_COLUMNS."""
    partners_list   = p.get("partners_list")   or []
    associates_list = p.get("associates_list") or []
    if isinstance(partners_list,   str): partners_list   = []
    if isinstance(associates_list, str): associates_list = []

    flat = {
        "Proposal ID":            p.get("proposal_id",         ""),
        "Action: Tamer":          p.get("action_tamer",         ""),
        "Action: Yasin":          p.get("action_yasin",         ""),
        "Action: Haseeb":         p.get("action_haseeb",        ""),
        "Action: Other":          p.get("action_other",         ""),
        "Comment":                p.get("comment",              ""),
        "PES Fund Request":       p.get("pes_fund_request",     ""),
        "Status":                 p.get("status",               ""),
        "Octa Budget (EUR)":      str(p.get("octa_budget",       0)),
        "Total Budget (EUR)":     str(p.get("total_budget",      0)),
        "Link to CloudEARTHi":    p.get("link_cloudearti",      ""),
        "Success Rate (%)":       str(p.get("success_rate",      0)),
        "Duration (months)":      str(p.get("duration_months",   0)),
        "Mandate/Support Letter": p.get("mandate_letter",       ""),
        "Responsible Person":     p.get("responsible_person",   ""),
        "Main Writer":            p.get("main_writer",          ""),
        "Form ID":                p.get("form_id",              ""),
        "Submission ID":          p.get("submission_id",        ""),
        "Acronym":                p.get("acronym",              ""),
        "Proposal Title":         p.get("proposal_title",       ""),
        "Call":                   p.get("call",                 ""),
        "Topic":                  p.get("topic",                ""),
        "Type of Action":         p.get("type_of_action",       ""),
        "Link to Call":           p.get("link_to_call",         ""),
        "Google Drive Link":      p.get("google_drive_link",    ""),
        "Deadline":               str(p.get("deadline")         or ""),
        "Submission Date":        str(p.get("submission_date")  or ""),
        "Announcement Date":      str(p.get("announcement_date") or ""),
        "Coordinator":            p.get("coordinator",          ""),
    }
    for i in range(1, MAX_PARTNERS + 1):
        flat[f"Partner {i}"] = (
            partners_list[i-1] if i-1 < len(partners_list) else "")
    for i in range(1, MAX_ASSOCIATES + 1):
        flat[f"Associated {i}"] = (
            associates_list[i-1] if i-1 < len(associates_list) else "")

    return [str(flat.get(col, "")) for col in SHEET_COLUMNS]
