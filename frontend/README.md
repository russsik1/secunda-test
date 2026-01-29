# Secunda frontend

Vue 3 + Vite + TypeScript + Tailwind (shadcn-style UI).

## Переменные окружения

- `VITE_API_BASE` — базовый URL бэка (например `http://localhost:8000`)
- `VITE_API_KEY` — API key для заголовка `X-API-Key` (по умолчанию `dev-api-key`)

См. `.env.example`.

## Запуск локально (без Docker)

```bash
npm install
npm run dev
```

## Запуск в Docker (dev, hot-reload)

```bash
docker compose up --build
```

По умолчанию фронт будет ходить на `http://host.docker.internal:8000` (удобно для Windows, когда бэк поднят на хосте).

