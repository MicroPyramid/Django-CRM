/**
 * Safe error logging for server-side code.
 *
 * `console.error('...', err)` runs the error through Node's util.inspect, which
 * walks the whole object graph. For an axios error that graph includes
 * `config.headers.Authorization` (the caller's JWT) and `config.data` (the
 * request body, which for the token-refresh call IS the refresh token, and for
 * the OAuth exchange is the authorization code plus the PKCE verifier). Those
 * end up in persistent server logs.
 *
 * Nothing here is derived from the request: no headers, no body, no URL. Only
 * the message, HTTP status and error code, which together with the caller's own
 * label are enough to identify what failed.
 */

/**
 * Reduce an error to a single line safe to write to server logs.
 *
 * @param {unknown} err - Any thrown value.
 * @returns {string} A compact description containing no credentials.
 */
export function describeError(err) {
  if (err === null || err === undefined) return 'unknown error';

  const message =
    typeof err === 'object' &&
    err !== null &&
    typeof (/** @type {any} */ (err).message) === 'string'
      ? /** @type {any} */ (err).message
      : String(err);

  const parts = [message];

  const status = /** @type {any} */ (err)?.response?.status ?? /** @type {any} */ (err)?.status;
  if (status !== undefined && status !== null) parts.push(`status=${status}`);

  const code = /** @type {any} */ (err)?.code;
  if (typeof code === 'string' && code) parts.push(`code=${code}`);

  return parts.join(' ');
}
