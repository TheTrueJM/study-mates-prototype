import { defineConfig, loadEnv } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const BACKEND_URL = env.VITE_BACKEND_URL || "http://localhost:5000";

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/staff": { target: BACKEND_URL + "/api", changeOrigin: true },
        "/student": { target: BACKEND_URL + "/api", changeOrigin: true },
        "/socket.io": { target: BACKEND_URL, ws: true, changeOrigin: true },
      },
    },
  }
});
