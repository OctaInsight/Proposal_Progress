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
from config import SHEET_COLUMNS_BASE


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
    Headers are built dynamically to match the actual partner count.
    """
    row_values = _db_to_sheet_row(proposal_db_row)
    headers    = _build_header_for_row(proposal_db_row)
    return _post({
        "action":      "write_row",
        "proposal_id": proposal_db_row.get("proposal_id",""),
        "headers":     headers,
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
    """
    Flatten DB dict → ordered list for Google Sheets.
    Partner and associate columns are fully dynamic — no upper limit.
    Column order: base fields | Partner 1..N | Associated 1..M
    """
    partners_list   = p.get("partners_list")   or []
    associates_list = p.get("associates_list") or []
    if isinstance(partners_list,   str): partners_list   = []
    if isinstance(associates_list, str): associates_list = []

    base_values = [
        str(p.get("proposal_id",         "")),
        str(p.get("action_tamer",         "")),
        str(p.get("action_yasin",         "")),
        str(p.get("action_haseeb",        "")),
        str(p.get("action_other",         "")),
        str(p.get("comment",              "")),
        str(p.get("pes_fund_request",     "")),
        str(p.get("status",               "")),
        # Budget — written with € sign so sheet displays correctly
        f"€{float(p.get('octa_budget', 0) or 0):,.2f}",
        f"€{float(p.get('total_budget', 0) or 0):,.2f}",
        str(p.get("link_cloudearti",      "")),
        # Success rate — written with % sign
        f"{float(p.get('success_rate', 0) or 0):.2f}%",
        str(p.get("duration_months",       0)),
        str(p.get("mandate_letter",       "")),
        str(p.get("responsible_person",   "")),
        str(p.get("main_writer",          "")),
        str(p.get("form_id",              "")),
        str(p.get("submission_id",        "")),
        str(p.get("acronym",              "")),
        str(p.get("proposal_title",       "")),
        str(p.get("call",                 "")),
        str(p.get("topic",                "")),
        str(p.get("type_of_action",       "")),
        str(p.get("link_to_call",         "")),
        str(p.get("google_drive_link",    "")),
        str(p.get("deadline")             or ""),
        str(p.get("submission_date")      or ""),
        str(p.get("announcement_date")    or ""),
        str(p.get("coordinator",          "")),
    ]

    # Append as many partner/associate columns as actually exist
    partner_values   = [str(v) for v in partners_list   if v is not None]
    associate_values = [str(v) for v in associates_list if v is not None]

    return base_values + partner_values + associate_values


def _build_header_for_row(p: dict) -> list:
    """Build matching header list for a given proposal row."""
    from config import SHEET_COLUMNS_BASE
    partners_list   = p.get("partners_list")   or []
    associates_list = p.get("associates_list") or []
    if isinstance(partners_list,   str): partners_list   = []
    if isinstance(associates_list, str): associates_list = []
    headers = list(SHEET_COLUMNS_BASE)
    for i in range(1, len(partners_list) + 1):
        headers.append(f"Partner {i}")
    for i in range(1, len(associates_list) + 1):
        headers.append(f"Associated {i}")
    return headers
