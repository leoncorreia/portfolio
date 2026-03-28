import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8000";
  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      /** Fail if 5173 is taken — avoids silently moving to 5174+ and breaking mental model (proxy → :8000). */
      strictPort: true,
      proxy: {
        "/api": target,
        "/health": target,
      },
    },
  };
});
