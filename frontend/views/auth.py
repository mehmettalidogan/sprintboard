import streamlit as st
from utils.api_client import login_user, register_user

# ── Sidebar gizle + stiller ───────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

.main .block-container {
    max-width: 100% !important;
    padding: 0 1.5rem !important;
}

/* Global h1/h2 override'larını auth paneli içinde etkisiz bırak */
[data-testid="stHtml"] h1,
[data-testid="stHtml"] h2 {
    color: inherit !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    letter-spacing: inherit !important;
}

/* Tab stilleri */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #F1F5F9 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 2px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    color: #64748B !important;
    padding: 0.45rem 1.25rem !important;
    transition: all .2s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 1px 5px rgba(0,0,0,0.1) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

/* Input stilleri */
.stTextInput input {
    background: #F8FAFC !important;
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    color: #0F172A !important;
    transition: border-color .2s, box-shadow .2s !important;
}
.stTextInput input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    background: #FFFFFF !important;
}

/* Submit butonu */
[data-testid="stForm"] .stButton > button {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    box-shadow: 0 4px 14px rgba(59,130,246,0.3) !important;
    transition: all .2s ease !important;
}
[data-testid="stForm"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 24px rgba(59,130,246,0.42) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
col_brand, col_form = st.columns([1.15, 0.85], gap="medium")

# ═══════════════════════════════════════════════
# SOL — Marka Paneli
# ═══════════════════════════════════════════════
with col_brand:
    st.html(
        "<div style='background:linear-gradient(150deg,#0F172A 0%,#1E293B 55%,#0F2044 100%);border-radius:18px;padding:3rem 2.75rem;min-height:80vh;font-family:Plus Jakarta Sans,system-ui,sans-serif;'>"

        # Logo
        "<div style='display:flex;align-items:center;gap:12px;margin-bottom:3rem;'>"
        "<div style='width:44px;height:44px;flex-shrink:0;background:linear-gradient(135deg,#3B82F6,#06B6D4);border-radius:12px;display:flex;align-items:center;justify-content:center;'>"
        "<span style='color:white;font-size:1.1rem;font-weight:900;font-family:monospace;'>SB</span>"
        "</div>"
        "<div>"
        "<p style='margin:0;font-size:1.1rem;font-weight:800;color:#F1F5F9;letter-spacing:-0.02em;'>SprintBoard AI</p>"
        "<p style='margin:0;font-size:0.65rem;color:#64748B;font-weight:500;letter-spacing:0.1em;text-transform:uppercase;'>Sprint Analitigi</p>"
        "</div></div>"

        # Ana başlık — <h1> yerine <div> kullanıyoruz (global CSS override'dan kaçınmak için)
        "<div style='margin-bottom:2.75rem;'>"
        "<div style='margin:0 0 1rem;font-size:2.4rem;font-weight:800;color:#F1F5F9;line-height:1.15;letter-spacing:-0.04em;'>"
        "Sprint<br>"
        "<span style='background:linear-gradient(90deg,#3B82F6,#06B6D4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>Performans\u0131n\u0131</span>"
        "<br>\u00d6l\u00e7.</div>"
        "<p style='margin:0;color:#94A3B8;font-size:0.92rem;line-height:1.65;max-width:300px;'>"
        "GitHub commit verisi, tatil takvimi ve Gini katsay\u0131s\u0131yla tak\u0131m\u0131n\u0131n ger\u00e7ek sprint performans\u0131n\u0131 analiz et."
        "</p></div>"

        # Özellik listesi
        "<div style='display:flex;flex-direction:column;gap:1.1rem;'>"

        "<div style='display:flex;align-items:center;gap:0.875rem;'>"
        "<div style='width:36px;height:36px;border-radius:9px;flex-shrink:0;background:rgba(59,130,246,0.18);display:flex;align-items:center;justify-content:center;'>"
        "<span style='color:#3B82F6;font-size:0.75rem;font-weight:800;font-family:monospace;'>01</span>"
        "</div>"
        "<div>"
        "<p style='margin:0;font-weight:600;color:#E2E8F0;font-size:0.875rem;'>Ger\u00e7ek zamanl\u0131 commit analizi</p>"
        "<p style='margin:0;color:#64748B;font-size:0.78rem;'>GitHub API ile otomatik veri \u00e7ekme</p>"
        "</div></div>"

        "<div style='display:flex;align-items:center;gap:0.875rem;'>"
        "<div style='width:36px;height:36px;border-radius:9px;flex-shrink:0;background:rgba(6,182,212,0.18);display:flex;align-items:center;justify-content:center;'>"
        "<span style='color:#06B6D4;font-size:0.75rem;font-weight:800;font-family:monospace;'>02</span>"
        "</div>"
        "<div>"
        "<p style='margin:0;font-weight:600;color:#E2E8F0;font-size:0.875rem;'>\u0130\u015f y\u00fck\u00fc dengesi (Gini)</p>"
        "<p style='margin:0;color:#64748B;font-size:0.78rem;'>Tak\u0131m da\u011f\u0131l\u0131m\u0131n\u0131 istatistiksel olarak \u00f6l\u00e7</p>"
        "</div></div>"

        "<div style='display:flex;align-items:center;gap:0.875rem;'>"
        "<div style='width:36px;height:36px;border-radius:9px;flex-shrink:0;background:rgba(16,185,129,0.18);display:flex;align-items:center;justify-content:center;'>"
        "<span style='color:#10B981;font-size:0.75rem;font-weight:800;font-family:monospace;'>03</span>"
        "</div>"
        "<div>"
        "<p style='margin:0;font-weight:600;color:#E2E8F0;font-size:0.875rem;'>Tatil takvimi entegrasyonu</p>"
        "<p style='margin:0;color:#64748B;font-size:0.78rem;'>Ger\u00e7ek i\u015f g\u00fcnlerini otomatik hesapla</p>"
        "</div></div>"

        "</div></div>"
    )

# ═══════════════════════════════════════════════
# SAG — Form Paneli
# ═══════════════════════════════════════════════
with col_form:
    st.html("<div style='height:8vh'></div>")

    st.html(
        "<div style='margin-bottom:1.75rem;'>"
        "<div style='margin:0 0 0.35rem;font-size:1.65rem;font-weight:800;color:#0F172A;letter-spacing:-0.03em;font-family:Plus Jakarta Sans,system-ui,sans-serif;'>Ho\u015f geldin</div>"
        "<p style='margin:0;color:#64748B;font-size:0.9rem;'>Hesab\u0131na giri\u015f yap veya yeni hesap olu\u015ftur</p>"
        "</div>"
    )

    login_tab, reg_tab = st.tabs(["\u00a0\u00a0Giri\u015f Yap\u00a0\u00a0", "\u00a0\u00a0Kay\u0131t Ol\u00a0\u00a0"])

    # ── Giriş Formu ───────────────────────────────────────────────────────────
    with login_tab:
        st.html("<div style='height:0.5rem'></div>")
        
        st.link_button("🐙 GitHub ile Giriş Yap", "http://localhost:8000/api/v1/auth/github/login", use_container_width=True)
        st.html("<div style='text-align: center; margin: 0.75rem 0; color: #94A3B8; font-size: 0.85rem;'>veya e-posta ile giriş yap</div>")

        with st.form("login_form"):
            email    = st.text_input("E-posta", placeholder="ornek@mail.com")
            password = st.text_input("Şifre", type="password", placeholder="••••••••")
            st.html("<div style='height:0.2rem'></div>")
            submit   = st.form_submit_button("Giriş Yap", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("E-posta ve şifre gerekli.")
            else:
                try:
                    with st.spinner("Giriş yapılıyor..."):
                        data = login_user(email, password)
                    st.session_state.token      = data["access_token"]
                    st.session_state.user_email = email
                    st.rerun()
                except Exception as exc:
                    msg = str(exc)
                    if "401" in msg:
                        st.error("E-posta veya şifre hatalı.")
                    elif "Connection" in msg:
                        st.error("Backend'e bağlanılamadı. Sunucu çalışıyor mu?")
                    else:
                        st.error(f"Giriş başarısız: {msg}")

    # ── Kayıt Formu ───────────────────────────────────────────────────────────
    with reg_tab:
        st.html("<div style='height:0.5rem'></div>")
        with st.form("register_form"):
            name     = st.text_input("Ad Soyad (isteğe bağlı)", placeholder="Ali Veli")
            email    = st.text_input("E-posta", placeholder="ornek@mail.com", key="reg_email")
            password = st.text_input(
                "Şifre", type="password", key="reg_pw",
                placeholder="••••••••", help="En az 8 karakter",
            )
            st.html("<div style='height:0.2rem'></div>")
            submit = st.form_submit_button("Hesap Oluştur", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("E-posta ve şifre gerekli.")
            elif len(password) < 8:
                st.error("Şifre en az 8 karakter olmalı.")
            else:
                try:
                    with st.spinner("Hesap oluşturuluyor..."):
                        data = register_user(email, password, name)
                    st.session_state.token      = data["access_token"]
                    st.session_state.user_email = email
                    st.rerun()
                except Exception as exc:
                    msg = str(exc)
                    if "409" in msg:
                        st.error("Bu e-posta zaten kayıtlı.")
                    elif "422" in msg or "Geçersiz" in msg or "Şifre" in msg or "E-posta" in msg:
                        st.error(f"⚠️ {msg}")
                    elif "Connection" in msg:
                        st.error("Backend'e bağlanılamadı. Sunucu çalışıyor mu?")
                    else:
                        st.error(f"Kayıt başarısız: {msg}")

    st.html(
        "<p style='margin-top:1.5rem;color:#94A3B8;font-size:0.78rem;text-align:center;'>"
        "Sprint verisi GitHub API \u00fczerinden g\u00fcvenli \u015fekilde \u00e7ekilir"
        "</p>"
    )
