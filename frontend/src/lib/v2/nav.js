/**
 * Every menu the shell draws, as data. Icons are lucide export names; the
 * components map them to the imported components. A module's items vanish
 * when it is switched off, and the server refuses its routes regardless.
 */
import { MODULE_KEYS, isOn } from '#lib/v2/modules.js';
import { t } from '#lib/terminology.js';

/**
 * @typedef {{ href: string, label: string, icon: string, count?: string, exact?: boolean }} NavItem
 * @typedef {import('#lib/v2/modules.js').ModuleRow} ModuleRow
 */

/** Sidebar item for each module, with the group it sits in. */
const MODULE_ITEMS = {
  deals: {
    group: 'Sell',
    item: {
      href: '/pipeline',
      label: 'Pipeline',
      icon: 'Columns3',
      count: 'pipeline',
      termKey: 'opportunity.plural'
    }
  },
  leads: {
    group: 'Sell',
    item: { href: '/leads', label: 'Leads', icon: 'Target', count: 'leads', termKey: 'lead.plural' }
  },
  goals: { group: 'Sell', item: { href: '/goals', label: 'Goals', icon: 'Trophy' } },
  tasks: {
    group: 'Serve',
    item: { href: '/tasks', label: 'Tasks', icon: 'CircleCheck', count: 'tasks' }
  },
  tickets: {
    group: 'Serve',
    item: { href: '/tickets', label: 'Tickets', icon: 'LifeBuoy', count: 'tickets' }
  },
  knowledge_base: {
    group: 'Serve',
    item: { href: '/solutions', label: 'Knowledge base', icon: 'BookOpen' }
  },
  documents: { group: 'Serve', item: { href: '/documents', label: 'Documents', icon: 'FileText' } },
  invoices: {
    group: 'Bill',
    item: {
      href: '/invoices',
      label: 'Invoices',
      icon: 'Receipt',
      count: 'invoices',
      termKey: 'invoice.plural'
    }
  },
  timesheet: { group: 'Bill', item: { href: '/timesheet', label: 'Timesheet', icon: 'Clock' } }
};

/**
 * Module keys in the org's order: the rows' order, then any key the list
 * does not carry. A null list is the default order.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {string[]}
 */
function orderedKeys(modules) {
  const fromRows = Array.isArray(modules) ? modules.map((m) => m.key) : [];
  const known = fromRows.filter((k) => MODULE_KEYS.includes(k));
  return [...known, ...MODULE_KEYS.filter((k) => !known.includes(k))];
}

/**
 * The sidebar's groups, without the Objects group.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @param {{ isAdmin?: boolean, terminology?: Record<string, string> | null }} [opts]
 * @returns {{ label: string, items: NavItem[] }[]}
 */
export function sidebarGroups(modules, { isAdmin = false, terminology = undefined } = {}) {
  const keys = orderedKeys(modules).filter((k) => isOn(modules, k));
  /** @param {string} group */
  const moduleItems = (group) =>
    keys
      .map((k) => MODULE_ITEMS[k])
      .filter((m) => m.group === group)
      .map((m) => m.item);

  const groups = [
    {
      label: 'Sell',
      items: [
        { href: '/', label: 'Today', icon: 'Sun', exact: true },
        ...moduleItems('Sell'),
        { href: '/accounts', label: 'Accounts', icon: 'Building2', termKey: 'account.plural' },
        { href: '/contacts', label: 'Contacts', icon: 'Users', termKey: 'contact.plural' }
      ]
    },
    { label: 'Serve', items: moduleItems('Serve') },
    { label: 'Bill', items: moduleItems('Bill') },
    {
      label: 'Run',
      items: [
        { href: '/team', label: 'Team and access', icon: 'UserCog', admin: true },
        { href: '/settings', label: 'Settings', icon: 'SlidersHorizontal' }
      ]
    }
  ];

  return groups
    .map((group) => ({
      label: group.label,
      items: group.items
        .filter((item) => isAdmin || !('admin' in item && item.admin))
        .map((item) => {
          const { termKey, admin: _admin, ...rest } = /** @type {any} */ (item);
          return termKey ? { ...rest, label: t(terminology, termKey, rest.label) } : rest;
        })
    }))
    .filter((group) => group.items.length > 0);
}

