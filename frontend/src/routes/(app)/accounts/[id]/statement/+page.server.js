import { getStatement, previousMonth } from '$lib/server/v2/statements.js';

/**
 * An account's statement for the period in the URL (`?start_date=&end_date=`),
 * this month so far when there is none. See `$lib/server/v2/statements.js`.
 *
 * @type {import('./$types').PageServerLoad}
 */
export async function load({ cookies, params, url }) {
  const result = await getStatement({ cookies }, params.id, url.searchParams);
  // The form shows what was asked for, so a refused period can be corrected.
  const period = result.statement
    ? { start_date: result.statement.start_date, end_date: result.statement.end_date }
    : {
        start_date: url.searchParams.get('start_date') ?? '',
        end_date: url.searchParams.get('end_date') ?? ''
      };
  return {
    ...result,
    accountId: params.id,
    period,
    previous: result.statement ? previousMonth(result.statement.start_date) : null
  };
}
