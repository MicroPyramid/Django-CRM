// Stub for SvelteKit's $app/env/private, which does not exist outside a Vite/SvelteKit build.
// Unset by default, like a server with nothing configured. Module exports are read-only, so a
// test that needs a value calls `setRelaySecret` and clears it with `setRelaySecret(undefined)`.

/** @type {string | undefined} */
export let RELAY_SECRET;

/** @param {string | undefined} value */
export function setRelaySecret(value) {
  RELAY_SECRET = value;
}
