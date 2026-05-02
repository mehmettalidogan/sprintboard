import re
import streamlit as st
import pandas as pd
from utils.api_client import generate_sprint_plan

def parse_github_users(input_string: str) -> list[str]:
    """
    Virgülle ayrılmış GitHub kullanıcı adlarını veya profil linklerini ayrıştırıp,
    sadece temizlenmiş kullanıcı adlarını içeren bir liste döndürür.
    """
    if not input_string:
        return []
        
    usernames = []
    # Virgülle ayır ve baştaki/sondaki boşlukları temizle
    raw_users = [u.strip() for u in input_string.split(',')]
    
    for raw_user in raw_users:
        if not raw_user:
            continue
            
        # Eğer giriş bir GitHub URL'si ise Regex ile sadece kullanıcı adını yakala
        match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([^/\s]+)', raw_user, re.IGNORECASE)
        
        if match:
            # Eşleşen URL'den kullanıcı adını al
            usernames.append(match.group(1))
        else:
            # Sadece kullanıcı adı girilmişse (başında @ varsa temizle, sondaki slash'leri at)
            clean_user = raw_user.lstrip('@').rstrip('/')
            if clean_user:
                usernames.append(clean_user)
                
    return usernames
st.title("🤖 AI Proje Planlayıcı")
st.markdown(
    "Gemini destekli yapay zeka ile projenizi oluşturun. "
    "Takım üyelerinin GitHub geçmişleri taranarak en uygun roller otomatik atanır."
)

st.divider()

if "planner_result" not in st.session_state:
    st.session_state.planner_result = None

with st.form("planner_form"):
    project_idea = st.text_area(
        "Proje Fikri / Hedefi",
        height=120,
        placeholder="Örn: Kullanıcıların harcamalarını takip edeceği, makbuz fotoğraflarından OCR ile veri çıkaran bir mobil uygulama yapıyoruz. Frontend React Native, Backend FastAPI olacak."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        sprint_count = st.number_input("Kaç Sprint Sürsün?", min_value=1, max_value=10, value=4)
        
    with col2:
        team_members_input = st.text_input(
            "Takım Üyeleri (GitHub Kullanıcı Adları veya Profil Linkleri)", 
            placeholder="Örn: Kullanici1, https://github.com/Kullanici2, Kullanici3"
        )
        
    submit = st.form_submit_button("Planı Oluştur 🚀", type="primary", use_container_width=True)
    
if submit:
    if not project_idea or not team_members_input:
        st.error("Lütfen proje fikrini ve en az bir takım üyesini girin.")
    else:
        members = parse_github_users(team_members_input)
        if not members:
            st.error("Geçerli bir takım üyesi bulunamadı.")
        else:
            with st.spinner("GitHub geçmişleri inceleniyor ve Gemini ile plan oluşturuluyor... (Bu işlem 15-30 sn sürebilir)"):
                try:
                    result = generate_sprint_plan(
                        project_idea=project_idea,
                        sprint_count=sprint_count,
                        team_members=members,
                        token=st.session_state.token
                    )
                    st.session_state.planner_result = result
                    st.success("Plan başarıyla oluşturuldu!")
                except Exception as e:
                    st.error(f"Bir hata oluştu: {str(e)}")


# -- Sonuclari Göster --
result = st.session_state.planner_result
if result:
    st.header(f"📦 Proje: Planlanan {result['sprint_count']} Sprint")
    
    sprints = result.get("sprints", [])
    if not sprints:
        st.info("Kayıtlı sprint bulunamadı.")
        
    for sprint in sprints:
        st.subheader(f"Sprint {sprint['sprint_number']}: {sprint['goal']}")
        
        # Görevleri tablo veya kart şeklinde göster
        tasks = sprint.get("tasks", [])
        if tasks:
            # Pandas dataframe ile şık bir tablo hazırlayabiliriz
            df = pd.DataFrame(tasks)
            # Sütun isimlerini Türkçeleştirelim
            df = df.rename(columns={
                "title": "Görev",
                "assignee": "Atanan Kişi",
                "role_assigned": "Rol",
                "description": "Açıklama"
            })
            # Sütun sırasını ayarlayalım
            if set(["Görev", "Atanan Kişi", "Rol", "Açıklama"]).issubset(df.columns):
                df = df[["Görev", "Açıklama", "Atanan Kişi", "Rol"]]
                
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
            )
        else:
            st.warning("Bu sprint için görev oluşturulamadı.")
            
        st.divider()
