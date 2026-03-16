# SprintBoard AI Sunucu Başlatma Kılavuzu

Projenin hem arka yüzünü (Backend - FastAPI) hem de ön yüzünü (Frontend - Streamlit) başlatmak için aşağıdaki adımları sırasıyla uygulayabilirsiniz.

Proje klasörünüz (`Sprint Board`) içerisinde iki ayrı terminal (komut satırı) penceresine ihtiyacınız olacak.

---

## 🏗️ 1. Adım: Backend (FastAPI) Sunucusunu Başlatmak

Veritabanı bağlantıları ve API endpoint'lerini yöneten arka plan sistemidir.

1. VS Code içerisinde projeyi açın.
2. Üst menüden **Terminal > New Terminal** seçeneğine tıklayarak yeni bir terminal başlatın.
3. Terminalde `backend` klasörüne geçiş yapın:
   ```bash
   cd backend
   ```
4. Eğer sanal ortamınız (virtual environment) aktif değilse aktif edin (isteğe bağlı, Docker kullanmıyorsanız gereklidir):
   ```bash
   # Windows için sanal ortamı aktif etme komutu (eğer varsa):
   ..\venv\Scripts\activate
   ```
5. Backend'i **Docker** ile başlatmak (Önerilen Yöntem):
   Bilgisayarınızda Docker uygulamasının açık ve çalıştığından emin olduktan sonra şu komutu girin:
   ```bash
   docker compose up --build
   ```
   *(Bu işlem FastAPI'yi http://localhost:8000 adresinde ayağa kaldırır)*

---

## 🎨 2. Adım: Frontend (Streamlit) Sunucusunu Başlatmak

Kullanıcı arayüzünü (UI) çalıştıran bölümdür. Önceki adımlardaki hata, `npm` (Node.js) komutlarını kullanmaya çalışmanızdan kaynaklanmıştır; bu proje frontend tarafında React/Next.js değil, **Python tabanlı Streamlit** kullanmaktadır.

1. VS Code içerisinde farklı bir sekme açarak **yeni bir terminal** başlatın (mevcut çalışan backend terminalini kapatmayın).
2. Terminalde proje ana dizinindeyken `frontend` klasörüne geçiş yapın:
   ```bash
   cd frontend
   ```
3. (Eğer `venv` kurulu değilse veya paketler eksikse) Önce gerekli Python kütüphanelerini kurun:
   ```bash
   pip install -r requirements.txt
   ```
4. Streamlit uygulamasını başlatın:
   ```bash
   python -m streamlit run app.py
   ```
5. Sistem başladığında, tarayıcınız otomatik açılacak veya şu adrese yönlendirecektir:
   [http://localhost:8501](http://localhost:8501)

---

## ✅ Özet Kontrol

Sistemin düzgün çalıştığını anlamak için:
*   🔗 **Backend API Swagger:** `http://localhost:8000/docs`
*   🔗 **Backend Veritabanı Testi:** `http://localhost:8000/db-status`
*   🔗 **Frontend Kullanıcı Paneli:** `http://localhost:8501`

*(Not: Docker kullanmadan ilerliyorsanız veritabanı adımlarını manuel olarak bilgisayarınızda kurduğunuz PostgreSQL'e göre `.env` dosyasından ayarlamanız gerekir).*
