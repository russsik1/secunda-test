#!/usr/bin/env bash
set -euo pipefail

# Скрипт предполагается запускать ВНУТРИ контейнера.
# Делает миграции + генерацию тестовых данных.

alembic upgrade head
python -m scripts.data_gen

echo "OK: migrate + data_gen"

