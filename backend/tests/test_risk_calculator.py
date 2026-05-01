"""
Unit tests for RiskCalculator — Sprint 2 Deliverable.

Test edilen senaryolar / Scenarios covered:
    1.  Boş veri → sıfırlanmış Low sonuç
        Empty data → zeroed Low result

    2.  Tüm görevler tamamlandı → Low risk
        All tasks completed → Low risk

    3.  Yüksek iş yükü senaryosu → High risk
        High workload scenario → High risk

    4.  Vadesi geçmiş görevler riski artırır
        Overdue tasks increase risk

    5.  Dengeli iş yükü (Gini ≈ 0) → düşük iş yükü riski
        Balanced workload (Gini ≈ 0) → low workload risk

    6.  Dengesiz iş yükü (Gini > 0) → artan iş yükü riski
        Skewed workload (Gini > 0) → elevated workload risk

    7.  Sprint plandan geride → yüksek zamanlama riski
        Sprint behind schedule → high timing risk

    8.  Sprint plandan ileride → sıfır zamanlama riski
        Sprint ahead of schedule → zero timing risk

    9.  Üye bazlı risk: 5+ vadesi geçmiş görev → High
        Member risk: 5+ overdue tasks → High

    10. Üye bazlı risk: tamamlanmış görevler → Low
        Member risk: all tasks completed → Low

    11. _gini yardımcısı — sınır durumları
        _gini helper — edge cases

    12. _urgency yardımcısı — tüm dallar
        _urgency helper — all branches

    13. _to_risk_level yardımcısı — eşik değerleri
        _to_risk_level helper — threshold values

    14. Tamamlanmamış atanmamış görevler orta iş yükü riski verir
        Unassigned incomplete tasks yield moderate workload risk

    15. Proje skoru 100'ü aşmaz
        Project score never exceeds 100

Testler saf (pure) birim testleridir; veritabanı veya ağ gerektirmez.
Tests are pure unit tests; no database or network required.
"""

from __future__ import annotations

import sys
import os
from datetime import date, timedelta

import pandas as pd
import pytest

# backend/ dizininin Python yolunda olduğundan emin ol
# Ensure backend/ directory is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.risk_calculator import (
    RiskCalculator,
    _gini,
    _to_risk_level,
    _urgency,
)

# ── Sabit referans tarihi (testlerde deterministik sonuçlar için) ──────────────
# Fixed reference date (for deterministic results in tests)
TODAY = date(2026, 4, 19)


# ══════════════════════════════════════════════════════════════════════════════
# DataFrame oluşturma yardımcıları / DataFrame builder helpers
# ══════════════════════════════════════════════════════════════════════════════

def _make_tasks(rows: list[dict]) -> pd.DataFrame:
    """
    Minimum sütun seti içeren bir tasks DataFrame'i oluşturur.
    Build a tasks DataFrame with the minimum required column set.
    """
    defaults = {"sprint_id": "sprint-1", "assignee_id": "user-1"}
    records = [{**defaults, **row} for row in rows]
    return pd.DataFrame(records)


def _make_sprints(rows: list[dict]) -> pd.DataFrame:
    """
    Minimum sütun seti içeren bir sprints DataFrame'i oluşturur.
    Build a sprints DataFrame with the minimum required column set.
    """
    defaults = {"project_id": "proj-1"}
    records = [{**defaults, **row} for row in rows]
    return pd.DataFrame(records)


def _calc(tasks: pd.DataFrame, sprints: pd.DataFrame | None = None) -> RiskCalculator:
    """
    TODAY referans tarihiyle yüklenmiş RiskCalculator döndürür (DRY).
    Return a RiskCalculator loaded with a fixed TODAY reference date (DRY).
    """
    return RiskCalculator().load(
        tasks, sprints if sprints is not None else pd.DataFrame(), today=TODAY
    )


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 1 — Boş veri / Empty data
# ══════════════════════════════════════════════════════════════════════════════

def test_empty_tasks_returns_zeroed_low_result():
    """
    Senaryo 1: Hiç görev olmadığında risk skoru 0, seviye Low olmalı.
    Scenario 1: With no tasks, risk score is 0 and level is Low.
    """
    result = _calc(pd.DataFrame()).calculate_project_risk()

    assert result.risk_score == 0.0
    assert result.risk_level == "Low"
    assert result.total_tasks == 0
    assert result.incomplete_tasks == 0


