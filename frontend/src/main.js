import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'
import App from './App.vue'
import './style.css'

// 抑制redi重复加载警告
if (typeof window !== 'undefined') {
  window.__REDI_WARN__ = false
  // 重写console.warn来过滤redi警告
  const originalWarn = console.warn
  console.warn = function(...args) {
    const message = args.join(' ')
    // 过滤redi相关警告
    if (message.includes('[redi]') || 
        message.includes('redi more than once') ||
        message.includes('You are loading scripts of redi') ||
        message.includes('redi.wendell.fun')) {
      return // 忽略redi警告
    }
    originalWarn.apply(console, args)
  }
  
  // 也过滤console.error中的redi警告
  const originalError = console.error
  console.error = function(...args) {
    const message = args.join(' ')
    if (message.includes('[redi]') || 
        message.includes('redi more than once') ||
        message.includes('You are loading scripts of redi') ||
        message.includes('redi.wendell.fun')) {
      return // 忽略redi错误
    }
    originalError.apply(console, args)
  }
  
  // 拦截所有console输出，过滤redi相关
  const originalLog = console.log
  console.log = function(...args) {
    const message = args.join(' ')
    if (message.includes('[redi]') || 
        message.includes('redi more than once') ||
        message.includes('You are loading scripts of redi')) {
      return
    }
    originalLog.apply(console, args)
  }
}

const app = createApp(App)
const pinia = createPinia()

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus)

app.mount('#app')
