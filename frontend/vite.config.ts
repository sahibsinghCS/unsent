/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// The FastAPI backend serves /api on :8000 (`make dev-stub`). Both the dev server and
// `vite preview` proxy to it, so the UI always talks to a relative /api URL.
const proxy = { '/api': { target: process.env.FR_API ?? 'http://localhost:8000', changeOrigin: true } };

export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy },
  preview: { port: 4173, proxy },
  build: {
    outDir: 'dist',
    // Chart.js is the only large dependency; keep it in its own cached chunk.
    rollupOptions: { output: { manualChunks: { chart: ['chart.js', 'react-chartjs-2'] } } },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
  },
});
