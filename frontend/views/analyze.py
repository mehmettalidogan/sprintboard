import re as _re
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from components.styles import (
    section_header, metric_card, badge, score_color,
    C_SUCCESS, C_DANGER, C_WARNING, C_ACCENT, C_TEXT_2, C_BORDER, FONT_MONO,
)
from components.charts import score_gauge, workload_pie, member_bar, active_days_bar
from utils.api_client import analyze_sprint

result = st.session_state.get("result")
error  = st.session_state.get("error")

# ══════════════════════════════════════════════════════════════════════════════
# FORM — Sonuç yokken göster
# ══════════════════════════════════════════════════════════════════════════════
if result is None:
    st.html("<div style='margin-bottom:2rem;'><div style='font-size:1.875rem;font-weight:800;color:#0F172A;letter-spacing:-0.03em;margin-bottom:0.25rem;'>Yeni Analiz</div><p style='margin:0;color:#64748B;font-size:0.95rem;'>GitHub sprint verisini analiz et</p></div>")

    if error:
        for msg in error:
            st.error(msg)
        st.html("<div style='height:0.5rem'></div>")

    col_form, col_guide = st.columns([3, 2], gap="large")

    with col_form:
        github_url = st.text_input(
            "GitHub Repo URL",
            placeholder="https://github.com/kullanici/repo",
            help="Herkese açık bir GitHub deposunun tam adresi",
        )
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("Sprint Başlangıç", value=date.today() - timedelta(days=14), format="DD.MM.YYYY")
        with col_d2:
            end_date = st.date_input("Sprint Bitiş", value=date.today(), format="DD.MM.YYYY")
        members_raw = st.text_area(
            "Takım Üyeleri",
            placeholder="alice\nbob\ncharlie\n\nHer satıra bir GitHub kullanıcı adı",
            height=130,
        )
        country_code = st.selectbox(
            "Ülke (Tatil Takvimi)",
            options=["TR", "US", "DE", "GB", "FR", "NL", "PL"],
            help="Resmi tatilleri hesaba katmak için ülke seçin",
        )
        st.html("<div style='height:0.5rem'></div>")
        run_btn = st.button("Analizi Başlat", use_container_width=True)

    with col_guide:
        st.html(
            "<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:16px;padding:2rem;'>"
            "<p style='margin:0 0 1.25rem;font-weight:700;color:#0F172A;font-size:1rem;'>Nas\u0131l \u00c7al\u0131\u015f\u0131r?</p>"
            "<div style='display:flex;flex-direction:column;gap:1.25rem;'>"
            "<div style='display:flex;gap:0.875rem;align-items:flex-start;'>"
            "<span style='background:#3B82F6;color:white;min-width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0;'>1</span>"
            "<div><p style='margin:0;font-weight:600;color:#0F172A;font-size:0.875rem;'>Repo URL'ini gir</p><p style='margin:2px 0 0;color:#64748B;font-size:0.8rem;line-height:1.5;'>Herkese a\u00e7\u0131k bir GitHub deposunun tam adresi olmal\u0131</p></div></div>"
            "<div style='display:flex;gap:0.875rem;align-items:flex-start;'>"
            "<span style='background:#3B82F6;color:white;min-width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0;'>2</span>"
            "<div><p style='margin:0;font-weight:600;color:#0F172A;font-size:0.875rem;'>Sprint tarihlerini belirle</p><p style='margin:2px 0 0;color:#64748B;font-size:0.8rem;line-height:1.5;'>Maks. 90 g\u00fcnl\u00fck aral\u0131k \u00f6nerilir</p></div></div>"
            "<div style='display:flex;gap:0.875rem;align-items:flex-start;'>"
            "<span style='background:#3B82F6;color:white;min-width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;flex-shrink:0;'>3</span>"
            "<div><p style='margin:0;font-weight:600;color:#0F172A;font-size:0.875rem;'>Tak\u0131m \u00fcyelerini ekle</p><p style='margin:2px 0 0;color:#64748B;font-size:0.8rem;line-height:1.5;'>GitHub kullan\u0131c\u0131 adlar\u0131n\u0131 alt alta yaz</p></div></div>"
            "<div style='display:flex;gap:0.875rem;align-items:flex-start;'>"
            "<span style='background:#10B981;color:white;min-width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;flex-shrink:0;'>4</span>"
            "<div><p style='margin:0;font-weight:600;color:#0F172A;font-size:0.875rem;'>Analizi ba\u015flat</p><p style='margin:2px 0 0;color:#64748B;font-size:0.8rem;line-height:1.5;'>Commit verisi \u00e7ekilir, performans &amp; i\u015f dengesi hesaplan\u0131r</p></div></div>"
            "</div>"
            "<div style='margin-top:1.5rem;padding-top:1.25rem;border-top:1px solid #E2E8F0;'>"
            "<p style='margin:0;font-size:0.8rem;color:#94A3B8;'>Analiz s\u00fcresi repo boyutuna ve tak\u0131m say\u0131s\u0131na g\u00f6re 10\u201360 sn s\u00fcrebilir</p>"
            "</div></div>"
        )

    # ── Analiz tetikleyici ─────────────────────────────────────────────────────
    if run_btn:
        st.session_state.error = None
        members = [m.strip() for m in members_raw.splitlines() if m.strip()]
        errors = []
        if not github_url.startswith("https://github.com/"):
            errors.append("Geçersiz URL: 'https://github.com/kullanici/repo' formatında girin.")
        if end_date <= start_date:
            errors.append("Tarih Hatası: Bitiş tarihi başlangıçtan sonra olmalı.")
        if (end_date - start_date).days > 90:
            errors.append("Süre Aşımı: En fazla 90 günlük aralık analiz edilebilir.")
        if not members:
            errors.append("Takım Üyeleri: En az bir GitHub kullanıcı adı girin.")
        if errors:
            st.session_state.error = errors
            st.rerun()
        else:
            with st.spinner("GitHub'dan veriler çekiliyor, analiz hesaplanıyor…"):
                try:
                    st.session_state.result = analyze_sprint(
                        github_url=github_url,
                        start_date=str(start_date),
                        end_date=str(end_date),
                        team_members=members,
                        country_code=country_code,
                        token=st.session_state.token,
                    )
                    st.session_state.error = None
                    st.rerun()
                except Exception as exc:
                    msg = str(exc).lower()
                    if "401" in msg and "bad credentials" not in msg:
                        err = "Oturum süresi dolmuş. Çıkış yapıp tekrar giriş yapın."
                    elif "502" in msg or "bad gateway" in msg:
                        if "bad credentials" in msg:
                            err = "GitHub Yetkilendirme Hatası: .env dosyasındaki GITHUB_TOKEN geçersiz veya süresi dolmuş."
                        else:
                            err = f"Sunucu Hatası / GitHub API Hatası: {exc}"
                    elif "timeout" in msg:
                        err = "Zaman Aşımı: Sprint tarih aralığını kısaltıp tekrar deneyin."
                    elif "404" in msg or "not found" in msg:
                        err = "Repo Bulunamadı: Repo gizli (private) olabilir veya URL yanlış."
                    else:
                        err = f"Beklenmeyen hata: {str(exc)}"
                    st.session_state.error = [err]
                    st.rerun()

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# SONUÇ
# ══════════════════════════════════════════════════════════════════════════════
r = result
repo_short = r["github_url"].replace("https://github.com/", "")
n_members  = len(r["member_performance"])

