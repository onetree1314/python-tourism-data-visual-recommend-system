import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    include: ['element-plus', '@element-plus/icons-vue'],
    exclude: ['redi']
  },
  build: {
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true
    },
    rollupOptions: {
      output: {
        // 抑制重复模块警告
        manualChunks: undefined
      }
    }
  },
  define: {
    // 全局定义，抑制redi警告
    'window.__REDI_WARN__': false
  }
})
