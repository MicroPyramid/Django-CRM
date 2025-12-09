import { writable } from 'svelte/store';

/**
 * @typedef {Object} OrgSettings
 * @property {string} default_currency - Default currency code (e.g., 'USD', 'EUR')
 * @property {string} currency_symbol - Currency symbol (e.g., '$', '€')
 * @property {string|null} default_country - Default country code or null
 */

/** @type {import('svelte/store').Writable<OrgSettings>} */
export const orgSettings = writable({
  default_currency: 'USD',
  currency_symbol: '$',
  default_country: null
});

/**
 * Initialize org settings from JWT or API response
 * @param {Partial<OrgSettings>} settings
 */
export function initOrgSettings(settings) {
  orgSettings.set({
    default_currency: settings.default_currency || 'USD',
    currency_symbol: settings.currency_symbol || '$',
    default_country: settings.default_country || null
  });
}
