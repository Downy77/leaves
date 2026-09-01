import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    host: "0.0.0.0",
    port: 5188,
    proxy: {
      "/auth": "http://127.0.0.1:8000",
      "/chat": "http://127.0.0.1:8000",
      "/documents": "http://127.0.0.1:8000",
      "/qa": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
    },
  },
});
