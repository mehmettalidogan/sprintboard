import streamlit as st
import pandas as pd
from components.styles import (
    inject_global_css, 
    sidebar_logo, 
    section_header,
    C_ACCENT, C_SUCCESS, C_DANGER
)
from components.charts import member_bar # Ana sayfadaki grafik stilini kullanmak için

# 1. Sayfa Ayarları
st.set_page_config(page_title="GitHub İçgörüleri", page_icon="📈", layout="wide")


inject_global_css()

# 3. Sol Menü (Sidebar) Tutarlılığı
with st.sidebar:
    sidebar_logo() # Logoyu buraya da ekledik
    st.markdown("<hr style='margin:0.75rem 0;border-color:#E2E8F0;'>", unsafe_allow_html=True)
    st.info("📈 Detaylı analiz sayfasındasınız.")

# 4. Veri Kontrolü
if "result" not in st.session_state or st.session_state.result is None:
    st.warning("⚠️ Henüz bir analiz yapılmadı. Lütfen ana sayfaya gidip bir repo analizi başlatın.")
    if st.button("🏠 Ana Sayfaya Dön"):
        st.switch_page("app.py")
    st.stop()

r = st.session_state.result

# 5. Başlık ve İçerik
st.title("📈 GitHub İçgörüleri")
section_header("Sprint Detayları", "Takım performansı ve dağılımı")

# Üst Metrikler
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Toplam Commit", f"{sum(m['total_commits'] for m in r['member_performance'])}")
with col2:
    st.metric("Performans Skoru", f"{r['performance_score']}/100")
with col3:
    st.metric("İş Yükü Dengesi", f"{r['workload_balance_score']}/100")

st.markdown("<br>", unsafe_allow_html=True)

# 6. Grafik 
section_header("Üye Katkı Karşılaştırması")
st.plotly_chart(
    member_bar(r["member_performance"]), 
    use_container_width=True,
    config={"displayModeBar": False}
)