def test_empty_tasks_member_risks_returns_empty_list():
    """
    Senaryo 1b: Hiç görev olmadığında üye risk listesi boş olmalı.
    Scenario 1b: With no tasks, member risk list should be empty.
    """
    results = _calc(pd.DataFrame()).calculate_member_risks()
    assert results == []


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 2 — Tüm görevler tamamlandı / All tasks completed
# ══════════════════════════════════════════════════════════════════════════════

def test_all_completed_tasks_yields_low_risk():
    """
    Senaryo 2: Tüm görevler tamamlandıysa proje riski Low olmalı.
    Scenario 2: If all tasks are completed the project risk must be Low.
    """
    tasks = _make_tasks([
        {"id": "t1", "status": "completed", "deadline": TODAY - timedelta(days=1)},
        {"id": "t2", "status": "completed", "deadline": TODAY + timedelta(days=5)},
        {"id": "t3", "status": "completed", "deadline": None},
    ])

    result = _calc(tasks).calculate_project_risk()

    # Tamamlanmamış görev yok → status_risk = 0
    assert result.incomplete_ratio_score == 0.0
    # Tamamlanmamış görev olmadığından deadline ve workload da sıfır olmalı
    assert result.deadline_risk_score == 0.0
    assert result.workload_risk_score == 0.0
    assert result.risk_score == 0.0
    assert result.risk_level == "Low"


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 3 — Yüksek iş yükü / High workload scenario
# ══════════════════════════════════════════════════════════════════════════════

def test_high_workload_and_overdue_tasks_yields_high_risk():
    """
    Senaryo 3: Çok sayıda vadesi geçmiş tamamlanmamış görev → High risk.
    Scenario 3: Many overdue incomplete tasks → High risk.
    """
    # 6 görev, hepsi tamamlanmamış ve vadesi geçmiş
    # 6 tasks, all incomplete and overdue
    overdue = TODAY - timedelta(days=5)
    tasks = _make_tasks([
        {"id": f"t{i}", "status": "in_progress", "deadline": overdue, "assignee_id": "user-1"}
        for i in range(6)
    ])

    result = _calc(tasks).calculate_project_risk()

    # Incomplete ratio = 100% → 40 puan
    assert result.incomplete_ratio_score == pytest.approx(40.0)
    # Deadline urgency: tüm görevler vadesi geçmiş → ortalama urgency = 1.0 → 40 puan
    assert result.deadline_risk_score == pytest.approx(40.0)
    # Toplam en az 80 puan → High
    assert result.risk_score >= 70.0
    assert result.risk_level == "High"


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 4 — Vadesi geçmiş görevler / Overdue tasks increase risk
# ══════════════════════════════════════════════════════════════════════════════

def test_overdue_tasks_increase_risk_compared_to_future_tasks():
    """
    Senaryo 4: Vadesi geçmiş görevler, vadesi uzak görevlere göre daha yüksek
    risk üretmeli.
    Scenario 4: Overdue tasks should produce higher risk than future tasks.
    """
    overdue_tasks = _make_tasks([
        {"id": "t1", "status": "pending", "deadline": TODAY - timedelta(days=3)},
        {"id": "t2", "status": "pending", "deadline": TODAY - timedelta(days=1)},
    ])
    future_tasks = _make_tasks([
        {"id": "t1", "status": "pending", "deadline": TODAY + timedelta(days=30)},
        {"id": "t2", "status": "pending", "deadline": TODAY + timedelta(days=60)},
    ])

    overdue_result = _calc(overdue_tasks).calculate_project_risk()
    future_result = _calc(future_tasks).calculate_project_risk()

    assert overdue_result.deadline_risk_score > future_result.deadline_risk_score


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 5 — Dengeli iş yükü / Balanced workload
# ══════════════════════════════════════════════════════════════════════════════

def test_balanced_workload_yields_minimal_workload_risk():
    """
    Senaryo 5: Her kişide eşit sayıda görev (Gini ≈ 0) → minimum iş yükü riski.
    Scenario 5: Equal tasks per person (Gini ≈ 0) → minimum workload risk.
    """
    tasks = _make_tasks([
        # Her kullanıcıya 1'er görev; mükemmel denge
        # 1 task per user; perfect balance
        {"id": "t1", "status": "in_progress", "deadline": None, "assignee_id": "user-1"},
        {"id": "t2", "status": "in_progress", "deadline": None, "assignee_id": "user-2"},
        {"id": "t3", "status": "in_progress", "deadline": None, "assignee_id": "user-3"},
    ])

    result = _calc(tasks).calculate_project_risk()

    # Gini = 0 → workload_risk = 0
    assert result.workload_risk_score == pytest.approx(0.0)


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 6 — Dengesiz iş yükü / Skewed workload
# ══════════════════════════════════════════════════════════════════════════════

