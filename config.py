"""Octa Proposals — Central configuration."""

APP_NAME    = "Octa Proposals"
APP_ICON    = "📋"
APP_VERSION = "1.0.0"

MAX_PARTNERS   = 12
MAX_ASSOCIATES = 4

PES_FUND_OPTIONS = [
    "", "Un-entitled to PES fund", "Entitled to PES fund",
    "PES fund application submitted", "PES fund granted", "PES fund received",
]
STATUS_OPTIONS   = ["Planned","In preparation","Submitted","Missed","Funded","Rejected"]
MANDATE_OPTIONS  = ["Not required","Received","Signed","Submitted"]
CLOUDEARTI_OPTIONS = ["","CloudEARTHi project","Octa Insight project"]
PARTNER_TYPES    = ["HEI","Business","NGO","Governmental body",
                    "Research institute","Municipality","Others"]

SHEET_COLUMNS = (
    ["Proposal ID",
     "Action: Tamer","Action: Yasin","Action: Haseeb","Action: Other",
     "Comment","PES Fund Request","Status",
     "Octa Budget (EUR)","Total Budget (EUR)","Link to CloudEARTHi",
     "Success Rate (%)","Duration (months)","Mandate/Support Letter",
     "Responsible Person","Main Writer","Form ID","Submission ID",
     "Acronym","Proposal Title","Call","Topic","Type of Action",
     "Link to Call","Google Drive Link",
     "Deadline","Submission Date","Announcement Date","Coordinator"]
    + [f"Partner {i}" for i in range(1, MAX_PARTNERS + 1)]
    + [f"Associated {i}" for i in range(1, MAX_ASSOCIATES + 1)]
)

COUNTRIES = [
    "Afghanistan","Albania","Algeria","Andorra","Angola","Argentina","Armenia",
    "Australia","Austria","Azerbaijan","Bahrain","Bangladesh","Belarus","Belgium",
    "Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Bulgaria","Cambodia",
    "Cameroon","Canada","Chile","China","Colombia","Congo","Costa Rica","Croatia",
    "Cuba","Cyprus","Czechia","Denmark","Dominican Republic","Ecuador","Egypt",
    "Estonia","Ethiopia","Finland","France","Georgia","Germany","Ghana","Greece",
    "Guatemala","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland",
    "Israel","Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kosovo",
    "Kuwait","Latvia","Lebanon","Libya","Lithuania","Luxembourg","Malaysia","Mali",
    "Malta","Mexico","Moldova","Monaco","Montenegro","Morocco","Mozambique",
    "Myanmar","Netherlands","New Zealand","Nigeria","North Macedonia","Norway",
    "Oman","Pakistan","Palestine","Panama","Peru","Philippines","Poland",
    "Portugal","Qatar","Romania","Russia","Rwanda","Saudi Arabia","Senegal",
    "Serbia","Singapore","Slovakia","Slovenia","South Africa","South Korea",
    "South Sudan","Spain","Sri Lanka","Sudan","Sweden","Switzerland","Syria",
    "Taiwan","Tanzania","Thailand","Tunisia","Turkey","Uganda","Ukraine",
    "United Arab Emirates","United Kingdom","United States","Uruguay",
    "Uzbekistan","Venezuela","Vietnam","Yemen","Zambia","Zimbabwe","Other",
]

DARK = {
    "bg":      "#0f1421",
    "bg2":     "#1a2235",
    "bg3":     "#232f45",
    "border":  "rgba(255,255,255,0.09)",
    "text":    "#e2e8f0",
    "muted":   "#8899b0",
    "accent":  "#00BCD4",
    "accent2": "#FF6B35",
    "sidebar": "#1B2A4A",
    "success": "#6fcf97",
    "warning": "#f6cc52",
    "danger":  "#fc8181",
}
