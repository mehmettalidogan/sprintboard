#  SprintBoard AI - Frontend (Sprint 1)

Bu depo, GitHub verilerini analiz eden ve takımlara sprint performansı hakkında içgörü sağlayan **SprintBoard AI** platformunun kullanıcı arayüzünü (frontend) içerir. 

Sprint 1 hedefi; backend'den bağımsız, modern görünümlü ve ölçeklenebilir bir temel kurmaktır.
1. UX Sertleştirme & Hata Yönetimi
Kullanıcıların teknik hata kodlarıyla (502, 404, Connection Refused vb.) kafasının karışmasını engelledik. Backend kapalı olsa bile kullanıcıya çözüm sunan (örneğin: "🔌 Sunucu Kapalı") açıklayıcı mesajlar ve emojiler ekledik.

2. Çok Sayfalı (Multi-Page) Yapı
Uygulamayı tek sayfaya tıkıştırmak yerine pages/ mimarisine geçtik. Bu sayede "GitHub İçgörüleri" gibi yeni ekranlar, sistem tarafından otomatik olarak sol menüye (sidebar) eklenir hale geldi.

3. Global Tasarım Dili (Style Injection)
components/styles.py içindeki inject_global_css() fonksiyonu ile tüm sayfalarda tutarlı bir marka dili oluşturduk.

Ana Renk: #0F172A (Koyu Lacivert Kurumsal Tema)
Vurgu: #3B82F6 / #06B6D4 (Enerjik Maviler)

Tipografi: Plus Jakarta Sans ve JetBrains Mono (Sayısal metrikler için)

4. Veri Görselleştirme
Plotly kullanarak interaktif üye katkı grafikleri ve performans gauge'ları oluşturduk. Bu grafikler backend'den gelen JSON verisine göre anlık olarak render edilmektedir.
## Hızlı Başlangıç

Arayüzü tek bir komutla yerel makinenizde çalıştırabilirsiniz:
-Giriş ekranını atlayıp direkt dashboard'u görmek isterseniz, app.py içindeki geçici geçiş anahtarı satırlarını aktif edebilirsiniz.

```bash
python -m streamlit run app.py
