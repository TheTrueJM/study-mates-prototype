import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  proxy: {
    '/staff': { target: 'https://study-mates-deployment.onrender.com', changeOrigin: true },
    '/student': { target: 'https://study-mates-deployment.onrender.com', changeOrigin: true },
    '/socket.io': { target: 'https://study-mates-deployment.onrender.com', ws: true, changeOrigin: true },
  },
});
