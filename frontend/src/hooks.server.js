import {sequence} from '@sveltejs/kit/hooks';
import * as Sentry from '@sentry/sveltekit';
/**
 * SvelteKit Server Hooks with JWT Authentication
 *
 * Authentication Flow:
 * 1. JWT tokens stored in cookies (httpOnly for security)
 * 2. Decode JWT locally to check org context (no API call needed)
 * 3. Only call switch-org if token doesn't have correct org
 * 4. Routes protected based on authentication and org membership
 */

import { redirect } from '@sveltejs/kit';
import axios from 'axios';
import { env } from '$env/dynamic/public';

const API_BASE_URL = `${env.PUBLIC_DJANGO_API_URL}/api`;

/**
 * @typedef {{ default_currency?: string, currency_symbol?: string, default_country?: string|null }} OrgSettingsPayload
 * @typedef {{ org_id?: string, org_name?: string, role?: string, user_id?: string, user_name?: string, user_email?: string, user_profile_pic?: string, exp?: number, iat?: number, org_settings?: OrgSettingsPayload }} JWTPayload
 * @typedef {{ id: string, name: string }} OrgInfo
 * @typedef {{ org: OrgInfo, role?: string }} ProfileInfo
 * @typedef {{ id?: string, organizations?: Array<{ id: string, name: string }> }} UserInfo
 * @typedef {{ access_token: string, refresh_token: string, current_org?: OrgInfo }} SwitchOrgResult
 */

/**
 * Decode JWT payload without verification (for reading claims only)
 * @param {string} token - JWT token
 * @returns {JWTPayload|null} Decoded payload or null if invalid
 */
function decodeJwtPayload(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = parts[1];
    // Handle base64url encoding
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = Buffer.from(base64, 'base64').toString('utf8');
    return /** @type {JWTPayload} */ (JSON.parse(jsonPayload));
  } catch (error) {
    return null;
  }
}

/**
 * Check if JWT token has the specified org_id in its payload
 * @param {string} token - JWT token
 * @param {string} orgId - Organization UUID to check
 * @returns {boolean} True if token has the org context
 */
function tokenHasOrgContext(token, orgId) {
  const payload = decodeJwtPayload(token);
  return Boolean(payload && payload.org_id === orgId);
}

/**
 * Verify JWT token locally by checking expiration
 * @param {string} accessToken - JWT access token
 * @returns {JWTPayload|null} JWT payload or null if expired/invalid
 */
function verifyTokenLocally(accessToken) {
  const payload = decodeJwtPayload(accessToken);
  if (!payload) return null;

  // Check if token is expired
  if (payload.exp && payload.exp * 1000 < Date.now()) {
    return null;
  }

  return payload;
}

/**
 * Refresh access token using refresh token
 * @param {string} refreshToken - JWT refresh token
 * @returns {Promise<string|null>} New access token or null if refresh failed
 */
async function refreshAccessToken(refreshToken) {
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/refresh-token/`, {
      refresh: refreshToken
    });

    return response.data.access;
  } catch (error) {
    console.error('Token refresh failed:', error);
    return null;
  }
}

// Profile info is now embedded in JWT - no API call needed

/**
 * Switch organization and get new tokens with org context
 * @param {string} accessToken - Current JWT access token
 * @param {string} orgId - Organization UUID to switch to
 * @returns {Promise<SwitchOrgResult|null>} New tokens and org data or null if failed
 */
async function switchOrg(accessToken, orgId) {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/auth/switch-org/`,
      { org_id: orgId },
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Org switch failed:', error);
    return null;
  }
}

export const handleError = Sentry.handleErrorWithSentry();

