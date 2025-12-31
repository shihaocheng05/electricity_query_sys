<template>
  <div class="notification-bell">
    <div class="notification-bell__icon" @click="toggleDropdown">
      🔔
      <span v-if="unreadCount > 0" class="notification-bell__badge">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </div>
    
    <div v-if="showDropdown" class="notification-bell__dropdown" @click.stop>
      <div class="notification-bell__header">
        <h3>通知消息</h3>
        <button v-if="unreadCount > 0" @click="markAllAsRead" class="notification-bell__mark-all">
          全部已读
        </button>
      </div>
      
      <div class="notification-bell__list">
        <div
          v-for="notification in notifications"
          :key="notification.notice_id"
          class="notification-bell__item"
          :class="{ 'notification-bell__item--unread': notification.status === 0 }"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-bell__item-content">
            <p class="notification-bell__item-title">{{ notification.title }}</p>
            <p class="notification-bell__item-message">{{ notification.content }}</p>
            <span class="notification-bell__item-time">{{ formatTime(notification.send_time) }}</span>
          </div>
          <span v-if="notification.status === 0" class="notification-bell__item-dot"></span>
        </div>
        
        <div v-if="notifications.length === 0" class="notification-bell__empty">
          <p>暂无通知消息</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { notificationApi } from '@/services/api/notification'

interface Notification {
  notice_id: number
  title: string
  content: string
  send_time: string
  status: number // 0-未读, 1-已读
}

const showDropdown = ref(false)
const notifications = ref<Notification[]>([])

const unreadCount = computed(() => {
  return notifications.value.filter(n => n.status === 0).length
})

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value) {
    loadNotifications()
  }
}

const loadNotifications = async () => {
  try {
    const response = await notificationApi.queryNotifications({
      page: 1,
      page_size: 10
    })
    if (response.code === 200 && response.data) {
      notifications.value = response.data.notifications || []
    }
  } catch (error) {
    console.error('加载通知失败:', error)
  }
}

const handleNotificationClick = async (notification: Notification) => {
  if (notification.status === 0) {
    try {
      await notificationApi.updateNotificationStatus({
        notice_ids: [notification.notice_id],
        status: 1
      })
      notification.status = 1
    } catch (error) {
      console.error('标记通知已读失败:', error)
    }
  }
  showDropdown.value = false
}

const markAllAsRead = async () => {
  const unreadIds = notifications.value
    .filter(n => n.status === 0)
    .map(n => n.notice_id)
  
  if (unreadIds.length === 0) return
  
  try {
    await notificationApi.updateNotificationStatus({
      notice_ids: unreadIds,
      status: 1
    })
    notifications.value.forEach(n => {
      if (n.status === 0) n.status = 1
    })
  } catch (error) {
    console.error('标记全部已读失败:', error)
  }
}

const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}小时前`
  
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.notification-bell')) {
    showDropdown.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  loadNotifications() // 初始加载获取未读数量
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.notification-bell__icon {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.notification-bell__icon:hover {
  background-color: var(--color-background-hover);
}

.notification-bell__badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 9px;
  background-color: #f56c6c;
  color: white;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.notification-bell__dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 480px;
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

.notification-bell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
}

.notification-bell__header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.notification-bell__mark-all {
  padding: 4px 12px;
  border: none;
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-bell__mark-all:hover {
  background-color: var(--color-primary);
  color: white;
}

.notification-bell__list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-bell__item {
  position: relative;
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.2s;
}

.notification-bell__item:hover {
  background-color: var(--color-background-hover);
}

.notification-bell__item--unread {
  background-color: #f0f7ff;
}

.notification-bell__item-content {
  padding-right: 20px;
}

.notification-bell__item-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.notification-bell__item-message {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-bell__item-time {
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.notification-bell__item-dot {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-primary);
}

.notification-bell__empty {
  padding: 48px 16px;
  text-align: center;
}

.notification-bell__empty p {
  margin: 0;
  color: var(--color-text-tertiary);
  font-size: 14px;
}

@media (max-width: 480px) {
  .notification-bell__dropdown {
    width: 320px;
    right: -100px;
  }
}
</style>
