import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from "@tailwindcss/vite";
// https://vite.dev/config/
export default defineConfig({
  plugins: [react(),tailwindcss()],

// vite.config.ts

  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000", // your Flask port
        changeOrigin: true,
      },
    },
  },
})
