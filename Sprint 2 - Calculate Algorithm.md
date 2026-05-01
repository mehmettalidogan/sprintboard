# Sprint 2 — Risk Skoru Hesaplama Algoritması
# Sprint 2 — Risk Score Calculation Algorithm

---

## 🇹🇷 Türkçe

### Genel Bakış

Bu sprint kapsamında, SprintBoard AI projesine **Pandas tabanlı Risk Skoru Hesaplama Motoru** eklenmiştir. Motor; iş dağılımındaki dengesizlikleri, sprint zamanlamalarını ve olası gecikmeleri hesaba katarak hem **proje bazlı** hem de **kişi bazlı** risk skorları üretmektedir.

---

### Mimari Karar: Neden Ayrı Bir Sınıf?

Önceki `ProjectService.calculate_risk_score()` metodu hem veritabanı sorgusunu hem de hesaplama mantığını aynı yerde barındırıyordu. Sprint 2'de hesaplama mantığı tamamen bağımsız bir sınıfa (`RiskCalculator`) taşındı.

**Sağlanan faydalar:**
- Veritabanı olmadan test edilebilir (29 birim testi geçiyor)
- Yeni risk boyutları eklemek için mevcut kodu değiştirmeye gerek yok
- Her katmanın tek bir sorumluluğu var

---

### SOLID Prensipleri Uygulaması

| Prensip | Uygulama |
|---------|----------|
| **S — Single Responsibility** | `RiskCalculator` yalnızca risk hesaplar. DB erişimi `ProjectService`'te, HTTP katmanı `projects.py`'da kalır. |
| **O — Open/Closed** | Yeni bir risk boyutu eklemek için yalnızca yeni bir `_score_*` metodu yazılır ve `calculate_project_risk()` içinde çağrılır. Mevcut metodlar değişmez. |
| **L — Liskov Substitution** | Dışa açık kalıtım zinciri bulunmadığından doğrudan uygulanmaz. |
| **I — Interface Segregation** | Dar ve odaklı genel API: `load()` / `calculate_project_risk()` / `calculate_member_risks()` / `get_sprint_timing_risk()` |
| **D — Dependency Inversion** | `RiskCalculator`, ORM modelleri yerine soyut `pd.DataFrame`'e bağımlıdır. Herhangi bir veri kaynağından beslenebilir. |

---

### DRY Prensibi Uygulaması

| Tekrar Önleme | Açıklama |
|---------------|----------|
| `_to_risk_level(score)` | Eşik sabitleri tek bir yerde tanımlanır; hem proje hem üye skoru bu fonksiyonu çağırır. |
| `_urgency(deadline, today)` | Aciliyet hesabı tek bir modül düzeyi fonksiyonda toplandı; tüm hesaplama yolları bunu kullanır. |
| `_gini(values)` | Gini katsayısı yalnızca bir kez tanımlanmıştır. |
| `_WEIGHT_*` sabitleri | Ağırlıklar tek bir satırda tanımlıdır; değiştirilmesi tüm hesaplamalara otomatik yansır. |

---

### Algoritma Bileşenleri

#### 1. Proje Risk Skoru (0–100)

Üç bileşenin ağırlıklı toplamıdır:

```
Proje Risk = incomplete_ratio_score + deadline_risk_score + workload_risk_score
```

| Bileşen | Ağırlık | Formül |
|---------|---------|--------|
| **Tamamlanmamış Görev Oranı** | 40 puan | `(tamamlanmamış / toplam) × 40` |
| **Son Tarih Aciliyeti** | 40 puan | `ortalama_aciliyet × 40` |
| **İş Yükü Dengesizliği (Gini)** | 20 puan | `gini_katsayısı × 20` |

