/**
 * Formatting utilities for consistent data display across the application
 * @module lib/utils/formatting
 */

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric'
});

const relativeFormatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

const RELATIVE_UNITS = /** @type {const} */ ([
  { unit: 'year', ms: 365.25 * 24 * 60 * 60 * 1000 },
  { unit: 'month', ms: 30.44 * 24 * 60 * 60 * 1000 },
  { unit: 'week', ms: 7 * 24 * 60 * 60 * 1000 },
  { unit: 'day', ms: 24 * 60 * 60 * 1000 },
  { unit: 'hour', ms: 60 * 60 * 1000 },
  { unit: 'minute', ms: 60 * 1000 },
  { unit: 'second', ms: 1000 }
]);

/**
 * Format a date string to a human-readable format (e.g., "Feb 18, 2026")
 * @param {string | Date | null | undefined} date - Date to format
 * @returns {string} Formatted date string or '-' if no date
 */
export function formatDate(date) {
  if (!date) return '-';
  try {
    return dateFormatter.format(new Date(date));
  } catch {
    return '-';
  }
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 * @param {string | Date | null | undefined} date - Date to format
 * @returns {string} Relative time string or '-' if no date
 */
export function formatRelativeDate(date) {
  if (!date) return '-';
  try {
    const diff = new Date(date).getTime() - Date.now();
    for (const { unit, ms } of RELATIVE_UNITS) {
      if (Math.abs(diff) >= ms || unit === 'second') {
        return relativeFormatter.format(Math.round(diff / ms), unit);
      }
    }
    return '-';
  } catch {
    return '-';
  }
}

/**
 * Format a number as currency
 * @param {number | string | null | undefined} amount - Amount to format
 * @param {string} [currency='USD'] - Currency code (ISO 4217)
 * @param {boolean} [compact=false] - Use compact notation (e.g., $1.2M)
 * @returns {string} Formatted currency string or '-' if no amount
 */
export function formatCurrency(amount, currency = 'USD', compact = false) {
  if (amount === null || amount === undefined) return '-';

  // Convert to number if string
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;

  // Handle NaN or invalid numbers
  if (isNaN(numAmount)) return '-';

  // Ensure valid currency code (fallback to USD)
  const currencyCode = currency && currency.length === 3 ? currency : 'USD';

  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode,
      notation: compact ? 'compact' : 'standard',
      maximumFractionDigits: compact ? 1 : 2
    }).format(numAmount);
  } catch {
    // Fallback if currency code is invalid
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: compact ? 'compact' : 'standard',
      maximumFractionDigits: compact ? 1 : 2
    }).format(numAmount);
  }
}

/**
 * Format a number with commas
 * @param {number | null | undefined} num - Number to format
 * @returns {string} Formatted number string or '-' if no number
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '-';
  return new Intl.NumberFormat('en-US').format(num);
}

/**
 * Get initials from a name string
 * @param {string | null | undefined} name - Full name
 * @param {number} [maxLength=2] - Maximum number of initials
 * @returns {string} Uppercase initials
 */
export function getInitials(name, maxLength = 2) {
  if (!name) return '';
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, maxLength);
}

/**
 * Get initials from first and last name
 * @param {string | null | undefined} firstName
 * @param {string | null | undefined} lastName
 * @returns {string} Uppercase initials
 */
export function getNameInitials(firstName, lastName) {
  const first = firstName?.[0] || '';
  const last = lastName?.[0] || '';
  return `${first}${last}`.toUpperCase();
}

/**
 * Format a phone number for display
 * @param {string | null | undefined} phone - Phone number
 * @returns {string} Formatted phone number or empty string
 */
export function formatPhone(phone) {
  if (!phone) return '';
  // Remove non-digits
  const digits = phone.replace(/\D/g, '');
  // Format as (XXX) XXX-XXXX if 10 digits
  if (digits.length === 10) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  }
  // Return original if not 10 digits
  return phone;
}
