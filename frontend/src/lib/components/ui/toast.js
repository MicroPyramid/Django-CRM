/**
 * Toast utility for easy toast notifications
 * Uses svelte-sonner under the hood
 *
 * @example
 * import { toast } from '$lib/components/ui/toast.js';
 *
 * // Success toast
 * toast.success('Lead created successfully');
 *
 * // Error toast
 * toast.error('Failed to save changes');
 *
 * // With description
 * toast.success('Lead created', {
 *   description: 'Sarah Mitchell has been added to your pipeline'
 * });
 *
 * // Promise toast for async operations
 * toast.promise(saveData(), {
 *   loading: 'Saving...',
 *   success: 'Saved successfully',
 *   error: 'Failed to save'
 * });
 */

import { toast as sonnerToast } from 'svelte-sonner';

export const toast = {
	/** Show a default toast */
	default: (/** @type {string} */ message, /** @type {any} */ options) =>
		sonnerToast(message, options),

	/** Show a success toast */
	success: (/** @type {string} */ message, /** @type {any} */ options) =>
		sonnerToast.success(message, options),

	/** Show an error toast */
	error: (/** @type {string} */ message, /** @type {any} */ options) =>
		sonnerToast.error(message, options),

	/** Show a warning toast */
	warning: (/** @type {string} */ message, /** @type {any} */ options) =>
		sonnerToast.warning(message, options),

	/** Show an info toast */
	info: (/** @type {string} */ message, /** @type {any} */ options) =>
		sonnerToast.info(message, options),

	/** Show a loading toast */
	loading: (/** @type {string} */ message, /** @type {any} */ options) =>
		sonnerToast.loading(message, options),

	/** Show a promise toast that updates based on promise state */
	promise: (/** @type {Promise<any>} */ promise, /** @type {any} */ options) =>
		sonnerToast.promise(promise, options),

	/** Dismiss a specific toast or all toasts */
	dismiss: (/** @type {string|number|undefined} */ id) => sonnerToast.dismiss(id),

	/** Show a custom toast with action buttons */
	action: (
		/** @type {string} */ message,
		/** @type {{ actionLabel: string; onAction: () => void; description?: string }} */ {
			actionLabel,
			onAction,
			...options
		}
	) =>
		sonnerToast(message, {
			...options,
			action: {
				label: actionLabel,
				onClick: onAction
			}
		})
};

export default toast;
