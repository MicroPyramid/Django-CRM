// src/lib/stores/auth.js
import { writable } from 'svelte/store';

export const auth = writable({
	isAuthenticated: false,
	user: null
});

// Helper to get the current session user from event.locals (SvelteKit convention)
/**
 * @param {any} event
 */
export function getSessionUser(event) {
	// If you use event.locals.user for authentication, return it
	// You can adjust this logic if your user is stored differently
	return event.locals?.user || null;
}
