# SprintBoard AI Sunucu Başlatma Kılavuzu

Projenin tam anlamıyla çalışabilmesi için 3 temel bileşenin sırasıyla başlatılması gerekmektedir:
1. **Veritabanı (PostgreSQL)**
2. **Backend (FastAPI)**
3. **Frontend (Streamlit)**

Lütfen VS Code içerisinde yeni terminaller açarak aşağıdaki adımları **sırasıyla** uygulayın.

---

## 🗄️ 1. Veritabanını Başlatmak (Docker ile)

Veritabanı (PostgreSQL) çalışmadan backend ayağa kalkmaz ve `alembic` hata verir. Önce veritabanını başlatmalıyız.

1. VS Code'da üst menüden **Terminal > New Terminal** (Ctrl+Shift+`) seçerek yeni bir terminal açın.
2. Terminalde ana dizinden `backend` klasörüne girin:
   ```powershell
   cd backend
   ```
3. Docker Compose kullanarak **sadece veritabanını** arka planda başlatın (Bilgisayarınızda Docker Desktop'ın açık olduğundan emin olun):
   ```powershell
   docker compose up -d db
   ```
*(Bu işlem veritabanını 5432 portunda çalışmaya başlatacaktır.)*

---

## ⚙️ 2. Backend (FastAPI) Sunucusunu Başlatmak

Veritabanı hazır olduktan sonra, API sunucusunu kendi bilgisayarımızda çalıştırabiliriz.

1. Aynı terminalde (`backend` klasöründe olduğunuzdan emin olun) sanal ortamı (virtual environment) aktif edin:
   ```powershell
   .\.venv\Scripts\activate
   ```
   *(Terminal satırının başında `(.venv)` yazısını görmelisiniz.)*

2. Veritabanı tablolarını oluşturmak / güncellemek için Alembic komutunu çalıştırın:
   ```powershell
   alembic upgrade head
   ```

3. FastAPI sunucusunu başlatın:
   ```powershell
   fastapi dev app/main.py
   ```
   *(Veya alternatif olarak: `uvicorn app.main:app --reload`)*

✅ **Kontrol:** Tarayıcınızda [http://localhost:8000/docs](http://localhost:8000/docs) adresini açarak API'nin çalıştığını görebilirsiniz.
*(Bu terminali kapatmayın, arka planda çalışmaya devam etsin.)*

---

## 🎨 3. Frontend (Streamlit) Sunucusunu Başlatmak

Kullanıcı arayüzünü çalıştırmak için yeni bir terminal penceresi kullanacağız.

1. VS Code içerisinde **Terminal sekmesinin sağ üst köşesindeki "+" (Artı) butonuna** tıklayarak **yeni bir terminal daha** açın.
2. Yeni terminalde proje ana dizinindeyken `frontend` klasörüne geçiş yapın:
   ```powershell
   cd frontend
   ```
3. Eğer paketler henüz yüklenmediyse gerekli kütüphaneleri kurun (sadece ilk seferde gereklidir):
   ```powershell
   pip install -r requirements.txt
   ```
4. Streamlit arayüzünü başlatın:
   ```powershell
   python -m streamlit run app.py
   ```

✅ **Kontrol:** Tarayıcınız otomatik olarak açılacak ve [http://localhost:8501](http://localhost:8501) adresinde arayüz görünecektir.

---

### 💡 Alternatif: Tüm Sistemi Tek Tıkla (Sadece Docker ile) Başlatmak
Eğer kod üzerinde anlık değişiklik yapıp test etmeyecekseniz (Sadece çalıştırmak istiyorsanız), tek bir komutla hem veritabanını hem de backend'i aynı anda ayağa kaldırabilirsiniz.
`backend` klasöründe iken şu komutu çalıştırın:
```powershell
docker compose up --build
```
*(Bu durumda 2. Adımdaki sanal ortam (`.venv`) ve `uvicorn` komutlarına gerek kalmaz. Sadece 3. Adımdaki Streamlit'i çalıştırmanız yeterli olur.)*
