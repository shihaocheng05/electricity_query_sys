import { createApp, type App as VueApp } from 'vue'
import Loading from '@/components/Loading.vue'

let loadingInstance: any = null
let loadingApp: VueApp | null = null

const initLoading = () => {
  if (loadingInstance) return loadingInstance

  const container = document.createElement('div')
  document.body.appendChild(container)

  loadingApp = createApp(Loading)
  loadingInstance = loadingApp.mount(container)

  return loadingInstance
}

export const loading = {
  show: (text?: string) => {
    const instance = initLoading()
    instance.show(text)
  },
  hide: () => {
    if (loadingInstance) {
      loadingInstance.hide()
    }
  }
}

export const destroyLoading = () => {
  if (loadingApp) {
    loadingApp.unmount()
    loadingApp = null
    loadingInstance = null
  }
}