def test_skewed_workload_increases_workload_risk():
    """
    Senaryo 6: Bir kişide çok görev, diğerlerinde az → yüksek Gini → yüksek iş yükü riski.
    Scenario 6: One person with many tasks, others with few → high Gini → high workload risk.
    """
    balanced_tasks = _make_tasks([
        {"id": "t1", "status": "pending", "deadline": None, "assignee_id": "user-1"},
        {"id": "t2", "status": "pending", "deadline": None, "assignee_id": "user-2"},
        {"id": "t3", "status": "pending", "deadline": None, "assignee_id": "user-3"},
    ])
    skewed_tasks = _make_tasks([
        # user-1: 5 görev, user-2: 1 görev → dengesiz dağılım
        # user-1: 5 tasks, user-2: 1 task → unequal distribution
        {"id": "t1", "status": "pending", "deadline": None, "assignee_id": "user-1"},
        {"id": "t2", "status": "pending", "deadline": None, "assignee_id": "user-1"},
        {"id": "t3", "status": "pending", "deadline": None, "assignee_id": "user-1"},
        {"id": "t4", "status": "pending", "deadline": None, "assignee_id": "user-1"},
        {"id": "t5", "status": "pending", "deadline": None, "assignee_id": "user-1"},
        {"id": "t6", "status": "pending", "deadline": None, "assignee_id": "user-2"},
    ])

    balanced_result = _calc(balanced_tasks).calculate_project_risk()
    skewed_result = _calc(skewed_tasks).calculate_project_risk()

    assert skewed_result.workload_risk_score > balanced_result.workload_risk_score


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 7 — Sprint plandan geride / Sprint behind schedule
# ══════════════════════════════════════════════════════════════════════════════

def test_sprint_behind_schedule_yields_high_timing_risk():
    """
    Senaryo 7: Sprint yarıya gelinmiş ama hiç tamamlanmış görev yok →
               büyük negatif progress_gap → yüksek zamanlama riski.
    Scenario 7: Sprint half elapsed but no tasks completed →
                large negative progress_gap → high timing risk.
    """
    sprint_start = TODAY - timedelta(days=10)  # 10 gün önce başladı / started 10 days ago
    sprint_end = TODAY + timedelta(days=10)    # 10 gün sonra bitiyor / ends in 10 days
    sprint_id = "sprint-behind"

    sprints = _make_sprints([{
        "id": sprint_id,
        "start_date": sprint_start,
        "end_date": sprint_end,
    }])

    # Görevlerin hepsi tamamlanmamış / All tasks incomplete
    tasks = _make_tasks([
        {"id": f"t{i}", "sprint_id": sprint_id, "status": "pending", "deadline": sprint_end}
        for i in range(4)
    ])

    timing = _calc(tasks, sprints).get_sprint_timing_risk()

    assert sprint_id in timing
    sprint_timing = timing[sprint_id]

    # İlerleme açığı negatif olmalı (tamamlanma oranı < geçen zaman oranı)
    # Progress gap should be negative (completion rate < elapsed ratio)
    assert sprint_timing["progress_gap"] < 0
    assert sprint_timing["timing_risk_score"] > 0
    assert sprint_timing["timing_risk_level"] in ("Medium", "High")


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 8 — Sprint ileride / Sprint ahead of schedule
# ══════════════════════════════════════════════════════════════════════════════

def test_sprint_ahead_of_schedule_yields_zero_timing_risk():
    """
    Senaryo 8: Tüm görevler tamamlandı ve sprint henüz bitmedi →
               progress_gap ≥ 0 → sıfır zamanlama riski.
    Scenario 8: All tasks completed, sprint not yet finished →
                progress_gap ≥ 0 → zero timing risk.
    """
    sprint_start = TODAY - timedelta(days=5)
    sprint_end = TODAY + timedelta(days=15)
    sprint_id = "sprint-ahead"

    sprints = _make_sprints([{
        "id": sprint_id,
        "start_date": sprint_start,
        "end_date": sprint_end,
    }])

    # Tüm görevler tamamlandı / All tasks completed
    tasks = _make_tasks([
        {"id": f"t{i}", "sprint_id": sprint_id, "status": "completed", "deadline": sprint_end}
        for i in range(4)
    ])

    timing = _calc(tasks, sprints).get_sprint_timing_risk()

    assert sprint_id in timing
    assert timing[sprint_id]["timing_risk_score"] == 0.0
    assert timing[sprint_id]["timing_risk_level"] == "Low"


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 9 — Üye bazlı: yüksek iş yükü / Member: high workload
# ══════════════════════════════════════════════════════════════════════════════

