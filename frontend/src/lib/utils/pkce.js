/**
 * PKCE (Proof Key for Code Exchange) utilities for OAuth 2.0
 *
 * PKCE adds security to the authorization code flow by:
 * 1. Generating a random code_verifier
 * 2. Creating a code_challenge from the verifier (SHA256)
 * 3. Sending challenge with authorization request
 * 4. Sending verifier with token exchange request
 *
 * This prevents authorization code interception attacks.
 */

import crypto from 'crypto';

/**
 * Generate a cryptographically random code verifier
 * RFC 7636: 43-128 characters from [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
 * @returns {string} Base64URL encoded random string (43 chars from 32 bytes)
 */
export function generateCodeVerifier() {
	const buffer = crypto.randomBytes(32);
	return base64URLEncode(buffer);
}

/**
 * Generate code challenge from verifier using SHA256
 * @param {string} verifier - The code verifier
 * @returns {string} Base64URL encoded SHA256 hash
 */
export function generateCodeChallenge(verifier) {
	const hash = crypto.createHash('sha256').update(verifier).digest();
	return base64URLEncode(hash);
}

/**
 * Generate a cryptographically random state parameter for CSRF protection
 * @returns {string} Base64URL encoded random string (32 bytes)
 */
export function generateState() {
	const buffer = crypto.randomBytes(32);
	return base64URLEncode(buffer);
}

/**
 * Base64URL encode a buffer per RFC 4648 Section 5
 * @param {Buffer} buffer - Buffer to encode
 * @returns {string} Base64URL encoded string (no padding)
 */
function base64URLEncode(buffer) {
	return buffer.toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}
