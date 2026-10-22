import { error } from '@sveltejs/kit';
import { getRule, listRuns, RULE_GONE } from '#lib/server/v2/automation.js';
import { UUID } from '#lib/v2/custom-objects.js';

/**
 * One rule's run history, a page at a time. The rule goes first so a member
 * is refused once, before any run is asked for.
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const { id } = event.params;
  if (!UUID.test(id)) error(404, RULE_GONE);
  const offset = Math.max(0, Number.parseInt(event.url.searchParams.get('offset') ?? '0', 10) || 0);
  try {
    const rule = await getRule(event, id);
    const page = await listRuns(event, id, offset);
    return { rule, ...page };
  } catch (/** @type {any} */ err) {
    if (err?.status === 403) return { forbidden: true };
    throw err;
  }
}
