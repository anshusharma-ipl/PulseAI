"""
Pulse AI — Customer Health Intelligence Dashboard
Enterprise Edition  |  Langflow RAG-backed  |  v3.0

Changes in v3.0:
  - Query to Langflow is now just the account_id (e.g. "ACC-003") for maximum
    RAG retrieval precision — see langflow_setup_guide.md for Langflow config.
  - Full visual redesign: stat tiles, ticket severity badges, KPI chips,
    numbered priority action cards, trend indicators, confidence meter.
  - All HTML built via string concatenation — no nested f-strings.
"""

import re
import hashlib
import urllib.parse
from datetime import datetime

import requests
import streamlit as st

try:
    import markdown as md_lib
    _HAS_MD = True
except ImportError:
    _HAS_MD = False

try:
    from fpdf import FPDF
    _HAS_FPDF = True
except ImportError:
    _HAS_FPDF = False


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pulse AI — Customer Health",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CREDENTIALS
# Priority order:
#   1. Streamlit query params  (?lf_url=...&lf_key=...&lf_portfolio=...)
#      — injected by the doc-site launcher page from its localStorage settings
#   2. Environment variables   (LANGFLOW_URL, LANGFLOW_API_KEY, LANGFLOW_PORTFOLIO_URL)
#      — useful for server deployments / .env files
#   3. Hard-coded fallback below (blank — app runs in shell-only mode)
# ─────────────────────────────────────────────────────────────────────────────
import os as _os

def _get_credential(qp_key: str, env_key: str, fallback: str = "") -> str:
    """Read a credential from query params first, then env vars, then fallback."""
    try:
        qp = st.query_params.get(qp_key, "")
        if qp:
            return qp
    except Exception:
        pass
    return _os.environ.get(env_key, fallback)

LANGFLOW_URL           = _get_credential("lf_url",       "LANGFLOW_URL",           "")
LANGFLOW_API_KEY       = _get_credential("lf_key",       "LANGFLOW_API_KEY",       "")
LANGFLOW_PORTFOLIO_URL = _get_credential("lf_portfolio", "LANGFLOW_PORTFOLIO_URL", "")

# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT MAP
# ─────────────────────────────────────────────────────────────────────────────
ACCOUNT_ID_MAP = {
    "Acme Corp": "ACC-001", "Globex Inc": "ACC-002", "Initech Systems": "ACC-003",
    "Umbrella Health": "ACC-004", "Stark Industries": "ACC-005", "Wayne Analytics": "ACC-006",
    "Oscorp Data": "ACC-007", "Pied Piper": "ACC-008", "Hooli Cloud": "ACC-009",
    "Massive Dynamic": "ACC-010", "Cyberdyne Systems": "ACC-011", "Soylent Corp": "ACC-012",
    "Wonka Enterprises": "ACC-013", "Tyrell Systems": "ACC-014",
    "Dunder Mifflin Digital": "ACC-015", "Prestige Global": "ACC-016",
    "Sterling Cooper Analytics": "ACC-017", "Bluth SaaS": "ACC-018",
    "Aperture Science": "ACC-019", "Weyland Analytics": "ACC-020",
}

ACCOUNTS = [
    "Acme Corp", "Stark Industries", "Cyberdyne Systems", "Aperture Science",
    "Umbrella Health", "Globex Inc", "Wayne Analytics", "Massive Dynamic",
    "Oscorp Data", "Tyrell Systems", "Prestige Global", "Sterling Cooper Analytics",
    "Weyland Analytics", "Soylent Corp", "Wonka Enterprises",
    "Initech Systems", "Hooli Cloud", "Pied Piper", "Dunder Mifflin Digital", "Bluth SaaS",
]

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────
INK      = "#0F1B2D"
PAPER    = "#EEF2F7"
CARD     = "#FFFFFF"
LINE     = "#DEE4EA"
TEAL     = "#1F9E8E"
AMBER    = "#E1993B"
CORAL    = "#E15B4C"
INK_SOFT = "#5C7089"
SLATE    = "#4A5A6B"
GREEN_BG = "#F0FAF8"
AMBER_BG = "#FEF9EE"
CORAL_BG = "#FEF2F1"
BLUE     = "#3B6FA0"

AVATAR_PALETTE = [TEAL, AMBER, CORAL, BLUE, "#7A5FB5", "#2E8B72"]

STATUS_META = {
    "Healthy":  {"color": TEAL,  "bg": GREEN_BG, "icon": "&#10003;", "label": "Healthy"},
    "At Risk":  {"color": AMBER, "bg": AMBER_BG, "icon": "&#9888;",  "label": "At Risk"},
    "Critical": {"color": CORAL, "bg": CORAL_BG, "icon": "&#33;",    "label": "Critical"},
    "Reviewed": {"color": SLATE, "bg": "#F4F5F7", "icon": "&#9679;", "label": "Reviewed"},
}

SEV_COLOR = {
    "Critical": (CORAL, CORAL_BG),
    "High":     (AMBER, AMBER_BG),
    "Medium":   (BLUE,  "#EFF4FA"),
    "Low":      (TEAL,  GREEN_BG),
    "Open":     (CORAL, CORAL_BG),
    "In Progress": (AMBER, AMBER_BG),
    "Resolved": (TEAL,  GREEN_BG),
}

