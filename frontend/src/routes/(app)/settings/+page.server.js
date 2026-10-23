import { getSettingsHub } from '#lib/server/v2/settings.js';
import { getModules } from '#lib/server/v2/modules.js';

/** @type {import('./$types').PageServerLoad} */
export async function load(event) {
  // One read decides which calls run and which rows show, so they agree.
  const modulesP = getModules(event).then((answer) => answer?.modules ?? null);
  const hub = await getSettingsHub(event, modulesP);
  return { ...hub, modules: await modulesP };
}
