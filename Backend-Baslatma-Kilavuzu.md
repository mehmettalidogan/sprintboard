# SprintBoard AI - Backend Başlatma Kılavuzu

Bu kılavuz, projenizin backend (API) ve veritabanı (PostgreSQL) kısımlarını Docker üzerinden kendi bilgisayarınızda nasıl ayağa kaldıracağınızı adım adım açıklamaktadır.

---

## 🏗️ Adım 1: Terminal veya VS Code'u Hazırlamak

1. VS Code içerisinde projeyi (Sprint Board) açın.
2. Üst menüden **Terminal > New Terminal** seçeneğine tıklayarak veya `Ctrl + ~` (veya `Ctrl + "`) kısayolunu kullanarak yeni bir terminal başlatın.
3. Arka uç işlemlerini uygulayacağımız `backend` klasörüne geçiş yapın. Terminale şu komutu yazın ve `Enter`'a basın:
   ```bash
   cd backend
   ```

---

## 🕵️‍♂️ Adım 2: Çevresel (Environment) Değişkenleri Ayarlamak

Sistemin düzgün çalışabilmesi için bir `.env` dosyasına ihtiyacı vardır. 
*Eğer daha önceden bir `.env` dosyanız var ve içi doluysa bu adımı atlayabilirsiniz.*

1. `backend` klasörü içinde bulunan **`.env.example`** dosyasının adını sadece **`.env`** olarak değiştirin (veya `.env.example` içeriğini kopyalayıp yeni bir `.env` dosyası oluşturun).
2. Dosyayı açın ve içerisinde bulunan **GitHub Token** alanını güncelleyin:
   ```env
   # 26. Satır civarında bulunan bu yeri:
   GITHUB_TOKEN=ghp_your_github_personal_access_token_here

   # Kendinize ait olan ve GitHub üzerinden oluşturduğunuz token ile değiştirin. 
   # Örnek:
   GITHUB_TOKEN=ghp_ABCXyz123...
   ```
*(Bu adım, uygulamanın GitHub üzerindeki sprint verilerini çekebilmesi için zorunludur.)*

---

## 🐳 Adım 3: Docker Kurulumu ve Başlatılması

Kurulumun bu aşamasında bilgisayarınızda **Docker Desktop**'ın arkada açık ve çalışır durumda olduğundan ("Engine Running" yeşil ikonu) emin olmalısınız.

1. Terminaliniz halen `backend` klasörünün içerisindeyken şu komutu çalıştırın:
   ```bash
   docker compose up --build
   ```
2. Bu komut ilk çalıştırıldığında gerekli veritabanı (Postgres) imajlarını indirecek ve Python uygulamanızın gereksinimlerini kuracaktır. (Bu işlem birkaç dakika sürebilir).

---

## ✅ Adım 4: Sistemin Çalıştığını Doğrulamak

Terminal pencerenizde aşağıdaki gibi yeşil yazılar görüyorsanız sistem başarıyla başlamış demektir:
```text
🚀 SprintBoard AI v0.1.0 started.
INFO:     Application startup complete.
```
> **İpucu:** Komut satırına bir daha yazı yazamayacaksınız çünkü log (kayıt) ekranındasınız. Bu normaldir ve sunucunun çalıştığı anlamına gelir. Sunucuyu durdurmak için `Ctrl + C` tuşlarına basabilirsiniz.

---

## 🚀 Adım 5: Swagger Arayüzüne (API Test Ekranı) Bağlanmak

Sistem çalışmaya başladığında oluşturulan tüm veri noktalarına (endpoint'ler) görsel bir arayüzden erişebilirsiniz.

1. İnternet tarayıcınızı (Chrome, Edge, Safari vb.) açın.
2. Adres çubuğuna şunu yazıp `Enter`'a basın:
   [http://localhost:8000/docs](http://localhost:8000/docs)
3. Karşınıza **Swagger UI** gelecektir. Bu ekran üzerinden uygulamanın sağlık durumunu kontrol edebilir (`/health`) veya hazırladığınız API hizmetlerini test edebilirsiniz.
