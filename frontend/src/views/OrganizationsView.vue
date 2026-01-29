<template>
  <div class="space-y-4">
    <div class="space-y-1">
      <h1 class="text-xl font-semibold">Организации</h1>
      <p class="text-sm text-muted-foreground">
        Здесь нет “общего списка” организаций — в API есть выборки по фильтрам.
        Этот экран грузит организации через
        <code class="rounded bg-muted px-1">/organizations/by-building/{building_id}</code>
        и детали через <code class="rounded bg-muted px-1">/organizations/{id}</code>.
      </p>
    </div>

    <Card>
      <CardHeader class="gap-3">
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs text-muted-foreground">Здание</label>
            <select
              v-model="selectedBuildingId"
              class="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            >
              <option :value="''">—</option>
              <option v-for="b in buildings" :key="b.id" :value="String(b.id)">
                #{{ b.id }} · {{ b.address }}
              </option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-xs text-muted-foreground">Открыть по ID организации</label>
            <Input v-model="orgIdRaw" inputmode="numeric" placeholder="Напр: 1" @keydown.enter="onLoadById" />
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <Button :disabled="loading" variant="secondary" @click="loadBuildings">Обновить здания</Button>
          <Button :disabled="loading || buildingId === null" variant="default" @click="loadOrganizations">
            Загрузить организации
          </Button>
          <Button :disabled="loading || orgId === null" variant="outline" @click="onLoadById">Открыть по ID</Button>
          <Button :disabled="loading" variant="ghost" @click="onClear">Сброс</Button>
        </div>

        <div v-if="error" class="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">
          <div class="font-medium">Ошибка</div>
          <div class="text-muted-foreground">{{ error }}</div>
        </div>
      </CardHeader>

      <CardContent>
        <div class="flex items-center justify-between">
          <div class="text-sm text-muted-foreground">
            <span v-if="loading">Загрузка…</span>
            <span v-else>Организаций: {{ items.length }}</span>
          </div>
        </div>

        <div class="mt-3 grid gap-3">
          <div
            v-for="org in items"
            :key="org.id"
            class="rounded-lg border p-3 hover:bg-accent/40"
            role="button"
            tabindex="0"
            @click="openDetails(org.id)"
            @keydown.enter="openDetails(org.id)"
          >
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
            Нет данных. Выберите здание и нажмите «Загрузить организации».
          </div>
        </div>
      </CardContent>
    </Card>

    <Card v-if="selected">
      <CardHeader class="gap-2">
        <div class="flex items-start justify-between gap-3">
          <div>
            <div class="text-xs text-muted-foreground">Детали организации</div>
            <div class="text-lg font-semibold">{{ selected.name }}</div>
            <div class="mt-1 text-sm text-muted-foreground">
              <span class="font-mono">#{{ selected.id }}</span>
              <span class="mx-2">·</span>
              {{ selected.building.address }}
            </div>
          </div>
          <Button variant="ghost" @click="selected = null">Закрыть</Button>
        </div>
      </CardHeader>

      <CardContent class="space-y-3">
        <div class="grid gap-3 sm:grid-cols-2">
          <div class="rounded-lg border p-3">
            <div class="text-xs font-medium text-muted-foreground">Телефоны</div>
            <div class="mt-2 space-y-1">
              <div v-if="selected.phones.length === 0" class="text-sm text-muted-foreground">Нет</div>
              <div v-for="p in selected.phones" :key="p" class="font-mono text-sm">{{ p }}</div>
            </div>
          </div>
          <div class="rounded-lg border p-3">
            <div class="text-xs font-medium text-muted-foreground">Здание</div>
            <div class="mt-2 text-sm">
              <div class="font-medium">{{ selected.building.address }}</div>
              <div class="mt-1 font-mono text-xs text-muted-foreground">
                lat={{ selected.building.latitude }}, lon={{ selected.building.longitude }}
              </div>
            </div>
          </div>
        </div>

        <div class="rounded-lg border p-3">
          <div class="text-xs font-medium text-muted-foreground">Виды деятельности</div>
          <div class="mt-2 flex flex-wrap gap-2">
            <div v-if="selected.activities.length === 0" class="text-sm text-muted-foreground">Нет</div>
            <Badge v-for="a in selected.activities" :key="a.id" variant="secondary">
              L{{ a.level }} · {{ a.name }}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { apiGet } from '@/api/client'
import type { BuildingOut, OrganizationOut } from '@/api/types'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import CardHeader from '@/components/ui/CardHeader.vue'
import Input from '@/components/ui/Input.vue'

const orgIdRaw = ref<string>('')

const buildings = ref<BuildingOut[]>([])
const selectedBuildingId = ref<string>('')

const items = ref<OrganizationOut[]>([])
const selected = ref<OrganizationOut | null>(null)
const loading = ref<boolean>(false)
const error = ref<string>('')

const buildingId = computed<number | null>(() => {
  const s = selectedBuildingId.value.trim()
  if (s.length === 0) return null
  const n = Number(s)
  if (!Number.isFinite(n)) return null
  if (!Number.isInteger(n)) return null
  if (n <= 0) return null
  return n
})

const orgId = computed<number | null>(() => {
  const s = orgIdRaw.value.trim()
  if (s.length === 0) return null
  const n = Number(s)
  if (!Number.isFinite(n)) return null
  if (!Number.isInteger(n)) return null
  if (n <= 0) return null
  return n
})

async function loadBuildings() {
  error.value = ''
  selected.value = null
  loading.value = true
  try {
    const res = await apiGet<BuildingOut[]>('/buildings', { query: { limit: 1000, offset: 0 } })
    buildings.value = res
    if (buildings.value.length > 0 && selectedBuildingId.value.trim().length === 0) {
      selectedBuildingId.value = String(buildings.value[0].id)
    }
  } catch (e) {
    buildings.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function loadOrganizations() {
  error.value = ''
  selected.value = null
  items.value = []

  const id = buildingId.value
  if (id === null) return

  loading.value = true
  try {
    const res = await apiGet<OrganizationOut[]>(`/organizations/by-building/${id}`, { query: { limit: 200, offset: 0 } })
    items.value = res
  } catch (e) {
    items.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function onLoadById() {
  error.value = ''
  const id = orgId.value
  if (id === null) return

  loading.value = true
  try {
    const res = await apiGet<OrganizationOut>(`/organizations/${id}`)
    selected.value = res
  } catch (e) {
    selected.value = null
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function openDetails(id: number) {
  orgIdRaw.value = String(id)
  await onLoadById()
}

function onClear() {
  orgIdRaw.value = ''
  selectedBuildingId.value = ''
  buildings.value = []
  items.value = []
  selected.value = null
  error.value = ''
}

watch(
  () => selectedBuildingId.value,
  async () => {
    if (selectedBuildingId.value.trim().length === 0) return
    await loadOrganizations()
  },
)

onMounted(async () => {
  await loadBuildings()
  await loadOrganizations()
})
</script>

