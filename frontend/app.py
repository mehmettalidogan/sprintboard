import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from datetime import date, timedelta

from components.styles import (
    inject_global_css,
    sidebar_logo,
    section_header,
    metric_card,
    badge,
    score_color,
    C_SUCCESS, C_DANGER, C_WARNING, C_ACCENT, C_TEXT_2, C_BORDER,
    FONT_MONO,
)
from components.charts import score_gauge, workload_pie, member_bar, active_days_bar
from utils.api_client import analyze_sprint, health_check

# ── Sayfa Konfigürasyonu ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="SprintBoard — Sprint Analizi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

# ── Session State ──────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Giriş Formu
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    sidebar_logo()

    st.markdown(
        f'<p style="font-size:0.7rem;font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:#475569;margin-bottom:1rem;">Sprint Parametreleri</p>',
        unsafe_allow_html=True,
    )

    github_url = st.text_input(
        "GitHub Repo URL",
        placeholder="https://github.com/org/repo",
        help="Analiz edilecek GitHub deposunun tam URL'si",
    )

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input(
            "Başlangıç",
            value=date.today() - timedelta(days=14),
            format="DD.MM.YYYY",
        )
    with col_d2:
        end_date = st.date_input(
            "Bitiş",
            value=date.today(),
            format="DD.MM.YYYY",
        )

    members_raw = st.text_area(
        "Takım Üyeleri",
        placeholder="alice\nbob\ncharlie",
        help="Her satıra bir GitHub kullanıcı adı",
        height=110,
    )

    country_code = st.selectbox(
        "Ülke (Tatil Takvimi)",
        options=["TR", "US", "DE", "GB", "FR", "NL", "PL"],
        index=0,
        help="Resmi tatilleri hesaba katmak için ülke seç",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    run_btn = st.button("Analizi Başlat", use_container_width=True)

    # Backend durum göstergesi
    st.markdown("<br>", unsafe_allow_html=True)
    _alive = health_check()
    _dot   = "🟢" if _alive else "🔴"
    _label = "Backend bağlı" if _alive else "Backend kapalı"
    st.markdown(
        f'<p style="font-size:0.75rem;color:#475569;text-align:center;">'
        f'{_dot} {_label}</p>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# ANALİZ — Tetikleyici
# ══════════════════════════════════════════════════════════════════════════════
if run_btn:
    st.session_state.result = None
    st.session_state.error  = None

    members = [m.strip() for m in members_raw.splitlines() if m.strip()]

    # Girdi doğrulama
    errors = []
    if not github_url.startswith("https://github.com/"):
        errors.append("Geçerli bir GitHub repo URL'si gir (https://github.com/...)")
    if end_date <= start_date:
        errors.append("Bitiş tarihi, başlangıç tarihinden sonra olmalı")
    if (end_date - start_date).days > 90:
        errors.append("Sprint süresi 90 günü geçemez")
    if not members:
        errors.append("En az bir takım üyesi gir")

    if errors:
        st.session_state.error = errors
    else:
        with st.spinner("GitHub'dan veriler çekiliyor ve analiz hesaplanıyor…"):
            try:
                st.session_state.result = analyze_sprint(
                    github_url=github_url,
                    start_date=str(start_date),
                    end_date=str(end_date),
                    team_members=members,
                    country_code=country_code,
                )
            except Exception as exc:
                st.session_state.error = [str(exc)]

# ══════════════════════════════════════════════════════════════════════════════
# ANA İÇERİK
# ══════════════════════════════════════════════════════════════════════════════

# ── Hata Gösterimi ─────────────────────────────────────────────────────────────
if st.session_state.error:
    for msg in st.session_state.error:
        st.error(msg)

# ── Sonuç Yok → Karşılama Ekranı ──────────────────────────────────────────────
if st.session_state.result is None and not st.session_state.error:
    st.markdown(
        f"""
        <div style="
            display:flex;flex-direction:column;align-items:center;
            justify-content:center;padding:5rem 2rem;text-align:center;
        ">
            <div style="
                width:72px;height:72px;
                background:linear-gradient(135deg,#3B82F6 0%,#06B6D4 100%);
                border-radius:20px;display:flex;align-items:center;
                justify-content:center;margin-bottom:1.5rem;
                box-shadow:0 8px 24px rgba(59,130,246,0.25);
            ">
                <span style="font-size:36px;line-height:1;">📊</span>
            </div>
            <h1 style="margin:0 0 0.5rem 0;font-size:1.75rem;font-weight:700;color:#0F172A;">
                SprintBoard
            </h1>
            <p style="margin:0;color:#64748B;font-size:1rem;max-width:400px;line-height:1.6;">
                Sol panelden sprint parametrelerini gir ve <strong>Analizi Başlat</strong>'a tıkla.
                GitHub verileri, tatil takvimi ve iş yükü dengesi otomatik hesaplanır.
            </p>
            <div style="
                display:flex;gap:2rem;margin-top:2.5rem;
                border-top:1px solid #E2E8F0;padding-top:2rem;
            ">
                <div style="text-align:center;">
                    <p style="margin:0;font-family:'{FONT_MONO}',monospace;font-size:1.5rem;
                               font-weight:600;color:#3B82F6;">0–100</p>
                    <p style="margin:4px 0 0;font-size:0.75rem;color:#94A3B8;font-weight:500;
                               text-transform:uppercase;letter-spacing:0.05em;">Performans Skoru</p>
                </div>
                <div style="text-align:center;">
                    <p style="margin:0;font-family:'{FONT_MONO}',monospace;font-size:1.5rem;
                               font-weight:600;color:#06B6D4;">Gini</p>
                    <p style="margin:4px 0 0;font-size:0.75rem;color:#94A3B8;font-weight:500;
                               text-transform:uppercase;letter-spacing:0.05em;">İş Yükü Dengesi</p>
                </div>
                <div style="text-align:center;">
                    <p style="margin:0;font-family:'{FONT_MONO}',monospace;font-size:1.5rem;
                               font-weight:600;color:#10B981;">TR</p>
                    <p style="margin:4px 0 0;font-size:0.75rem;color:#94A3B8;font-weight:500;
                               text-transform:uppercase;letter-spacing:0.05em;">Tatil Takvimi</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# ── Sonuç Gösterimi ────────────────────────────────────────────────────────────
r = st.session_state.result

# Başlık
repo_short = r["github_url"].replace("https://github.com/", "")
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.25rem;">
        <h1 style="margin:0;font-size:1.5rem;font-weight:700;color:#0F172A;">{repo_short}</h1>
        {badge("Tamamlandı", C_SUCCESS)}
    </div>
    <p style="color:#64748B;font-size:0.875rem;margin:0 0 1.75rem 0;">
        {r['start_date']} → {r['end_date']} &nbsp;·&nbsp;
        <span style="font-family:'{FONT_MONO}',monospace;">{r['total_working_days']}</span> çalışma günü &nbsp;·&nbsp;
        {len(r['member_performance'])} takım üyesi
    </p>
    """,
    unsafe_allow_html=True,
)

# ── Skor Gauge'ları ────────────────────────────────────────────────────────────
col_g1, col_g2, col_info = st.columns([1, 1, 2])

with col_g1:
    perf  = r["performance_score"]
    st.plotly_chart(
        score_gauge(perf, "Performans Skoru", score_color(perf)),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_g2:
    bal   = r["workload_balance_score"]
    st.plotly_chart(
        score_gauge(bal, "İş Yükü Dengesi", score_color(bal)),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_info:
    section_header("Analiz Notları")
    notes = r.get("analysis_notes", "")
    for line in notes.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("✅"):
            color = C_SUCCESS
        elif line.startswith("⚠️"):
            color = C_WARNING
        elif line.startswith("❌"):
            color = C_DANGER
        else:
            color = C_TEXT_2

        st.markdown(
            f'<p style="margin:0 0 8px 0;font-size:0.875rem;color:{color};">{line}</p>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    # Özet metrikler
    mc1, mc2, mc3 = st.columns(3)
    total_commits = sum(m["total_commits"] for m in r["member_performance"])
    total_add     = sum(m["total_additions"] for m in r["member_performance"])
    total_del     = sum(m["total_deletions"] for m in r["member_performance"])
    mc1.markdown(metric_card("Toplam Commit", str(total_commits), C_ACCENT), unsafe_allow_html=True)
    mc2.markdown(metric_card("Eklenen Satır", f"+{total_add}", C_SUCCESS), unsafe_allow_html=True)
    mc3.markdown(metric_card("Silinen Satır", f"-{total_del}", C_DANGER), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Grafikler ──────────────────────────────────────────────────────────────────
st.markdown(f'<hr style="border:none;border-top:1px solid {C_BORDER};margin:0.5rem 0 1.5rem 0;">', unsafe_allow_html=True)

col_ch1, col_ch2 = st.columns([1, 2])

with col_ch1:
    section_header("Commit Dağılımı", "Takım üyesi bazında iş yükü")
    st.plotly_chart(
        workload_pie(r["member_performance"]),
        use_container_width=True,
        config={"displayModeBar": False},
    )

with col_ch2:
    section_header("Üye Karşılaştırması", "Commit · Ekleme (+) · Silme (-)")
    st.plotly_chart(
        member_bar(r["member_performance"]),
        use_container_width=True,
        config={"displayModeBar": False},
    )

# ── Aktif Gün Grafiği ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
section_header("Aktif Günler", f"Sprint boyunca commit yapılan gün sayısı (toplam {r['total_working_days']} iş günü)")
st.plotly_chart(
    active_days_bar(r["member_performance"], r["total_working_days"]),
    use_container_width=True,
    config={"displayModeBar": False},
)

# ── Detay Tablosu ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
section_header("Üye Detayları")

import pandas as pd

df = pd.DataFrame(r["member_performance"])
df = df.rename(columns={
    "github_login":    "GitHub",
    "total_commits":   "Commit",
    "total_additions": "+ Satır",
    "total_deletions": "- Satır",
    "active_days":     "Aktif Gün",
    "workload_share":  "İş Payı",
})
df["İş Payı"] = df["İş Payı"].apply(lambda x: f"{x * 100:.1f}%")
df = df.sort_values("Commit", ascending=False)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "GitHub":     st.column_config.TextColumn(width="medium"),
        "Commit":     st.column_config.NumberColumn(format="%d"),
        "+ Satır":    st.column_config.NumberColumn(format="%d"),
        "- Satır":    st.column_config.NumberColumn(format="%d"),
        "Aktif Gün":  st.column_config.NumberColumn(format="%d"),
        "İş Payı":    st.column_config.TextColumn(),
    },
)