**Toplam maksimum: 100 puan** (aşarsa 100'e sabitlenir)

#### 2. Aciliyet Fonksiyonu

```
_urgency(deadline, today):
  eğer son_tarih yoksa      → 0.5   (belirsizlik riski)
  eğer days_left ≤ 0        → 1.0   (vadesi geçmiş, maksimum)
  eğer days_left > 14       → 0.0   (acil değil)
  aksi hâlde               → (14 - days_left) / 14   (doğrusal interpolasyon)
```

#### 3. Gini Katsayısı (İş Yükü Dengesizliği)

Gini = 0 → tüm takım üyelerine eşit dağılım → minimum iş yükü riski  
Gini → 1 → tüm görevler tek kişide → maksimum iş yükü riski

```
G = (2 × Σ[(i+1) × v_i]) / (n × Σv_i) − (n+1)/n
```
*(v_i: artan sıraya göre sıralanmış kişi başına görev sayısı)*

#### 4. Sprint Zamanlama Riski

```
elapsed_ratio    = geçen_gün / toplam_sprint_günü
completion_rate  = tamamlanan_görev / toplam_görev
progress_gap     = completion_rate − elapsed_ratio

eğer progress_gap ≥ 0  → timing_risk = 0     (plana uygun veya ileride)
aksi hâlde             → timing_risk = min(|progress_gap| × 100, 100)
```

#### 5. Kişi Bazlı Risk Skoru (0–60)

```
Kişi Risk = deadline_risk_score (0–40) + workload_score (0–20)
```

> **Not:** Kişi risk formülünde tamamlanmamış oran bileşeni bulunmadığından üye skorunun matematiksel maksimumu **60**'tır. Bu nedenle bireysel risk seviyesi en fazla **Medium** olabilir.

---

### Risk Seviyeleri

| Skor | Seviye |
|------|--------|
| 0 – 29.99 | 🟢 Low (Düşük) |
| 30 – 69.99 | 🟡 Medium (Orta) |
| 70 – 100 | 🔴 High (Yüksek) |

---

### Yeni API Uç Noktaları

| Yöntem | URL | Açıklama |
|--------|-----|----------|
| `GET` | `/api/v1/projects/{id}/risk-score` | Proje bazlı risk skoru *(Sprint 1'den bu yana var, Sprint 2'de güncellendi)* |
| `GET` | `/api/v1/projects/{id}/member-risk-scores` | Kişi bazlı risk skorları *(Sprint 2'de eklendi)* |

---

### Test Sonuçları

```
29 birim testi — 29 GEÇTI, 0 BAŞARISIZ
```

Kapsanan senaryolar:
- Boş veri → sıfırlanmış Low sonuç
- Tüm görevler tamamlandı → Low risk
- Yüksek iş yükü + vadesi geçmiş görevler → High risk
- Dengeli iş yükü (Gini ≈ 0) → düşük iş yükü riski
- Dengesiz iş yükü (Gini > 0) → artan iş yükü riski
- Sprint plandan geride → yüksek zamanlama riski
- Sprint plandan ileride → sıfır zamanlama riski
- Üye bazlı risk doğrulaması (maksimum skor = 60)
- `_gini`, `_urgency`, `_to_risk_level` yardımcıları için sınır değer testleri

---

### Dosya Yapısı

```
backend/
├── app/
│   ├── services/
│   │   ├── risk_calculator.py        ← YENİ: Saf pandas hesaplama motoru
│   │   └── project_service.py        ← GÜNCELLENDİ: RiskCalculator'a delege ediyor
│   ├── schemas/
│   │   └── project_analysis.py       ← GÜNCELLENDİ: MemberRiskScore eklendi
│   └── api/v1/endpoints/
│       └── projects.py               ← GÜNCELLENDİ: /member-risk-scores uç noktası
└── tests/
    └── test_risk_calculator.py       ← YENİ: 29 birim testi
```

---

---

## 🇬🇧 English

### Overview

In this sprint, a **Pandas-based Risk Score Calculation Engine** was added to SprintBoard AI. The engine accounts for work distribution imbalances, sprint timings, and potential delays to produce both **project-level** and **per-member** risk scores.

---

### Architectural Decision: Why a Separate Class?

The previous `ProjectService.calculate_risk_score()` method combined database queries and calculation logic in the same place. In Sprint 2, the computation logic was moved entirely to an independent class (`RiskCalculator`).

**Benefits:**
- Testable without a database (29 unit tests pass)
- New risk dimensions can be added without modifying existing code
- Each layer has a single responsibility

---

### SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S — Single Responsibility** | `RiskCalculator` only calculates risk. DB access stays in `ProjectService`, HTTP layer in `projects.py`. |
| **O — Open/Closed** | Adding a new risk dimension requires only a new `_score_*` method called from `calculate_project_risk()`. Existing methods remain unchanged. |
| **L — Liskov Substitution** | No public inheritance chain is exposed; not directly applicable. |
| **I — Interface Segregation** | Thin, focused public API: `load()` / `calculate_project_risk()` / `calculate_member_risks()` / `get_sprint_timing_risk()` |
| **D — Dependency Inversion** | `RiskCalculator` depends on abstract `pd.DataFrame`, not on ORM models. Can be fed from any data source. |

---

### DRY Principle Applied

| Deduplication | Description |
|---------------|-------------|
| `_to_risk_level(score)` | Threshold constants defined once; both project and member scoring call this function. |
| `_urgency(deadline, today)` | Urgency calculation consolidated into one module-level function; all scoring paths use it. |
| `_gini(values)` | Gini coefficient defined exactly once. |
| `_WEIGHT_*` constants | Weights defined in one line; changing them automatically affects all calculations. |

---

### Algorithm Components

#### 1. Project Risk Score (0–100)

A weighted sum of three components:

```
Project Risk = incomplete_ratio_score + deadline_risk_score + workload_risk_score
```

| Component | Weight | Formula |
|-----------|--------|---------|
| **Incomplete Task Ratio** | 40 pts | `(incomplete / total) × 40` |
| **Deadline Urgency** | 40 pts | `mean_urgency × 40` |
| **Workload Imbalance (Gini)** | 20 pts | `gini_coefficient × 20` |

**Total maximum: 100 points** (capped if exceeded)

#### 2. Urgency Function

```
_urgency(deadline, today):
  if no deadline            → 0.5   (uncertainty risk)
  if days_left ≤ 0          → 1.0   (overdue, maximum)
  if days_left > 14         → 0.0   (not urgent)
  otherwise                 → (14 - days_left) / 14   (linear interpolation)
```

#### 3. Gini Coefficient (Workload Imbalance)

Gini = 0 → equal distribution across all team members → minimum workload risk  
Gini → 1 → all tasks on one person → maximum workload risk

```
G = (2 × Σ[(i+1) × v_i]) / (n × Σv_i) − (n+1)/n
```
*(v_i: task counts per person sorted in ascending order)*

#### 4. Sprint Timing Risk

```
elapsed_ratio    = elapsed_days / total_sprint_days
completion_rate  = completed_tasks / total_tasks
progress_gap     = completion_rate − elapsed_ratio

if progress_gap ≥ 0   → timing_risk = 0     (on track or ahead)
otherwise             → timing_risk = min(|progress_gap| × 100, 100)
```

#### 5. Per-Member Risk Score (0–60)

```
Member Risk = deadline_risk_score (0–40) + workload_score (0–20)
```

> **Note:** Since the member risk formula does not include an incomplete ratio component, the mathematical maximum for a member score is **60**. Therefore individual risk level tops out at **Medium**.

---

### Risk Levels

| Score | Level |
|-------|-------|
| 0 – 29.99 | 🟢 Low |
| 30 – 69.99 | 🟡 Medium |
| 70 – 100 | 🔴 High |

---

### New API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/v1/projects/{id}/risk-score` | Project-level risk score *(existed since Sprint 1, updated in Sprint 2)* |
| `GET` | `/api/v1/projects/{id}/member-risk-scores` | Per-member risk scores *(added in Sprint 2)* |

---

### Test Results

```
29 unit tests — 29 PASSED, 0 FAILED
```

Scenarios covered:
- Empty data → zeroed Low result
- All tasks completed → Low risk
- High workload + overdue tasks → High risk
- Balanced workload (Gini ≈ 0) → minimal workload risk
- Skewed workload (Gini > 0) → elevated workload risk
- Sprint behind schedule → high timing risk
- Sprint ahead of schedule → zero timing risk
- Per-member risk validation (max score = 60)
- Edge-case tests for `_gini`, `_urgency`, `_to_risk_level` helpers

---

### File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── risk_calculator.py        ← NEW: Pure pandas computation engine
│   │   └── project_service.py        ← UPDATED: Delegates to RiskCalculator
│   ├── schemas/
│   │   └── project_analysis.py       ← UPDATED: MemberRiskScore added
│   └── api/v1/endpoints/
│       └── projects.py               ← UPDATED: /member-risk-scores endpoint
└── tests/
    └── test_risk_calculator.py       ← NEW: 29 unit tests
```
