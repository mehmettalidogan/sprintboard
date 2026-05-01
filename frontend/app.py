import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from components.styles import inject_global_css, sidebar_logo

st.set_page_config(
    page_title="SprintBoard AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

# ── Session State ──────────────────────────────────────────────────────────────
_defaults = {"token": None, "user_email": None, "result": None, "error": None}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── GitHub OAuth Token Capture ────────────────────────────────────────────────
if "token" in st.query_params and "email" in st.query_params:
    st.session_state.token = st.query_params.get("token")
    st.session_state.user_email = st.query_params.get("email")
    st.query_params.clear()

# ══════════════════════════════════════════════════════════════════════════════
# NAVİGASYON
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.token:
    # Giriş yapılmamış → yalnızca auth sayfası, sidebar nav gizli
    pg = st.navigation(
        [st.Page("views/auth.py", title="Giris Yap")],
        position="hidden",
    )
else:
    # Giriş yapılmış → sidebar: logo, kullanıcı bilgisi, çıkış butonu
    with st.sidebar:
        sidebar_logo()
        st.markdown(
            f'<p style="font-size:0.75rem;color:#94A3B8;margin:0 0 0.5rem;">'
            f'Giriş: <strong style="color:#E2E8F0;">{st.session_state.user_email}</strong></p>',
            unsafe_allow_html=True,
        )
        if st.button("Çıkış Yap", use_container_width=True, key="__logout"):
            for _k in ("token", "user_email", "result", "error"):
                st.session_state[_k] = None
            st.rerun()
        st.markdown(
            "<hr style='margin:0.75rem 0;border-color:#1E293B;'>",
            unsafe_allow_html=True,
        )

    pg = st.navigation([
        st.Page("views/home.py",    title="Ana Sayfa"),
        st.Page("views/planner.py", title="AI Planlayıcı"),
        st.Page("views/analyze.py", title="Yeni Analiz"),
        st.Page("views/history.py", title="Gecmis"),
    ])

pg.run()
