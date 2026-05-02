#!/bin/sh
# ── SprintBoard AI — Container Entrypoint ─────────────────────────────────────
# Veritabanı hazır olduğunda migration'ları uygular, ardından API'yi başlatır.

set -e

echo "⏳ Alembic migration'ları uygulanıyor..."
alembic upgrade head
echo "✅ Migration tamamlandı."

echo "🚀 SprintBoard API başlatılıyor..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
