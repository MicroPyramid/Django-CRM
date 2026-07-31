/**
 * Section tab sets, defined once so a destination shows the same tabs from
 * whichever of its pages you arrive on. v1 defined them per page, which is how
 * the Invoices header ended up with "Estimates" and "Recurring" buttons that
 * went nowhere while /invoices/estimates existed.
 *
 * `count` names a key in the shell counts, which SectionTabs reads from the
 * layout data. Naming the key rather than passing the number keeps the tab
 * list a static declaration.
 */
export const TAB_SETS = {
  tickets: [
    { href: '/v2/tickets', label: 'Queue', exact: true, count: 'tickets' },
    { href: '/v2/tickets/approvals', label: 'Approvals', count: 'approvals' },
    { href: '/v2/tickets/analytics', label: 'Analytics' }
  ],
  /**
   * These two are NOT two views of one list. `tasks.Task` and
   * `tasks.BoardTask` are separate tables — a card on a board is not a task in
   * the task list and never appears there. Tabs are still right (both are
   * "Tasks", and you move between them in one sitting), but the board page
   * says the rest out loud, because nothing about the word suggests it.
   */
  tasks: [
    { href: '/v2/tasks', label: 'Task list', exact: true, count: 'tasks' },
    { href: '/v2/tasks/board', label: 'Boards' },
    { href: '/v2/tasks/calendar', label: 'Calendar' }
  ],
  invoices: [
    { href: '/v2/invoices', label: 'Invoices', exact: true, count: 'invoices' },
    { href: '/v2/invoices/estimates', label: 'Estimates' },
    { href: '/v2/invoices/recurring', label: 'Recurring' },
    { href: '/v2/invoices/products', label: 'Products' },
    { href: '/v2/invoices/reports', label: 'Reports' },
    { href: '/v2/invoices/templates', label: 'Templates' }
  ]
};

/**
 * Settings deliberately has no tab set.
 *
 * Tabs are for peers you flip between — Queue / Approvals / Analytics are all
 * "Tickets", and you move among them in one sitting. The twelve settings pages
 * are not that: you arrive at exactly one of them, change a thing, and leave.
 * A twelve-item strip would push the destination you came for off the right
 * edge and make the other eleven look like they were also on your list.
 *
 * So settings uses the hub at /v2/settings as its index and a `crumb` back to
 * it on each page — which is also the shape that keeps working as the count
 * grows past twelve.
 */
