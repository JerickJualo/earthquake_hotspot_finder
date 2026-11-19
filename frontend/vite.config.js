import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          mapping: ["leaflet", "react-leaflet"],
          charts: ["recharts"],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
  },
});