SECTION_META = {
    "overview":  {"color": INK_SOFT, "bg": "#F7F8FA", "label": "Account Summary",
                  "icon": '<path d="M4 12h4l2-7 4 14 2-7h4"/>'},
    "usage":     {"color": TEAL,     "bg": GREEN_BG,  "label": "Usage & Adoption",
                  "icon": '<path d="M4 20V10M10 20V4M16 20v-7M22 20v-4"/>'},
    "support":   {"color": AMBER,    "bg": AMBER_BG,  "label": "Support & Escalations",
                  "icon": '<path d="M4 13a8 8 0 0 1 16 0v5a2 2 0 0 1-2 2h-1v-7h3M4 18v-5h3v7H6a2 2 0 0 1-2-2z"/>'},
    "financial": {"color": BLUE,     "bg": "#EFF4FA", "label": "Commercial Health",
                  "icon": '<circle cx="12" cy="12" r="8"/><path d="M12 7v10M9.5 9.5h3.2a1.8 1.8 0 1 1 0 3.6H9.8a1.8 1.8 0 1 0 0 3.6h3.4"/>'},
    "risk":      {"color": CORAL,    "bg": CORAL_BG,  "label": "Risk Signals",
                  "icon": '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>'},
    "action":    {"color": TEAL,     "bg": GREEN_BG,  "label": "Recommended Actions",
                  "icon": '<path d="M9 18h6M10 21h4M12 3a5 5 0 0 0-3 9c.6.5 1 1.2 1 2h4c0-.8.4-1.5 1-2a5 5 0 0 0-3-9z"/>'},
    "general":   {"color": INK_SOFT, "bg": "#F7F8FA", "label": "Additional Detail",
                  "icon": '<path d="M4 6h16M4 12h16M4 18h10"/>'},
    "portfolio_health": {"color": INK_SOFT, "bg": "#F7F8FA", "label": "Overview",
                  "icon": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>'},
    "attention": {"color": CORAL, "bg": CORAL_BG, "label": "Risk Signals",
                  "icon": '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>'},
    "insights":  {"color": TEAL, "bg": GREEN_BG, "label": "Insights",
                  "icon": '<path d="M9 18h6M10 21h4M12 3a5 5 0 0 0-3 9c.6.5 1 1.2 1 2h4c0-.8.4-1.5 1-2a5 5 0 0 0-3-9z"/>'},
}


# ─────────────────────────────────────────────────────────────────────────────
# PURE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def svg(path: str, color: str, size: int = 16) -> str:
    return (
        '<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 24 24" fill="none" '
        'stroke="' + color + '" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        + path + '</svg>'
    )


def avatar(name: str) -> str:
    words    = name.split()
    initials = (words[0][0] + (words[1][0] if len(words) > 1 else "")).upper()
    color    = AVATAR_PALETTE[int(hashlib.md5(name.encode()).hexdigest(), 16) % len(AVATAR_PALETTE)]
    return (
        '<div style="width:52px;height:52px;border-radius:12px;background:' + color + ';'
        'display:flex;align-items:center;justify-content:center;'
        'color:#fff;font-weight:700;font-size:1.15rem;flex-shrink:0;">'
        + initials + '</div>'
    )


def sev_badge(label: str) -> str:
    color, bg = SEV_COLOR.get(label, (SLATE, "#F4F5F7"))
    return (
        '<span style="display:inline-block;padding:2px 9px;border-radius:999px;font-size:0.75rem;'
        'font-weight:700;background:' + bg + ';color:' + color + ';border:1px solid ' + color + '20;">'
        + label + '</span>'
    )


def trend_arrow(direction: str) -> str:
    """direction: 'up' | 'down' | 'flat'"""
    if direction == "up":
        return '<span style="color:' + TEAL + ';font-size:1rem;margin-left:4px;">&#9650;</span>'
    if direction == "down":
        return '<span style="color:' + CORAL + ';font-size:1rem;margin-left:4px;">&#9660;</span>'
    return '<span style="color:' + SLATE + ';font-size:1rem;margin-left:4px;">&#9654;</span>'


def kv_row(label: str, value: str) -> str:
    if len(value) > 70:
        # Long, narrative-style values read poorly right-aligned and ragged.
        # Stack label above value and left-align like body copy instead.
        return (
            '<div style="padding:10px 0;border-bottom:1px solid ' + LINE + ';">'
            '<div style="font-size:0.83rem;color:' + INK_SOFT + ';font-weight:500;margin-bottom:5px;">'
            + label + '</div>'
            '<div style="font-size:0.91rem;color:' + INK + ';font-weight:500;line-height:1.65;text-align:left;">'
            + value + '</div>'
            '</div>'
        )
    return (
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        'padding:7px 0;border-bottom:1px solid ' + LINE + ';">'
        '<span style="font-size:0.83rem;color:' + INK_SOFT + ';font-weight:500;">' + label + '</span>'
        '<span style="font-size:0.88rem;color:' + INK + ';font-weight:600;text-align:right;max-width:60%;">' + value + '</span>'
        '</div>'
    )


def section_header(meta: dict, title: str) -> str:
    icon_html = svg(meta["icon"], meta["color"], 16)
    return (
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
        '<div style="width:28px;height:28px;border-radius:7px;background:' + meta["bg"] + ';'
        'display:flex;align-items:center;justify-content:center;">' + icon_html + '</div>'
        '<span style="font-size:0.72rem;font-weight:700;letter-spacing:0.07em;'
        'text-transform:uppercase;color:' + meta["color"] + ';">' + meta["label"] + '</span>'
        '</div>'
        '<p style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:600;font-size:1.08rem;'
        'color:' + INK + ';margin:0 0 14px;">' + title + '</p>'
    )


def card_wrap(content: str, border_color: str, bg: str = CARD) -> str:
    return (
        '<div style="background:' + bg + ';border:1px solid ' + LINE + ';'
        'border-left:4px solid ' + border_color + ';border-radius:12px;'
        'padding:20px 22px;margin-bottom:16px;">'
        + content + '</div>'
    )


def md_to_html(text: str) -> str:
    if _HAS_MD:
        return md_lib.markdown(text, extensions=["extra", "sane_lists"])
    out, in_list = [], False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append("<li>" + s[2:] + "</li>")
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            if s:
                out.append("<p>" + s + "</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


# ─────────────────────────────────────────────────────────────────────────────
# TEXT ANALYSIS HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def detect_status(text: str) -> str:
    t = text.lower()
    if re.search(r"overall status\s*:\s*critical", t):  return "Critical"
    if re.search(r"overall status\s*:\s*at risk", t):   return "At Risk"
    if re.search(r"overall status\s*:\s*healthy", t):   return "Healthy"
    if re.search(r"critical|severe.{0,10}risk|immediate attention", t): return "Critical"
    if re.search(r"at risk|caution|declining|moderate risk", t):         return "At Risk"
    if re.search(r"healthy|strong|stable|low risk|expanding", t):        return "Healthy"
    return "Reviewed"


def extract_score(text: str):
    m = re.search(
        r"health\s*score\s*[:\-]?\s*\**(\d{1,3})\**\s*(?:/\s*100)?",
        text, re.I,
    )
    if m:
        return max(0, min(int(m.group(1)), 100))
    return None


def extract_confidence(text: str) -> str:
    m = re.search(r"confidence\s*[:\-]\s*(high|medium|low)", text, re.I)
    return m.group(1).capitalize() if m else ""


def classify_section(title: str) -> str:
    t = title.lower()
    if re.search(r"risk|churn|concern|warning|alert", t):                    return "risk"
    if re.search(r"usage|adopt|engagement|activity|product|trend", t):       return "usage"
    if re.search(r"support|ticket|escalat", t):                              return "support"
    if re.search(r"financ|revenue|contract|renewal|arr|billing|commercial", t): return "financial"
    if re.search(r"recommend|action|next step|suggest|priorit", t):          return "action"
    if re.search(r"overview|summary|executive", t):                           return "overview"
    return "general"


def parse_sections(text: str) -> list:
    lines     = text.replace("\r\n", "\n").split("\n")
    header_re = re.compile(r"^\s{0,3}#{1,6}\s+(.*)")
    bold_re   = re.compile(r"^\s{0,3}\*\*(.+?)\*\*:?\s*$")
    sections, current = [], {"title": "Summary", "body": []}
    for line in lines:
        m  = header_re.match(line)
        m2 = bold_re.match(line) if not m else None
        if m or m2:
            if current["body"] and "".join(current["body"]).strip():
                sections.append(current)
            title   = (m.group(1) if m else m2.group(1)).strip().strip("*").rstrip(":")
            current = {"title": title, "body": []}
        else:
            current["body"].append(line)
    if current["body"] and "".join(current["body"]).strip():
        sections.append(current)
    return sections or [{"title": "Summary", "body": lines}]


# ─────────────────────────────────────────────────────────────────────────────
# SCORE RING
# ─────────────────────────────────────────────────────────────────────────────
def score_ring(score: int, color: str) -> str:
    c      = 2 * 3.14159 * 30
    offset = c * (1 - score / 100)
    return (
        '<div style="position:relative;width:78px;height:78px;flex-shrink:0;">'
        '<svg width="78" height="78" viewBox="0 0 78 78">'
        '<circle cx="39" cy="39" r="30" stroke="' + LINE + '" stroke-width="7" fill="none"/>'
        '<circle cx="39" cy="39" r="30" stroke="' + color + '" stroke-width="7" fill="none"'
        ' stroke-linecap="round"'
        ' stroke-dasharray="' + f'{c:.1f}' + '"'
        ' stroke-dashoffset="' + f'{offset:.1f}' + '"'
        ' transform="rotate(-90 39 39)"/>'
        '</svg>'
        '<div style="position:absolute;inset:0;display:flex;flex-direction:column;'
        'align-items:center;justify-content:center;">'
        '<span style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
        'font-size:1.25rem;color:' + INK + ';line-height:1;">' + str(score) + '</span>'
        '<span style="font-size:0.6rem;color:' + INK_SOFT + ';font-weight:500;'
        'text-transform:uppercase;letter-spacing:0.04em;">/ 100</span>'
        '</div>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# STAT TILE  — used in Usage cards
# ─────────────────────────────────────────────────────────────────────────────
def stat_tile(label: str, value: str, sub: str, trend: str = "flat", color: str = TEAL) -> str:
    arrow = trend_arrow(trend)
    return (
        '<div style="background:' + PAPER + ';border:1px solid ' + LINE + ';border-radius:10px;'
        'padding:12px 14px;flex:1;min-width:120px;">'
        '<div style="font-size:0.72rem;color:' + INK_SOFT + ';font-weight:600;'
        'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">' + label + '</div>'
        '<div style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
        'font-size:1.4rem;color:' + color + ';line-height:1.1;">' + value + arrow + '</div>'
        '<div style="font-size:0.75rem;color:' + INK_SOFT + ';margin-top:3px;">' + sub + '</div>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# TICKET CARD  — used in Support cards
# ─────────────────────────────────────────────────────────────────────────────
def ticket_card(tid: str, severity: str, status: str, category: str, description: str) -> str:
    sev_html    = sev_badge(severity)
    status_html = sev_badge(status)
    icon_path   = '<path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.8 19.8 0 0 1 3.08 5.18 2 2 0 0 1 5.07 3h3a2 2 0 0 1 2 1.72c.13 1 .36 1.96.7 2.88a2 2 0 0 1-.45 2.11L9.08 11a16 16 0 0 0 5.92 5.92l1.3-1.3a2 2 0 0 1 2.11-.45c.92.34 1.88.57 2.88.7A2 2 0 0 1 22 16.92z"/>'
    return (
        '<div style="background:' + PAPER + ';border:1px solid ' + LINE + ';border-radius:9px;'
        'padding:12px 14px;margin-bottom:10px;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:6px;">'
        '<div style="display:flex;align-items:center;gap:8px;">'
        + svg(icon_path, INK_SOFT, 14) +
        '<span style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
        'font-size:0.88rem;color:' + INK + ';">' + tid + '</span>'
        '<span style="font-size:0.78rem;color:' + INK_SOFT + ';">' + category + '</span>'
        '</div>'
        '<div style="display:flex;gap:6px;">' + sev_html + status_html + '</div>'
        '</div>'
        '<p style="font-size:0.88rem;color:#33414F;margin:0;line-height:1.5;">' + description + '</p>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY ACTION CARD
# ─────────────────────────────────────────────────────────────────────────────
def action_card(num: int, title: str, what: str, why: str) -> str:
    colors = [CORAL, AMBER, TEAL]
    bgs    = [CORAL_BG, AMBER_BG, GREEN_BG]
    c  = colors[(num - 1) % 3]
    bg = bgs[(num - 1) % 3]
    return (
        '<div style="display:flex;gap:14px;background:' + bg + ';border:1px solid ' + LINE + ';'
        'border-radius:10px;padding:14px 16px;margin-bottom:10px;">'
        '<div style="width:32px;height:32px;border-radius:50%;background:' + c + ';'
        'display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
        '<span style="color:#fff;font-weight:700;font-size:0.9rem;">' + str(num) + '</span>'
        '</div>'
        '<div style="flex:1;">'
        '<p style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
        'font-size:0.95rem;color:' + INK + ';margin:0 0 6px;">' + title + '</p>'
        '<p style="font-size:0.86rem;color:#33414F;margin:0 0 4px;">'
        '<b style="color:' + INK + ';">What:</b> ' + what + '</p>'
        '<p style="font-size:0.86rem;color:#33414F;margin:0;">'
        '<b style="color:' + c + ';">Why:</b> ' + why + '</p>'
        '</div>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# CONFIDENCE METER
# ─────────────────────────────────────────────────────────────────────────────
def confidence_meter(level: str) -> str:
    levels = {"High": 3, "Medium": 2, "Low": 1}
    colors = {"High": TEAL, "Medium": AMBER, "Low": CORAL}
    n      = levels.get(level, 0)
    c      = colors.get(level, SLATE)
    dots   = ""
    for i in range(1, 4):
        bg = c if i <= n else LINE
        dots += '<div style="width:10px;height:10px;border-radius:50%;background:' + bg + ';"></div>'
    return (
        '<div style="display:flex;align-items:center;gap:8px;margin-top:10px;">'
        '<span style="font-size:0.78rem;color:' + INK_SOFT + ';font-weight:600;'
        'text-transform:uppercase;letter-spacing:0.05em;">Confidence</span>'
        '<div style="display:flex;gap:4px;">' + dots + '</div>'
        '<span style="font-size:0.82rem;font-weight:700;color:' + c + ';">' + level + '</span>'
        '</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION-SPECIFIC RENDERERS
# Each receives the raw body text from the LLM and returns rich HTML
# ─────────────────────────────────────────────────────────────────────────────
def render_overview(body_md: str) -> str:
    """Executive Summary: extract Overall Status, Primary Driver, Narrative as distinct items."""
    lines = body_md.split("\n")
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Detect key: value pattern
        m = re.match(r"^(Overall Status|Primary Driver|Account Narrative|Risk Level)\s*[:\-]\s*(.+)", stripped, re.I)
        if m:
            key = m.group(1).strip()
            val = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", m.group(2).strip())
            rows.append(kv_row(key, val))
        else:
            clean = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", stripped)
            rows.append(
                '<p style="font-size:0.91rem;color:#33414F;line-height:1.65;margin:6px 0;">'
                + clean + '</p>'
            )
    return "".join(rows)


def render_usage(body_md: str) -> str:
    """Usage: show stat tiles for any numbers found, then bullet lists."""
    lines  = body_md.split("\n")
    tiles  = []
    bullets_pos  = []
    bullets_warn = []
    insight_lines = []
    mode = "none"

    for line in lines:
        s = line.strip()
        if not s:
            continue
        sl = s.lower()
        if re.search(r"positive signal|positive:", sl):
            mode = "pos"; continue
        if re.search(r"warning signal|warning:", sl):
            mode = "warn"; continue
        if re.search(r"adoption insight|insight:", sl):
            mode = "insight"
            # Might have inline content after the label
            rest = re.sub(r"^adoption insight\s*[:\-]\s*", "", s, flags=re.I).strip()
            if rest:
                insight_lines.append(rest)
            continue

        # Try to extract a stat tile from bullet lines containing numbers
        if mode == "pos" and s.startswith(("- ", "* ")):
            content = s[2:]
            # Look for DAU, NPS, adoption%, API calls patterns
            num_m = re.search(r"(\d[\d,\.]+)\s*(%|k|K)?", content)
            label_m = re.search(r"(DAU|NPS|adoption|API calls?|logins?|session|exports?)", content, re.I)
            if num_m and label_m:
                val = num_m.group(1) + (num_m.group(2) or "")
                lbl = label_m.group(1).upper()
                trend_dir = "up" if re.search(r"up|increas|grow|improv", content, re.I) else "flat"
                tiles.append(stat_tile(lbl, val, content, trend_dir, TEAL))
            else:
                bullets_pos.append('<li>' + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content) + '</li>')
        elif mode == "warn" and s.startswith(("- ", "* ")):
            content = s[2:]
            num_m = re.search(r"(\d[\d,\.]+)\s*(%|k|K)?", content)
            label_m = re.search(r"(DAU|NPS|adoption|API calls?|logins?|session|exports?)", content, re.I)
            if num_m and label_m:
                val = num_m.group(1) + (num_m.group(2) or "")
                lbl = label_m.group(1).upper()
                tiles.append(stat_tile(lbl, val, content, "down", CORAL))
            else:
                bullets_warn.append('<li>' + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content) + '</li>')
        elif mode == "insight":
            insight_lines.append(re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s))
        else:
            # Plain body line
            bullets_pos.append('<li>' + re.sub(r"\*{1,2}(.+?)\*{1,2}", r"<b>\1</b>", s.lstrip("-* ")) + '</li>')

    html = ""

    # Stat tiles row
    if tiles:
        html += (
            '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">'
            + "".join(tiles) + '</div>'
        )

    # Positive bullets
    if bullets_pos:
        html += (
            '<div style="margin-bottom:10px;">'
            '<div style="font-size:0.75rem;font-weight:700;color:' + TEAL + ';'
            'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">'
            + svg('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>', TEAL, 12)
            + '&nbsp;Positive Signals</div>'
            '<ul style="padding-left:16px;margin:0;color:#33414F;font-size:0.91rem;line-height:1.65;">'
            + "".join(bullets_pos) + '</ul></div>'
        )

    # Warning bullets
    if bullets_warn:
        html += (
            '<div style="margin-bottom:10px;">'
            '<div style="font-size:0.75rem;font-weight:700;color:' + CORAL + ';'
            'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">'
            + svg('<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>', CORAL, 12)
            + '&nbsp;Warning Signals</div>'
            '<ul style="padding-left:16px;margin:0;color:#33414F;font-size:0.91rem;line-height:1.65;">'
            + "".join(bullets_warn) + '</ul></div>'
        )

    # Insight paragraph
    if insight_lines:
        html += (
            '<div style="background:' + PAPER + ';border-left:3px solid ' + TEAL + ';'
            'border-radius:6px;padding:10px 14px;margin-top:4px;">'
            '<span style="font-size:0.72rem;font-weight:700;color:' + TEAL + ';'
            'text-transform:uppercase;letter-spacing:0.05em;">Adoption Insight</span>'
            '<p style="font-size:0.88rem;color:#33414F;margin:4px 0 0;line-height:1.6;">'
            + " ".join(insight_lines) + '</p></div>'
        )

    return html if html else md_to_html(body_md)


def render_support(body_md: str) -> str:
    """Support: extract tickets into badge cards, then summary rows."""
    lines = body_md.split("\n")
    ticket_blocks = []
    summary_rows  = []

    # Look for ticket lines: "TKT-XXX · severity · category · description"
    # or "- TKT-XXX ..."
    ticket_re = re.compile(
        r"(TKT-\d+)\s*[·|]\s*(Critical|High|Medium|Low)?\s*[·|]?\s*(\w[\w\s]*)?\s*[·|]?\s*(.*)",
        re.I,
    )
    alt_ticket_re = re.compile(
        r"(TKT-\d+)[^:]*:\s*(.+)", re.I
    )

    mode = "none"
    for line in lines:
        s = line.strip()
        if not s:
            continue
        sl = s.lower()
        if re.search(r"ticket overview|ticket summary", sl):
            mode = "tickets"; continue
        if re.search(r"resolution|satisfaction", sl):
            mode = "resolution"; continue
        if re.search(r"recurring", sl):
            mode = "recurring"; continue

        # Try to parse a ticket line
        m = ticket_re.search(s)
        if m and mode == "tickets":
            tid   = m.group(1)
            sev   = m.group(2) or "Medium"
            cat   = (m.group(3) or "").strip() or "General"
            desc  = (m.group(4) or "").strip() or s
            ticket_blocks.append(ticket_card(tid, sev, "Open", cat, desc))
            continue

        m2 = alt_ticket_re.search(s)
        if m2 and "TKT-" in s:
            tid  = m2.group(1)
            desc = m2.group(2).strip()
            # Try to extract severity from description
            sev = "Medium"
            for sv in ("Critical", "High", "Low"):
                if sv.lower() in s.lower():
                    sev = sv; break
            ticket_blocks.append(ticket_card(tid, sev, "Open", "Support", desc))
            continue

        if s.startswith(("- ", "* ")):
            content = s[2:]
            # Count ticket references
            if re.search(r"TKT-\d+", content):
                summary_rows.append(
                    '<li style="color:#33414F;font-size:0.88rem;line-height:1.65;">'
                    + re.sub(r"(TKT-\d+)", r'<b style="color:' + AMBER + r';">\1</b>', content)
                    + '</li>'
                )
            else:
                summary_rows.append(
                    '<li style="color:#33414F;font-size:0.88rem;line-height:1.65;">'
                    + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content) + '</li>'
                )
        elif not re.search(r"ticket overview|resolution|recurring|support", sl):
            clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>",
                           re.sub(r"\*(.+?)\*", r"\1", s))
            if clean:
                summary_rows.append(
                    '<p style="font-size:0.88rem;color:#33414F;line-height:1.65;margin:4px 0;">'
                    + clean + '</p>'
                )

    html = ""
    if ticket_blocks:
        html += "".join(ticket_blocks)
    if summary_rows:
        # Determine if list or paragraphs
        if any(r.startswith("<li") for r in summary_rows):
            html += (
                '<ul style="padding-left:16px;margin:8px 0 0;">'
                + "".join(r for r in summary_rows) + '</ul>'
            )
        else:
            html += "".join(summary_rows)

    return html if html else md_to_html(body_md)


def render_financial(body_md: str) -> str:
    """Commercial: extract KV pairs into a clean info grid."""
    lines = body_md.split("\n")
    kv_rows = []
    expansion_lines = []
    mode = "kv"

    for line in lines:
        s = line.strip()
        if not s:
            continue
        sl = s.lower()
        if re.search(r"expansion|license|upsell|intelligence", sl):
            mode = "expansion"
            rest = re.sub(r"^expansion[^:]*:\s*", "", s, flags=re.I).strip()
            if rest and len(rest) > 6:
                expansion_lines.append(rest)
            continue

        if mode == "kv":
            # Try key: value
            m = re.match(r"^[-*]?\s*(Contract Value|Renewal Date|Plan Tier|Segment|Region|Industry|CSM[^:]*|ARR)[^:]*:\s*(.+)", s, re.I)
            if m:
                kv_rows.append(kv_row(m.group(1).strip(), re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", m.group(2).strip())))
            else:
                # try pipe-separated
                for part in re.split(r"[|·]", s):
                    pm = re.match(r"\s*([\w\s]+?)\s*:\s*(.+)", part)
                    if pm:
                        kv_rows.append(kv_row(pm.group(1).strip(), re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", pm.group(2).strip())))
        else:
            clean = re.sub(r"^[-*]\s*", "", re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s))
            if clean:
                expansion_lines.append(clean)

    html = ""
    if kv_rows:
        html += '<div style="margin-bottom:12px;">' + "".join(kv_rows) + '</div>'

    if expansion_lines:
        exp_text = " ".join(expansion_lines)
        # Decide colour by content
        exp_color = TEAL if re.search(r"expan|upsell|seat|add|upgrade", exp_text, re.I) else INK_SOFT
        html += (
            '<div style="background:' + PAPER + ';border-left:3px solid ' + exp_color + ';'
            'border-radius:6px;padding:10px 14px;margin-top:6px;">'
            '<span style="font-size:0.72rem;font-weight:700;color:' + exp_color + ';'
            'text-transform:uppercase;letter-spacing:0.05em;">Expansion Signal</span>'
            '<p style="font-size:0.88rem;color:#33414F;margin:4px 0 0;line-height:1.6;">'
            + exp_text + '</p></div>'
        )

    return html if html else md_to_html(body_md)


def render_risk(body_md: str, confidence: str) -> str:
    """Risk: score tile + risk factor badges + confidence meter."""
    lines = body_md.split("\n")
    risk_factors = []
    extra_lines  = []
    score_val    = None
    risk_level   = ""

    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Score line
        sm = re.search(r"health\s*score\s*[:\-]?\s*\**(\d{1,3})\**", s, re.I)
        if sm:
            score_val = int(sm.group(1))
            continue
        # Risk level
        rlm = re.search(r"risk\s*level\s*[:\-]\s*(healthy|at risk|critical)", s, re.I)
        if rlm:
            risk_level = rlm.group(1).capitalize()
            continue
        # Confidence line handled externally
        if re.search(r"^confidence\s*[:\-]", s, re.I):
            continue
        # Risk factor bullets
        if s.startswith(("- ", "* ")):
            content = s[2:]
            # Highlight ticket/record IDs
            content = re.sub(r"(TKT-\d+|CRM-\d+|SIG-\d+)", r'<b style="color:' + CORAL + r';">\1</b>', content)
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
            risk_factors.append(content)
        else:
            clean = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s)
            if clean and not re.search(r"top risk|factor|confidence", clean, re.I):
                extra_lines.append(clean)

    rl_color = STATUS_META.get(risk_level, STATUS_META["Reviewed"])["color"] if risk_level else SLATE
    html = ""

    # Score + risk level row
    if score_val is not None or risk_level:
        html += '<div style="display:flex;align-items:center;gap:20px;margin-bottom:14px;flex-wrap:wrap;">'
        if score_val is not None:
            s_color = CORAL if score_val < 40 else (AMBER if score_val < 70 else TEAL)
            html += score_ring(score_val, s_color)
        if risk_level:
            rl_bg = STATUS_META.get(risk_level, STATUS_META["Reviewed"])["bg"]
            html += (
                '<div style="background:' + rl_bg + ';border:1px solid ' + rl_color + '30;'
                'border-radius:8px;padding:8px 16px;">'
                '<div style="font-size:0.72rem;font-weight:700;color:' + INK_SOFT + ';'
                'text-transform:uppercase;letter-spacing:0.05em;">Risk Level</div>'
                '<div style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
                'font-size:1.1rem;color:' + rl_color + ';margin-top:2px;">' + risk_level + '</div>'
                '</div>'
            )
        html += '</div>'

    # Risk factors
    if risk_factors:
        html += (
            '<div style="font-size:0.75rem;font-weight:700;color:' + CORAL + ';'
            'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">'
            + svg('<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>', CORAL, 12)
            + '&nbsp;Top Risk Factors</div>'
        )
        for i, factor in enumerate(risk_factors[:5]):
            html += (
                '<div style="display:flex;gap:10px;align-items:flex-start;'
                'padding:8px 12px;background:' + CORAL_BG + ';border-radius:8px;'
                'margin-bottom:7px;">'
                '<span style="background:' + CORAL + ';color:#fff;border-radius:50%;'
                'width:18px;height:18px;display:flex;align-items:center;justify-content:center;'
                'font-size:0.7rem;font-weight:700;flex-shrink:0;">' + str(i + 1) + '</span>'
                '<span style="font-size:0.88rem;color:#33414F;line-height:1.5;">' + factor + '</span>'
                '</div>'
            )

    for el in extra_lines:
        html += '<p style="font-size:0.88rem;color:#33414F;line-height:1.65;margin:6px 0;">' + el + '</p>'

    if confidence:
        html += confidence_meter(confidence)

    return html if html else md_to_html(body_md)


def render_actions(body_md: str) -> str:
    """Actions: numbered priority cards."""
    lines = body_md.split("\n")
    cards = []
    current_num   = 0
    current_title = ""
    current_what  = ""
    current_why   = ""

    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Priority N — Title:
        pm = re.match(r"priority\s*(\d)\s*[—\-:]\s*(.*)", s, re.I)
        if pm:
            if current_num and current_title:
                cards.append(action_card(current_num, current_title, current_what, current_why))
            current_num   = int(pm.group(1))
            current_title = pm.group(2).rstrip(":").strip()
            current_what  = ""
            current_why   = ""
            continue
        wm = re.match(r"what\s*[:\-]\s*(.*)", s, re.I)
        if wm:
            current_what = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", wm.group(1))
            continue
        ym = re.match(r"why\s*[:\-]\s*(.*)", s, re.I)
        if ym:
            current_why = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", ym.group(1))
            continue
        # Continuation of what/why
        if current_why:
            current_why += " " + re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s.lstrip("-* "))
        elif current_what:
            current_what += " " + re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", s.lstrip("-* "))

    if current_num and current_title:
        cards.append(action_card(current_num, current_title, current_what, current_why))

    return "".join(cards) if cards else md_to_html(body_md)


# ─────────────────────────────────────────────────────────────────────────────
# DISPATCH: route section body to the right renderer
# ─────────────────────────────────────────────────────────────────────────────
def render_section_body(cat: str, body_md: str, confidence: str = "") -> str:
    if cat == "overview":   return render_overview(body_md)
    if cat == "usage":      return render_usage(body_md)
    if cat == "support":    return render_support(body_md)
    if cat == "financial":  return render_financial(body_md)
    if cat == "risk":       return render_risk(body_md, confidence)
    if cat == "action":     return render_actions(body_md)
    return md_to_html(body_md)


# ─────────────────────────────────────────────────────────────────────────────
# UNICODE → LATIN-1 SAFE  (for fpdf2 Helvetica font)
# ─────────────────────────────────────────────────────────────────────────────
def to_latin1(text: str) -> str:
    for src, dst in {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
        "\u2192": "->", "\u2190": "<-", "\u00b7": "*",
        "\u00ae": "(R)", "\u00a9": "(C)", "\u2122": "(TM)",
    }.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="ignore").decode("latin-1")


# ─────────────────────────────────────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_pdf(account: str, status: str, score, generated_at: str, acc_id: str, explanation: str) -> bytes:
    if not _HAS_FPDF:
        return (
            f"PULSE AI -- CUSTOMER HEALTH REPORT\n{'='*50}\n\n"
            f"Account   : {account}  ({acc_id})\n"
            f"Status    : {status}\n"
            f"Score     : {score if score is not None else 'N/A'} / 100\n"
            f"Generated : {generated_at}\n\n{'--'*25}\n\n{explanation}"
        ).encode("utf-8")

    STATUS_RGB = {
        "Healthy": (31,158,142), "At Risk": (225,153,59),
        "Critical": (225,91,76), "Reviewed": (74,90,107),
    }
    r, g, b = STATUS_RGB.get(status, (74,90,107))
    s_acct  = to_latin1(account)
    s_stat  = to_latin1(status)
    s_date  = to_latin1(generated_at)
    s_expl  = to_latin1(explanation)

    class PDF(FPDF):
        def header(self):
            self.set_fill_color(15, 27, 45)
            self.rect(0, 0, 210, 18, "F")
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(255, 255, 255)
            self.set_xy(10, 4)
            self.cell(140, 10, "Pulse AI  |  Customer Health Intelligence", align="L")
            self.set_font("Helvetica", "", 9)
            self.set_xy(0, 5)
            self.cell(200, 8, s_date, align="R")
            self.ln(14)

        def footer(self):
            self.set_y(-13)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(140, 140, 140)
            self.cell(0, 10, f"Pulse AI  |  Confidential  |  Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Cover
    pdf.set_fill_color(247, 248, 250)
    pdf.rect(10, pdf.get_y(), 190, 38, "F")
    pdf.set_xy(14, pdf.get_y() + 5)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(15, 27, 45)
    pdf.cell(0, 9, s_acct, ln=True)
    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 100, 115)
    score_str = to_latin1(f"  |  Health Score: {score}/100" if score is not None else "")
    pdf.cell(0, 7, f"Status: {s_stat}{score_str}  |  {acc_id}  |  {s_date}", ln=True)
    pdf.set_fill_color(r, g, b)
    pw = 40
    pdf.set_xy(210 - 14 - pw, pdf.get_y() - 14)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pw, 8, f"  {s_stat}  ", align="C", fill=True)
    pdf.ln(18)

    ACCENT_RGB = {
        "risk": (225,91,76), "support": (225,153,59),
        "action": (31,158,142), "financial": (59,111,160),
        "usage": (31,158,142), "overview": (92,112,137),
    }
    for sec in parse_sections(s_expl):
        body = "\n".join(sec["body"]).strip()
        if not body:
            continue
        cat  = classify_section(sec["title"])
        ar, ag, ab = ACCENT_RGB.get(cat, (15, 27, 45))
        pdf.set_fill_color(ar, ag, ab)
        pdf.rect(10, pdf.get_y(), 3, 8, "F")
        pdf.set_xy(16, pdf.get_y())
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(15, 27, 45)
        pdf.cell(0, 8, to_latin1(sec["title"]), ln=True)
        pdf.ln(1)
        clean = re.sub(r"\*\*(.+?)\*\*", r"\1", body)
        clean = re.sub(r"\*(.+?)\*",     r"\1", clean)
        clean = re.sub(r"^#{1,6}\s+",    "",    clean, flags=re.M)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 79)
        pdf.set_x(14)
        pdf.multi_cell(182, 5.5, clean)
        pdf.ln(5)

    return bytes(pdf.output())


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
html, body, [class*="css"] {{
  font-family:'Inter','Segoe UI',system-ui,sans-serif,'Apple Color Emoji','Segoe UI Emoji','Noto Color Emoji';
}}
/* 'Space Grotesk' and 'Inter' Google Fonts @import removed — system fonts
   are used instead to eliminate the extra network round-trips on load. */

