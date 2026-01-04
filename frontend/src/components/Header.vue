<template>
  <header class="header">
    <div class="header__left">
      <h2 class="header__title">⚡ 用电信息系统</h2>
    </div>
    
    <div class="header__right">
      <NotificationBell class="header__notification" />
      
      <div class="header__user" @click="toggleUserMenu">
        <div class="header__avatar">{{ userInitial }}</div>
        <span class="header__username">{{ user?.username || '用户' }}</span>
        <span class="header__role-badge">{{ roleName }}</span>
        
        <div v-if="showUserMenu" class="header__dropdown" @click.stop>
          <div class="header__dropdown-item" @click="goToSettings">
            <span class="icon">⚙️</span>
            <span>个人设置</span>
          </div>
          <div class="header__dropdown-divider"></div>
          <div class="header__dropdown-item" @click="handleLogout">
            <span class="icon">🚪</span>
            <span>退出登录</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import NotificationBell from './NotificationBell.vue'

const router = useRouter()
const { user, logout } = useAuth()

const showUserMenu = ref(false)

const userInitial = computed(() => {
  return user.value?.username?.charAt(0).toUpperCase() || 'U'
})

const roleName = computed(() => {
  const roleMap: Record<number, string> = {
    1: '超级管理员',
    2: '片区管理员',
    3: '居民'
  }
  return roleMap[user.value?.role || 3] || '用户'
})

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const goToSettings = () => {
  showUserMenu.value = false
  router.push('/settings')
}

const handleLogout = async () => {
  showUserMenu.value = false
  await logout()
  router.push('/login')
}

// 点击外部关闭菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.header__user')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
}

.header__left {
  display: flex;
  align-items: center;
}

.header__title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header__right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header__notification {
  cursor: pointer;
}

.header__user {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.header__user:hover {
  background-color: var(--color-background-hover);
}

.header__avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
}

.header__username {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.header__role-badge {
  padding: 4px 8px;
  border-radius: 4px;
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 500;
}

.header__dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  min-width: 180px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  z-index: 1000;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header__dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 14px;
  color: var(--color-text-primary);
}

.header__dropdown-item:hover {
  background-color: var(--color-background-hover);
}

.header__dropdown-item .icon {
  font-size: 18px;
}

.header__dropdown-divider {
  height: 1px;
  background-color: var(--color-border);
  margin: 4px 0;
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .header__title {
    font-size: 18px;
  }
  
  .header__username {
    display: none;
  }
}
</style>
