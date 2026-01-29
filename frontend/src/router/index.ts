import { createRouter, createWebHistory } from 'vue-router'

import OrganizationsView from '@/views/OrganizationsView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'organizations', component: OrganizationsView },
    { path: '/buildings', name: 'buildings', component: () => import('@/views/BuildingsView.vue') },
    { path: '/activities', name: 'activities', component: () => import('@/views/ActivitiesView.vue') },
    { path: '/geo', name: 'geo', component: () => import('@/views/GeoView.vue') },
  ],
})

