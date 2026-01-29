<template>
  <div class="space-y-4">
    <div class="space-y-1">
      <h1 class="text-xl font-semibold">Здания</h1>
      <p class="text-sm text-muted-foreground">
        Список из <code class="rounded bg-muted px-1">/buildings</code> и организации в здании из
        <code class="rounded bg-muted px-1">/organizations/by-building/{building_id}</code>.
      </p>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader class="gap-3">
          <div class="flex items-center justify-between gap-2">
            <div class="font-medium">Список зданий</div>
            <Button :disabled="loading" size="sm" variant="secondary" @click="loadBuildings">Обновить</Button>
          </div>

          <div class="text-sm text-muted-foreground">
            <span v-if="loading">Загрузка…</span>
            <span v-else>Зданий: {{ buildings.length }}</span>
          </div>

          <div v-if="error" class="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">
            <div class="font-medium">Ошибка</div>
            <div class="text-muted-foreground">{{ error }}</div>
          </div>
        </CardHeader>

        <CardContent>
          <div class="grid gap-3">
            <div
              v-for="b in buildings"
              :key="b.id"
              class="rounded-lg border p-3 hover:bg-accent/40"
              :class="{ 'bg-accent/30': String(b.id) === selectedBuildingId }"
              role="button"
              tabindex="0"
              @click="selectBuilding(b.id)"
              @keydown.enter="selectBuilding(b.id)"
            >
              <div class="flex items-start justify-between gap-2">
                <div>
                  <div class="font-medium">{{ b.address }}</div>
                  <div class="mt-1 font-mono text-xs text-muted-foreground">
                    #{{ b.id }} · lat={{ b.latitude }}, lon={{ b.longitude }}
                  </div>
                </div>
                <Badge v-if="String(b.id) === selectedBuildingId" variant="secondary">выбрано</Badge>
              </div>
            </div>

            <div v-if="!loading && buildings.length === 0" class="rounded-lg border p-6 text-center text-sm text-muted-foreground">
              Нет зданий.
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader class="gap-2">
          <div class="flex items-center justify-between gap-2">
            <div class="font-medium">Организации в здании</div>
            <div class="text-sm text-muted-foreground">
              <span v-if="loading">Загрузка…</span>
              <span v-else-if="buildingId !== null">Найдено: {{ organizations.length }}</span>
              <span v-else>Выберите здание</span>
            </div>
          </div>

          <div v-if="buildingDetails" class="text-sm text-muted-foreground">
            <span class="font-mono">#{{ buildingDetails.id }}</span>
            <span class="mx-2">·</span>
            {{ buildingDetails.address }}
          </div>
        </CardHeader>

        <CardContent>
          <div class="grid gap-3">
            <div v-for="org in organizations" :key="org.id" class="rounded-lg border p-3">
              <div class="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <div class="font-medium">{{ org.name }}</div>
                  <div class="mt-1 text-sm text-muted-foreground">
                    <span class="font-mono">#{{ org.id }}</span>
                    <span class="mx-2">·</span>
                    тел: {{ org.phones.length }}
                  </div>
                </div>
                <div class="flex flex-wrap gap-2">
                  <Badge v-for="a in org.activities" :key="a.id" variant="secondary">L{{ a.level }} · {{ a.name }}</Badge>
                </div>
              </div>
            </div>

            <div v-if="!loading && buildingId !== null && organizations.length === 0" class="rounded-lg border p-6 text-center">
              <div class="text-sm text-muted-foreground">В этом здании организаций не найдено.</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
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

const buildings = ref<BuildingOut[]>([])
const organizations = ref<OrganizationOut[]>([])

const selectedBuildingId = ref<string>('')
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

const buildingDetails = computed<BuildingOut | null>(() => {
  const id = buildingId.value
  if (id === null) return null
  for (let i = 0; i < buildings.value.length; i += 1) {
    const b = buildings.value[i]
    if (b.id === id) return b
  }
  return null
})

async function loadBuildings() {
  error.value = ''
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
  organizations.value = []

  const id = buildingId.value
  if (id === null) return

  loading.value = true
  try {
    const res = await apiGet<OrganizationOut[]>(`/organizations/by-building/${id}`, {
      query: { limit: 200, offset: 0 },
    })
    organizations.value = res
  } catch (e) {
    organizations.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function selectBuilding(id: number) {
  selectedBuildingId.value = String(id)
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

