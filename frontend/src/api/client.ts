type AuthMode = 'apiKey' | 'none'

type ApiGetOptions = {
  auth?: AuthMode
  query?: Record<string, string | number | boolean | undefined | null>
  signal?: AbortSignal
}

const DEFAULT_API_BASE = 'http://localhost:8000'
const DEFAULT_API_KEY = 'dev-api-key'

function getApiBase(): string {
  const base = import.meta.env.VITE_API_BASE
  if (base && base.trim().length > 0) return base.trim()
  return DEFAULT_API_BASE
}

function getApiKey(): string {
  const k = import.meta.env.VITE_API_KEY
  if (k && k.trim().length > 0) return k.trim()
  return DEFAULT_API_KEY
}

function buildUrl(path: string, query?: ApiGetOptions['query']): string {
  const base = getApiBase()
  const url = new URL(path, base)

  if (query) {
    const keys = Object.keys(query)
    for (let i = 0; i < keys.length; i += 1) {
      const key = keys[i]
      const value = query[key]
      if (value === undefined || value === null) continue
      url.searchParams.set(key, String(value))
    }
  }

  return url.toString()
}

export async function apiGet<T>(path: string, options?: ApiGetOptions): Promise<T> {
  const auth: AuthMode = options?.auth ?? 'apiKey'
  const url = buildUrl(path, options?.query)

  const headers: Record<string, string> = {
    Accept: 'application/json',
  }

  if (auth === 'apiKey') {
    headers['X-API-Key'] = getApiKey()
  }

  const res = await fetch(url, {
    method: 'GET',
    headers,
    signal: options?.signal,
  })

  if (!res.ok) {
    let detail = ''
    try {
      const body = (await res.json()) as unknown
      if (body && typeof body === 'object' && 'detail' in body) {
        detail = String((body as { detail: unknown }).detail)
      } else {
        detail = JSON.stringify(body)
      }
    } catch {
      try {
        detail = await res.text()
      } catch {
        detail = ''
      }
    }

    const msg = detail.length > 0 ? detail : `${res.status} ${res.statusText}`
    throw new Error(msg)
  }

  return (await res.json()) as T
}