col_title, col_btn = st.columns([5, 1])
with col_title:
    _badge_html   = badge("Tamamland\u0131", C_SUCCESS)
    _start        = r["start_date"]
    _end          = r["end_date"]
    _working_days = r["total_working_days"]
    _calısma      = "\u00e7al\u0131\u015fma g\u00fcn\u00fc"
    _takim        = "tak\u0131m \u00fcyesi"
    st.html(
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:0.25rem;'>"
        f"<div style='font-size:1.5rem;font-weight:700;color:#0F172A;'>{repo_short}</div>"
        f"{_badge_html}"
        f"</div>"
        f"<p style='color:#64748B;font-size:0.875rem;margin:0 0 1.75rem;'>"
        f"{_start} &rarr; {_end} &nbsp;&middot;&nbsp; "
        f"<span style='font-family:JetBrains Mono,monospace;'>{_working_days}</span> "
        f"{_calısma} &nbsp;&middot;&nbsp; {n_members} {_takim}</p>"
    )
with col_btn:
    st.html("<div style='height:1rem'></div>")
    if st.button("Yeni Analiz", use_container_width=True):
        st.session_state.result = None
        st.session_state.error  = None
        st.rerun()

# ── Gauge + Notlar ────────────────────────────────────────────────────────────
col_g1, col_g2, col_info = st.columns([1, 1, 2])
with col_g1:
    perf = r["performance_score"]
    st.plotly_chart(score_gauge(perf, "Performans Skoru", score_color(perf)), use_container_width=True, config={"displayModeBar": False})
