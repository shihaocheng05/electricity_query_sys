<template>
  <div class="admin-layout">
    <Sidebar class="admin-layout__sidebar" />
    <div class="admin-layout__main">
      <Header class="admin-layout__header" />
      <main class="admin-layout__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import Header from '@/components/Header.vue'
import Sidebar from '@/components/Sidebar.vue'

const router = useRouter()
const { isLoggedIn, initAuth } = useAuth()

onMounted(async () => {
  await initAuth()
  if (!isLoggedIn.value) {
    router.push('/login')
  }
})
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: var(--color-background);
}

.admin-layout__sidebar {
  width: 240px;
  flex-shrink: 0;
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
}

.admin-layout__main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-layout__header {
  height: 60px;
  flex-shrink: 0;
  background-color: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.admin-layout__content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

@media (max-width: 768px) {
  .admin-layout__sidebar {
    width: 80px;
  }
  
  .admin-layout__content {
    padding: 16px;
  }
}
</style>
