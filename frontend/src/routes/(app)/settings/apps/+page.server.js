import { fail, redirect } from '@sveltejs/kit';
import {
  getModules,
  moduleErrors,
  moveBody,
  putModules,
  switchBody
} from '#lib/server/v2/modules.js';
import {
  appRefusal,
  installApp,
  isAppAction,
  isAppId,
  listApps,
  previewApp,
  removeApp,
  upgradeApp
} from '#lib/server/v2/apps.js';
import { clearSampleData } from '#lib/server/packs.js';
import { readableError } from '#lib/server/v2/form-errors.js';
import { viewerIsAdmin } from '#lib/server/v2/organization.js';

/**
 * Settings › Apps: industry apps above the modules. `?app=<id>&do=<action>`
 * opens the confirmation for one app with the server's preview, and an action
 * that succeeds lands on `?done=<action>&app=<id>`, so the page reads the new
 * state rather than the old preview.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const { cookies, url } = event;
  const [answer, apps] = await Promise.all([getModules(event), listApps(cookies)]);
  // The modules answer is the server's word on who may edit; without it, the token's claim.
  const canEdit = answer ? answer.canEdit : viewerIsAdmin(cookies);
  if (!canEdit) return { forbidden: true };

  const known = (/** @type {string | null} */ id) => apps.apps.find((a) => a.id === id) ?? null;

  /** @type {any} */
  let confirm = null;
  const id = url.searchParams.get('app');
  const action = url.searchParams.get('do');
  if (apps.state === 'ok' && known(id) && isAppAction(action)) {
    try {
      const preview = await previewApp(cookies, /** @type {string} */ (id), String(action));
      confirm = { app: id, action, preview, error: '' };
    } catch (/** @type {any} */ err) {
      confirm = { app: id, action, preview: null, error: appRefusal(err, String(action)) };
    }
  }

  const doneAction = url.searchParams.get('done');
  const done = isAppAction(doneAction) && known(id) ? { action: doneAction, app: id } : null;

  return {
    modules: answer?.modules ?? null,
    modulesFailed: !answer,
    apps,
    confirm,
    done
  };
}

/**
 * Re-reads the list, builds the body from it and writes it.
 *
 * @param {any} event
 * @param {string} key
 * @param {(rows: import('#lib/v2/modules.js').ModuleRow[]) => { off: string[], order: string[] } | null} build
 */
async function writeModules(event, key, build) {
  const answer = await getModules(event);
  if (!answer) return fail(400, { errors: ['Modules could not be loaded.'], key });
  if (!answer.canEdit) {
    return fail(403, { errors: ['Only an organization admin can switch modules on or off.'], key });
  }
  const body = build(answer.modules);
  if (!body) return fail(400, { errors: ['That module could not be changed.'], key });
  try {
    await putModules(event, body);
  } catch (/** @type {any} */ err) {
    return fail(err?.status === 403 ? 403 : 400, { errors: moduleErrors(err), key });
  }
  return { saved: true };
}

/**
 * @param {any} event
 * @param {'install' | 'upgrade' | 'remove'} action
 */
async function appAction(event, action) {
  const form = await event.request.formData();
  const id = form.get('app')?.toString() ?? '';
  if (!isAppId(id)) return fail(400, { appError: 'That app is not in the catalogue.', app: id });
  try {
    if (action === 'install') {
      // An unticked box submits nothing, so absent is an explicit no.
      await installApp(event.cookies, id, form.get('sample_data') === 'on');
    } else if (action === 'upgrade') {
      await upgradeApp(event.cookies, id);
    } else {
      await removeApp(event.cookies, id);
    }
  } catch (/** @type {any} */ err) {
    const status = [403, 404, 409].includes(err?.status) ? err.status : 400;
    return fail(status, { appError: appRefusal(err, action), app: id });
  }
  redirect(303, `/settings/apps?done=${action}&app=${encodeURIComponent(id)}`);
}

/** @type {import('./$types').Actions} */
export const actions = {
  install: (event) => appAction(event, 'install'),
  upgrade: (event) => appAction(event, 'upgrade'),
  remove: (event) => appAction(event, 'remove'),

  async switch(event) {
    const form = await event.request.formData();
    const key = form.get('key')?.toString() ?? '';
    const on = form.get('on')?.toString();
    if (on !== 'true' && on !== 'false') {
      return fail(400, { errors: ['That module could not be changed.'], key });
    }
    return writeModules(event, key, (rows) => switchBody(rows, key, on === 'true'));
  },

  async move(event) {
    const form = await event.request.formData();
    const key = form.get('key')?.toString() ?? '';
    const direction = form.get('direction')?.toString() ?? '';
    return writeModules(event, key, (rows) => moveBody(rows, key, direction));
  },

  clearSampleData: async ({ cookies }) => {
    try {
      const { deleted, retained_by_type } = await clearSampleData(cookies);
      // Kept records are sample rows someone has since attached real work to.
      const retained = Object.values(retained_by_type ?? {}).reduce((a, b) => a + b, 0);
      return { cleared: deleted ?? 0, retained };
    } catch (/** @type {any} */ err) {
      if (err?.status === 403) {
        return fail(403, { sampleError: 'Only an administrator can clear sample data.' });
      }
      return fail(400, { sampleError: readableError(err, 'Could not clear sample data.') });
    }
  }
};
