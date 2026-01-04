import { createApp, type App as VueApp } from 'vue'
import Toast from '@/components/Toast.vue'

let toastInstance: any = null
let toastApp: VueApp | null = null

const initToast = () => {
  if (toastInstance) return toastInstance

  const container = document.createElement('div')
  document.body.appendChild(container)

  toastApp = createApp(Toast)
  toastInstance = toastApp.mount(container)

  return toastInstance
}

export const toast = {
  success: (message: string, duration?: number) => {
    const instance = initToast()
    instance.show(message, 'success', duration)
  },
  error: (message: string, duration?: number) => {
    const instance = initToast()
    instance.show(message, 'error', duration)
  },
  warning: (message: string, duration?: number) => {
    const instance = initToast()
    instance.show(message, 'warning', duration)
  },
  info: (message: string, duration?: number) => {
    const instance = initToast()
    instance.show(message, 'info', duration)
  }
}

// 便捷函数
export const showToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info', duration?: number) => {
  const instance = initToast()
  instance.show(message, type, duration)
}

// 清理函数（可选）
export const destroyToast = () => {
  if (toastApp) {
    toastApp.unmount()
    toastApp = null
    toastInstance = null
  }
}