def test_member_with_many_overdue_tasks_gets_maximum_member_risk():
    """
    Senaryo 9: 5'ten fazla vadesi geçmiş göreve sahip üye maksimum üye risk skoruna ulaşmalı.

    Üye risk formülü:
        deadline_risk_score (0-40) + workload_score (0-20) = maksimum 60 puan
    Bu nedenle üye için en yüksek erişilebilir seviye Medium'dur (30 ≤ skor < 70).
    Tüm görevler vadesi geçmişse ve kişi başına görev ≥ 5 ise skor = 60 → "Medium".

    Scenario 9: Member with 5+ overdue tasks should reach the maximum member risk score.

    Member risk formula:
        deadline_risk_score (0-40) + workload_score (0-20) = max 60 points
    Therefore the highest reachable level for a member is Medium (30 ≤ score < 70).
    With all tasks overdue and task count ≥ 5: score = 60 → "Medium".
    """
    overdue = TODAY - timedelta(days=2)
    tasks = _make_tasks([
        {"id": f"t{i}", "status": "in_progress", "deadline": overdue, "assignee_id": "heavy-user"}
        for i in range(6)
    ])

    member_results = _calc(tasks).calculate_member_risks()

    heavy = next(r for r in member_results if r.assignee_id == "heavy-user")

    # 6 vadesi geçmiş görev → workload kapasitesi aşıldı, deadline urgency maks
    # 6 overdue tasks → workload capped, deadline urgency maxed
    assert heavy.overdue_tasks == 6
    assert heavy.incomplete_tasks == 6

    # dl_score = 1.0 * 40 = 40, workload = min(6/5, 1.0) * 20 = 20 → toplam = 60 → Medium
    # dl_score = 1.0 * 40 = 40, workload = min(6/5, 1.0) * 20 = 20 → total = 60 → Medium
    assert heavy.deadline_risk_score == pytest.approx(40.0)
    assert heavy.workload_score == pytest.approx(20.0)
    assert heavy.risk_score == pytest.approx(60.0)
    assert heavy.risk_level == "Medium"


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 10 — Üye bazlı: tüm tamamlandı / Member: all completed
# ══════════════════════════════════════════════════════════════════════════════

def test_member_with_all_completed_tasks_gets_zero_risk():
    """
    Senaryo 10: Tüm görevleri tamamlanmış üye sıfır risk skoru almalı.
    Scenario 10: A member whose all tasks are completed should get zero risk score.
    """
    tasks = _make_tasks([
        {"id": "t1", "status": "completed", "deadline": TODAY - timedelta(days=1), "assignee_id": "done-user"},
        {"id": "t2", "status": "completed", "deadline": TODAY + timedelta(days=3), "assignee_id": "done-user"},
    ])

    member_results = _calc(tasks).calculate_member_risks()

    done = next(r for r in member_results if r.assignee_id == "done-user")

    assert done.incomplete_tasks == 0
    assert done.risk_score == 0.0
    assert done.risk_level == "Low"


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 11 — _gini yardımcısı sınır durumları / _gini edge cases
# ══════════════════════════════════════════════════════════════════════════════

def test_gini_perfect_equality():
    """Eşit dağılım Gini = 0 vermelidir / Equal distribution should give Gini = 0."""
    assert _gini([2.0, 2.0, 2.0, 2.0]) == pytest.approx(0.0, abs=1e-9)


def test_gini_empty_returns_zero():
    """Boş dizi için Gini = 0 olmalı / Empty sequence should return Gini = 0."""
    assert _gini([]) == 0.0


def test_gini_all_zeros_returns_zero():
    """Tüm değerler sıfırsa Gini = 0 olmalı / All-zero values should return Gini = 0."""
    assert _gini([0.0, 0.0, 0.0]) == 0.0


def test_gini_single_element_returns_zero():
    """
    Tek eleman durumunda eşitsizlik yok → Gini = 0 olmalı.
    Single element → no inequality → Gini = 0.
    """
    assert _gini([5.0]) == pytest.approx(0.0, abs=1e-9)


