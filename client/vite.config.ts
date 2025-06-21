import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
	base: "/",
	plugins: [react(), tailwindcss()],
	preview: {
		port: 8081,
		strictPort: true,
	},
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "./src"),
		},
	},
	server: {
		host: true,
		origin: "http://0.0.0.0:8081",
		port: 8081,
		proxy: {
			"/api/genai": "http://localhost:3003/api/genai",
			"/api/repositories": "http://localhost:8080/api/repositories",
			"/api/search": "http://localhost:8082/api/search",
		},
		strictPort: true,
	},
});
