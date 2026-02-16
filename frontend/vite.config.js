import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  proxy: {
    '/staff': { target: BACKEND_URL, changeOrigin: true },
    '/student': { target: BACKEND_URL, changeOrigin: true },
    '/socket.io': { target: BACKEND_URL, ws: true, changeOrigin: true },
  },
});
