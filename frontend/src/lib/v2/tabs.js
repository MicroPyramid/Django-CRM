import { isOn } from '#lib/v2/modules.js';

/**
 * Section tab sets, defined once so a destination shows the same tabs from
 * whichever of its pages you arrive on. v1 defined them per page, which is how
 * the Invoices header ended up with "Estimates" and "Recurring" buttons that
 * went nowhere while /invoices/estimates existed.
 *
 * `count` names a key in the shell counts, which SectionTabs reads from the
 * layout data. Naming the key rather than passing the number keeps the tab
 * list a static declaration.
 *
 * `admin: true` marks a tab whose page is a "for administrators" gate to a
 * member. SectionTabs hides it for non-admins so they are not offered a tab
 * that only turns them away. The backend still enforces the gate; this is UX.
 */
export const TAB_SETS = {
  tickets: [
    { href: '/tickets', label: 'Queue', exact: true, count: 'tickets', module: 'tickets' },
    { href: '/tickets/approvals', label: 'Approvals', count: 'approvals', module: 'tickets' },
    { href: '/tickets/analytics', label: 'Analytics', admin: true, module: 'tickets' }
  ],
  /**
   * These two are NOT two views of one list. `tasks.Task` and
   * `tasks.BoardTask` are separate tables. A card on a board is not a task in
   * the task list and never appears there. Tabs are still right (both are
   * "Tasks", and you move between them in one sitting), but the board page
   * says the rest out loud, because nothing about the word suggests it.
   */
  tasks: [
    { href: '/tasks', label: 'Task list', exact: true, count: 'tasks', module: 'tasks' },
    { href: '/tasks/board', label: 'Boards', module: 'tasks' },
    { href: '/tasks/calendar', label: 'Calendar', module: 'tasks' }
  ],
  invoices: [
    { href: '/invoices', label: 'Invoices', exact: true, count: 'invoices', module: 'invoices' },
    { href: '/invoices/estimates', label: 'Estimates', module: 'invoices' },
    { href: '/invoices/recurring', label: 'Recurring', module: 'invoices' },
    { href: '/invoices/products', label: 'Products', anyOf: ['invoices', 'deals'] },
    { href: '/invoices/reports', label: 'Reports', admin: true, module: 'invoices' },
    { href: '/invoices/templates', label: 'Templates', module: 'invoices' }
  ]
};

/**
 * Settings deliberately has no tab set.
 *
 * Tabs are for peers you flip between. Queue / Approvals / Analytics are all
 * "Tickets", and you move among them in one sitting. The twelve settings pages
 * are not that: you arrive at exactly one of them, change a thing, and leave.
 * A twelve-item strip would push the destination you came for off the right
 * edge and make the other eleven look like they were also on your list.
 *
 * So settings uses the hub at /v2/settings as its index and a `crumb` back to
 * it on each page, which is also the shape that keeps working as the count
 * grows past twelve.
 */

/**
 * The tabs of a set that this person can use: admin tabs for admins, and only
 * those whose module is on.
 *
 * @param {keyof typeof TAB_SETS} set
 * @param {{ isAdmin?: boolean, modules?: import('#lib/v2/modules.js').ModuleRow[] | null }} [opts]
 */
export function visibleTabs(set, { isAdmin = false, modules = null } = {}) {
  return (TAB_SETS[set] ?? []).filter((tab) => {
    const t = /** @type {any} */ (tab);
    if (t.admin && !isAdmin) return false;
    if (t.module && !isOn(modules, t.module)) return false;
    if (t.anyOf && !t.anyOf.some((/** @type {string} */ k) => isOn(modules, k))) return false;
    return true;
  });
}
