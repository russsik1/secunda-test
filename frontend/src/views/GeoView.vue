<template>
  <div class="space-y-4">
    <div class="space-y-1">
      <h1 class="text-xl font-semibold">Геопоиск</h1>
      <p class="text-sm text-muted-foreground">
        Ручки: <code class="rounded bg-muted px-1">/organizations/geo/radius</code> и
        <code class="rounded bg-muted px-1">/organizations/geo/box</code>.
      </p>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader class="gap-3">
          <div class="font-medium">По радиусу</div>
          <div class="grid gap-3 sm:grid-cols-3">
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">lat</label>
              <Input v-model="lat" inputmode="decimal" placeholder="55.75" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">lon</label>
              <Input v-model="lon" inputmode="decimal" placeholder="37.62" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">radius_km</label>
              <Input v-model="radiusKm" inputmode="decimal" placeholder="1.0" />
            </div>
          </div>
          <div class="flex gap-2">
            <Button :disabled="loading" @click="searchRadius">Искать</Button>
            <Button :disabled="loading" variant="ghost" @click="clearResults">Сброс</Button>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader class="gap-3">
          <div class="font-medium">По прямоугольнику</div>
          <div class="grid gap-3 sm:grid-cols-2">
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">lat_min</label>
              <Input v-model="latMin" inputmode="decimal" placeholder="55.70" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">lat_max</label>
              <Input v-model="latMax" inputmode="decimal" placeholder="55.80" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">lon_min</label>
              <Input v-model="lonMin" inputmode="decimal" placeholder="37.55" />
            </div>
            <div>
              <label class="mb-1 block text-xs text-muted-foreground">lon_max</label>
              <Input v-model="lonMax" inputmode="decimal" placeholder="37.70" />
            </div>
          </div>
          <div class="flex gap-2">
            <Button :disabled="loading" variant="secondary" @click="searchBox">Искать</Button>
            <Button :disabled="loading" variant="ghost" @click="clearResults">Сброс</Button>
          </div>
        </CardHeader>
      </Card>
    </div>

    <Card>
      <CardHeader class="gap-2">
        <div class="flex items-center justify-between">
          <div class="font-medium">Результаты</div>
          <div class="text-sm text-muted-foreground">
            <span v-if="loading">Загрузка…</span>
            <span v-else>Найдено: {{ items.length }}</span>
          </div>
        </div>
        <div v-if="error" class="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">
          <div class="font-medium">Ошибка</div>
          <div class="text-muted-foreground">{{ error }}</div>
        </div>
      </CardHeader>

      <CardContent>
        <div class="grid gap-3">
          <div v-for="org in items" :key="org.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div>
                <div class="font-medium">{{ org.name }}</div>
                <div class="mt-1 text-sm text-muted-foreground">
                  <span class="font-mono">#{{ org.id }}</span>
                  <span class="mx-2">·</span>
                  {{ org.building.address }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Badge variant="secondary">тел: {{ org.phones.length }}</Badge>
                <Badge variant="outline">активн: {{ org.activities.length }}</Badge>
              </div>
            </div>
          </div>

          <div v-if="!loading && items.length === 0" class="rounded-lg border p-6 text-center text-sm text-muted-foreground">
            Пока пусто. Заполните параметры и нажмите «Искать».
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { apiGet } from '@/api/client'
import type { OrganizationOut } from '@/api/types'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import CardHeader from '@/components/ui/CardHeader.vue'
import Input from '@/components/ui/Input.vue'

const lat = ref<string>('')
const lon = ref<string>('')
const radiusKm = ref<string>('1')

const latMin = ref<string>('')
const latMax = ref<string>('')
const lonMin = ref<string>('')
const lonMax = ref<string>('')

const items = ref<OrganizationOut[]>([])
const loading = ref<boolean>(false)
const error = ref<string>('')

function toNumberOrNull(s: string): number | null {
  const t = s.trim()
  if (t.length === 0) return null
  const n = Number(t.replace(',', '.'))
  if (!Number.isFinite(n)) return null
  return n
}

async function searchRadius() {
  error.value = ''
  items.value = []

  const nLat = toNumberOrNull(lat.value)
  const nLon = toNumberOrNull(lon.value)
  const nRadius = toNumberOrNull(radiusKm.value)
  if (nLat === null || nLon === null || nRadius === null) {
    error.value = 'Нужно заполнить lat, lon и radius_km числами.'
    return
  }

  loading.value = true
  try {
    const res = await apiGet<OrganizationOut[]>('/organizations/geo/radius', {
      query: { lat: nLat, lon: nLon, radius_km: nRadius, limit: 500, offset: 0 },
    })
    items.value = res
  } catch (e) {
    items.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function searchBox() {
  error.value = ''
  items.value = []

  const nLatMin = toNumberOrNull(latMin.value)
  const nLatMax = toNumberOrNull(latMax.value)
  const nLonMin = toNumberOrNull(lonMin.value)
  const nLonMax = toNumberOrNull(lonMax.value)
  if (nLatMin === null || nLatMax === null || nLonMin === null || nLonMax === null) {
    error.value = 'Нужно заполнить lat_min/lat_max/lon_min/lon_max числами.'
    return
  }

  loading.value = true
  try {
    const res = await apiGet<OrganizationOut[]>('/organizations/geo/box', {
      query: { lat_min: nLatMin, lat_max: nLatMax, lon_min: nLonMin, lon_max: nLonMax, limit: 500, offset: 0 },
    })
    items.value = res
  } catch (e) {
    items.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function clearResults() {
  items.value = []
  error.value = ''
}
</script>

