/**
 * Vite 构建配置
 * 【基础功能】前端开发服务器 + 打包工具
 * 【学习知识点】
 *   1. proxy — 开发时将 /api 请求转发到 FastAPI 后端 (localhost:8000)
 *      前端 fetch('/api/users') → Vite 自动转发到 http://localhost:8000/api/users
 *      这样就避免了跨域 CORS 问题（开发环境）
 *   2. 生产环境不会用这个 proxy，由 Nginx 或 FastAPI StaticFiles 处理
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000, // React 开发服务器端口
    proxy: {
      // 【关键】所有 /api 开头的请求，转发到 FastAPI 后端
      // 前端不用写完整 URL，直接 fetch('/api/users') 即可
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
