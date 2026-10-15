import { sentrySvelteKit } from '@sentry/sveltekit/vite';
import tailwindcss from '@tailwindcss/vite';
import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  return {
    plugins: [
      sentrySvelteKit({
        org: 'micropyramid-fa',
        project: 'bottlecrm-app',
        authToken: env.SENTRY_AUTH_TOKEN,
        autoUploadSourceMaps: !!env.PUBLIC_SENTRY_DSN
      }),
      tailwindcss(),
      // SvelteKit 3 reads its config here; svelte.config.js is gone.
      // src/instrumentation.server.js is picked up because it exists.
      sveltekit({
        adapter: adapter(),
        prebundleSvelteLibraries: false,
        version: {
          pollInterval: 60000
        },
        tracing: {
          server: true
        }
      })
    ],
    ssr: {
      // A CSS-only package: its exports offer only the `style` condition. The
      // server build otherwise tries to externalise app.css's
      // `@import 'tw-animate-css'` as a Node module and fails to resolve it.
      noExternal: ['tw-animate-css']
    },
    server: {
      port: 5181,
      strictPort: true
    }
  };
});
