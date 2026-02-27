import { sentrySvelteKit } from "@sentry/sveltekit";
import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sentrySvelteKit({
    org: "micropyramid-fa",
    project: "bottlecrm-app",
    autoUploadSourceMaps: !!process.env.PUBLIC_SENTRY_DSN
  }), tailwindcss(), sveltekit()],
  optimizeDeps: {
    exclude: ['esm-env']
  }
});