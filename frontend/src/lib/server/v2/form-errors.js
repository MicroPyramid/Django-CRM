/**
 * Turning a DRF rejection back into a sentence.
 *
 * The API answers a bad save with `{"error": true, "errors": {"field":
 * ["message"]}}`, and `apiRequest` flattens that into an Error whose message
 * carries the JSON. Showing "Request failed" over the top of it throws away the
 * one useful thing in the response: the API already said exactly what was wrong
 * with which field.
 *
 * This lived twice in the accounts routes and was about to live twice more in
 * contacts. Two copies of a function is how the backend ended up with five
 * different opinions about who may open a record.
 */

/**
 * @param {any} err the error thrown by `apiRequest`
 * @param {string} fallback what to say when the response explained nothing
 * @returns {string} a message worth putting in front of somebody
 */
export function readableError(err, fallback) {
  const message = String(err?.message ?? '');
  const start = message.indexOf('{');
  if (start === -1) return message || fallback;
  try {
    const parsed = JSON.parse(message.slice(start));
    const errors = parsed.errors ?? parsed;
    if (typeof errors === 'string') return errors;
    const first = Object.entries(errors)[0];
    if (!first) return fallback;
    const [field, detail] = first;
    const text = Array.isArray(detail) ? detail[0] : detail;
    return field === 'non_field_errors' ? String(text) : `${field}: ${text}`;
  } catch {
    return message;
  }
}
