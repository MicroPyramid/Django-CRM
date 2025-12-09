/**
 * Profile Page - API Version
 *
 * Migrated from Prisma to Django REST API
 * Django endpoint: GET/PATCH /api/profile/
 *
 * To activate:
 *   mv +page.server.js +page.server.prisma.js
 *   mv +page.server.api.js +page.server.js
 */

import { fail, redirect } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';
import { validatePhoneNumber, formatPhoneForStorage } from '$lib/utils/phone.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals, cookies }) {
  if (!locals.user) {
    throw redirect(307, '/login');
  }

  const org = locals.org;

  try {
    // Fetch user profile from Django API
    const response = await apiRequest('/profile/', {}, { cookies, org });

    // Django profile response structure may vary
    const profileData = response.user_obj || response;

    // Get user details
    const userDetails = profileData.user_details || profileData.user || {};

    // Transform to Prisma structure
    const user = {
      id: profileData.id || locals.user.id,
      user_id: profileData.user_id || userDetails.id,
      email: userDetails.email || profileData.email || locals.user.email,
      name: userDetails.name || profileData.name || userDetails.email,
      profilePhoto:
        profileData.profile_photo || userDetails.profile_photo || userDetails.profile_pic || null,
      phone: profileData.phone || userDetails.phone || null,
      isActive: profileData.is_active !== undefined ? profileData.is_active : true,
      lastLogin: userDetails.last_login || null,
      createdAt:
        profileData.created_at || profileData.created_on || userDetails.date_joined || null,
      organizations: [] // Django might not return this in profile endpoint
    };

    return { user };
  } catch (err) {
    console.error('Error loading profile:', err);
    throw redirect(307, '/login');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  updateProfile: async ({ request, locals, cookies }) => {
    if (!locals.user) {
      throw redirect(307, '/login');
    }

    const org = locals.org;
    const formData = await request.formData();
    const name = formData.get('name')?.toString();
    const phone = formData.get('phone')?.toString();

    // Validation
    const errors = {};

    if (!name || name.trim().length === 0) {
      errors.name = 'Name is required';
    } else if (name.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters long';
    }

    // Validate phone if provided
    let formattedPhone = null;
    if (phone && phone.trim().length > 0) {
      const phoneValidation = validatePhoneNumber(phone.trim());
      if (!phoneValidation.isValid) {
        errors.phone = phoneValidation.error || 'Please enter a valid phone number';
      } else {
        formattedPhone = formatPhoneForStorage(phone.trim());
      }
    }

    if (Object.keys(errors).length > 0) {
      return fail(400, {
        errors,
        data: { name, phone }
      });
    }

    try {
      // Transform to Django field names
      const djangoData = {
        name: name.trim(),
        phone: formattedPhone
      };

      // Update profile via API
      await apiRequest(
        '/profile/',
        {
          method: 'PATCH',
          body: djangoData
        },
        { cookies, org }
      );

      return {
        success: true,
        message: 'Profile updated successfully'
      };
    } catch (err) {
      console.error('Error updating profile:', err);
      return fail(500, {
        error:
          'Failed to update profile: ' + (err instanceof Error ? err.message : 'Unknown error'),
        data: { name, phone }
      });
    }
  }
};
