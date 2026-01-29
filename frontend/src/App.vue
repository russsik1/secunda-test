<template>
  <div class="min-h-dvh bg-background text-foreground">
    <header class="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
      <div class="mx-auto flex h-14 max-w-5xl items-center gap-4 px-4">
        <div class="font-semibold">Secunda</div>

        <nav class="flex items-center gap-3 text-sm text-muted-foreground">
          <RouterLink class="hover:text-foreground" to="/">Организации</RouterLink>
          <RouterLink class="hover:text-foreground" to="/buildings">Здания</RouterLink>
          <RouterLink class="hover:text-foreground" to="/activities">Виды деятельности</RouterLink>
          <RouterLink class="hover:text-foreground" to="/geo">Геопоиск</RouterLink>
        </nav>

        <div class="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          <span v-if="health.status === 'ok'">API: ok</span>
          <span v-else-if="health.status === 'error'">API: ошибка</span>
          <span v-else>API: …</span>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-6">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'

import { apiGet } from '@/api/client'

const health = reactive<{ status: 'idle' | 'ok' | 'error' }>({ status: 'idle' })

onMounted(async () => {
  try {
    const res = await apiGet<{ status: string }>('/health', { auth: 'none' })
    health.status = res.status === 'ok' ? 'ok' : 'error'
  } catch {
    health.status = 'error'
  }
})
</script>

