import streamlit as st

# ── Renk Paleti ──────────────────────────────────────────────────────────────
C_PRIMARY    = "#0F172A"
C_ACCENT     = "#3B82F6"
C_CYAN       = "#06B6D4"
C_SUCCESS    = "#10B981"
C_DANGER     = "#EF4444"
C_WARNING    = "#F59E0B"
C_BG         = "#F8FAFC"
C_CARD       = "#FFFFFF"
C_BORDER     = "#E2E8F0"
C_TEXT_1     = "#0F172A"
C_TEXT_2     = "#475569"
C_TEXT_3     = "#94A3B8"

FONT_SANS  = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO  = "'JetBrains Mono', 'Courier New', monospace"

_GLOBAL_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Temel Reset ──────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ── Ana İçerik Alanı ─────────────────────────────────────────────────────── */
.main .block-container {
    padding: 2rem 2.5rem 4rem 2.5rem !important;
    max-width: 1280px !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #F1F5F9 !important;
}
[data-testid="stSidebar"] label {
    color: #94A3B8 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stTextArea textarea,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
}
[data-testid="stSidebar"] .stTextInput input:focus,
[data-testid="stSidebar"] .stTextArea textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}
[data-testid="stSidebar"] .stDateInput input {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
}

/* Sidebar logo/başlık bölgesi */
[data-testid="stSidebarContent"] > div:first-child {
    padding-top: 1.5rem;
}

/* ── Butonlar ─────────────────────────────────────────────────────────────── */
.stButton > button {
    background-color: #3B82F6 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.4rem !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    letter-spacing: 0.01em !important;
    transition: background-color 0.15s ease, transform 0.1s ease !important;
    width: 100%;
}
.stButton > button:hover {
    background-color: #2563EB !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Başlıklar ────────────────────────────────────────────────────────────── */
h1 { font-size: 1.875rem !important; font-weight: 700 !important; color: #0F172A !important; letter-spacing: -0.02em !important; }
h2 { font-size: 1.375rem !important; font-weight: 600 !important; color: #0F172A !important; letter-spacing: -0.01em !important; }
h3 { font-size: 1.125rem !important; font-weight: 600 !important; color: #0F172A !important; }

/* ── Metrik Kartları (st.metric) ──────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem 1.5rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: #64748B !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: #0F172A !important;
}

/* ── Divider ──────────────────────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #E2E8F0 !important;
    margin: 1.5rem 0 !important;
}

/* ── Tablolar ─────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    overflow: hidden;
    border: 1px solid #E2E8F0 !important;
}

/* ── Spinner / Progress ───────────────────────────────────────────────────── */
[data-testid="stSpinner"] {
    color: #3B82F6 !important;
}

/* ── Navigasyon (st.navigation / sidebar nav) ─────────────────────────────── */
[data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    margin: 2px 8px !important;
    color: #94A3B8 !important;
    font-weight: 500 !important;
}
[data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebarNavLink"][aria-selected="true"] {
    background-color: rgba(59,130,246,0.12) !important;
    color: #3B82F6 !important;
}

/* ── Genel input focus ────────────────────────────────────────────────────── */
input:focus, textarea:focus, select:focus {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.2) !important;
}

/* ── Toast / Alert ────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
    font-size: 0.875rem !important;
}

/* ── Mono sayılar için yardımcı sınıf ────────────────────────────────────── */
.mono {
    font-family: 'JetBrains Mono', monospace !important;
}
</style>
"""


def inject_global_css() -> None:
    """Her sayfanın en üstünde bir kez çağır."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def metric_card(label: str, value: str, color: str = C_ACCENT, sublabel: str = "") -> str:
    """Özel HTML metrik kartı döndürür — st.markdown ile kullan."""
    sub_html = f'<p style="margin:0;font-size:0.75rem;color:{C_TEXT_3};margin-top:4px">{sublabel}</p>' if sublabel else ""
    return f"""
    <div style="
        background:{C_CARD};
        border:1px solid {C_BORDER};
        border-radius:12px;
        padding:1.25rem 1.5rem;
        box-shadow:0 1px 3px rgba(0,0,0,0.04);
    ">
        <p style="margin:0;font-size:0.7rem;font-weight:600;letter-spacing:0.06em;
                  text-transform:uppercase;color:{C_TEXT_2};">{label}</p>
        <p style="margin:0;margin-top:6px;font-family:'JetBrains Mono',monospace;
                  font-size:2.25rem;font-weight:600;color:{color};line-height:1.1;">{value}</p>
        {sub_html}
    </div>
    """


def section_header(title: str, subtitle: str = "") -> None:
    """Bölüm başlığı (h2 + açıklama satırı)."""
    sub_html = f'<p style="margin:4px 0 0 0;color:{C_TEXT_2};font-size:0.875rem;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""<div style="margin-bottom:1.25rem">
            <h2 style="margin:0;font-size:1.25rem;font-weight:700;color:{C_PRIMARY};">{title}</h2>
            {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = C_ACCENT) -> str:
    """Küçük renkli etiket — st.markdown ile satır içi kullan."""
    bg = color + "18"
    return (
        f'<span style="background:{bg};color:{color};border:1px solid {color}33;'
        f'border-radius:6px;padding:2px 8px;font-size:0.72rem;font-weight:600;'
        f'letter-spacing:0.04em;font-family:\'Plus Jakarta Sans\',sans-serif;">{text}</span>'
    )


def score_color(score: float) -> str:
    """Skora göre renk döndürür."""
    if score >= 75:
        return C_SUCCESS
    if score >= 50:
        return C_WARNING
    return C_DANGER


def sidebar_logo() -> None:
    """Sidebar üstüne SprintBoard logosu/başlığı yazar."""
    st.markdown(
        f"""
        <div style="padding:0 1rem 1.5rem 1rem;border-bottom:1px solid #1E293B;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;gap:10px;">
                <div style="width:32px;height:32px;background:linear-gradient(135deg,#3B82F6,#06B6D4);
                            border-radius:8px;display:flex;align-items:center;justify-content:center;">
                    <span style="color:white;font-size:16px;font-weight:800;line-height:1;">S</span>
                </div>
                <div>
                    <p style="margin:0;font-size:1rem;font-weight:700;color:#F1F5F9;line-height:1.2;">SprintBoard</p>
                    <p style="margin:0;font-size:0.68rem;color:#64748B;font-weight:500;letter-spacing:0.06em;text-transform:uppercase;">AI Sprint Analyzer</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
