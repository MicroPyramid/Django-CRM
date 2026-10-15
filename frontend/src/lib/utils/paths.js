/**
 * Mark a dynamically assembled string as an internal pathname, in the form
 * `resolve()` from `$app/paths` takes one.
 *
 * SvelteKit 3 reads an argument that starts with `/` as a route ID and runs it
 * through route-ID parsing, so `/leads?tag=x` would be treated as a route. A
 * pathname goes in without the leading slash, which this strips.
 *
 * @param {string} path an app-relative pathname such as `/leads?tag=x`
 * @returns {any}
 */
export function asInternalPath(path) {
  return path.replace(/^\//, '');
}
