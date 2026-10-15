import { defineConfig } from 'vitest/config';
import path from 'node:path';

/**
 * THE CEILING OF THIS HARNESS
 *
 * This is a bare Vite config, not the app's own `vite.config.js`, so none of
 * SvelteKit's virtual modules exist here by default. `#lib` needs nothing: it
 * is a subpath import declared in package.json, which Vite resolves on its
 * own. The two aliases below stand in for `$app/env/public` and
 * `$app/env/private`, which SvelteKit generates from `src/env.js` at build and
 * dev time, so a plain vitest run cannot resolve them without a stub. Server
 * modules such as `#lib/api-helpers.js` and `#lib/server/relay.js` import them
 * at module scope.
 *
 * That is as far as this config goes. It resolves `#lib`, `$app/env/public`
 * and `$app/env/private` and nothing else: `$app/forms`, `$app/navigation`
 * and the rest of `$app/*` are all still unresolvable here, and there is no
 * Svelte plugin, so `.svelte` files cannot be compiled at all.
 * `include: ['src/**\/*.test.js']` will happily pick up a test placed
 * anywhere under `src/`, including next to a route module or a component, but
 * importing either from a test run through this config fails with an opaque
 * "Failed to resolve import" rather than a clear "not supported here".
 *
 * This harness therefore covers server modules only (`#lib/server/v2/*.js`
 * and similar, functions over `apiRequest` with no SvelteKit runtime
 * dependency). Testing a route module (`+page.server.js`, which pulls in
 * `$app/forms` via its actions) or a `.svelte` component means moving
 * `test: {}` into the app's own `vite.config.js`, where the `sveltekit()`
 * plugin already provides `$app/*` and Svelte compilation for free. That is a
 * real tradeoff, not a strict improvement: it also pulls `sentrySvelteKit()`
 * and `tailwindcss()` into every test run, which this standalone config exists
 * specifically to avoid.
 *
 * `path.resolve('./test/...')` below resolves against `process.cwd()`, not
 * against this file's location, so `pnpm test` (and `vitest` directly) must
 * be run from `frontend/`.
 */
export default defineConfig({
  test: {
    // Server modules only. They are plain functions over `apiRequest`, so they
    // need no DOM, and a node environment keeps the run fast.
    environment: 'node',
    include: ['src/**/*.test.js'],
    maxWorkers: '50%'
  },
  resolve: {
    alias: {
      '$app/env/public': path.resolve('./test/stubs/app-env-public.js'),
      '$app/env/private': path.resolve('./test/stubs/app-env-private.js')
    }
  }
});