def test_gini_maximum_inequality():
    """
    Bir kişide tüm görevler, diğerleri sıfır → Gini > 0 olmalı.
    All tasks on one person, others zero → Gini > 0.
    Sıfır değerler Gini hesaplamasını etkilemez (sıfır ağırlıklı).
    Zero values don't affect Gini calculation (zero-weighted).
    """
    # Sadece pozitif değerleri gönder; sıfırları dropna ile filtrele
    # Send only positive values; zeros are filtered in groupby
    result = _gini([4.0, 1.0, 1.0, 1.0, 1.0])
    assert result > 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 12 — _urgency yardımcısı / _urgency helper branches
# ══════════════════════════════════════════════════════════════════════════════

def test_urgency_none_deadline_returns_half():
    """Son tarih yoksa belirsizlik riski 0.5 olmalı / No deadline → uncertainty risk 0.5."""
    assert _urgency(None, TODAY) == 0.5


def test_urgency_overdue_returns_one():
    """Vadesi geçmiş son tarih → maksimum aciliyet 1.0 / Overdue → max urgency 1.0."""
    overdue = TODAY - timedelta(days=1)
    assert _urgency(overdue, TODAY) == 1.0


def test_urgency_today_returns_one():
    """Bugün vadesi dolan → maksimum aciliyet 1.0 / Due today → max urgency 1.0."""
    assert _urgency(TODAY, TODAY) == 1.0


def test_urgency_far_future_returns_zero():
    """Uzak gelecekteki son tarih → sıfır aciliyet / Far future → zero urgency."""
    far_future = TODAY + timedelta(days=30)
    assert _urgency(far_future, TODAY) == 0.0


def test_urgency_within_window_returns_interpolated():
    """
    Aciliyet penceresi içinde: 7 gün kaldı → 0.5 bekleniyor.
    7 days remaining within 14-day window → expect 0.5.
    """
    seven_days = TODAY + timedelta(days=7)
    result = _urgency(seven_days, TODAY)
    assert result == pytest.approx(0.5, abs=1e-9)


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 13 — _to_risk_level eşik değerleri / _to_risk_level thresholds
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("score, expected_level", [
    (0.0,   "Low"),
    (29.99, "Low"),
    (30.0,  "Medium"),
    (69.99, "Medium"),
    (70.0,  "High"),
    (100.0, "High"),
])
def test_to_risk_level_thresholds(score: float, expected_level: str):
    """
    Senaryo 13: Risk seviyesi eşik değerlerini doğrula.
    Scenario 13: Verify risk level threshold boundaries.
    """
    assert _to_risk_level(score) == expected_level


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 14 — Atanmamış görevler / Unassigned tasks
# ══════════════════════════════════════════════════════════════════════════════

def test_unassigned_incomplete_tasks_yield_moderate_workload_risk():
    """
    Senaryo 14: Tamamlanmamış tüm görevler atanmamışsa orta iş yükü riski
               (%50 × _WEIGHT_WORKLOAD = 10) döndürülmeli.
    Scenario 14: If all incomplete tasks are unassigned, moderate workload risk
                (50% × _WEIGHT_WORKLOAD = 10) is expected.
    """
    tasks = _make_tasks([
        # assignee_id = None → atanmamış / unassigned
        {"id": "t1", "status": "pending", "deadline": None, "assignee_id": None},
        {"id": "t2", "status": "pending", "deadline": None, "assignee_id": None},
    ])

    result = _calc(tasks).calculate_project_risk()

    # 50% × 20 = 10.0
    assert result.workload_risk_score == pytest.approx(10.0, abs=1e-9)


# ══════════════════════════════════════════════════════════════════════════════
# Senaryo 15 — Skor hiçbir zaman 100'ü aşmaz / Score never exceeds 100
# ══════════════════════════════════════════════════════════════════════════════

def test_project_risk_score_never_exceeds_100():
    """
    Senaryo 15: Olası en kötü senaryoda bile proje risk skoru 100'ü aşmamalı.
    Scenario 15: Even in the worst-case scenario, project risk score must not exceed 100.
    """
    overdue = TODAY - timedelta(days=10)
    # Tek kullanıcıya yığılmış, vadesi geçmiş, çok sayıda görev
    # All tasks on one user, all overdue, large count
    tasks = _make_tasks([
        {"id": f"t{i}", "status": "delayed", "deadline": overdue, "assignee_id": "only-user"}
        for i in range(20)
    ])

    result = _calc(tasks).calculate_project_risk()

    assert result.risk_score <= 100.0
