import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: ['app.daco-group.com', 'localhost', '100.86.194.83'],
    proxy: {
      '/api': {
        target: 'https://api.daco-group.com',
        changeOrigin: true,
      },
    },
  },
})