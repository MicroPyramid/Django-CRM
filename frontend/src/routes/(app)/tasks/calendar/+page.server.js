/**
 * Calendar Page - Redirect to Tasks List
 *
 * The calendar view is now integrated into the main tasks page.
 * This redirect ensures backward compatibility for any bookmarks or links.
 */

import { redirect } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load() {
  // Redirect to tasks list page - calendar is now integrated there
  throw redirect(302, '/tasks');
}
