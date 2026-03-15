import requests
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SHORT = 5
TIMEOUT_LONG = 90


def health_check() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT_SHORT)
        return r.status_code == 200
    except Exception:
        return False


def register_user(email: str, password: str, full_name: str = "") -> dict:
    """POST /api/v1/auth/register — yeni hesap oluştur, token döner."""
    payload = {"email": email, "password": password}
    if full_name:
        payload["full_name"] = full_name
    r = requests.post(f"{BASE_URL}/api/v1/auth/register", json=payload, timeout=TIMEOUT_SHORT)
    r.raise_for_status()
    return r.json()


def login_user(email: str, password: str) -> dict:
    """POST /api/v1/auth/login — giriş yap, token döner."""
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT_SHORT,
    )
    r.raise_for_status()
    return r.json()


def get_me(token: str) -> dict:
    """GET /api/v1/auth/me — token ile profil bilgisi al."""
    r = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT_SHORT,
    )
    r.raise_for_status()
    return r.json()


def analyze_sprint(
    github_url: str,
    start_date: str,
    end_date: str,
    team_members: list[str],
    country_code: str = "TR",
    token: Optional[str] = None,
) -> dict:
    """POST /api/v1/sprints/analyze — tam sprint analizi (JWT gerektirir)."""
    payload = {
        "github_url": github_url,
        "start_date": start_date,
        "end_date": end_date,
        "team_members": team_members,
        "country_code": country_code,
    }
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.post(
        f"{BASE_URL}/api/v1/sprints/analyze",
        json=payload,
        headers=headers,
        timeout=TIMEOUT_LONG,
    )
    r.raise_for_status()
    return r.json()


def get_user_sprints(token: str) -> list[dict]:
    """GET /api/v1/sprints/ — kullanıcının geçmiş sprint analizleri."""
    r = requests.get(
        f"{BASE_URL}/api/v1/sprints/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT_SHORT,
    )
    r.raise_for_status()
    return r.json()


def delete_sprint(sprint_id: str, token: str) -> bool:
    """DELETE /api/v1/sprints/{id} — sprint soft delete."""
    r = requests.delete(
        f"{BASE_URL}/api/v1/sprints/{sprint_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=TIMEOUT_SHORT,
    )
    return r.status_code == 200
