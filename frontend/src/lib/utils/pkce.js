/**
 * PKCE (Proof Key for Code Exchange) utilities for OAuth 2.0
 * @module lib/utils/pkce
 */

/**
 * Generate a random code verifier for PKCE
 * @returns {string} Random code verifier string
 */
export function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64URLEncode(array);
}

/**
 * Generate a code challenge from a verifier using SHA-256
 * @param {string} verifier - The code verifier
 * @returns {Promise<string>} Code challenge
 */
export async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64URLEncode(new Uint8Array(digest));
}

/**
 * Generate a random state string for CSRF protection
 * @returns {string} Random state string
 */
export function generateState() {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return base64URLEncode(array);
}

/**
 * Base64 URL encode a byte array
 * @param {Uint8Array} buffer - Byte array to encode
 * @returns {string} Base64 URL encoded string
 */
function base64URLEncode(buffer) {
  return btoa(String.fromCharCode(...buffer))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}
