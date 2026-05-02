# 📋 Octa Proposals
> Proposal tracking + partner management with Google Sheets sync and Supabase storage.

---

## Setup in 4 Steps

### Step 1 — Supabase
1. Go to **supabase.com** → new project
2. SQL Editor → paste `setup_supabase.sql` → Run
3. Settings → API → copy **URL** and **service_role** key

### Step 2 — Google Sheets
1. Create a Google Sheet and note its **Sheet ID** (the long string in the URL)
2. Go to **console.cloud.google.com** → new project
3. Enable **Google Sheets API** and **Google Drive API**
4. IAM → Service Accounts → Create → download JSON key
5. **Share your Google Sheet** with the service account email (Editor access)

### Step 3 — GitHub
```bash
git init && git add . && git commit -m "feat: Octa Proposals v1.0"
git remote add origin https://github.com/YOUR_ORG/octa-proposals.git
git push -u origin main
```

### Step 4 — Streamlit Cloud
1. **share.streamlit.io** → New app → select repo → `app.py`
2. Advanced settings → Secrets → paste:

```toml
[supabase]
url = "https://xxxx.supabase.co"
key = "service-role-key"

[sheets]
sheet_id   = "your-sheet-id"
sheet_name = "Sheet1"

[gcp_service_account]
type              = "service_account"
project_id        = "..."
private_key_id    = "..."
private_key       = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email      = "...@....iam.gserviceaccount.com"
client_id         = "..."
auth_uri          = "https://accounts.google.com/o/oauth2/auth"
token_uri         = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

---

## How It Works

```
App loads → reads Google Sheet → compares Proposal IDs → 
imports any new rows into Supabase → session reads from DB only

On Save → writes to Supabase → mirrors to Google Sheet
```

**Source of truth:** Supabase  
**Google Sheet:** bidirectional mirror — team can still use it freely

---

## Proposal ID Format
`Octa_Proposal_001`, `Octa_Proposal_002`, … (auto-incremented, zero-padded)

---

## File Structure
```
octa_proposals/
├── app.py                          # Landing page + sync on load
├── config.py                       # All field options + constants
├── requirements.txt
├── setup_supabase.sql
├── .streamlit/secrets.toml.example
├── modules/
│   ├── database.py                 # Supabase CRUD
│   ├── sheets.py                   # Google Sheets read/write/sync
│   └── ui_helpers.py               # Dark CSS + shared components
└── pages/
    ├── dashboard.py                # Proposals dashboard + edit
    ├── proposal_form.py            # Add / Edit proposal form
    └── partners.py                 # Partner management
```
