/**
 * Industry apps (`/api/apps/`): the catalogue with this org's install state,
 * what an action would do, and install, upgrade and remove. Any member reads
 * the list; the rest is for admins, and the server decides. An API without
 * apps answers 404 and the Apps page hides the section.
 *
 * Every call takes something with a `.get('jwt_access')`, so signup can pass
 * a bearer-only reader for the org it just created (`org/new/+page.server.js`).
 */
import { apiRequest } from '#lib/api-helpers.js';
import { readableError } from '#lib/server/v2/form-errors.js';

/** @typedef {import('@sveltejs/kit').Cookies | { get: (name: string) => string | undefined }} CookieReader */

const APP_ACTIONS = /** @type {const} */ (['install', 'upgrade', 'remove']);

/** Catalogue ids look like `professional-services`; anything else is never sent. */
const APP_ID = /^[a-z0-9][a-z0-9_-]{0,63}$/;

/** @param {unknown} id */
export function isAppId(id) {
  return typeof id === 'string' && APP_ID.test(id);
}

/** @param {unknown} action */
export function isAppAction(action) {
  return APP_ACTIONS.includes(/** @type {any} */ (action));
}

/** @param {CookieReader} cookies */
const auth = (cookies) => ({ cookies: /** @type {import('@sveltejs/kit').Cookies} */ (cookies) });

/** @param {any} raw */
function toApp(raw) {
  const by = raw?.installed_by_details;
  return {
    id: String(raw?.id ?? ''),
    name: String(raw?.name ?? raw?.id ?? ''),
    description: String(raw?.description ?? ''),
    version: raw?.version ?? null,
    status: ['installed', 'removed'].includes(raw?.status) ? raw.status : 'not_installed',
    installedVersion: raw?.installed_version ?? null,
    updateAvailable: raw?.update_available === true,
    skippedModules: Array.isArray(raw?.skipped_modules) ? raw.skipped_modules.map(String) : [],
    installedAt: raw?.installed_at ?? null,
    installedBy: by && typeof by === 'object' ? String(by.name ?? '') : ''
  };
}

/** @typedef {ReturnType<typeof toApp>} App */

/**
 * The catalogue, in its own order. `absent` on an API without apps (404),
 * `failed` when the read broke, so the page can say which.
 *
 * @param {CookieReader} cookies
 * @returns {Promise<{ state: 'ok' | 'absent' | 'failed', apps: App[] }>}
 */
export async function listApps(cookies) {
  try {
    const resp = await apiRequest(
      '/apps/',
      { quietErrors: true, expectedStatuses: [404] },
      auth(cookies)
    );
    const rows = Array.isArray(resp?.apps) ? resp.apps : [];
    return { state: 'ok', apps: rows.map(toApp).filter((a) => a.id) };
  } catch (/** @type {any} */ err) {
    return { state: err?.status === 404 ? 'absent' : 'failed', apps: [] };
  }
}

/** Preview item types in the order the confirmation lists them. */
const TYPES = [
  ['wording', 'Wording'],
  ['field', 'Fields'],
  ['pipeline', 'Pipelines'],
  ['stage', 'Stages'],
  ['tag', 'Tags'],
  ['source', 'Lead sources'],
  ['product', 'Products']
];

const EFFECTS = /** @type {Record<string, string>} */ ({
  add: 'Will add',
  keep: 'Already here, kept as it is',
  turn_off: 'Will turn off',
  turn_on: 'Will turn back on',
  restore_wording: 'Will go back to the default wording',
  skipped_module: 'Skipped while its module is off',
  add_by_hand: 'Not added: add this stage by hand'
});

const TARGETS = /** @type {Record<string, string>} */ ({
  lead: 'leads',
  contact: 'contacts',
  account: 'accounts',
  deal: 'deals',
  opportunity: 'deals',
  ticket: 'tickets',
  case: 'tickets',
  task: 'tasks',
  invoice: 'invoices',
  estimate: 'estimates',
  recurring_invoice: 'recurring invoices'
});

