/**
 * API Helper Functions
 *
 * Shared utilities for making API requests to Django backend.
 * Used by SvelteKit server files during migration from Prisma to API.
 */

import * as env from '$app/env/public';

const API_BASE_URL = `${env.PUBLIC_DJANGO_API_URL}/api`;

/**
 * @typedef {import('@sveltejs/kit').Cookies} Cookies
 */

/**
 * Make authenticated API request to Django backend
 *
 * This helper is designed for SvelteKit server-side use, where cookies
 * are managed by hooks and locals contains the user and org context.
 *
 * @param {string} endpoint - API endpoint (e.g., '/accounts/', '/leads/123/')
 * @param {{ method?: string, body?: Record<string, unknown> | FormData, headers?: Record<string, string>, quietErrors?: boolean, expectedStatuses?: number[] }} options - Fetch options.
 *   `quietErrors` logs a failed request's status and the server's `message`
 *   only, never the response body: for replies that can quote the caller's
 *   data, such as an import's skipped rows and their cells.
 *   `expectedStatuses` lists statuses that are an answer rather than a failure
 *   (a 404 from a route this install does not have): they are thrown as usual,
 *   with `status` and `body`, but never logged.
 * @param {{ cookies?: Cookies, org?: { id: string } } | Cookies} locals - SvelteKit locals object or cookies directly
 * @returns {Promise<any>} Response data
 * @throws {Error} If request fails
 */
export async function apiRequest(endpoint, options = {}, locals) {
  const {
    method = 'GET',
    body,
    headers = {},
    quietErrors = false,
    expectedStatuses = []
  } = options;

  // Get access token from cookies (server-side)
  // In server load functions, cookies is passed directly
  /** @type {Cookies | undefined} */
  const cookies = /** @type {Cookies | undefined} */ (
    /** @type {{ cookies?: Cookies }} */ (locals).cookies || locals
  );
  const accessToken = cookies?.get?.('jwt_access');

  // A FormData body is a file upload (multipart). Do NOT set Content-Type for it
  //. Fetch has to add the multipart boundary itself, and a hand-set
  // 'application/json' would make Django parse the parts as a JSON string and
  // find neither the field nor the file. Plain-object bodies stay JSON, so every
  // existing caller is unaffected.
  const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

  // Build request headers
  /** @type {Record<string, string>} */
  const requestHeaders = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...headers
  };

  // Add authentication
  // Note: Organization context is now embedded in JWT token, not sent as header
  if (accessToken) {
    requestHeaders['Authorization'] = `Bearer ${accessToken}`;
  }

  // Build request options
  /** @type {RequestInit} */
  const requestOptions = {
    method,
    headers: requestHeaders
  };

  // Add body for non-GET requests
  if (body && method !== 'GET') {
    requestOptions.body = isFormData ? body : JSON.stringify(body);
  }

  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, requestOptions);

    // Handle error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Extract meaningful error message from various Django error formats
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.error && typeof errorData.error === 'string') {
        errorMessage = errorData.error;
      } else if (errorData.errors && typeof errorData.errors === 'object') {
        // Handle field-level errors
        const fieldErrors = Object.entries(errorData.errors)
          .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
          .join('; ');
        errorMessage = fieldErrors || errorMessage;
      } else if (errorData.non_field_errors) {
        errorMessage = Array.isArray(errorData.non_field_errors)
          ? errorData.non_field_errors.join(', ')
          : errorData.non_field_errors;
      } else if (typeof errorData === 'object' && Object.keys(errorData).length > 0) {
        // Handle field-level validation errors from DRF serializers
        const fieldErrors = Object.entries(errorData)
          .filter(([key, value]) => key !== 'error' || typeof value === 'string')
          .map(([field, msgs]) => {
            if (Array.isArray(msgs)) {
              return `${field}: ${msgs.join(', ')}`;
            } else if (typeof msgs === 'string') {
              return `${field}: ${msgs}`;
            }
            return null;
          })
          .filter(Boolean)
          .join('; ');
        if (fieldErrors) {
          errorMessage = fieldErrors;
        }
      }

      if (expectedStatuses.includes(response.status)) {
        // Thrown below, not logged.
      } else if (quietErrors) {
        console.error(
          `API Error Response: ${method} ${endpoint} ${response.status}`,
          typeof errorData.message === 'string' ? errorData.message : ''
        );
      } else {
        console.error(`API Error Response:`, errorData);
      }
      /*
       * The status travels with the error.
       *
       * Callers used to decide "is this a 404?" by searching the message for
       * the string "404" or "not found", and Django's own message for a
       * missing record is "No Lead matches the given query.", which contains
       * neither. So a perfectly ordinary 404 rendered as a 500. Sniffing prose
       * to recover a number that was right there is a bug waiting for the day
       * somebody rewords an error.
       */
      const failure = /** @type {Error & { status: number, body: any }} */ (
        new Error(errorMessage)
      );
      failure.status = response.status;
      failure.body = errorData;
      throw failure;
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null;
    }

    // Return JSON response
    return await response.json();
  } catch (error) {
    const status = /** @type {{ status?: number }} */ (error).status;
    if (status !== undefined && expectedStatuses.includes(status)) {
      // An expected answer, already left unlogged above.
    } else if (!quietErrors) {
      console.error(`API request failed: ${method} ${endpoint}`, error);
    } else if (!(/** @type {{ status?: number }} */ (error).status)) {
      // A network failure; an error reply was logged quietly above. The
      // error object itself is not logged, since it carries the body.
      console.error(`API request failed: ${method} ${endpoint}`, String(error));
    }
    throw error;
  }
}
