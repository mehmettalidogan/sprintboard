# Sprint 1 — Veritabanı Kurulumu ve Kullanıcı Sistemi

Bu doküman, Sprint 1 kapsamında veritabanı altyapısının nasıl kurulduğunu, hangi kararların alındığını ve sistemin mevcut durumunu özetler.

---

## Sprint Hedefi

SQLAlchemy + PostgreSQL altyapısını ayağa kaldırmak, kullanıcı kayıt/giriş sistemini oluşturmak ve sprint analiz sonuçlarını veritabanına kalıcı olarak kaydetmek.

---

## Teknoloji Seçimi

| Bileşen | Seçim | Neden |
|---------|-------|-------|
| Veritabanı | PostgreSQL 15 | Prodüksiyon uyumlu, ARRAY/UUID gibi gelişmiş tipler |
| ORM | SQLAlchemy 2.0 (async) | Tip güvenliği, async-native, modern API |
| Async sürücü | asyncpg | PostgreSQL için en hızlı async Python sürücüsü |
| Migration | Alembic | SQLAlchemy ile entegre, versiyon kontrollü şema yönetimi |
| Çalıştırma | Docker Compose | PostgreSQL'i yerel kurulum gerektirmeden çalıştırır |

---

## Veritabanı Şeması

### `users` tablosu
Kullanıcı hesaplarını tutar. Şifre asla düz metin saklanmaz, bcrypt ile hashlenir.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | UUID | Primary key |
| `email` | VARCHAR(255) | Benzersiz, giriş kimliği |
| `full_name` | VARCHAR(255) | İsteğe bağlı görünen ad |
| `hashed_password` | VARCHAR(255) | bcrypt hash |
| `is_active` | BOOLEAN | Devre dışı kullanıcılar giriş yapamaz |
| `is_superuser` | BOOLEAN | Admin erişimi |
| `created_at` | TIMESTAMPTZ | Kayıt tarihi |
| `updated_at` | TIMESTAMPTZ | Son güncelleme |

### `sprints` tablosu
Her sprint analizi oturumunu temsil eder. Kullanıcıya bağlıdır.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | UUID | Primary key |
| `user_id` | UUID (FK) | Sahibi — `users.id` |
| `github_url` | VARCHAR(512) | Analiz edilen repo URL'si |
| `start_date` | DATE | Sprint başlangıç tarihi |
| `end_date` | DATE | Sprint bitiş tarihi |
| `team_members` | ARRAY(TEXT) | Takım üyelerinin GitHub kullanıcı adları |
| `country_code` | VARCHAR(2) | Tatil takvimi için ülke kodu (örn. TR) |
| `performance_score` | FLOAT | 0–100 performans skoru |
| `workload_balance_score` | FLOAT | 0–100 iş yükü denge skoru |
| `total_working_days` | INTEGER | Hafta sonu ve tatiller çıkarılmış çalışma günü |
| `analysis_notes` | TEXT | İnsan okunabilir analiz özeti |
| `created_at` | TIMESTAMPTZ | Analiz tarihi |
| `updated_at` | TIMESTAMPTZ | Son güncelleme |
| `deleted_at` | TIMESTAMPTZ | Soft delete — NULL ise aktif, dolu ise silinmiş |

### `sprint_member_performances` tablosu
Her sprint için üye bazlı performans detaylarını saklar.

| Kolon | Tip | Açıklama |
|-------|-----|----------|
| `id` | UUID | Primary key |
| `sprint_id` | UUID (FK) | Ait olduğu sprint — `sprints.id` |
| `github_login` | VARCHAR(255) | Takım üyesinin GitHub kullanıcı adı |
| `total_commits` | INTEGER | Sprint boyunca toplam commit sayısı |
| `total_additions` | INTEGER | Eklenen toplam satır sayısı |
| `total_deletions` | INTEGER | Silinen toplam satır sayısı |
| `active_days` | INTEGER | Commit yapılan farklı gün sayısı |
| `workload_share` | FLOAT | Toplam commit içindeki pay (0–1) |
| `created_at` | TIMESTAMPTZ | Kayıt tarihi |

---

## Migration Geçmişi

| # | Revision | Açıklama |
|---|----------|----------|
| 1 | `99d299276cf8` | `users` ve `sprints` tablolarını oluştur |
| 2 | `333e874b0ca5` | `sprints` tablosuna `user_id` ve `total_working_days` ekle |
| 3 | `2351b195bdc5` | `sprint_member_performances` tablosunu oluştur |
| 4 | `67ab13989207` | `sprints` tablosuna `deleted_at` (soft delete) ekle |

---

## API Endpoint'leri

### Auth

| Method | URL | Açıklama |
|--------|-----|----------|
| `POST` | `/api/v1/auth/register` | Yeni kullanıcı kaydı, JWT token döner |
| `POST` | `/api/v1/auth/login` | Giriş, JWT token döner |
| `GET` | `/api/v1/auth/me` | Giriş yapan kullanıcının profili |

### Sprints

| Method | URL | Açıklama |
|--------|-----|----------|
| `POST` | `/api/v1/sprints/analyze` | Sprint analizi yap ve DB'ye kaydet |
| `GET` | `/api/v1/sprints/` | Kullanıcının geçmiş analizleri |
| `DELETE` | `/api/v1/sprints/{id}` | Sprint'i soft delete ile sil |

---

## Yeni Dosyalar

```
backend/
├── alembic/                          ← Yeni — migration sistemi
│   ├── env.py
│   ├── versions/
│   │   ├── 99d299276cf8_initial_tables.py
│   │   ├── 333e874b0ca5_add_user_id_and_working_days.py
│   │   ├── 2351b195bdc5_add_sprint_member_performances.py
│   │   └── 67ab13989207_add_soft_delete_to_sprints.py
│   └── alembic.ini
├── app/
│   ├── models/
│   │   └── sprint_member_performance.py  ← Yeni
│   ├── schemas/
│   │   └── user.py                       ← Yeni
│   ├── services/
│   │   ├── user_service.py               ← Yeni
│   │   └── sprint_service.py             ← Yeni
│   └── api/v1/endpoints/
│       └── auth.py                       ← Yeni
└── .env                                  ← Yeni (git'te yok)
```

---

## Çalıştırma

```powershell
# 1. PostgreSQL başlat (Docker)
cd backend
docker compose up -d db

# 2. Bağımlılıkları kur
pip install -r requirements.txt

# 3. Migration uygula
python -m alembic upgrade head

# 4. Backend başlat
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Soft Delete Nedir?

Sprint silindiğinde fiziksel olarak veritabanından kaldırılmaz. Bunun yerine `deleted_at` kolonu doldurulur. `GET /sprints/` sorgusu `deleted_at IS NULL` filtresi uygular, dolayısıyla kullanıcı silinen kaydı görmez. Bu yaklaşım:

- Veri kaybını önler
- Geri alma imkânı sağlar
- Audit trail (iz takibi) için temel oluşturur

---

## Sonraki Adımlar (Sprint 2)

- [ ] Kullanıcı başına GitHub token desteği (rate limit yönetimi)
- [ ] Sprint geçmişini frontend'de gösterme
- [ ] Silinen sprint'leri geri alma endpoint'i
- [ ] Analiz sonuçlarının önbelleğe alınması (aynı repo + tarih aralığı tekrar sorgulanmasın)
- [ ] Pytest ile unit ve integration testleri
