<template>
  <span
    :class="
      cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors',
        variantClass,
        props.class,
      )
    "
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    variant?: 'default' | 'secondary' | 'outline'
    class?: string
  }>(),
  {
    variant: 'default',
    class: '',
  },
)

const variantClass = computed(() => {
  if (props.variant === 'secondary') return 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
  if (props.variant === 'outline') return 'text-foreground'
  return 'bg-primary text-primary-foreground hover:bg-primary/90'
})
</script>

