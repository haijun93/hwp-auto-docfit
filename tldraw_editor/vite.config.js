import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: '../flutter_ui/assets/diagram_editor',
    emptyOutDir: true,
    manifest: 'asset-manifest.json',
  },
});
