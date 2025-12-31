<template>
  <aside class="sidebar">
    <nav class="sidebar__nav">
      <router-link
        v-for="item in visibleMenuItems"
        :key="item.path"
        :to="item.path"
        class="sidebar__item"
        :class="{ 'sidebar__item--active': isActive(item.path) }"
      >
        <span class="sidebar__icon">{{ item.icon }}</span>
        <span class="sidebar__label">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const { user } = useAuth()

interface MenuItem {
  path: string
  label: string
  icon: string
  roles?: string[] // 允许访问的角色，不设置表示所有角色都可访问
}

const menuItems: MenuItem[] = [
  {
    path: '/dashboard',
    label: '仪表盘',
    icon: '📊'
  },
  {
    path: '/usage-analysis',
    label: '用电分析',
    icon: '📈'
  },
  {
    path: '/region-analysis',
    label: '片区分析',
    icon: '🗺️',
    roles: ['super_admin', 'area_admin'] // 仅管理员可见
  },
  {
    path: '/admin',
    label: '系统管理',
    icon: '🔧',
    roles: ['super_admin'] // 仅超级管理员可见
  },
  {
    path: '/bills',
    label: '账单管理',
    icon: '💰'
  },
  {
    path: '/settings',
    label: '设置',
    icon: '⚙️'
  }
]

// 根据用户角色过滤菜单项
const visibleMenuItems = computed(() => {
  return menuItems.filter(item => {
    if (!item.roles) return true
    const userRole = user.value?.role || 'resident'
    return item.roles.includes(userRole)
  })
})

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<style scoped>
.sidebar {
  height: 100%;
  padding: 24px 0;
  overflow-y: auto;
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0 12px;
}

.sidebar__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--color-text-secondary);
  transition: all 0.2s;
  position: relative;
}

.sidebar__item:hover {
  background-color: var(--color-background-hover);
  color: var(--color-text-primary);
}

.sidebar__item--active {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}

.sidebar__item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 24px;
  background: var(--color-primary);
  border-radius: 0 4px 4px 0;
}

.sidebar__icon {
  font-size: 20px;
  flex-shrink: 0;
}

.sidebar__label {
  font-size: 14px;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .sidebar {
    padding: 16px 0;
  }
  
  .sidebar__nav {
    padding: 0 8px;
  }
  
  .sidebar__label {
    display: none;
  }
  
  .sidebar__item {
    justify-content: center;
    padding: 12px 8px;
  }
}
</style>
