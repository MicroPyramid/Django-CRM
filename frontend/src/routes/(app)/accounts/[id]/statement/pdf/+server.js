import { forwardStatementPdf } from '$lib/server/v2/statements.js';

/**
 * The statement as a PDF, for the period in the query string. The API decides
 * who may have it; `forwardStatementPdf` has the why.
 *
 * @type {import('./$types').RequestHandler}
 */
export function GET(event) {
  return forwardStatementPdf(event);
}
