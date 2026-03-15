import streamlit as st
from components.styles import section_header, metric_card, score_color, C_ACCENT, C_TEXT_3
from utils.api_client import get_user_sprints

# ── Veri ─────────────────────────────────────────────────────────────────────
sprints: list[dict] = []
load_error = False
try:
    sprints = get_user_sprints(st.session_state.token)
except Exception:
    load_error = True

total    = len(sprints)
avg_perf = round(sum(s.get("performance_score", 0) for s in sprints) / total, 1) if total else 0
avg_bal  = round(sum(s.get("workload_balance_score", 0) for s in sprints) / total, 1) if total else 0
first_name = (st.session_state.user_email or "").split("@")[0].capitalize()

# ── Başlık ────────────────────────────────────────────────────────────────────
st.html(f"<div style='margin-bottom:2rem;'><div style='margin:0 0 0.25rem;font-size:1.875rem;font-weight:800;color:#0F172A;letter-spacing:-0.03em;'>Merhaba, {first_name}</div><p style='margin:0;color:#64748B;font-size:0.95rem;'>Sprint analizlerine genel bak\u0131\u015f</p></div>")

# ── İstatistik Kartları ───────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.html(metric_card("Toplam Analiz", str(total), C_ACCENT))
with c2:
    st.html(metric_card("Ort. Performans", f"{avg_perf}/100" if total else "\u2014", score_color(avg_perf) if total else C_TEXT_3))
with c3:
    st.html(metric_card("Ort. \u0130\u015f Dengesi", f"{avg_bal}/100" if total else "\u2014", score_color(avg_bal) if total else C_TEXT_3))

st.html("<div style='height:1rem'></div>")

# ── Hızlı Erişim ──────────────────────────────────────────────────────────────
section_header("H\u0131zl\u0131 Eri\u015fim")
qa1, qa2 = st.columns(2)
with qa1:
    st.html("<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;padding:1.75rem;box-shadow:0 1px 4px rgba(0,0,0,0.04);border-left:4px solid #3B82F6;'><p style='margin:0 0 0.75rem;font-weight:700;color:#0F172A;font-size:1.05rem;'>Yeni Analiz Ba\u015flat</p><p style='margin:0;color:#64748B;font-size:0.875rem;line-height:1.5;'>GitHub reposu, tarih aral\u0131\u011f\u0131 ve tak\u0131m \u00fcyeleriyle sprint analizi \u00e7al\u0131\u015ft\u0131r</p></div>")
with qa2:
    st.html(f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;padding:1.75rem;box-shadow:0 1px 4px rgba(0,0,0,0.04);border-left:4px solid #06B6D4;'><p style='margin:0 0 0.75rem;font-weight:700;color:#0F172A;font-size:1.05rem;'>Ge\u00e7mi\u015f Analizler</p><p style='margin:0;color:#64748B;font-size:0.875rem;line-height:1.5;'>{total} kay\u0131tl\u0131 analiz &middot; Ge\u00e7mi\u015f sprint performans kay\u0131tlar\u0131</p></div>")

st.html("<div style='height:1rem'></div>")

# ── Son Analiz ────────────────────────────────────────────────────────────────
if load_error:
    st.warning("Geçmiş analizler yüklenemedi. Backend çalışıyor mu?")
elif sprints:
    section_header("Son Analiz")
    last = sprints[0]
    repo = last.get("github_url", "").replace("https://github.com/", "")
    perf = last.get("performance_score", 0)
    bal  = last.get("workload_balance_score", 0)
    days = last.get("total_working_days", 0)
    n_members = len(last.get("team_members", []))
    sd = last.get("start_date", "")
    ed = last.get("end_date", "")
    st.html(
        f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;padding:1.75rem;box-shadow:0 1px 4px rgba(0,0,0,0.04);'>"
        f"<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:1rem;'>"
        f"<div><p style='margin:0;font-weight:700;color:#0F172A;font-size:1.05rem;'>{repo}</p>"
        f"<p style='margin:6px 0 0;color:#64748B;font-size:0.875rem;'>{sd} &rarr; {ed} &nbsp;&middot;&nbsp; {days} i\u015f g\u00fcn\u00fc &nbsp;&middot;&nbsp; {n_members} tak\u0131m \u00fcyesi</p></div>"
        f"<div style='display:flex;gap:2rem;'>"
        f"<div style='text-align:center;'><p style='margin:0;font-family:JetBrains Mono,monospace;font-size:2rem;font-weight:700;color:{score_color(perf)};'>{perf}</p><p style='margin:2px 0 0;font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;'>Performans</p></div>"
        f"<div style='text-align:center;'><p style='margin:0;font-family:JetBrains Mono,monospace;font-size:2rem;font-weight:700;color:{score_color(bal)};'>{bal}</p><p style='margin:2px 0 0;font-size:0.7rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;'>\u0130\u015f Dengesi</p></div>"
        f"</div></div></div>"
    )
else:
    st.html("<div style='background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:16px;padding:3rem;text-align:center;'><p style='margin:0;font-weight:600;color:#0F172A;font-size:1rem;'>Hen\u00fcz analiz yap\u0131lmad\u0131</p><p style='margin:8px 0 0;color:#64748B;font-size:0.875rem;'>Sol men\u00fcden <strong>Yeni Analiz</strong> sayfas\u0131na gidip ilk sprintini analiz et</p></div>")

# ── Sistem Nasıl Çalışır ──────────────────────────────────────────────────────
st.html("<div style='height:1rem'></div>")
section_header("Sistem Nas\u0131l \u00c7al\u0131\u015f\u0131r?")

s1, s2, s3, s4 = st.columns(4)
steps = [
    ("01", "Repo URL", "GitHub reposunun tam adresini gir"),
    ("02", "Tarih Aral\u0131\u011f\u0131", "Sprint ba\u015flang\u0131\u00e7 ve biti\u015f tarihlerini belirle"),
    ("03", "Tak\u0131m", "GitHub kullan\u0131c\u0131 adlar\u0131n\u0131 ekle"),
    ("04", "Analiz", "Performans ve i\u015f y\u00fck\u00fc dengesi otomatik hesaplan\u0131r"),
]
for col, (num, title, desc) in zip([s1, s2, s3, s4], steps):
    with col:
        st.html(f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:1.25rem;box-shadow:0 1px 3px rgba(0,0,0,0.03);'><p style='margin:0 0 0.5rem;font-family:JetBrains Mono,monospace;font-size:0.75rem;font-weight:700;color:#3B82F6;letter-spacing:0.05em;'>ADIM {num}</p><p style='margin:0 0 4px;font-weight:600;color:#0F172A;font-size:0.875rem;'>{title}</p><p style='margin:0;color:#64748B;font-size:0.8rem;line-height:1.4;'>{desc}</p></div>")
