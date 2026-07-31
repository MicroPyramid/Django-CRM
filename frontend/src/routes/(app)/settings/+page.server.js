import { getSettingsHub } from '$lib/server/v2/settings.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  return getSettingsHub(event);
}
