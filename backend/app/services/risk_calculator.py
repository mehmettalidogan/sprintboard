"""
Risk Calculator — Sprint 2 Deliverable.

Pandas tabanlı, saf veri-odaklı risk hesaplama motoru.
Pure pandas-based, database-agnostic risk calculation engine.

──────────────────────────────────────────────────────────────
SOLID Uyumu / SOLID Compliance
──────────────────────────────────────────────────────────────
  S — Single Responsibility:
        Bu sınıfın tek sorumluluğu risk skorlarını hesaplamaktır.
        DB erişimi, HTTP çağrıları ve kimlik doğrulama başka katmanlarda kalır.
        This class is solely responsible for computing risk scores.
        DB access, HTTP calls, and auth live in other layers.

  O — Open/Closed:
        Yeni bir risk boyutu eklemek için yalnızca yeni bir `_score_*`
        metodu yazıp `calculate_project_risk` içinde çağırmak yeterlidir;
        mevcut metodları değiştirmeye gerek kalmaz.
        Adding a new risk dimension requires only a new `_score_*` method
        called from `calculate_project_risk` — no existing methods change.

  L — Liskov Substitution:
        Dışa açık bir kalıtım zinciri bulunmadığından bu ilke burada
        doğrudan uygulanmaz.
        No public inheritance chain is exposed; not directly applicable.

  I — Interface Segregation:
        Dar ve odaklı genel API: load() / calculate_project_risk() /
        calculate_member_risks() / get_sprint_timing_risk().
        Thin, focused public API: load() / calculate_project_risk() /
        calculate_member_risks() / get_sprint_timing_risk().

  D — Dependency Inversion:
        Sınıf, ORM modelleri yerine soyut pd.DataFrame'e bağımlıdır;
        bu sayede herhangi bir veri kaynağından beslenerek test edilebilir.
        The class depends on abstract pd.DataFrame, not on ORM models,
        allowing it to be tested with any data source.

──────────────────────────────────────────────────────────────
DRY Uyumu / DRY Compliance
──────────────────────────────────────────────────────────────
  - Eşik sabitleri (_THRESHOLD_LOW, _THRESHOLD_HIGH) tek yerde tanımlanır;
    hem proje hem üye skorlamasında yeniden kullanılır.
    Threshold constants defined once and reused across project + member scoring.

  - _urgency() ve _to_risk_level() saf (pure) modül-düzeyi fonksiyonlar
    olarak tanımlanmıştır; tüm hesaplayıcılar bu fonksiyonları çağırır.
    _urgency() and _to_risk_level() are pure module-level functions
    called by all scoring paths.

  - _gini() Gini katsayısı hesaplaması tek yerde tanımlanmıştır.
    _gini() Gini coefficient computation is defined exactly once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Sequence

import pandas as pd

# ── Risk seviyesi eşik değerleri (tek tanım, her yerde kullanılır) ─────────────
# Risk level thresholds (single definition, reused everywhere)
_THRESHOLD_LOW: float = 30.0
_THRESHOLD_HIGH: float = 70.0

# ── Ağırlıklar — toplamları 100 olmalı ────────────────────────────────────────
# Scoring weights — must sum to 100
_WEIGHT_INCOMPLETE: float = 40.0   # Tamamlanmamış görev oranı / Incomplete task ratio
_WEIGHT_DEADLINE: float = 40.0     # Son tarih aciliyeti / Deadline urgency
_WEIGHT_WORKLOAD: float = 20.0     # İş yükü dengesizliği / Workload imbalance

# ── Aciliyet penceresi (gün) — bu gün sayısının altındaki son tarihler risk taşır ──
# Urgency window (days) — deadlines within this window carry urgency risk
_URGENCY_WINDOW_DAYS: int = 14

# ── Kişi başına maksimum görev sayısı — bu değer aşıldığında tam iş yükü riski ──
# Max tasks per person — at or above this value triggers full workload risk
_MAX_TASKS_PER_PERSON: int = 5


# ══════════════════════════════════════════════════════════════════════════════
# Sonuç veri sınıfları / Result dataclasses
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProjectRiskResult:
    """
    RiskCalculator'ın proje düzeyinde döndürdüğü yapılandırılmış sonuç.
    Structured result returned by RiskCalculator for a project.
    """
    risk_score: float               # 0–100 toplam risk skoru / total risk score
    risk_level: str                 # "Low" | "Medium" | "High"
    incomplete_ratio_score: float   # Durum alt skoru / Status sub-score (0–40)
    deadline_risk_score: float      # Son tarih alt skoru / Deadline sub-score (0–40)
    workload_risk_score: float      # İş yükü alt skoru / Workload sub-score (0–20)
    total_tasks: int
    incomplete_tasks: int
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemberRiskResult:
    """
    Tek bir ekip üyesi için RiskCalculator'ın döndürdüğü yapılandırılmış sonuç.
    Structured result returned by RiskCalculator for a single team member.
    """
    assignee_id: str
    risk_score: float               # 0–100 toplam risk skoru / total risk score
    risk_level: str                 # "Low" | "Medium" | "High"
    assigned_tasks: int             # Atanan toplam görev / Total assigned tasks
    incomplete_tasks: int           # Tamamlanmamış görev sayısı / Incomplete tasks
    overdue_tasks: int              # Vadesi geçmiş görev sayısı / Overdue tasks
    deadline_risk_score: float      # Son tarih alt skoru / Deadline sub-score (0–40)
    workload_score: float           # İş yükü alt skoru / Workload sub-score (0–20)
    extra: Dict[str, Any] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
# Saf yardımcı fonksiyonlar / Pure helper functions  (DRY — tek tanım)
# ══════════════════════════════════════════════════════════════════════════════

def _to_risk_level(score: float) -> str:
    """
    0-100 sayısal risk skorunu kategorik seviyeye dönüştürür.
    Map a 0-100 numeric risk score to a categorical level.

    < 30  → "Low"
    30-70 → "Medium"
    ≥ 70  → "High"
    """
    if score < _THRESHOLD_LOW:
        return "Low"
    if score < _THRESHOLD_HIGH:
        return "Medium"
    return "High"


def _urgency(deadline: Any, today: date) -> float:
    """
    Tek bir son tarih için 0-1 aciliyet değeri döndürür.
    Return a 0-1 urgency value for a single deadline.

    Kurallar / Rules:
      - Son tarih yok (None/NaT) → 0.5  (belirsizlik riski / uncertainty risk)
      - Vadesi geçmiş (days ≤ 0) → 1.0  (maksimum aciliyet / maximum urgency)
      - Pencere dışı (> _URGENCY_WINDOW_DAYS gün kaldı) → 0.0  (acil değil / not urgent)
      - Pencere içinde → doğrusal interpolasyon / linear interpolation
    """
    # Eksik son tarih: orta düzey belirsizlik riski atar
    # Missing deadline: assign moderate uncertainty risk
    if pd.isna(deadline) or deadline is None:
        return 0.5

    try:
        days_left = (deadline - today).days
    except TypeError:
        # Tip uyuşmazlığı olması halinde orta risk döndür
        # Return medium risk on type mismatch
        return 0.5

    if days_left <= 0:
        # Vadesi geçmiş veya bugün son gün → maksimum aciliyet
        # Overdue or due today → maximum urgency
        return 1.0

    if days_left > _URGENCY_WINDOW_DAYS:
        # Yeterince uzak → şu an için risk yok
        # Far enough out → no immediate risk
        return 0.0

    # Aciliyet penceresinde: doğrusal düşüş
    # Within urgency window: linear decay
    return (_URGENCY_WINDOW_DAYS - days_left) / _URGENCY_WINDOW_DAYS


def _gini(values: Sequence[float]) -> float:
    """
    Negatif olmayan değerler dizisi için Gini katsayısını hesaplar.
    Compute the Gini coefficient for a sequence of non-negative values.

    Gini = 0.0 → mükemmel eşitlik / perfect equality (sıfır iş yükü dengesizliği / zero imbalance)
    Gini → 1.0 → maksimum eşitsizlik / maximum inequality (tek kişide yoğunlaşma / single person)

    Boş veya sıfır toplamı olan diziler için 0.0 döndürür.
    Returns 0.0 for empty or all-zero sequences.
    """
    if len(values) == 0:
        return 0.0

    total = sum(values)
    if total == 0:
        return 0.0

    # Sıralı kümülatif toplam formülü (sorting-based Gini formula)
    sorted_v = sorted(values)
    n = len(sorted_v)
    weighted_sum = sum((i + 1) * v for i, v in enumerate(sorted_v))

    # Standart Gini formülü: G = (2 * Σ[(i+1)*v_i]) / (n * Σv_i) - (n+1)/n
    # Standard Gini formula
    return (2 * weighted_sum) / (n * total) - (n + 1) / n


# ══════════════════════════════════════════════════════════════════════════════
# Ana hesaplayıcı sınıfı / Main calculator class
# ══════════════════════════════════════════════════════════════════════════════

class RiskCalculator:
    """
    Durumsuz, pandas tabanlı risk hesaplayıcısı.
    Stateless, pandas-based risk calculator.

    Kullanım / Usage:
        calc = RiskCalculator()
        calc.load(tasks_df, sprints_df)           # ham veriyi yükle / load raw data
        project_result = calc.calculate_project_risk()
        member_results = calc.calculate_member_risks()
        timing_risks   = calc.get_sprint_timing_risk()

    Beklenen DataFrame şemaları / Expected DataFrame schemas:
        tasks_df sütunları / columns:
            id          (str | uuid)
            status      (str)  — "completed" | "in_progress" | "pending" | "delayed"
            deadline    (date | None)
            assignee_id (str | None)
            sprint_id   (str | uuid)

        sprints_df sütunları / columns:
            id          (str | uuid)
            start_date  (date)
            end_date    (date)
            project_id  (str | uuid)
    """

    # ── Yaşam döngüsü / Lifecycle ──────────────────────────────────────────────

    def __init__(self) -> None:
        # Boş DataFrame'lerle başlat; load() çağrısına kadar hesaplama yapılmaz
        # Start with empty DataFrames; no computation until load() is called
        self._tasks: pd.DataFrame = pd.DataFrame()
        self._sprints: pd.DataFrame = pd.DataFrame()
        self._today: date = datetime.now(tz=timezone.utc).date()

    def load(
        self,
        tasks_df: pd.DataFrame,
        sprints_df: pd.DataFrame,
        today: date | None = None,
    ) -> "RiskCalculator":
        """
        Ham veriyi yükler.  Akıcı kullanım (chaining) için self döndürür.
        Load raw data.  Returns self to allow method chaining.

        İki DataFrame de kopya olarak saklanır; böylece çağıran verisi değiştirilmez.
        Both DataFrames are stored as copies to avoid mutating caller data.

        today parametresi testlerde tarihi sabitlemek için kullanılır.
        The today parameter can be used in tests to pin the reference date.
        """
        self._tasks = tasks_df.copy()
        self._sprints = sprints_df.copy()

        # Test senaryolarında tarihi sabitlemeye izin ver
        # Allow pinning the reference date in test scenarios
        if today is not None:
            self._today = today

        return self

    # ── Genel API / Public API ─────────────────────────────────────────────────

    def calculate_project_risk(self) -> ProjectRiskResult:
        """
        Tüm görev sinyallerini tek bir 0-100 proje risk skoruna toplar.
        Aggregate all task-level signals into a single 0-100 project risk score.

        Görev yoksa sıfırlanmış bir sonuç döndürür.
        Returns a zeroed result when there are no tasks.

        Skor bileşenleri / Score components:
            incomplete_ratio_score  (0–40) — tamamlanmamış görev oranı
            deadline_risk_score     (0–40) — son tarih aciliyeti
            workload_risk_score     (0–20) — Gini tabanlı iş yükü dengesizliği
        """
        df = self._tasks

        # Veri yoksa erken dön / Early return for empty data
        if df.empty:
            return ProjectRiskResult(
                risk_score=0.0,
                risk_level="Low",
                incomplete_ratio_score=0.0,
                deadline_risk_score=0.0,
                workload_risk_score=0.0,
                total_tasks=0,
                incomplete_tasks=0,
                extra={"message": "No tasks found."},
            )

        # Tamamlanmamış görev alt kümesini bir kez hesapla, alt metodlara aktar
        # Compute incomplete subset once and pass to sub-methods (DRY)
        incomplete_df = df[df["status"] != "completed"]

        # Her boyut için alt skor hesapla / Compute sub-score for each dimension
        status_score = self._score_incomplete_ratio(df, incomplete_df)
        deadline_score = self._score_deadline_urgency(incomplete_df)
        workload_score = self._score_workload_imbalance(incomplete_df)

        # Toplamı 100 ile sınırla / Cap total at 100
        total = min(status_score + deadline_score + workload_score, 100.0)

        return ProjectRiskResult(
            risk_score=round(total, 2),
            risk_level=_to_risk_level(total),
            incomplete_ratio_score=round(status_score, 2),
            deadline_risk_score=round(deadline_score, 2),
            workload_risk_score=round(workload_score, 2),
            total_tasks=len(df),
            incomplete_tasks=len(incomplete_df),
        )

    def calculate_member_risks(self) -> List[MemberRiskResult]:
        """
        Görev setindeki her atanan kişi için kişisel risk profili hesaplar.
        Compute a per-member risk profile for every assignee in the task set.

        Tamamlanmamış görevi olmayan üyeler sıfırlanmış sonuç alır.
        Members with no assigned tasks receive a zeroed result.
        """
        df = self._tasks

        if df.empty:
            return []

        # Atanmamış görevleri filtrele / Filter out unassigned tasks
        assigned_df = df.dropna(subset=["assignee_id"])

        results: List[MemberRiskResult] = []
        for assignee_id, member_df in assigned_df.groupby("assignee_id"):
            results.append(self._build_member_result(str(assignee_id), member_df))

        return results

    def get_sprint_timing_risk(self) -> Dict[str, Any]:
        """
        Sprint düzeyinde zamanlama sinyallerini analiz eder.
        Analyse sprint-level timing signals.

        Her sprint için şunları hesaplar / For each sprint, computes:
            days_elapsed         — sprint başlangıcından bugüne geçen gün
            days_remaining       — sprint bitimine kalan gün
            total_sprint_days    — toplam sprint süresi
            completion_rate      — tamamlanan görev oranı (0-1)
            elapsed_ratio        — geçen zaman oranı (0-1)
            progress_gap         — tamamlanma - geçen zaman (negatif → gecikme)
            timing_risk_score    — 0-100 zamanlama risk skoru
            timing_risk_level    — "Low" | "Medium" | "High"

        Boş veri için boş dict döndürür / Returns empty dict for empty data.
        """
        if self._sprints.empty or self._tasks.empty:
            return {}

        timing: Dict[str, Any] = {}
        today = self._today

        for _, sprint in self._sprints.iterrows():
            sprint_id = str(sprint["id"])

            # Bu sprinte ait görevleri filtrele / Filter tasks belonging to this sprint
            sprint_tasks = self._tasks[self._tasks["sprint_id"] == sprint["id"]]
            total = len(sprint_tasks)
            completed = int((sprint_tasks["status"] == "completed").sum())

            # Tarihleri güvenli şekilde date nesnesine dönüştür
            # Safely coerce to date objects
            start = _to_date(sprint["start_date"])
            end = _to_date(sprint["end_date"])

            total_days = max((end - start).days, 1)
            elapsed_days = max(min((today - start).days, total_days), 0)
            remaining_days = max((end - today).days, 0)

            # Zaman kullanım oranı vs tamamlanma oranı karşılaştırması
            # Time usage ratio vs completion rate comparison
            elapsed_ratio = elapsed_days / total_days
            completion_rate = completed / total if total > 0 else 0.0

            # Negatif fark → plandan geride (negative gap → behind schedule)
            progress_gap = completion_rate - elapsed_ratio

            # Zamanlama riski: plandan ne kadar geride olunduğuna göre 0-100
            # Timing risk: 0-100 based on how far behind schedule the sprint is
            if progress_gap >= 0:
                # Plana uygun veya ileride → risk yok
                # On track or ahead → no timing risk
                t_risk = 0.0
            else:
                # Büyük negatif fark → yüksek risk; -1.0 fark → 100 puan
                # Large negative gap → high risk; gap of -1.0 → 100 points
                t_risk = min(abs(progress_gap) * 100.0, 100.0)

            timing[sprint_id] = {
                "days_elapsed": elapsed_days,
                "days_remaining": remaining_days,
                "total_sprint_days": total_days,
                "completion_rate": round(completion_rate, 4),
                "elapsed_ratio": round(elapsed_ratio, 4),
                "progress_gap": round(progress_gap, 4),
                "timing_risk_score": round(t_risk, 2),
                "timing_risk_level": _to_risk_level(t_risk),
            }

        return timing

    # ── Özel skorlama yardımcıları / Private scoring helpers ──────────────────

    def _score_incomplete_ratio(
        self,
        all_tasks: pd.DataFrame,
        incomplete_tasks: pd.DataFrame,
    ) -> float:
        """
        Tamamlanmamış görev oranını ağırlıklı skora dönüştürür.
        Convert incomplete task ratio to a weighted score.

        Formül / Formula:  score = (incomplete / total) × _WEIGHT_INCOMPLETE
        Aralık / Range:    0 → 40
        """
        if len(all_tasks) == 0:
            return 0.0

        ratio = len(incomplete_tasks) / len(all_tasks)
        return ratio * _WEIGHT_INCOMPLETE

    def _score_deadline_urgency(self, incomplete_df: pd.DataFrame) -> float:
        """
        Tamamlanmamış görevlerin ortalama aciliyetini ağırlıklı skora dönüştürür.
        Convert mean urgency of incomplete tasks to a weighted score.

        Formül / Formula:  score = mean(urgency_i) × _WEIGHT_DEADLINE
        Aralık / Range:    0 → 40

        _urgency() fonksiyonu modül düzeyinde tek bir yerde tanımlanmıştır (DRY).
        _urgency() is defined once at module level (DRY).
        """
        if incomplete_df.empty:
            return 0.0

        today = self._today
        urgency_series = incomplete_df["deadline"].apply(
            lambda dl: _urgency(dl, today)
        )
        return urgency_series.mean() * _WEIGHT_DEADLINE

    def _score_workload_imbalance(self, incomplete_df: pd.DataFrame) -> float:
        """
        Gini katsayısı tabanlı iş yükü dengesizliği skoru hesaplar.
        Compute workload imbalance score using the Gini coefficient.

        Formül / Formula:  score = gini(task_counts_per_member) × _WEIGHT_WORKLOAD
        Aralık / Range:    0 → 20

        Gini = 0.0 → mükemmel eşitlik → minimum iş yükü riski
        Gini = 1.0 → tek kişide yoğunlaşma → maksimum iş yükü riski

        Gini = 0.0 → perfectly even → minimum workload risk
        Gini = 1.0 → all tasks on one person → maximum workload risk

        Atanmamış görevler orta düzey risk atar (belirsiz sahip = risk).
        Unassigned tasks yield moderate risk (no clear owner = risk).
        """
        if incomplete_df.empty:
            return 0.0

        assigned = incomplete_df.dropna(subset=["assignee_id"])

        if assigned.empty:
            # Tüm tamamlanmamış görevler atanmamış → orta risk
            # All incomplete tasks are unassigned → moderate risk
            return _WEIGHT_WORKLOAD * 0.5

        # Kişi başına tamamlanmamış görev sayısını hesapla
        # Count incomplete tasks per assignee
        counts = list(assigned.groupby("assignee_id").size().values.astype(float))
        gini = _gini(counts)
        return gini * _WEIGHT_WORKLOAD

    def _build_member_result(
        self, assignee_id: str, member_df: pd.DataFrame
    ) -> MemberRiskResult:
        """
        Tek bir ekip üyesi için MemberRiskResult oluşturur.
        Build a MemberRiskResult for one team member.

        Paylaşılan _urgency() ve _WEIGHT_* sabitlerini kullanır (DRY).
        Uses shared _urgency() and _WEIGHT_* constants (DRY).
        """
        today = self._today
        incomplete_df = member_df[member_df["status"] != "completed"]

        # Vadesi geçmiş tamamlanmamış görev sayısını bul
        # Count overdue incomplete tasks
        overdue_count = int(
            incomplete_df["deadline"]
            .apply(lambda dl: (not pd.isna(dl)) and dl is not None and (dl - today).days <= 0)
            .sum()
        )

        # Bu üyenin tamamlanmamış görevleri için son tarih aciliyeti
        # Deadline urgency for this member's incomplete tasks
        dl_score = 0.0
        if not incomplete_df.empty:
            urgency_series = incomplete_df["deadline"].apply(
                lambda dl: _urgency(dl, today)
            )
            dl_score = round(urgency_series.mean() * _WEIGHT_DEADLINE, 2)

        # İş yükü skoru: kişi başına maksimum görev sayısına göre normalleştirilmiş
        # Workload score: normalised against the global per-person cap
        workload_score = round(
            min(len(incomplete_df) / _MAX_TASKS_PER_PERSON, 1.0) * _WEIGHT_WORKLOAD, 2
        )

        total = round(min(dl_score + workload_score, 100.0), 2)

        return MemberRiskResult(
            assignee_id=assignee_id,
            risk_score=total,
            risk_level=_to_risk_level(total),
            assigned_tasks=len(member_df),
            incomplete_tasks=len(incomplete_df),
            overdue_tasks=overdue_count,
            deadline_risk_score=dl_score,
            workload_score=workload_score,
        )


# ══════════════════════════════════════════════════════════════════════════════
# Özel yardımcı (dahili) / Internal helper
# ══════════════════════════════════════════════════════════════════════════════

def _to_date(value: Any) -> date:
    """
    Çeşitli türleri (str, datetime, date) güvenli şekilde date nesnesine dönüştürür.
    Safely coerce various types (str, datetime, date) to a date object.

    Sprint zamanlama analizinde sprint satırlarından gelen değerleri normalize eder.
    Used in sprint timing analysis to normalise values coming from sprint rows.
    """
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    # string ISO formatı için son çare / last resort for ISO string format
    return date.fromisoformat(str(value))
