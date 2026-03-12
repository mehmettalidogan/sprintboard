# Sprint 1 - Setup / Creating User Interface

Bu doküman, frontend tarafında Sprint 1 kapsamında neyin bittiğini ve neyin kaldığını herkesin anlayacağı şekilde özetler.

## Sprint 1 hedefi

Backend'e dokunmadan, modern görünümlü ve kullanımı net bir frontend temelini kurmak.

## Altın Kural

- Backend kodu, endpoint yapısı ve iş mantığı değiştirilmeyecek.
- Frontend sadece mevcut API'leri kullanacak.
- Hata durumlarında frontend kullanıcıya net mesaj verecek, ama backend davranışını değiştirmeyecek.

## Şu an tamamlananlar

- `frontend/` klasör yapısı oluşturuldu.
- Streamlit + Plotly + Requests + Pandas kuruldu.
- Tema dosyası oluşturuldu (`.streamlit/config.toml`).
- Global stil ve marka dili tanımlandı:
  - Ana renk: `#0F172A`
  - Vurgu: `#3B82F6` / `#06B6D4`
  - Başarı: `#10B981`
  - Risk: `#EF4444`
  - Arka plan: `#F8FAFC`
- Font yaklaşımı uygulandı:
  - Arayüz: Plus Jakarta Sans
  - Sayısal metrikler: JetBrains Mono
- API istemcisi yazıldı (`frontend/utils/api_client.py`).
- Grafik bileşenleri yazıldı (`frontend/components/charts.py`).
- Ana sayfa yazıldı (`frontend/app.py`):
  - Form alanları
  - Analizi tetikleme
  - Sonuç metrikleri
  - Plotly grafikler
  - Tablo görünümü

## Sprint 1 içinde kalan işler

## 1) Ana sayfa UX sertleştirme

- 502, timeout, hatalı URL gibi durumlar için kullanıcı dostu hata mesajları.
- Boş state metinlerini sadeleştirme.
- Input doğrulamalarını daha açıklayıcı hale getirme.

Beklenen çıktı:
- Kullanıcı teknik hata metni görmeden ne yapacağını anlayabilmeli.

## 2) Sayfa yapısını ölçeklenebilir hale getirme

- `pages/` altında ikinci ekran için temel navigasyon hazırlığı.
- Sidebar içeriğinin bilgi mimarisi olarak düzenlenmesi.

Beklenen çıktı:
- Uygulama tek sayfadan çok sayfalı yapıya hazır olmalı.

## 3) GitHub İçgörüleri sayfası (Sprint 1 sonu veya Sprint 2 başı)

- Ayrı bir sayfada commit trendleri, contributor karşılaştırması.
- `api/v1/github/analyze` veya `api/v1/github/commits` verilerinin görselleştirilmesi.

Beklenen çıktı:
- Ana sprint skoru ekranından bağımsız bir "GitHub Insights" görünümü.

## 4) Görsel kalite (polish)

- Kart boşlukları, tipografi dengesi, buton durumları (hover/active).
- Responsive davranışın iyileştirilmesi (özellikle dar ekranlar).

Beklenen çıktı:
- Yapay ve "template" hissi vermeyen, gerçek ürün kalitesine yakın arayüz.

## 5) Çalıştırma ve teslim standardı

- Çalıştırma adımlarını kısa bir README'e yazmak.
- Frontend için tek komutla ayağa kalkma netleştirmek:
  - `python -m streamlit run app.py`

Beklenen çıktı:
- Projeyi alan bir kişi 2-3 komutta UI'ı açabilmeli.

## Sprint 1 DoD (Definition of Done)

Sprint 1 "bitti" sayılması için:

- Ana sayfa hatasız açılıyor olmalı.
- Formdan gelen veri backend'e doğru formatta gidiyor olmalı.
- Sonuç metrikleri ve grafikler doğru render edilmeli.
- Hata durumlarında kullanıcı yönlendirici mesaj görmeli.
- Kod yapısı ikinci sayfayı eklemeye hazır olmalı.

## Teknik notlar

- `streamlit` komutu PATH'te görünmüyorsa aşağıdaki komut kullanılmalı:
  - `python -m streamlit run app.py`
- Backend kapalıysa analiz çağrıları doğal olarak başarısız olur.
- 502 hatası genelde upstream (GitHub API/token/ağ) kaynaklıdır; frontend kaynaklı değildir.

## Önerilen bir sonraki adım

Sprint 1'i tamamlamak için ilk iş:

1. Ana sayfada hata/boş durum UX iyileştirmelerini bitir.
2. Sonra `pages/` altında GitHub İçgörüleri sayfasını ekle.
3. En son kısa bir frontend README yaz ve Sprint 1'i kapat.
