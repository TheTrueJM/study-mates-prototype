import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Vite config exported as a function so we can load environment variables
export default ({ mode }) => {
  // Merge all env variables into process.env so import.meta.env works in the client
  const env = loadEnv(mode, process.cwd(), '');
  const BACKEND_URL = env.VITE_BACKEND_URL || 'http://localhost:5000';

  return defineConfig({
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
};
