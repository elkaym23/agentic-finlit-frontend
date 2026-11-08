import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs on :7860 (uvicorn); Vite proxies /api to it.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:7860" },
  },
});
