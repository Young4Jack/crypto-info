import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'

// 读取后端 config.json 中的端口配置
let frontendPort = 5173;
let backendPort = 8000;

try {
  const configPath = path.resolve(__dirname, '../backend/config.json');
  if (fs.existsSync(configPath)) {
    const configStr = fs.readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configStr);
    if (config.system_settings) {
      frontendPort = config.system_settings.frontend_port || 5173;
      backendPort = config.system_settings.backend_port || 8000;
    }
  }
} catch (e) {
  console.warn('读取后端 config.json 失败，将使用默认端口配置');
}

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: frontendPort,
    cors: true,
    strictPort: false,
    hmr: {
      host: '0.0.0.0'
    },
    // 【核心新增：Vite 本地反向代理配置】
    proxy: {
      '/api': {
        // 将所有以 /api 开头的请求，偷偷转发给本地运行的 Python 后端
        target: `http://127.0.0.1:${backendPort}`, 
        changeOrigin: true,
        // 重写路径：把 '/api' 抹除掉，防止后端路由匹配失败
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})