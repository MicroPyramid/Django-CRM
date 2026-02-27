import { sentrySvelteKit } from "@sentry/sveltekit";
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sentrySvelteKit({
    org: "micropyramid-fa",
    project: "bottlecrm-app",
    sourceMapsUploadOptions: {
      enabled: process.env.NODE_ENV === 'production'
    }
  }), tailwindcss(), sveltekit()],
  optimizeDeps: {
    exclude: ['esm-env']
  }
});