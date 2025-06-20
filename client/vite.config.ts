import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  preview: {
    port: 8081,
    strictPort: true,
  },
  server: {
    proxy: {
      "/api/repositories": "http://localhost:8080/api/repositories",
      "/api/search": "http://localhost:8082/api/search",
      "/api/genai": "http://localhost:3003/api/genai",
    },
    port: 8081,
    strictPort: true,
    host: true,
    origin: "http://0.0.0.0:8081",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