@keyframes pulse-dot {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.25; }} }}
.pulse-dot {{
  width:8px;height:8px;border-radius:50%;background:#3FCBB8;display:inline-block;
  animation:pulse-dot 1s ease-in-out infinite;
}}
.stApp {{ background:{PAPER}; }}

/* Streamlit adds its own ~1rem gap between stacked elements on top of each
   card's own margin-bottom, which is what produced the big empty band
   between cards. Zero that out in the main content area only (not the
   sidebar, where native widgets rely on default spacing) so card_wrap's
   margin is the single source of vertical rhythm. */
.main [data-testid="stVerticalBlock"],
[data-testid="stMain"] [data-testid="stVerticalBlock"] {{ gap:0 !important; }}

[data-testid="stSidebar"] {{ background:{INK}; }}
[data-testid="stSidebar"] * {{ color:#E7ECF1 !important; }}
[data-testid="stSidebar"] hr {{ border-color:#223245; }}
[data-testid="stSidebar"] .stSelectbox label {{ font-size:0.85rem;font-weight:500;color:#A9BACB !important; }}

/* Selected-value + placeholder text in the account dropdown was rendering in a
   low-contrast BaseWeb default color. Force a light, legible color on the
   closed control, the open menu, and the search input. */
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  background:#16283C !important;border:1px solid #2A415C !important;border-radius:8px !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] div,
[data-testid="stSidebar"] [data-baseweb="select"] span {{
  color:#F2F5F8 !important;font-weight:500 !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] input {{ color:#F2F5F8 !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] svg {{ fill:#8DA0B4 !important; }}
[data-testid="stSidebar"] [data-baseweb="popover"] li[role="option"] {{ color:{INK} !important; }}

/* Buttons — one consistent shape/radius/padding scale across the whole app;
   primary (filled) vs secondary (outline) is a color distinction only. */
div.stButton > button, div.stDownloadButton > button {{
  width:100%;background:{INK};color:#FFF;border:1px solid {LINE};
  font-weight:600;font-size:0.9rem;padding:0.55rem 1rem;border-radius:8px;
  transition:all .18s ease;cursor:pointer;font-family:inherit; }}
div.stButton > button:hover, div.stDownloadButton > button:hover {{
  background:{TEAL};color:#FFF;border-color:{TEAL}; }}
div.stButton > button:disabled {{
  background:#C7CFD8;border-color:#C7CFD8;color:#FFF;cursor:not-allowed; }}

div[class*="st-key-refresh_portfolio_btn"] button {{
  width:auto !important;background:{CARD} !important;color:{INK_SOFT} !important;
  border:1px solid {LINE} !important;font-weight:600;font-size:0.85rem;
  padding:0.4rem 0.85rem;border-radius:8px;white-space:nowrap; }}
div[class*="st-key-refresh_portfolio_btn"] button:hover {{
  background:{GREEN_BG} !important;color:{TEAL} !important;border-color:{TEAL} !important; }}
div[class*="st-key-refresh_portfolio_btn"] {{
  display:flex !important;justify-content:flex-end; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE  (must run before SIDEBAR so live status colors are ready on first paint)
# ─────────────────────────────────────────────────────────────────────────────
if "report_cache" not in st.session_state:
    st.session_state.report_cache = {}

if "portfolio_cache" not in st.session_state:
    st.session_state.portfolio_cache = None

if "portfolio_error" not in st.session_state:
    st.session_state.portfolio_error = None

if "portfolio_loaded_at" not in st.session_state:
    st.session_state.portfolio_loaded_at = None

# Tracks an account name while its report is being fetched. Set on the rerun
# triggered by the button click, then acted on the NEXT rerun (see comment
# by the st.rerun() call below for why this is split across two reruns).
if "pending_generate" not in st.session_state:
    st.session_state.pending_generate = None


def parse_portfolio_table(text: str):
    lines = [ln for ln in (text or "").strip().split("\n") if ln.strip()]
    rows = []
    for line in lines[1:]:  # skip header row
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        acc_id, name, score_str, status = parts[0], parts[1], parts[2], parts[3]
        try:
            score = int(float(score_str))
        except ValueError:
            score = None
        rows.append({"account_id": acc_id, "account_name": name, "score": score, "status": status})
    counts = {"Healthy": 0, "At Risk": 0, "Critical": 0}
    for r in rows:
        if r["status"] in counts:
            counts[r["status"]] += 1
    return {"counts": counts, "top5": rows[:5], "all": rows}  # already sorted ascending by the aggregator


def fetch_portfolio():
    try:
        pf_response = requests.post(
            LANGFLOW_PORTFOLIO_URL,
            json={"input_value": "portfolio", "input_type": "chat", "session_id": "portfolio"},
            headers={"Content-Type": "application/json", "x-api-key": LANGFLOW_API_KEY},
            timeout=120,
        )
        pf_response.raise_for_status()
        pf_result = pf_response.json()
        pf_outputs = pf_result["outputs"][0]["outputs"]

        narrative_text, table_text = None, None
        for out in pf_outputs:
            msg = out["results"]["message"]
            text = msg["text"]
            source_name = msg.get("properties", {}).get("source", {}).get("display_name", "")
            if source_name == "Portfolio Aggregator":
                table_text = text
            else:
                narrative_text = text

        chart_json = parse_portfolio_table(table_text)
        st.session_state.portfolio_cache = {"chart": chart_json, "narrative": narrative_text}
        st.session_state.portfolio_error = None
        st.session_state.portfolio_loaded_at = datetime.now().strftime("%I:%M %p")
    except Exception as e:
        st.session_state.portfolio_error = str(e)


# Auto-load on first launch — runs once per session, since portfolio_cache
# stays populated (or portfolio_error stays set) on every subsequent rerun.
if st.session_state.portfolio_cache is None and st.session_state.portfolio_error is None:
    with st.spinner("Loading portfolio overview…"):
        fetch_portfolio()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    pulse_icon = svg('<path d="M3 12h4l2-8 4 16 2-8h6"/>', "#FFF", 20)
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">'
        '<div style="width:36px;height:36px;border-radius:10px;'
        'background:linear-gradient(135deg,' + TEAL + ',#14776b);'
        'display:flex;align-items:center;justify-content:center;flex-shrink:0;">'
        + pulse_icon + '</div>'
        '<div>'
        '<div style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;font-size:1.1rem;color:#FFF !important;">Pulse AI</div>'
        '<div style="font-size:0.8rem;color:#93A8BD !important;">Customer Health Intelligence</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr/>", unsafe_allow_html=True)

    account  = st.selectbox(
        "Select account", ACCOUNTS, index=None, placeholder="Select account",
    )
    acc_id   = ACCOUNT_ID_MAP.get(account, "") if account else ""

    # Live status badge for the selected account, colored from the same
    # STATUS_META palette used everywhere else on the page.
    pf_lookup = {}
    if st.session_state.portfolio_cache:
        for r in st.session_state.portfolio_cache["chart"].get("all", []):
            pf_lookup[r["account_name"]] = r

    live = pf_lookup.get(account)
    if live:
        sm = STATUS_META.get(live["status"], STATUS_META["Reviewed"])
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:space-between;'
            'background:' + sm["color"] + '1A;border:1px solid ' + sm["color"] + '55;'
            'border-radius:8px;padding:8px 12px;margin-bottom:12px;">'
            '<span style="font-size:0.8rem;color:#C5D5E4 !important;">Current status</span>'
            '<span style="display:inline-flex;align-items:center;gap:5px;font-weight:700;'
            'font-size:0.78rem;color:' + sm["color"] + ' !important;">'
            + sm["icon"] + '&nbsp;' + sm["label"] + '</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    is_pending = st.session_state.pending_generate is not None
    generate = st.button(
        "\u26a1 Generate Health Report",
        use_container_width=True,
        disabled=(account is None) or is_pending,
    )

    if generate and account:
        # Don't call the (slow) API in this same rerun — a synchronous
        # network call blocks before the browser gets a chance to paint
        # the "generating" state, which is why the click used to look
        # like nothing happened. Set a flag and rerun immediately instead;
        # the actual request happens on the next rerun, once this one has
        # already rendered and the spinner below is on screen.
        st.session_state.pending_generate = account
        st.toast(f"Generating report for {account}…", icon="⚡")
        st.rerun()

    if is_pending:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:8px;font-size:0.82rem;'
            'color:#7FD9CC !important;margin-top:8px;">'
            '<span class="pulse-dot"></span>Generating report for '
            '<b>' + st.session_state.pending_generate + '</b>…</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size:0.82rem;color:#A9BACB !important;line-height:1.6;'
        'background:#16283C;border:1px solid #223A52;border-radius:10px;'
        'padding:11px 13px;margin-top:12px;">'
        'Retrieves all signals from your RAG knowledge base — usage, tickets, '
        'CRM notes, and contract data — then generates an executive health report.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<hr/>", unsafe_allow_html=True)

    # Live portfolio snapshot — replaces the old static "richest demo accounts"
    # list, which could drift out of sync with actual data. Colors are pulled
    # directly from STATUS_META so they always match the rest of the page.
    st.markdown(
        '<div style="font-size:0.76rem;font-weight:700;color:#A9BACB !important;'
        'text-transform:uppercase;letter-spacing:0.04em;margin-bottom:8px;">Portfolio snapshot</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.portfolio_cache:
        counts = st.session_state.portfolio_cache["chart"].get("counts", {})
        for label in ["Healthy", "At Risk", "Critical"]:
            sm = STATUS_META[label]
            st.markdown(
                '<div style="display:flex;align-items:center;justify-content:space-between;'
                'padding:4px 0;font-size:0.82rem;">'
                '<span style="display:flex;align-items:center;gap:7px;color:#C5D5E4 !important;">'
                '<span style="width:9px;height:9px;border-radius:3px;background:' + sm["color"] + ';display:inline-block;"></span>'
                + label + '</span>'
                '<span style="font-weight:700;color:#FFF !important;">' + str(counts.get(label, 0)) + '</span>'
                '</div>',
                unsafe_allow_html=True,
            )
    elif st.session_state.portfolio_error:
        st.markdown(
            '<div style="font-size:0.78rem;color:' + CORAL + ' !important;">Snapshot unavailable</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:0.78rem;color:#57718A !important;">Loading…</div>',
            unsafe_allow_html=True,
        )



# HEADER BANNER
# ─────────────────────────────────────────────────────────────────────────────
pulse_line = (
    '<svg width="100%" height="30" viewBox="0 0 600 30" preserveAspectRatio="none"'
    ' style="display:block;margin-top:14px;opacity:0.85;">'
    '<polyline points="0,15 140,15 165,4 185,26 205,15 320,15 345,2 365,28 385,15 600,15"'
    ' fill="none" stroke="#3FCBB8" stroke-width="2.2" stroke-linecap="round"/>'
    '</svg>'
)
c1 = svg('<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z"/><path d="M12 6v6l4 2"/>', "#7FD9CC", 13)
c2 = svg('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>', "#7FD9CC", 13)
c3 = svg('<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>', "#7FD9CC", 13)

def chip(icon_html, text):
    return (
        '<div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.13);'
        'border-radius:8px;padding:5px 12px;font-size:0.8rem;color:#C5D5E4;'
        'display:inline-flex;align-items:center;gap:5px;">'
        + icon_html + '&nbsp;' + text + '</div>'
    )

def chip_status(icon_html, text, color):
    return (
        '<div style="background:' + color + '26;border:1px solid ' + color + '66;'
        'border-radius:8px;padding:5px 12px;font-size:0.8rem;font-weight:700;color:' + color + ';'
        'display:inline-flex;align-items:center;gap:5px;">'
        + icon_html + '&nbsp;' + text + '</div>'
    )

attention_chip = ""
if st.session_state.portfolio_cache:
    counts = st.session_state.portfolio_cache["chart"].get("counts", {})
    needs_attention = counts.get("At Risk", 0) + counts.get("Critical", 0)
    if needs_attention > 0:
        alert_icon = svg('<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>', CORAL, 13)
        attention_chip = chip_status(alert_icon, str(needs_attention) + " accounts need attention", CORAL)

st.markdown(
    '<div style="background:linear-gradient(135deg,' + INK + ' 0%,#17324A 55%,#1D5A52 130%);'
    'border-radius:18px;padding:30px 36px 20px;margin-bottom:22px;overflow:hidden;">'
    '<div style="font-size:0.83rem;font-weight:500;color:#7FD9CC;margin-bottom:8px;">Executive Insights Panel</div>'
    '<p style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;font-size:1.9rem;'
    'color:#FFF;letter-spacing:-0.01em;margin:0;">Account Health Intelligence Dashboard</p>'
    '<p style="color:#A9BECF;font-size:0.94rem;margin-top:6px;max-width:520px;">'
    'Real-time telemetry from usage patterns, support burden, and contract milestones '
    '— synthesised by RAG into a clear executive narrative.</p>'
    '<div style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap;">'
    + chip(c1, "Live telemetry")
    + chip(c2, str(len(ACCOUNTS)) + " accounts tracked")
    + chip(c3, "RAG-powered risk signals")
    + attention_chip
    + '</div>'
    + pulse_line + '</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO OVERVIEW
# Collapsed automatically once an individual account's report is on screen,
# so the report is the focus and the portfolio-wide view doesn't compete for
# space — still one click away via the expander if the user wants it back.
# ─────────────────────────────────────────────────────────────────────────────
has_active_report = bool(account) and bool(st.session_state.report_cache.get(account))

with st.expander("📊 Portfolio Overview", expanded=not has_active_report):
    head_col, btn_col = st.columns([6, 1])
    with head_col:
        subtitle = (
            "Last updated " + st.session_state.portfolio_loaded_at
            if st.session_state.portfolio_loaded_at else "Live scoring across all tracked accounts"
        )
        st.markdown(
            '<p style="color:#7C8DA0;font-size:0.82rem;margin:0 0 14px;">' + subtitle + '</p>',
            unsafe_allow_html=True,
        )
    with btn_col:
        if st.button("&#8635; Refresh", key="refresh_portfolio_btn"):
            with st.spinner("Refreshing portfolio…"):
                fetch_portfolio()
            st.rerun()

    if st.session_state.portfolio_error:
        st.markdown(
            '<div style="background:' + CORAL_BG + ';border:1px solid ' + CORAL + '40;border-radius:10px;'
            'padding:12px 16px;margin-bottom:18px;color:' + CORAL + ';font-size:0.86rem;">'
            '<b>Portfolio data unavailable.</b>&nbsp; ' + st.session_state.portfolio_error
            + '</div>',
            unsafe_allow_html=True,
        )

    if st.session_state.portfolio_cache:
        pf_chart = st.session_state.portfolio_cache["chart"]
        pf_narrative = st.session_state.portfolio_cache["narrative"]
        counts = pf_chart.get("counts", {})
        top5 = pf_chart.get("top5", [])

        def donut_chart(counts: dict) -> str:
            total = sum(counts.values()) or 1
            order = [("Healthy", TEAL), ("At Risk", AMBER), ("Critical", CORAL)]
            r, cx, cy, sw, size = 84, 100, 100, 30, 200
            circ = 2 * 3.14159 * r
            offset = 0
            segments = ""
            for label, color in order:
                frac = counts.get(label, 0) / total
                seg_len = circ * frac
                segments += (
                    '<circle cx="' + str(cx) + '" cy="' + str(cy) + '" r="' + str(r) + '" '
                    'stroke="' + color + '" stroke-width="' + str(sw) + '" fill="none" '
                    'stroke-dasharray="' + f'{seg_len:.1f} {circ - seg_len:.1f}' + '" '
                    'stroke-dashoffset="' + f'{-offset:.1f}' + '" '
                    'transform="rotate(-90 ' + str(cx) + ' ' + str(cy) + ')"/>'
                )
                offset += seg_len
            legend = ""
            for label, color in order:
                legend += (
                    '<div style="display:flex;align-items:center;gap:8px;padding:9px 0;'
                    'border-bottom:1px solid ' + LINE + ';">'
                    '<div style="width:11px;height:11px;border-radius:3px;background:' + color + ';flex-shrink:0;"></div>'
                    '<span style="font-size:0.9rem;color:' + INK + ';font-weight:500;">' + label + '</span>'
                    '<span style="font-size:0.95rem;color:' + INK_SOFT + ';margin-left:auto;font-weight:700;">'
                    + str(counts.get(label, 0)) + '</span></div>'
                )
            return (
                '<div style="display:flex;align-items:center;gap:32px;flex-wrap:wrap;justify-content:center;">'
                '<div style="position:relative;width:' + str(size) + 'px;height:' + str(size) + 'px;flex-shrink:0;">'
                '<svg width="' + str(size) + '" height="' + str(size) + '" viewBox="0 0 ' + str(size) + ' ' + str(size) + '">'
                + segments + '</svg>'
                '<div style="position:absolute;inset:0;display:flex;flex-direction:column;'
                'align-items:center;justify-content:center;">'
                '<span style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
                'font-size:2.1rem;color:' + INK + ';line-height:1;">' + str(total) + '</span>'
                '<span style="font-size:0.72rem;color:' + INK_SOFT + ';font-weight:500;'
                'text-transform:uppercase;letter-spacing:0.04em;margin-top:2px;">Accounts</span>'
                '</div></div>'
                '<div style="flex:1;min-width:170px;">' + legend + '</div></div>'
            )

        def attention_row(rank: int, name: str, score, status: str) -> str:
            sm = STATUS_META.get(status, STATUS_META["Reviewed"])
            return (
                '<div style="display:flex;align-items:center;gap:12px;padding:10px 0;'
                'border-bottom:1px solid ' + LINE + ';">'
                '<span style="font-weight:700;color:' + INK_SOFT + ';width:20px;">' + str(rank) + '</span>'
                + avatar(name) +
                '<span style="flex:1;font-weight:600;color:' + INK + ';">' + name + '</span>'
                '<span style="display:inline-flex;align-items:center;gap:5px;background:' + sm["color"] + ';'
                'color:#FFF;font-weight:700;font-size:0.78rem;padding:4px 12px;border-radius:999px;">'
                + sm["label"] + '</span></div>'
            )

        col_a, col_b = st.columns([1, 1.3])
        with col_a:
            st.markdown(card_wrap(
                section_header(SECTION_META["portfolio_health"], "Portfolio Health")
                + donut_chart(counts), INK_SOFT
            ), unsafe_allow_html=True)
        with col_b:
            rows = "".join(attention_row(i + 1, r["account_name"], r["score"], r["status"]) for i, r in enumerate(top5))
            st.markdown(card_wrap(
                section_header(SECTION_META["attention"], "Top 5 Accounts Needing Attention")
                + rows, CORAL
            ), unsafe_allow_html=True)

        narrative_html = md_lib.markdown(pf_narrative) if _HAS_MD else '<p>' + pf_narrative.replace(chr(10), '<br/>') + '</p>'
        st.markdown(card_wrap(
            section_header(SECTION_META["insights"], "Portfolio Insights")
            + '<div style="font-size:0.91rem;color:#33414F;line-height:1.65;">' + narrative_html + '</div>',
            TEAL
        ), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GENERATE REPORT
# Query is just the account_id — maximum retrieval precision.
# See langflow_setup_guide.md for how to configure the vector store.
# ─────────────────────────────────────────────────────────────────────────────
pending_account = st.session_state.pending_generate
if pending_account:
    pending_acc_id = ACCOUNT_ID_MAP.get(pending_account, "")
    with st.status(
        f"Retrieving signals for {pending_account} ({pending_acc_id})…",
        expanded=True,
    ) as status_box:
        st.write("Querying the RAG knowledge base — usage, tickets, CRM notes, contract data…")
        try:
            response = requests.post(
                LANGFLOW_URL,
                json={
                    "input_value": pending_acc_id,
                    "input_type": "chat",
                    "session_id": pending_acc_id,
                },
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": LANGFLOW_API_KEY,
                },
                timeout=90,
            )
        except Exception as e:
            status_box.update(label="Unable to reach Langflow.", state="error")
            st.session_state.pending_generate = None
            st.error(f"**Unable to reach Langflow.**\n\n`{e}`")
            st.stop()

        if response.status_code != 200:
            status_box.update(label="Langflow returned an error.", state="error")
            st.session_state.pending_generate = None
            st.error(f"Langflow returned HTTP {response.status_code}:\n```\n{response.text[:400]}\n```")
            st.stop()

        try:
            result = response.json()
        except Exception:
            status_box.update(label="Langflow response was not valid JSON.", state="error")
            st.session_state.pending_generate = None
            st.error("Langflow response was not valid JSON.")
            st.stop()

        try:
            explanation = result["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        except Exception:
            status_box.update(label="Unexpected Langflow response structure.", state="error")
            st.session_state.pending_generate = None
            st.warning("Unexpected Langflow response structure.")
            st.json(result)
            st.stop()

        st.session_state.report_cache[pending_account] = {
            "explanation":  explanation,
            "generated_at": datetime.now().strftime("%b %d, %Y · %I:%M %p"),
            "acc_id":       pending_acc_id,
        }
        status_box.update(label=f"Report ready for {pending_account}.", state="complete")

    # Clear the flag now that the request has resolved (success or handled
    # failure) so this block doesn't re-run on every later rerun, and so the
    # sidebar's "Generating…" note and disabled button turn back off.
    st.session_state.pending_generate = None
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# RENDER REPORT
# ─────────────────────────────────────────────────────────────────────────────
cached = st.session_state.report_cache.get(account)

if cached:
    explanation  = cached["explanation"]
    generated_at = cached["generated_at"]
    status       = detect_status(explanation)
    sm           = STATUS_META[status]
    score        = extract_score(explanation)
    confidence   = extract_confidence(explanation)

    # ── Identity top-bar ────────────────────────────────────────────────────
    av = avatar(account)
    ring = score_ring(score, sm["color"]) if score is not None else ""
    ring_block = (
        '<div style="display:flex;align-items:center;gap:12px;">'
        + ring +
        '<div style="font-size:0.72rem;color:' + INK_SOFT + ';font-weight:500;'
        'text-transform:uppercase;letter-spacing:0.04em;line-height:1.5;">'
        'Health<br/>Score</div></div>'
    ) if score is not None else ""

    status_block = (
        '<div style="text-align:right;">'
        '<span style="display:inline-flex;align-items:center;gap:7px;'
        'background:' + sm["color"] + ';color:#FFF;font-weight:700;font-size:0.85rem;'
        'padding:8px 18px;border-radius:999px;">'
        + sm["icon"] + '&nbsp;' + sm["label"] + '</span>'
        '<div style="font-size:0.8rem;color:' + INK_SOFT + ';margin-top:6px;max-width:240px;">'
        + {
            "Healthy": "Stable, well-adopted account.",
            "At Risk": "Proactive attention warranted this cycle.",
            "Critical": "Urgent CSM intervention required.",
            "Reviewed": "No explicit risk signal detected.",
        }[status] + '</div></div>'
    )

    st.markdown(
        '<div style="background:' + CARD + ';border:1px solid ' + LINE + ';border-radius:14px;'
        'padding:18px 22px;margin-bottom:18px;display:flex;align-items:center;'
        'justify-content:space-between;flex-wrap:wrap;gap:12px;">'
        '<div style="display:flex;align-items:center;gap:14px;">'
        + av +
        '<div>'
        '<p style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;'
        'font-size:1.2rem;color:' + INK + ';margin:0;">' + account + '</p>'
        '<div style="font-size:0.81rem;color:#8A96A3;margin-top:2px;">'
        + cached["acc_id"] + '&nbsp;&nbsp;&middot;&nbsp;&nbsp;Generated ' + generated_at
        + '</div></div></div>'
        + ring_block
        + status_block
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Section cards ────────────────────────────────────────────────────────
    for sec in parse_sections(explanation):
        body_md = "\n".join(sec["body"]).strip()
        if not body_md:
            continue
        cat  = classify_section(sec["title"])
        meta = SECTION_META[cat]
        title = "Account Summary" if cat == "overview" else sec["title"]
        head = section_header(meta, title)
        body = render_section_body(cat, body_md, confidence)
        st.markdown(
            card_wrap(head + body, meta["color"]),
            unsafe_allow_html=True,
        )

    # ── Export row ───────────────────────────────────────────────────────────
    # NOTE: this used to be `margin:18px 0 8px` on the <p>. The block-gap:0
    # rule above (added to remove the big gaps between cards) was also
    # stripping the space Streamlit normally puts between this label and the
    # button row beneath it, so the two ended up almost touching. Padding on
    # the element's own box isn't affected by that rule, so it can't collapse
    # away the same way.
    st.markdown(
        '<div style="font-size:0.82rem;color:#7C8DA0;padding:22px 0 18px;">Export or share this report:</div>',
        unsafe_allow_html=True,
    )
    col_pdf, col_email, _ = st.columns([1.3, 1.3, 3.4])

    with col_pdf:
        pdf_bytes = generate_pdf(account, status, score, generated_at, cached["acc_id"], explanation)
        st.download_button(
            label="&#128229; Download PDF",
            data=pdf_bytes,
            file_name=account.replace(" ", "_") + "_health_report." + ("pdf" if _HAS_FPDF else "txt"),
            mime="application/pdf" if _HAS_FPDF else "text/plain",
            use_container_width=True,
        )

    with col_email:
        subj  = f"Pulse AI Health Alert: {account} ({status})"
        score_ln = f"Health Score  : {score}/100\n" if score is not None else ""
        body_txt = (
            f"Hi Team,\n\nPulse AI health assessment for {account} ({cached['acc_id']}).\n\n"
            f"Status        : {status}\n{score_ln}"
            f"Generated     : {generated_at}\n\n"
            f"-- Summary --\n{explanation[:1400]}"
            f"{'...' if len(explanation) > 1400 else ''}\n\n"
            f"Full report in Pulse AI dashboard.\n\nBest,\nPulse AI"
        )
        mailto = "mailto:?subject=" + urllib.parse.quote(subj) + "&body=" + urllib.parse.quote(body_txt)
        st.markdown(
            '<a href="' + mailto + '" target="_blank" style="text-decoration:none;display:block;">'
            '<button style="width:100%;background:' + INK + ';color:#FFF;'
            'border:1px solid ' + LINE + ';font-weight:600;padding:0.55rem 1rem;'
            'border-radius:8px;cursor:pointer;font-size:0.9rem;font-family:inherit;">'
            '&#128228;&nbsp; Share via Email</button></a>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size:0.76rem;color:#A0AABB;text-align:center;'
        'border-top:1px solid ' + LINE + ';padding-top:14px;margin-top:24px;">'
        'Pulse AI &nbsp;&middot;&nbsp; Automated telemetry assessment &nbsp;&middot;&nbsp; '
        + generated_at + '</div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE / GENERATING STATE
# ─────────────────────────────────────────────────────────────────────────────
else:
    if st.session_state.pending_generate:
        # ── Active generation in progress ────────────────────────────────────
        gen_acct = st.session_state.pending_generate
        spinner_anim = (
            '<style>'
            '@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}'
            '@keyframes fade-pulse{0%,100%{opacity:.4}50%{opacity:1}}'
            '.gen-ring{'
            'width:52px;height:52px;border-radius:50%;'
            'border:4px solid ' + LINE + ';'
            'border-top-color:' + TEAL + ';'
            'animation:spin 0.9s linear infinite;'
            'margin:0 auto 18px;}'
            '.gen-dot{'
            'display:inline-block;width:6px;height:6px;border-radius:50%;'
            'background:' + TEAL + ';margin:0 3px;'
            'animation:fade-pulse 1.2s ease-in-out infinite;}'
            '.gen-dot:nth-child(2){animation-delay:.2s}'
            '.gen-dot:nth-child(3){animation-delay:.4s}'
            '</style>'
        )
        st.markdown(
            spinner_anim +
            '<div style="background:' + CARD + ';border:1px solid ' + LINE + ';border-radius:14px;'
            'padding:60px 32px;text-align:center;">'
            '<div class="gen-ring"></div>'
            '<p style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:700;font-size:1.15rem;'
            'color:' + INK + ';margin:0 0 6px;">Generating health report&hellip;</p>'
            '<p style="color:#7C8DA0;font-size:0.88rem;margin:0 0 16px;">'
            'Querying RAG knowledge base for&nbsp;<b style="color:' + INK + ';">' + gen_acct + '</b>'
            '&nbsp;&mdash; usage, tickets, CRM notes, contract data.'
            '</p>'
            '<div style="display:flex;justify-content:center;align-items:center;gap:2px;margin-bottom:20px;">'
            '<span class="gen-dot"></span><span class="gen-dot"></span><span class="gen-dot"></span>'
            '</div>'
            '<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">'
            '<div style="background:' + PAPER + ';border:1px solid ' + LINE + ';border-radius:8px;'
            'padding:8px 16px;font-size:0.8rem;color:' + INK_SOFT + ';">'
            + svg('<path d="M4 20V10M10 20V4M16 20v-7M22 20v-4"/>', TEAL, 13) +
            '&nbsp;Retrieving usage signals</div>'
            '<div style="background:' + PAPER + ';border:1px solid ' + LINE + ';border-radius:8px;'
            'padding:8px 16px;font-size:0.8rem;color:' + INK_SOFT + ';">'
            + svg('<path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.8 19.8 0 0 1 3.08 5.18 2 2 0 0 1 5.07 3h3a2 2 0 0 1 2 1.72c.13 1 .36 1.96.7 2.88a2 2 0 0 1-.45 2.11L9.08 11a16 16 0 0 0 5.92 5.92l1.3-1.3a2 2 0 0 1 2.11-.45c.92.34 1.88.57 2.88.7A2 2 0 0 1 22 16.92z"/>', AMBER, 13) +
            '&nbsp;Analysing support tickets</div>'
            '<div style="background:' + PAPER + ';border:1px solid ' + LINE + ';border-radius:8px;'
            'padding:8px 16px;font-size:0.8rem;color:' + INK_SOFT + ';">'
            + svg('<circle cx="12" cy="12" r="8"/><path d="M12 7v10M9.5 9.5h3.2a1.8 1.8 0 1 1 0 3.6H9.8a1.8 1.8 0 1 0 0 3.6h3.4"/>', BLUE, 13) +
            '&nbsp;Reviewing commercial data</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        # ── Nothing selected yet ──────────────────────────────────────────────
        empty_icon = svg('<path d="M3 12h4l2-8 4 16 2-8h6"/>', TEAL, 38)
        st.markdown(
            '<div style="background:' + CARD + ';border:1px dashed ' + LINE + ';border-radius:14px;'
            'padding:56px 32px;text-align:center;">'
            + empty_icon +
            '<p style="font-family:system-ui,\'Segoe UI\',sans-serif;font-weight:600;font-size:1.1rem;'
            'color:' + INK + ';margin-top:14px;">No report generated yet</p>'
            '<p style="color:#7C8DA0;font-size:0.88rem;max-width:400px;margin:6px auto 0;">'
            'Select an account from the sidebar and click <b>Generate Health Report</b> '
            'to retrieve live signals and build an executive health narrative.'
            '</p></div>',
            unsafe_allow_html=True,
        )