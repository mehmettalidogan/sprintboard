# SprintBoard Backend Değişiklikleri: GitHub OAuth2 Entegrasyonu

Bu döküman, SprintBoard projesine entegre edilen "GitHub ile Tek Tıkla Giriş / Kayıt" özelliğinin arka plandaki teknik detaylarını ve değiştirilen dosyaları özetlemektedir.

## 📁 Güncellenen ve Oluşturulan Dosyalar

GitHub OAuth akışının dahil edilebilmesi için backend mimarisinde aşağıdaki güncellemeler yapılmıştır:

*   **`app/api/v1/endpoints/auth.py`**
    *   `GET /github/login`: Kullanıcıyı GitHub'ın OAuth onay sayfasına (authorize) yönlendiren endpoint eklendi. Frontend, butona tıklandığında bu adresi çağırır.
    *   `GET /github/callback`: Kullanıcı GitHub'da onay verdikten sonra dönen `code` değerini yakalayan endpoint. `httpx` kullanılarak bu code GitHub'a gönderilir, karşılığında `access_token` ve profil bilgileri (isim, e-posta, kullanıcı adı) alınır. Ardından işlem başarıyla sonuçlanınca kullanıcı JWT token ile birlikte Streamlit frontend'ine geri yönlendirilir (`RedirectResponse`).

*   **`app/services/user_service.py`**
    *   `authenticate_via_github(email, full_name, github_username)` fonksiyonu eklendi. Tüm **Upsert** (Kayıt/Giriş) iş mantığı burada ele alınmaktadır.

*   **`app/core/config.py`**
    *   Sistemin konfigürasyonlarını yöneten `Settings` sınıfına `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` ve Streamlit tarafına yönlendirme yapabilmek için `FRONTEND_URL` tanımlamaları eklendi.

*   **`backend/.env`**
    *   Yeni eklenen değişkenlerin sistem tarafından okunabilmesi için environment dosyası güncellendi.

---

## ⚙️ Teknik İşleyiş: Upsert (Kayıt/Giriş Birleşik) Mantığı

Kullanıcı "GitHub ile Giriş Yap" butonuna tıkladıktan sonra, klasik bir "Kayıt Ol" ya da "Giriş Yap" ayrımı yapılmaz. Tüm süreç tek akışta (Upsert) arka planda otomatik yönetilir:

1.  **Kullanıcı Sorgulama:** 
    GitHub'dan başarılı bir şekilde e-posta ve kullanıcı adı verileri alındıktan sonra veritabanında `github_username` değerine sahip bir kullanıcı olup olmadığına bakılır.
2.  **Kullanıcı Varsa (Login):**
    Eğer kullanıcı veritabanında mevcutsa, ek bir işleme gerek kalmadan hesabı tespit edilir ve doğrudan oturum açması için JWT token üretilir.
3.  **Kullanıcı Yoksa (Register / Sign Up):**
    Eğer kullanıcı veritabanında **yoksa**, arka planda tamamen şeffaf bir kayıt işlemi başlatılır:
    *   Profil verilerinden bir User nesnesi oluşturulur.
    *   Sistem zorunlu şifre alanı için rastgele 16-32 karakter uzunluğunda son derece güvenli bir parola üretir ve kriptolayarak kaydeder.
    *   Profil `is_active=True` olarak doğrudan aktifleştirilir.
    *   Kayıt anında tamamlanır ve yeni üretilen bu kullanıcı hesabı için JWT token verilerek sisteme dahil edilir.

Bu sayede hem sistemde manuel kayıt sürtünmesi (friction) ortadan kaldırılmış hem de her durum tek fonksiyonla (`authenticate_via_github`) modüler şekilde kapsanmış olur.
