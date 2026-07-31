import { listLeads } from '$lib/server/v2/leads.js';
import { listDeals } from '$lib/server/v2/deals.js';
import { listTickets, OPEN_STATUSES } from '$lib/server/v2/tickets.js';
import { listTasks } from '$lib/server/v2/tasks.js';
import { listInvoices } from '$lib/server/v2/invoices.js';
import { countAwaitingApprovals } from '$lib/server/v2/approvals.js';
import { countUnread } from '$lib/server/v2/notifications.js';

/**
 * Counts for migrated modules, fetched for real and merged over the fixtures.
 *
 * Leaving a migrated module on its fixture count puts "Leads 24" in the
 * sidebar beside "18 open" in the page, and a nav badge that disagrees with
 * the page it links to is worse than no badge.
 *
 * Add a line here in the same change that adds a prefix to `migrated.js`.
 */
const LIVE_COUNTS = {
  /** @param {any} event */
  leads: async (event) =>
    (await listLeads(event, new URLSearchParams({ limit: '1' }))).totals.count,
  /** @param {any} event */
  pipeline: async (event) =>
    (await listDeals(event, new URLSearchParams({ limit: '1' }))).totals.count,
  /**
   * Open tickets only. A support badge counting closed ones would never go
   * down, which is the same objection as the accounts note below.
   *
   * @param {any} event
   */
  tickets: async (event) => {
    const params = new URLSearchParams({ limit: '1' });
    for (const status of OPEN_STATUSES) params.append('status', status);
    return (await listTickets(event, params)).totals.open;
  },
  /**
   * Open tasks only, and the API already counts them per requester — an
   * admin's badge covers the org, a member's covers their own list. Same
   * argument as tickets: a badge counting completed tasks would only ever go
   * up.
   *
   * @param {any} event
   */
  tasks: async (event) => (await listTasks(event, new URLSearchParams({ limit: '1' }))).totals.open,
  /**
   * Invoices waiting on this person: drafts to send plus anything overdue to
   * chase, counted by the API per requester. Not the total invoice count —
   * that is inventory, the same objection as the accounts note below — and not
   * the outstanding *amount*, which the pills on the page already show. The
   * shell has always carried a needs-action invoice badge; this keeps it real.
   *
   * @param {any} event
   */
  invoices: async (event) =>
    (await listInvoices(event, new URLSearchParams({ limit: '1' }))).totals.action_needed,
  /**
   * Approvals waiting on *this* person — the ones only they can clear (the
   * inbox scopes `mine=true&state=pending` to the actionable set, and a
   * requester's own rows are excluded by the self-approval rule). This is work,
   * not inventory: it goes down as they decide, so it earns a badge.
   *
   * @param {any} event
   */
  approvals: async (event) => await countAwaitingApprovals(event),
  /**
   * Unread notifications waiting on this person — `GET /notifications/` scopes
   * to `recipient=request.profile` and reports `unread_count` over the whole
   * feed, so the badge matches the page it links to (which was the point of
   * this map). This is work, not inventory: it goes to zero as you read, so it
   * earns a badge. Was the fixture `notificationTotals.unread` until now.
   *
   * @param {any} event
   */
  notifications: async (event) => await countUnread(event)
  /*
   * No `accounts` entry, deliberately, even though the module is wired.
   *
   * These badges count work: leads to call, deals to move, tickets to answer.
   * "Accounts 10" counts inventory — it never goes down, nothing about it is
   * ever waiting on you, and a badge you learn to ignore teaches you to ignore
   * the ones beside it. The nav has never had an accounts count and should not
   * gain one just because the number became available.
   *
   * No `team` entry either. A people count is the same inventory objection, and
   * the one actionable number there — live tokens on deactivated accounts — is
   * admin-only (the count endpoint 403s a member) and the page already surfaces
   * it prominently. A badge only some roles can compute does not fit a shell
   * that is the same for everyone.
   */
};

/**
 * The shell: nav counts and the org name.
 *
 * The org name is display-only and comes from the JWT via `locals.org` — never
 * the client, never a fixture. Counts run concurrently (in sequence they would
 * add a round trip per module to every page) and start empty: every badge the
 * sidebar renders is in LIVE_COUNTS, so a count that fails just shows no badge
 * rather than a stale number.
 *
 * Still worth fixing: each count builds an entire page context — accounts,
 * tags, users, industries — to answer a question about one integer. One counts
 * endpoint covering every module is the right shape; N list calls is not.
 *
 * @type {import('./$types').LayoutServerLoad}
 */
export async function load(event) {
  const shell = {
    counts: /** @type {Record<string, number>} */ ({}),
    org: { name: event.locals.org?.name || 'BottleCRM' }
  };

  const keys = Object.keys(LIVE_COUNTS);
  const counted = await Promise.allSettled(
    keys.map((key) => LIVE_COUNTS[/** @type {keyof typeof LIVE_COUNTS} */ (key)](event))
  );

  keys.forEach((key, index) => {
    const result = counted[index];
    if (result.status === 'fulfilled') shell.counts[key] = result.value;
  });

  return shell;
}
