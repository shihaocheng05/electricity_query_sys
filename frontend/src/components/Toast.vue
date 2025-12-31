<template>
  <Teleport to="body">
    <transition-group name="toast" tag="div" class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', `toast-${toast.type}`]"
      >
        <span class="toast-icon">{{ getIcon(toast.type) }}</span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </transition-group>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

const toasts = ref<Toast[]>([])
let toastId = 0

const getIcon = (type: string) => {
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  }
  return icons[type as keyof typeof icons] || 'ℹ'
}

const show = (message: string, type: Toast['type'] = 'info', duration = 3000) => {
  const id = toastId++
  toasts.value.push({ id, message, type })
  
  setTimeout(() => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }, duration)
}

defineExpose({ show })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 300px;
  padding: 16px 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: auto;
  font-size: 14px;
  line-height: 1.5;
}

.toast-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  font-weight: bold;
  flex-shrink: 0;
}

.toast-success {
  border-left: 4px solid #67c23a;
}

.toast-success .toast-icon {
  background: #67c23a;
  color: white;
}

.toast-error {
  border-left: 4px solid #f56c6c;
}

.toast-error .toast-icon {
  background: #f56c6c;
  color: white;
}

.toast-warning {
  border-left: 4px solid #e6a23c;
}

.toast-warning .toast-icon {
  background: #e6a23c;
  color: white;
}

.toast-info {
  border-left: 4px solid #409eff;
}

.toast-info .toast-icon {
  background: #409eff;
  color: white;
}

.toast-message {
  flex: 1;
  color: var(--color-text-primary);
}

/* 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}
</style>
