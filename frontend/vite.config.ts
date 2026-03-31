import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import fs from 'fs'

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
  define: {
    __BACKEND_PORT__: JSON.stringify(backendPort),
  },
  server: {
    host: '0.0.0.0',
    port: frontendPort,
    cors: true,
    strictPort: false,
    hmr: {
      host: 'localhost'
    },
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${backendPort}`, 
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        ws: true  // 核心新增：开启 WebSocket 代理转发
      }
    }
  }
})