with col_g2:
    bal = r["workload_balance_score"]
    st.plotly_chart(score_gauge(bal, "\u0130\u015f Y\u00fck\u00fc Dengesi", score_color(bal)), use_container_width=True, config={"displayModeBar": False})
with col_info:
    section_header("Analiz Notlar\u0131")
    notes = r.get("analysis_notes", "")
    for line in notes.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("\u2705"):
            color, prefix = C_SUCCESS, "OLUMLU"
        elif line.startswith("\u26a0"):
            color, prefix = C_WARNING, "UYARI"
        elif line.startswith("\u274c"):
            color, prefix = C_DANGER, "DIKKAT"
        else:
            color, prefix = C_TEXT_2, ""
        clean = _re.sub(
            r"[\U0001F300-\U0001F9FF\U00002700-\U000027BF\U00002600-\U000026FF"
            r"\U0000FE00-\U0000FE0F\U0001F1E0-\U0001F1FF\u2300-\u23FF"
            r"\u2705\u274c\u26a0\uFE0F]+", "", line,
        ).strip()
        label = f"<span style='font-size:0.68rem;font-weight:700;letter-spacing:0.05em;margin-right:6px;opacity:0.6;'>{prefix}</span>" if prefix else ""
        st.html(f"<p style='margin:0 0 8px;font-size:0.875rem;color:{color};'>{label}{clean}</p>")

    st.html("<div style='height:0.5rem'></div>")
    mc1, mc2, mc3 = st.columns(3)
    total_commits = sum(m["total_commits"] for m in r["member_performance"])
    total_add     = sum(m["total_additions"] for m in r["member_performance"])
    total_del     = sum(m["total_deletions"] for m in r["member_performance"])
    with mc1:
        st.html(metric_card("Toplam Commit", str(total_commits), C_ACCENT))
    with mc2:
        st.html(metric_card("Eklenen Sat\u0131r", f"+{total_add}", C_SUCCESS))
    with mc3:
        st.html(metric_card("Silinen Sat\u0131r", f"-{total_del}", C_DANGER))

st.html(f"<hr style='border:none;border-top:1px solid {C_BORDER};margin:1.5rem 0;'>")

# ── Grafikler ─────────────────────────────────────────────────────────────────
col_ch1, col_ch2 = st.columns([1, 2])
with col_ch1:
    section_header("Commit Da\u011f\u0131l\u0131m\u0131", "Tak\u0131m \u00fcyesi baz\u0131nda i\u015f y\u00fck\u00fc")
    st.plotly_chart(workload_pie(r["member_performance"]), use_container_width=True, config={"displayModeBar": False})
with col_ch2:
    section_header("\u00dcye K\u0131yaslaması", "Commit \u00b7 Ekleme (+) \u00b7 Silme (-)")
    st.plotly_chart(member_bar(r["member_performance"]), use_container_width=True, config={"displayModeBar": False})

st.html("<div style='height:0.5rem'></div>")
section_header("Aktif G\u00fcnler", f"Sprint boyunca commit yap\u0131lan g\u00fcn say\u0131s\u0131 (toplam {r['total_working_days']} i\u015f g\u00fcn\u00fc)")
st.plotly_chart(active_days_bar(r["member_performance"], r["total_working_days"]), use_container_width=True, config={"displayModeBar": False})

# ── Tablo ─────────────────────────────────────────────────────────────────────
st.html("<div style='height:0.5rem'></div>")
section_header("\u00dcye Detaylar\u0131")
df = pd.DataFrame(r["member_performance"])
df = df.rename(columns={
    "github_login": "GitHub", "total_commits": "Commit",
    "total_additions": "+ Sat\u0131r", "total_deletions": "- Sat\u0131r",
    "active_days": "Aktif G\u00fcn", "workload_share": "\u0130\u015f Pay\u0131",
})
df["\u0130\u015f Pay\u0131"] = df["\u0130\u015f Pay\u0131"].apply(lambda x: f"{x * 100:.1f}%")
df = df.sort_values("Commit", ascending=False)
st.dataframe(df, use_container_width=True, hide_index=True, column_config={
    "GitHub": st.column_config.TextColumn(width="medium"),
    "Commit": st.column_config.NumberColumn(format="%d"),
    "+ Sat\u0131r": st.column_config.NumberColumn(format="%d"),
    "- Sat\u0131r": st.column_config.NumberColumn(format="%d"),
    "Aktif G\u00fcn": st.column_config.NumberColumn(format="%d"),
    "\u0130\u015f Pay\u0131": st.column_config.TextColumn(),
})