export const handle = sequence(Sentry.sentryHandle(), async function _handle({ event, resolve }) {
  // Get tokens from cookies
  /** @type {string | undefined} */
  let accessToken = event.cookies.get('jwt_access');
  const refreshToken = event.cookies.get('jwt_refresh');
  const orgId = event.cookies.get('org');

  /** @type {JWTPayload | null} */
  let jwtPayload = null;

  // Try to authenticate user (LOCAL JWT DECODE - no API call!)
  if (accessToken) {
    jwtPayload = verifyTokenLocally(accessToken);

    // If access token expired, try to refresh
    if (!jwtPayload && refreshToken) {
      const newAccessToken = await refreshAccessToken(refreshToken);
      if (newAccessToken) {
        // Update cookie with new access token
        event.cookies.set('jwt_access', newAccessToken, {
          path: '/',
          httpOnly: true,
          sameSite: 'lax',
          secure: process.env.NODE_ENV === 'production',
          maxAge: 60 * 60 * 24 // 1 day
        });
        accessToken = newAccessToken;
        jwtPayload = verifyTokenLocally(newAccessToken);
      } else {
        // Refresh failed, clear cookies
        event.cookies.delete('jwt_access', { path: '/' });
        event.cookies.delete('jwt_refresh', { path: '/' });
        event.cookies.delete('org', { path: '/' });
      }
    }
  }

  // Set user in locals from JWT payload (no API call needed!)
  if (jwtPayload) {
    // Build user object from JWT claims
    event.locals.user = {
      id: jwtPayload.user_id,
      name: jwtPayload.user_name || '',
      email: jwtPayload.user_email || '',
      profilePhoto: jwtPayload.user_profile_pic || ''
    };

    // Check if org cookie is set and token has org context
    if (orgId) {
      const token = /** @type {string} */ (accessToken);

      if (tokenHasOrgContext(token, orgId)) {
        // Token has org context - extract org info from JWT (no API call!)
        event.locals.org = {
          id: jwtPayload.org_id || orgId,
          name: jwtPayload.org_name || 'Organization'
        };
        /** @type {any} */ (event.locals).profile = {
          org: event.locals.org,
          role: jwtPayload.role || 'USER'
        };
        event.locals.org_name = jwtPayload.org_name || 'Organization';
        // Extract org settings for currency/locale
        event.locals.org_settings = jwtPayload.org_settings || {
          default_currency: 'USD',
          currency_symbol: '$',
          default_country: null
        };
      } else {
        // Token doesn't have org context, need to switch (1 API call)
        const switchResult = await switchOrg(token, orgId);

        if (switchResult) {
          // Update cookies with new tokens that have org context
          event.cookies.set('jwt_access', switchResult.access_token, {
            path: '/',
            httpOnly: true,
            sameSite: 'lax',
            secure: process.env.NODE_ENV === 'production',
            maxAge: 60 * 60 * 24 // 1 day
          });
          event.cookies.set('jwt_refresh', switchResult.refresh_token, {
            path: '/',
            httpOnly: true,
            sameSite: 'lax',
            secure: process.env.NODE_ENV === 'production',
            maxAge: 60 * 60 * 24 * 365 // 1 year
          });

          // Extract org info from switch result (no additional API call!)
          event.locals.org = switchResult.current_org;
          /** @type {any} */ (event.locals).profile = {
            org: switchResult.current_org,
            role: 'USER' // Will be in new JWT
          };
          event.locals.org_name = switchResult.current_org?.name || 'Organization';
          // Decode new token to get org_settings
          const newPayload = decodeJwtPayload(switchResult.access_token);
          event.locals.org_settings = newPayload?.org_settings || {
            default_currency: 'USD',
            currency_symbol: '$',
            default_country: null
          };
        } else {
          // Org switch failed, clear org cookie and redirect
          event.cookies.delete('org', { path: '/' });
          throw redirect(307, '/org');
        }
      }
    }
  }

  // Route protection
  const pathname = event.url.pathname;

  // Define public routes (no auth required)
  const PUBLIC_ROUTES = ['/login', '/logout', '/bounce'];

  // Define semi-protected routes (auth required, but no org)
  const AUTH_ONLY_ROUTES = ['/org'];

  // Check if public route
  const isPublicRoute = PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + '/')
  );

  // Check if auth-only route
  const isAuthOnlyRoute = AUTH_ONLY_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + '/')
  );

  if (isAuthOnlyRoute) {
    // Auth-only route - require user
    if (!jwtPayload) {
      throw redirect(307, '/login');
    }
  } else if (!isPublicRoute) {
    // Protected route - require user + org
    if (!jwtPayload) {
      throw redirect(307, '/login');
    }
    if (!event.locals.org) {
      throw redirect(307, '/org');
    }
  }

  return resolve(event);
});