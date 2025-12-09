/**
 * Organization Create Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: POST /api/org/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { env } from '$env/dynamic/private';
import { env as publicEnv } from '$env/dynamic/public';
import axios from 'axios';

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies }) {
  // No data needed for load
}

/** @satisfies {import('./$types').Actions} */
export const actions = {
  default: async ({ request, cookies, locals }) => {
    // Get the user from locals
    const user = locals.user;

    if (!user) {
      return {
        error: {
          name: 'You must be logged in to create an organization'
        }
      };
    }

    // Get the submitted form data
    const formData = await request.formData();
    const orgName = formData.get('org_name')?.toString();

    if (!orgName || orgName.trim().length === 0) {
      return {
        error: {
          name: 'Organization name is required'
        }
      };
    }

    try {
      const jwtAccess = cookies.get('jwt_access');
      if (!jwtAccess) {
        return {
          error: {
            name: 'Authentication required'
          }
        };
      }

      const apiUrl = publicEnv.PUBLIC_DJANGO_API_URL;

      // Create organization and profile via Django API
      // Django's OrgProfileCreateView creates both org and profile
      const response = await axios.post(
        `${apiUrl}/api/org/`,
        {
          name: orgName.trim()
        },
        {
          headers: {
            Authorization: `Bearer ${jwtAccess}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Response should contain the created org
      const newOrg = response.data.org || response.data;

      // Set org cookie for the newly created org
      await cookies.set('org', newOrg.id, {
        path: '/',
        httpOnly: true,
        sameSite: 'strict',
        secure: env.NODE_ENV === 'production'
      });

      // Return success
      return {
        data: {
          name: orgName
        }
      };
    } catch (err) {
      console.error('Error creating organization:', err);

      // Check if it's a duplicate name error
      if (err.response?.status === 400) {
        return {
          error: {
            name:
              err.response.data?.name?.[0] ||
              err.response.data?.error ||
              'Organization with this name may already exist'
          }
        };
      }

      return {
        error: {
          name: 'An unexpected error occurred while creating the organization.'
        }
      };
    }
  }
};
