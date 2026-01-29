<template>
  <div class="space-y-4">
    <div class="space-y-1">
      <h1 class="text-xl font-semibold">Виды деятельности</h1>
      <p class="text-sm text-muted-foreground">
        Список из <code class="rounded bg-muted px-1">/activities</code>. По выбранному виду:
        <code class="rounded bg-muted px-1">/organizations/by-activity/{activity_id}</code> или
        <code class="rounded bg-muted px-1">/organizations/search/by-activity-tree/{activity_id}</code>.
      </p>
    </div>

    <Card>
      <CardHeader class="gap-3">
        <div class="grid gap-3 sm:grid-cols-2">
          <div>
            <label class="mb-1 block text-xs text-muted-foreground">Вид деятельности</label>
            <select v-model="selectedActivityId" class="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option :value="''">—</option>
              <option v-for="a in activities" :key="a.id" :value="String(a.id)">
                {{ activityLabel(a) }}
              </option>
            </select>
          </div>

          <div>
            <label class="mb-1 block text-xs text-muted-foreground">Режим</label>
            <select v-model="mode" class="h-9 w-full rounded-md border border-input bg-background px-3 text-sm">
              <option value="exact">Только выбранный вид</option>
              <option value="tree">Выбранный + подкатегории (до 3 уровней)</option>
            </select>
          </div>
        </div>

        <div class="flex flex-wrap gap-2">
          <Button :disabled="loading" variant="secondary" @click="loadActivities">Обновить список</Button>
          <Button :disabled="loading || activityId === null" @click="loadOrganizations">Показать организации</Button>
          <Button :disabled="loading" variant="ghost" @click="onClear">Сброс</Button>
        </div>

        <div v-if="error" class="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">
          <div class="font-medium">Ошибка</div>
          <div class="text-muted-foreground">{{ error }}</div>
        </div>
      </CardHeader>

      <CardContent class="space-y-3">
        <div class="text-sm text-muted-foreground">
          <span v-if="loading">Загрузка…</span>
          <span v-else>Видов: {{ activities.length }}</span>
        </div>

        <div v-if="activityDetails" class="rounded-lg border p-3">
          <div class="font-medium">{{ activityDetails.name }}</div>
          <div class="mt-1 font-mono text-xs text-muted-foreground">
            #{{ activityDetails.id }} · level={{ activityDetails.level }} · parent_id={{ activityDetails.parent_id ?? 'null' }}
          </div>
        </div>

        <div class="grid gap-3">
          <div v-if="!loading && organizations.length > 0" class="text-sm font-medium">
            Организации: {{ organizations.length }}
          </div>

          <div v-for="org in organizations" :key="org.id" class="rounded-lg border p-3">
            <div class="flex flex-wrap items-start justify-between gap-2">
              <div>
                <div class="font-medium">{{ org.name }}</div>
                <div class="mt-1 text-sm text-muted-foreground">
                  <span class="font-mono">#{{ org.id }}</span>
                  <span class="mx-2">·</span>
                  {{ org.building.address }}
                </div>
              </div>
              <div class="flex flex-wrap gap-2">
                <Badge v-for="a in org.activities" :key="a.id" variant="secondary">L{{ a.level }} · {{ a.name }}</Badge>
              </div>
            </div>
          </div>

          <div v-if="!loading && activityId !== null && organizations.length === 0" class="rounded-lg border p-6 text-center">
            <div class="text-sm text-muted-foreground">По этому виду деятельности организаций не найдено.</div>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { apiGet } from '@/api/client'
import type { ActivityOut, OrganizationOut } from '@/api/types'
import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import CardContent from '@/components/ui/CardContent.vue'
import CardHeader from '@/components/ui/CardHeader.vue'

type Mode = 'exact' | 'tree'

const activities = ref<ActivityOut[]>([])
const organizations = ref<OrganizationOut[]>([])

const selectedActivityId = ref<string>('')
const mode = ref<Mode>('tree')

const loading = ref<boolean>(false)
const error = ref<string>('')

const activityId = computed<number | null>(() => {
  const s = selectedActivityId.value.trim()
  if (s.length === 0) return null
  const n = Number(s)
  if (!Number.isFinite(n)) return null
  if (!Number.isInteger(n)) return null
  if (n <= 0) return null
  return n
})

const activityDetails = computed<ActivityOut | null>(() => {
  const id = activityId.value
  if (id === null) return null
  for (let i = 0; i < activities.value.length; i += 1) {
    const a = activities.value[i]
    if (a.id === id) return a
  }
  return null
})

function activityLabel(a: ActivityOut): string {
  let indent = ''
  for (let i = 1; i < a.level; i += 1) {
    indent += '—'
  }
  if (indent.length > 0) indent += ' '
  return `${indent}${a.name} (#${a.id})`
}

async function loadActivities() {
  error.value = ''
  loading.value = true
  try {
    const res = await apiGet<ActivityOut[]>('/activities', { query: { limit: 2000, offset: 0 } })
    activities.value = res
  } catch (e) {
    activities.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

async function loadOrganizations() {
  error.value = ''
  organizations.value = []

  const id = activityId.value
  if (id === null) return

  loading.value = true
  try {
    if (mode.value === 'exact') {
      const res = await apiGet<OrganizationOut[]>(`/organizations/by-activity/${id}`, { query: { limit: 200, offset: 0 } })
      organizations.value = res
    } else {
      const res = await apiGet<OrganizationOut[]>(`/organizations/search/by-activity-tree/${id}`, {
        query: { limit: 500, offset: 0 },
      })
      organizations.value = res
    }
  } catch (e) {
    organizations.value = []
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

function onClear() {
  selectedActivityId.value = ''
  organizations.value = []
  error.value = ''
}

onMounted(async () => {
  await loadActivities()
})
</script>

