import { getToday } from '#lib/server/v2/today.js';
import { getCurrentGoals } from '#lib/server/v2/goals.js';
import { getModules } from '#lib/server/v2/modules.js';
import { isOn } from '#lib/v2/modules.js';

/**
 * Today, plus the goals running today.
 *
 * Requests in parallel rather than one: `/dashboard/today/` builds the
 * queue and `/opportunities/goals/` the strip, and neither waits on the other.
 * `getCurrentGoals` swallows its own failure, so a goals outage costs the strip
 * and not the page. The strip is not asked for while Goals is off.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load(event) {
  const [today, goals] = await Promise.all([
    getToday(event),
    getModules(event).then((answer) =>
      isOn(answer?.modules, 'goals') ? getCurrentGoals(event) : []
    )
  ]);
  return { ...today, goals };
}
