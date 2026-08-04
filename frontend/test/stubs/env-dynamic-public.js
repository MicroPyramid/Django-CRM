// Stub for SvelteKit's $env/dynamic/public, which does not exist outside a Vite/SvelteKit build.
// Unit tests here mock the network layer, so the value only has to be present, not correct.

export const env = {
  PUBLIC_DJANGO_API_URL: 'http://localhost:8000'
};