/**
 * Preview items grouped by type, in a fixed order, each group keeping the
 * server's order. A type this client does not know is listed last under its
 * own name rather than dropped.
 *
 * @param {any[]} items
 * @returns {{ type: string, label: string, items: { label: string, target: string, effect: string, effectLabel: string }[] }[]}
 */
function groupPreview(items) {
  /** @type {Map<string, any[]>} */
  const byType = new Map();
  for (const item of Array.isArray(items) ? items : []) {
    const type = String(item?.type ?? '');
    if (!type) continue;
    const effect = String(item?.effect ?? '');
    const target = item?.target ? String(item.target) : '';
    byType.set(type, [
      ...(byType.get(type) ?? []),
      {
        label: String(item?.label ?? ''),
        target: target ? (TARGETS[target] ?? target) : '',
        effect,
        effectLabel: EFFECTS[effect] ?? effect.replaceAll('_', ' ')
      }
    ]);
  }
  const known = TYPES.filter(([type]) => byType.has(type)).map(([type, label]) => ({
    type,
    label,
    items: byType.get(type) ?? []
  }));
  const other = [...byType.keys()]
    .filter((type) => !TYPES.some(([t]) => t === type))
    .map((type) => ({ type, label: type.replaceAll('_', ' '), items: byType.get(type) ?? [] }));
  return [...known, ...other];
}

/**
 * What an action would do, grouped for the confirmation. Writes nothing.
 *
 * @param {CookieReader} cookies
 * @param {string} id
 * @param {string} action
 */
export async function previewApp(cookies, id, action) {
  const resp = await apiRequest(
    `/apps/${encodeURIComponent(id)}/preview/?action=${encodeURIComponent(action)}`,
    { quietErrors: true, expectedStatuses: [403, 404] },
    auth(cookies)
  );
  const sample = resp?.sample_data ?? {};
  return {
    action: String(resp?.action ?? action),
    groups: groupPreview(resp?.items),
    sampleData: {
      offered: sample.offered === true,
      defaultOn: sample.default_on === true,
      records: Number.isFinite(sample.records) ? sample.records : 0
    }
  };
}

/**
 * @param {CookieReader} cookies
 * @param {string} id
 * @param {boolean} sampleData sent on every install, true or false
 */
export async function installApp(cookies, id, sampleData) {
  const resp = await apiRequest(
    `/apps/${encodeURIComponent(id)}/install/`,
    { method: 'POST', body: { sample_data: sampleData === true } },
    auth(cookies)
  );
  return resp?.app ? toApp(resp.app) : null;
}

/**
 * @param {CookieReader} cookies
 * @param {string} id
 */
export async function upgradeApp(cookies, id) {
  const resp = await apiRequest(
    `/apps/${encodeURIComponent(id)}/upgrade/`,
    { method: 'POST', body: {} },
    auth(cookies)
  );
  return resp?.app ? toApp(resp.app) : null;
}

/**
 * @param {CookieReader} cookies
 * @param {string} id
 */
export async function removeApp(cookies, id) {
  const resp = await apiRequest(
    `/apps/${encodeURIComponent(id)}/remove/`,
    { method: 'POST', body: {} },
    auth(cookies)
  );
  return resp?.app ? toApp(resp.app) : null;
}

const VERB = /** @type {Record<string, string>} */ ({
  install: 'install',
  upgrade: 'update',
  remove: 'remove'
});

/**
 * A refused action as one sentence. A 409 carries the server's own reason
 * (nothing new to add, not installed).
 *
 * @param {any} err
 * @param {string} action
 */
export function appRefusal(err, action) {
  const verb = VERB[action] ?? 'change';
  if (err?.status === 403) return `Only an organization admin can ${verb} an app.`;
  if (err?.status === 404) return 'That app is not in the catalogue.';
  return readableError(err, `Could not ${verb} this app.`);
}
