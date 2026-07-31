import { listGoals } from '$lib/server/v2/goals.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  return await listGoals(event);
}
