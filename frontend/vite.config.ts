/// <reference types="vitest" />
import { copyFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

// FastAPI serves dist/ with StaticFiles(html=True), which answers unknown paths with 404.html.
// Making 404.html a copy of index.html lets deep links like /chat/<id> load the app on refresh.
const spaFallback = (): Plugin => ({
  name: 'spa-404-fallback',
  apply: 'build',
  closeBundle() {
    copyFileSync(resolve(__dirname, 'dist/index.html'), resolve(__dirname, 'dist/404.html'));
  },
});

// The FastAPI backend serves /api on :8000 (`make dev-stub`). Both the dev server and
// `vite preview` proxy to it, so the UI always talks to a relative /api URL.
const proxy = { '/api': { target: process.env.FR_API ?? 'http://localhost:8000', changeOrigin: true } };

export default defineConfig({
  plugins: [react(), spaFallback()],
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
