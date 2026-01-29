#!/usr/bin/env bash
set -euo pipefail

# Скрипт предполагается запускать ВНУТРИ контейнера.
# По умолчанию запускает uvicorn в foreground (правильно для Docker).
#
# Если хочется "в screen", можно выставить:
#   USE_SCREEN=1
# Тогда uvicorn стартует в screen-сессии `secunda_api`,
# а скрипт оставит контейнер живым через `sleep infinity`.

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if [[ "${USE_SCREEN:-0}" == "1" ]] && command -v screen >/dev/null 2>&1; then
  if screen -list | grep -q "\.secunda_api"; then
    echo "screen session 'secunda_api' already running"
  else
    screen -dmS secunda_api bash -lc "uvicorn app.main:app --host ${HOST} --port ${PORT}"
    echo "OK: started in screen session 'secunda_api'"
  fi

  exec sleep infinity
fi

exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"

