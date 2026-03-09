# SprintBoard AI — Backend

## Genel Bakış

SprintBoard AI, GitHub verilerini analiz ederek sprint performansını ve iş yükü dengesini hesaplayan bir platformdur. Bu backend, **FastAPI** + **PostgreSQL** + **Docker** üzerine kurulu, async-first ve SOLID prensiplerine uygun bir mimariye sahiptir.

---

## Sprint 1 Kapsamında Yapılanlar

- **Proje İskeleti:** `app/api`, `app/core`, `app/models`, `app/schemas` ve `app/services` klasör yapısı oluşturuldu.
- **Konfigürasyon (Core):** `pydantic-settings` ile `.env` dosyasından değişkenleri okuyan merkezi bir `config.py` ve JWT/Bcrypt işlemleri için `security.py` eklendi.
- **Veritabanı (PostgreSQL):** SQLAlchemy 2.0 kullanılarak asenkron PostgreSQL bağlantısı (`database.py`) yapıldı.
- **Modeller ve Şemalar:** 
  - ORM modelleri olarak `Sprint` ve `User` yazıldı. 
  - API veri doğrulama işlemleri için Pydantic şemaları (`sprint.py`, `github.py`, `common.py`) oluşturuldu.
- **Servis Katmanı (İş Mantığı):** 
  - **`GitHubService`**: `httpx` üzerinden asenkron olarak GitHub REST API'den commit geçmişi ve katkıcı istatistiklerini çeken sınıf tasarlandı.
  - **`HolidayService`**: Nager.Date genel tatil API'sine bağlanılarak çalışma günlerini doğru hesaplamak üzere bir servis oluşturuldu.
  - **`AnalysisService`**: Verileri derleyip Sprint'in iş yükü dengesini (Gini katsayısı kullanılarak) ve performans skorunu hesaplayan asıl analiz motoru kodlandı.
- **API (Controller):** Temel analizleri başlatan `/api/v1/sprints/analyze` ve repo verilerini getiren `/api/v1/github/analyze` uç noktaları eklendi.
- **Docker & CI/CD Altyapısı:** Uygulamayı kolayca ayağa kaldırmak için `Multi-stage Dockerfile` ile `docker-compose.yml` dosyası yazıldı.

---

## Klasör Yapısı

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependency injection (DB, auth, servisler)
│   │   └── v1/
│   │       ├── router.py        # Tüm v1 router'larını birleştirir
│   │       └── endpoints/
│   │           ├── sprints.py   # POST /api/v1/sprints/analyze
│   │           └── github.py    # POST /api/v1/github/analyze
│   ├── core/
│   │   ├── config.py            # pydantic-settings ile .env okuma
│   │   └── security.py         # JWT oluşturma/doğrulama, bcrypt
│   ├── models/
│   │   ├── sprint.py            # Sprint SQLAlchemy ORM modeli
│   │   └── user.py              # User SQLAlchemy ORM modeli
│   ├── schemas/
│   │   ├── common.py            # HealthResponse, ErrorResponse, PaginatedResponse
│   │   ├── github.py            # GitHubAnalysisRequest/Response, CommitData
│   │   └── sprint.py            # SprintCreate, SprintResponse, MemberPerformance
│   ├── services/
│   │   ├── github_service.py   # GitHubService — async httpx istemcisi
│   │   ├── holiday_service.py  # HolidayService — Nager.Date API entegrasyonu
│   │   └── analysis_service.py # AnalysisService — Gini & velocity skorlama
│   ├── database.py              # Async SQLAlchemy engine + get_db dependency
│   └── main.py                  # FastAPI app factory, lifespan, CORS, /health
├── .env.example                 # Çevre değişkeni şablonu
├── requirements.txt             # Pinned bağımlılıklar
├── Dockerfile                   # Multi-stage production build
└── docker-compose.yml           # FastAPI + PostgreSQL 15 servisleri
```

---

## Mimari Kararlar

| Konu | Karar | Neden |
|------|-------|-------|
| Web framework | FastAPI | Async-native, otomatik OpenAPI, tip doğrulama |
| HTTP client | httpx (async) | GitHub & Holiday API çağrıları için non-blocking |
| ORM | SQLAlchemy 2 async | Modern async query desteği, tip güvenliği |
| Config | pydantic-settings | `.env` → Python nesnesi, tek import ile erişim |
| Auth | JWT (python-jose) + bcrypt | Stateless, ölçeklenebilir, endüstri standardı |
| Skor: iş dengesi | Gini katsayısı | Commit dağılımındaki eşitsizliği 0–100 arası ölçer |
| Skor: performans | Velocity + Consistency + Churn | Üç boyutlu, ağırlıklı formül |

---

## Kurulum ve Çalıştırma

### 1. Çevre Değişkenleri

```powershell
cd backend
Copy-Item .env.example .env
# .env dosyasını açıp SECRET_KEY ve GITHUB_TOKEN değerlerini doldur
```

### 2. Docker ile Başlatma (Önerilen)

```powershell
docker compose up --build
```

| URL | Açıklama |
|-----|----------|
| `http://localhost:8000/docs` | Swagger UI (interaktif API docs) |
| `http://localhost:8000/redoc` | ReDoc API docs |
| `http://localhost:8000/health` | Liveness probe |

### 3. Lokal Geliştirme (Docker olmadan)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## Örnek API İstekleri

### Sprint Analizi Başlat

```http
POST /api/v1/sprints/analyze
Content-Type: application/json

{
  "github_url": "https://github.com/myorg/my-project",
  "start_date": "2025-01-06",
  "end_date": "2025-01-17",
  "team_members": ["alice", "bob", "charlie"],
  "country_code": "TR"
}
```

### GitHub Repo Analizi

```http
POST /api/v1/github/analyze
Content-Type: application/json

{
  "github_url": "https://github.com/myorg/my-project",
  "branch": "main"
}
```

---

## Sonraki Adımlar (Sprint 2+)

- [ ] Alembic migrations (`alembic init`, ilk migration)
- [ ] Kullanıcı kayıt & giriş endpoint'leri (`/auth/register`, `/auth/login`)
- [ ] Sprint sonuçlarını DB'ye kaydetme (şu an sadece response olarak dönüyor)
- [ ] Background task desteği (analiz uzunsa Celery / ARQ ile async kuyruk)
- [ ] Rate limiting middleware (slowapi)
- [ ] Unit & integration testleri (pytest-asyncio)