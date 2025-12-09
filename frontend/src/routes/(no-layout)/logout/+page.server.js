/**
 * Logout Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Clears JWT tokens and session data
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { redirect } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
  // Clear all authentication-related cookies
  const cookiesToClear = ['jwt_access', 'jwt_refresh', 'org', 'oauth_state', 'oauth_code_verifier'];

  for (const cookieName of cookiesToClear) {
    if (cookies.get(cookieName)) {
      await cookies.delete(cookieName, { path: '/' });
    }
  }

  // Clear locals
  if (locals.user) {
    delete locals.user;
  }
  if (locals.org) {
    delete locals.org;
  }

  // Redirect to login page
  throw redirect(303, '/login');
}
