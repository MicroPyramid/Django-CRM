import adapter from '@sveltejs/adapter-node';

const config = { vitePlugin: {
  prebundleSvelteLibraries: false
}, kit: {
  adapter: adapter(),

  version: {
    pollInterval: 60000
  },

  experimental: {
    tracing: {
      server: true
    },

    instrumentation: {
      server: true
    }
  }
} };

export default config;