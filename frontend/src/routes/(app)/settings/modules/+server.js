import { redirect } from '@sveltejs/kit';

/** Settings › Modules is now the Modules section of Settings › Apps. */
export function GET() {
  redirect(308, '/settings/apps');
}
