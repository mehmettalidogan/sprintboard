import streamlit as st
from components.styles import section_header, score_color, C_SUCCESS, C_DANGER, C_WARNING, C_BORDER
from utils.api_client import get_user_sprints, delete_sprint

# ── Başlık ────────────────────────────────────────────────────────────────────
st.html("<div style='margin-bottom:2rem;'><div style='margin:0 0 0.25rem;font-size:1.875rem;font-weight:800;color:#0F172A;letter-spacing:-0.03em;'>Ge\u00e7mi\u015f Analizler</div><p style='margin:0;color:#64748B;font-size:0.95rem;'>Daha \u00f6nce \u00e7al\u0131\u015ft\u0131r\u0131lan sprint analizleri</p></div>")

# ── Veri ─────────────────────────────────────────────────────────────────────
try:
    sprints = get_user_sprints(st.session_state.token)
except Exception as exc:
    st.error(f"Analizler yüklenemedi: {exc}")
    st.stop()

if not sprints:
    st.html("<div style='background:#F8FAFC;border:1px dashed #CBD5E1;border-radius:16px;padding:3rem;text-align:center;'><p style='margin:0;font-weight:600;color:#0F172A;'>Hen\u00fcz analiz yap\u0131lmad\u0131</p><p style='margin:6px 0 0;color:#64748B;font-size:0.875rem;'>Sol men\u00fcden <strong>Yeni Analiz</strong> sayfas\u0131na gidip ilk sprintini analiz et</p></div>")
    st.stop()

st.html(f"<p style='color:#64748B;font-size:0.875rem;margin-bottom:1.25rem;'>{len(sprints)} analiz bulundu</p>")

# ── Sprint Listesi ────────────────────────────────────────────────────────────
for sprint in sprints:
    repo     = sprint.get("github_url", "").replace("https://github.com/", "")
    perf     = sprint.get("performance_score", 0)
    bal      = sprint.get("workload_balance_score", 0)
    members  = sprint.get("team_members", [])
    sid      = sprint.get("id", "")
    sd       = sprint.get("start_date", "")
    ed       = sprint.get("end_date", "")
    days     = sprint.get("total_working_days", 0)
    perf_label = "\u0130yi" if perf >= 75 else ("Orta" if perf >= 50 else "D\u00fc\u015f\u00fck")
    perf_color = C_SUCCESS if perf >= 75 else (C_WARNING if perf >= 50 else C_DANGER)
    members_str = ", ".join(members[:4]) + ("..." if len(members) > 4 else "")

    with st.container():
        col_info, col_scores, col_del = st.columns([4, 2, 0.6])

        with col_info:
            st.html(
                f"<div style='padding:1.1rem 0;'>"
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                f"<p style='margin:0;font-weight:700;color:#0F172A;font-size:0.975rem;'>{repo}</p>"
                f"<span style='background:{perf_color}18;color:{perf_color};border:1px solid {perf_color}33;border-radius:6px;padding:1px 8px;font-size:0.7rem;font-weight:600;'>{perf_label}</span>"
                f"</div>"
                f"<p style='margin:0;color:#64748B;font-size:0.83rem;'>{sd} &rarr; {ed} &nbsp;&middot;&nbsp; {days} i\u015f g\u00fcn\u00fc &nbsp;&middot;&nbsp; {len(members)} \u00fcye</p>"
                f"<p style='margin:4px 0 0;color:#94A3B8;font-size:0.78rem;'>{members_str}</p>"
                f"</div>"
            )

        with col_scores:
            sc1, sc2 = st.columns(2)
            with sc1:
                st.html(f"<div style='text-align:center;padding:1rem 0;'><p style='margin:0;font-family:JetBrains Mono,monospace;font-size:1.75rem;font-weight:700;color:{score_color(perf)};'>{perf}</p><p style='margin:2px 0 0;font-size:0.68rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;'>Performans</p></div>")
            with sc2:
                st.html(f"<div style='text-align:center;padding:1rem 0;'><p style='margin:0;font-family:JetBrains Mono,monospace;font-size:1.75rem;font-weight:700;color:{score_color(bal)};'>{bal}</p><p style='margin:2px 0 0;font-size:0.68rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.06em;'>Denge</p></div>")

        with col_del:
            st.html("<div style='height:1rem'></div>")
            if st.button("Sil", key=f"del_{sid}", help="Bu analizi sil"):
                try:
                    ok = delete_sprint(sid, st.session_state.token)
                    if ok:
                        st.success("Silindi.")
                        st.rerun()
                    else:
                        st.error("Silinemedi.")
                except Exception as exc:
                    st.error(f"Hata: {exc}")

        st.html(f"<hr style='border:none;border-top:1px solid {C_BORDER};margin:0;'>")
