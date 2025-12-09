/**
 * UI helper utilities for consistent styling across the application
 * @module lib/utils/ui-helpers
 */

/**
 * Lead/Contact status class mapping
 * @param {string | null | undefined} status
 * @returns {string} Tailwind CSS classes
 */
export function getLeadStatusClass(status) {
  /** @type {{ [key: string]: string }} */
  const classes = {
    NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    ASSIGNED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    IN_PROCESS: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    PENDING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    CONTACTED: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    QUALIFIED: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    CONVERTED: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
    RECYCLED: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    CLOSED: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  };
  return classes[status?.toUpperCase() || ''] || classes.NEW;
}

/**
 * Case status class mapping
 * @param {string | null | undefined} status
 * @returns {string} Tailwind CSS classes
 */
export function getCaseStatusClass(status) {
  /** @type {{ [key: string]: string }} */
  const classes = {
    NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    ASSIGNED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    OPEN: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    PENDING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    'IN PROGRESS': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    IN_PROGRESS: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    CLOSED: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    REJECTED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    DUPLICATE: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
  };
  return classes[status?.toUpperCase() || ''] || classes.NEW;
}

/**
 * Case type class mapping
 * @param {string | null | undefined} caseType
 * @returns {string} Tailwind CSS classes
 */
export function getCaseTypeClass(caseType) {
  /** @type {{ [key: string]: string }} */
  const classes = {
    QUESTION: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    INCIDENT: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    PROBLEM: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  };
  return (
    classes[caseType?.toUpperCase() || ''] ||
    'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  );
}

/**
 * Priority class mapping
 * @param {string | null | undefined} priority
 * @returns {string} Tailwind CSS classes
 */
export function getPriorityClass(priority) {
  /** @type {{ [key: string]: string }} */
  const classes = {
    URGENT: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    HIGH: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    NORMAL: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
  };
  return classes[priority?.toUpperCase() || ''] || classes.NORMAL;
}

/**
 * Lead rating configuration
 * @param {string | null | undefined} rating
 * @returns {{ color: string, bgColor: string, dots: number }}
 */
export function getRatingConfig(rating) {
  /** @type {{ [key: string]: { color: string, bgColor: string, dots: number } }} */
  const configs = {
    HOT: { color: 'text-red-500', bgColor: 'bg-red-500', dots: 3 },
    WARM: { color: 'text-orange-500', bgColor: 'bg-orange-500', dots: 2 },
    COLD: { color: 'text-blue-500', bgColor: 'bg-blue-500', dots: 1 }
  };
  return (
    configs[rating?.toUpperCase() || ''] || {
      color: 'text-gray-400',
      bgColor: 'bg-gray-400',
      dots: 0
    }
  );
}

/**
 * Task status class mapping
 * @param {string | null | undefined} status
 * @returns {string} Tailwind CSS classes
 */
export function getTaskStatusClass(status) {
  /** @type {{ [key: string]: string }} */
  const classes = {
    NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'NOT STARTED': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    'IN PROGRESS': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    IN_PROGRESS: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    PENDING: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    COMPLETED: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    DEFERRED: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  };
  return classes[status?.toUpperCase() || ''] || classes.NEW;
}

/**
 * Format status for display (replace underscores with spaces)
 * @param {string | null | undefined} status
 * @returns {string}
 */
export function formatStatusDisplay(status) {
  if (!status) return 'Unknown';
  return status.replace(/_/g, ' ');
}
