/**
 * Which modules an org has switched off, and what that means for a route.
 *
 * Browser-safe: no server or framework imports. "On" has one definition,
 * `isOn`: a missing list or a missing row reads as on, so an older API that
 * does not serve the list changes nothing. The server refuses an off module
 * regardless; this only decides what to show.
 */

/**
 * One row of `GET /org/modules/`.
 *
 * @typedef {{
 *   key: string,
 *   label: string,
 *   group: 'sell' | 'serve' | 'bill',
 *   covers: string,
 *   stops: string,
 *   enabled: boolean,
 *   available: boolean,
 *   needs: string | null
 * }} ModuleRow
 */

/** @typedef {{ all: string[] } | { any: string[] }} Requirement */

export const MODULE_KEYS = [
  'deals',
  'leads',
  'goals',
  'tasks',
  'tickets',
  'knowledge_base',
  'documents',
  'invoices',
  'timesheet'
];

/** @type {Record<string, string>} */
export const DEFAULT_LABELS = {
  deals: 'Pipeline',
  leads: 'Leads',
  goals: 'Goals',
  tasks: 'Tasks',
  tickets: 'Tickets',
  knowledge_base: 'Knowledge base',
  documents: 'Documents',
  invoices: 'Invoices',
  timesheet: 'Timesheet'
};

/** Record kinds a page can show, by the module that serves them. */
export const OBJECT_MODULES = /** @type {Record<string, string>} */ ({
  lead: 'leads',
  deal: 'deals',
  ticket: 'tickets',
  task: 'tasks'
});

/** Custom field targets, by the module that serves them. */
export const TARGET_MODULES = /** @type {Record<string, string>} */ ({
  Lead: 'leads',
  Opportunity: 'deals',
  Case: 'tickets',
  Task: 'tasks',
  Invoice: 'invoices',
  Estimate: 'invoices',
  RecurringInvoice: 'invoices'
});

/**
 * @param {ModuleRow[] | null | undefined} modules
 * @param {string} key
 * @returns {boolean}
 */
export function isOn(modules, key) {
  if (!Array.isArray(modules)) return true;
  const row = modules.find((m) => m.key === key);
  return row ? row.available !== false : true;
}

/**
 * Products are served while deals or invoices is on.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {boolean}
 */
export function productsOn(modules) {
  return isOn(modules, 'deals') || isOn(modules, 'invoices');
}

/**
 * Inbound mailboxes are served while tickets or leads is on, since an address
 * makes one or the other.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {boolean}
 */
export function mailboxesOn(modules) {
  return isOn(modules, 'tickets') || isOn(modules, 'leads');
}

/**
 * @param {ModuleRow[] | null | undefined} modules
 * @param {string} key
 * @returns {string}
 */
export function labelOf(modules, key) {
  const row = Array.isArray(modules) ? modules.find((m) => m.key === key) : undefined;
  return row?.label || DEFAULT_LABELS[key] || key;
}

/** @type {Record<string, Requirement>} */
const ROUTES = {
  '/leads': { all: ['leads'] },
  '/settings/lead-pipelines': { all: ['leads'] },
  '/settings/lead-capture': { all: ['leads'] },
  '/pipeline': { all: ['deals'] },
  '/settings/deal-pipelines': { all: ['deals'] },
  '/goals': { all: ['goals'] },
  '/tasks': { all: ['tasks'] },
  '/profile/calendar-feed': { all: ['tasks'] },
  '/tickets': { all: ['tickets'] },
  '/settings/routing': { all: ['tickets'] },
  '/settings/escalation': { all: ['tickets'] },
  '/settings/business-hours': { all: ['tickets'] },
  '/settings/ticket-approvals': { all: ['tickets'] },
  '/settings/reopen': { all: ['tickets'] },
  '/settings/inbound-email': { any: ['tickets', 'leads'] },
  '/settings/macros': { all: ['tickets'] },
  '/solutions': { all: ['knowledge_base'] },
  '/settings/help-center': { all: ['knowledge_base'] },
  '/timesheet': { all: ['timesheet'] },
  '/invoices': { all: ['invoices'] },
  '/accounts/[id]/statement': { all: ['invoices'] },
  '/invoices/products': { any: ['invoices', 'deals'] },
  '/documents': { all: ['documents'] }
};

/**
 * What a route needs switched on, or null for a core route.
 *
 * @param {string | null | undefined} routeId SvelteKit's `route.id`, groups allowed
 * @returns {Requirement | null}
 */
export function requirementFor(routeId) {
  if (!routeId) return null;
  const path = routeId.replace(/\/\([^/)]*\)/g, '');
  let best = '';
  for (const prefix of Object.keys(ROUTES)) {
    if ((path === prefix || path.startsWith(prefix + '/')) && prefix.length > best.length) {
      best = prefix;
    }
  }
  return best ? ROUTES[best] : null;
}

/**
 * The module a route is waiting on, or null when it can be shown.
 *
 * @param {string | null | undefined} routeId
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {{ key: string, label: string } | null}
 */
export function refusalFor(routeId, modules) {
  const need = requirementFor(routeId);
  if (!need) return null;
  let key;
  if ('all' in need) key = need.all.find((k) => !isOn(modules, k));
  else if (!need.any.some((k) => isOn(modules, k))) key = need.any[0];
  return key ? { key, label: labelOf(modules, key) } : null;
}

/**
 * What Today says it is clear of, naming only the modules that are on.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {string}
 */
export function todayClearText(modules) {
  const parts = [
    ['tickets', 'tickets'],
    ['invoices', 'invoices'],
    ['deals', 'quiet deals'],
    ['tasks', 'tasks']
  ]
    .filter(([key]) => isOn(modules, key))
    .map(([, noun]) => noun);
  if (!parts.length) return 'Nothing is waiting on you.';
  const first = parts.findIndex((p) => p !== 'quiet deals');
  if (first >= 0) parts[first] = `overdue ${parts[first]}`;
  const list =
    parts.length === 1
      ? parts[0]
      : `${parts.slice(0, -1).join(', ')} or ${parts[parts.length - 1]}`;
  return `No ${list}.`;
}

/**
 * The empty notifications line; ticket activity is named only while Tickets is on.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {string}
 */
export function notificationsEmptyText(modules) {
  return isOn(modules, 'tickets')
    ? 'Notifications arrive for CRM ticket activity, automation rules, and updates from BottleCRM Support.'
    : 'Notifications arrive for automation rules and updates from BottleCRM Support.';
}

/**
 * The words whose module is on, joined as prose: "a, b and c". A word keyed
 * `null` belongs to no module and always stays.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @param {[string | null, string][]} words each a module key and its word
 * @param {string} [last] what joins the final two
 * @returns {string} '' when every word's module is off
 */
export function wordsOn(modules, words, last = 'and') {
  const kept = words.filter(([key]) => key === null || isOn(modules, key)).map(([, word]) => word);
  if (kept.length < 2) return kept[0] ?? '';
  return `${kept.slice(0, -1).join(', ')} ${last} ${kept[kept.length - 1]}`;
}