/** Tab bar candidates after Today, in priority order. */
const TAB_CANDIDATES = [
  {
    key: 'deals',
    href: '/pipeline',
    label: 'Pipeline',
    icon: 'Columns3',
    termKey: 'opportunity.plural'
  },
  { key: 'tickets', href: '/tickets', label: 'Tickets', icon: 'LifeBuoy' },
  {
    key: 'invoices',
    href: '/invoices',
    label: 'Invoices',
    icon: 'Receipt',
    termKey: 'invoice.plural'
  },
  { key: 'leads', href: '/leads', label: 'Leads', icon: 'Target', termKey: 'lead.plural' },
  { key: 'tasks', href: '/tasks', label: 'Tasks', icon: 'CircleCheck' }
];

/**
 * Today, then the first three candidates that are on.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @param {Record<string, string> | null | undefined} [terminology]
 * @returns {NavItem[]}
 */
export function tabBar(modules, terminology) {
  const rest = TAB_CANDIDATES.filter((c) => isOn(modules, c.key))
    .slice(0, 3)
    .map(({ href, label, icon, termKey }) => ({
      href,
      label: termKey ? t(terminology, termKey, label) : label,
      icon
    }));
  return [{ href: '/', label: 'Today', icon: 'Sun', exact: true }, ...rest];
}

const FAB_CANDIDATES = [
  { key: 'deals', href: '/pipeline/new', label: 'New deal', icon: 'Plus' },
  { key: 'tickets', href: '/tickets/new', label: 'New ticket', icon: 'Plus' },
  { key: 'leads', href: '/leads/new', label: 'New lead', icon: 'Plus' },
  { key: 'tasks', href: '/tasks/new', label: 'New task', icon: 'Plus' }
];

/**
 * The floating button: the first candidate whose module is on, or null.
 *
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {{ href: string, label: string, icon: string } | null}
 */
export function fabAction(modules) {
  const hit = FAB_CANDIDATES.find((c) => isOn(modules, c.key));
  return hit ? { href: hit.href, label: hit.label, icon: hit.icon } : null;
}

/**
 * The palette's actions before anything is typed.
 *
 * @param {ModuleRow[] | null | undefined} modules
 */
export function paletteActions(modules) {
  const all = [
    {
      module: 'deals',
      id: 'act-deal',
      title: 'New deal',
      meta: 'Pipeline',
      href: '/pipeline/new',
      icon: 'Plus'
    },
    { module: null, id: 'act-today', title: 'Go to Today', meta: '', href: '/', icon: 'Columns3' },
    {
      module: 'tasks',
      id: 'act-tasks',
      title: 'Go to Tasks',
      meta: '',
      href: '/tasks',
      icon: 'Columns3'
    },
    {
      module: 'invoices',
      id: 'act-invoices',
      title: 'Go to Invoices',
      meta: '',
      href: '/invoices',
      icon: 'Receipt'
    }
  ];
  return all
    .filter((a) => !a.module || isOn(modules, a.module))
    .map(({ module: _m, ...a }) => ({ kind: 'Actions', ...a }));
}

/**
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {string}
 */
export function searchPlaceholder(modules) {
  const words = [
    isOn(modules, 'deals') && 'deals',
    'accounts',
    'people',
    isOn(modules, 'tickets') && 'tickets',
    isOn(modules, 'invoices') && 'invoices'
  ].filter(Boolean);
  return `Search ${words.join(', ')}…`;
}

/**
 * @param {string} query
 * @param {ModuleRow[] | null | undefined} modules
 * @returns {string}
 */
export function noHitsText(query, modules) {
  const tries = [
    'an account name',
    isOn(modules, 'deals') && 'a deal',
    isOn(modules, 'invoices') && 'an invoice number'
  ].filter(Boolean);
  const list = tries.length === 3 ? `${tries[0]}, ${tries[1]}, or ${tries[2]}` : tries.join(' or ');
  return `Nothing matches “${query}”. Try ${list}.`;
}
