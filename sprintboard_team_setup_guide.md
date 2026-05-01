# SprintBoard Ekip Kurulum Rehberi (GitHub OAuth)

Bu rehber, GitHub OAuth entegrasyonu tamamlanmış olan SprintBoard projesini kendi bilgisayarınızda (local) sorunsuz bir şekilde çalıştırmanız için izlemeniz gereken adımları içermektedir.

---

## Adım 1: Gerekli Kütüphanelerin Kurulumu

Backend koduna eklenen yeni özellikler için dış ağ isteklerini yapacak olan `httpx` kütüphanesinin kurulması gerekmektedir. Projenizin `backend` klasöründe olduğunuzdan ve sanal ortamınızın aktif olduğundan emin olun.

```bash
cd sprintboard/backend
pip install httpx python-jose pydantic-settings
```
*(Projede `python-jose` gibi diğer gerekli JWT paketleri hali hazırda gereksinimlerde (requirements) yoksa lütfen onları da kurun).*

---

## Adım 2: `.env` Dosyasının Güncellenmesi

Sistemin GitHub ile haberleşebilmesi için arka tarafta bazı gizli anahtarlara ihtiyacı vardır. `sprintboard/backend/.env` dosyanızı aşağıdaki şablona göre güncelleyin veya eksikse ekleyin:

```env
# Klasik Veritabanı ve Token Ayarları
DATABASE_URL=postgresql+asyncpg://postgres:SIFRENIZ@localhost:5432/sprintboard_db
SECRET_KEY=sprintboard_secret_key_buraya
GEMINI_API_KEY=google_gemini_key_buraya

# YENİ: GitHub OAuth2 Ayarları
GITHUB_CLIENT_ID=KENDI_CLIENT_ID_DEGERINIZ
GITHUB_CLIENT_SECRET=KENDI_CLIENT_SECRET_DEGERINIZ

# YENİ: Frontend Yönlendirme
FRONTEND_URL=http://localhost:8501
```

---

## Adım 3: GitHub Developer Settings'den Anahtar Almak

Yukarıdaki `.env` dosyasını doldurabilmek için kendi GitHub uygulamanızı (OAuth App) oluşturmalısınız:

1. **GitHub'a gidin:** Sağ üstten Profil > `Settings` > Sol alt köşeden `Developer settings` > `OAuth Apps` yolunu izleyin.
2. **Uygulama Oluşturun:** `New OAuth App` butonuna tıklayın.
3. **Formu Doldurun:**
   * **Application name:** `SprintBoard Local Dev` (veya dilediğiniz bir isim)
   * **Homepage URL:** `http://localhost:8000`
   * **Authorization callback URL:** **`http://127.0.0.1:8000/api/v1/auth/github/callback`** veya **`http://localhost:8000/api/v1/auth/github/callback`** *(Kendi backend URL'niz neyse o portu kullanın, genelde localhost:8000'dir)*
4. **Kaydedin ve Secret Üretin:** 
   * `Register application` deyin.
   * Çıkan ekranda **Client ID** değerini kopyalayıp `.env` içindeki `GITHUB_CLIENT_ID` alanına yapıştırın.
   * **Generate a new client secret** butonuna basarak gizli anahtarı kopyalayın ve `.env` içindeki `GITHUB_CLIENT_SECRET` alanına yapıştırın.

---

## Adım 4: Sistemi Test Etmek (Swagger Üzerinden)

Her şeyi doğru kurduğunuzu kontrol etmek için hızlıca API testi yapabilirsiniz:

1. Uvicorn sunucusunu başlatın:
   ```bash
   uvicorn app.main:app --reload
   ```
2. Tarayıcınızı açın ve [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) adresine gidin.
3. **Auth** sekmesi altındaki `GET /api/v1/auth/github/login` endpoint'ini bulun.
4. `Try it out` diyerek çalıştırın (`Execute`).
5. Dönen yanıtta bulunan (Responses alanındaki) URL kısmına tıklayın. Sistem sizi GitHub ekranına yönlendirmelidir. Yetki verdiğinizde işlemler arka planda tamamlanacak ve token oluşturulacaktır.
6. (Eğer frontend yönlendirmesi aktifse, `http://localhost:8501` adresine token ile otomatik yönlenecektir. Sadece backend testi için bu kısımda Swagger Response Headers ve URL değişimlerini izleyebilirsiniz).

Tebrikler, tüm geliştirme ortamınız artık GitHub Login özelliğiyle kullanıma hazır!
