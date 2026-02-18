/**
 * Get Tailwind color classes for a goal status value.
 * @param {string} statusValue
 */
export function getStatusColor(statusValue) {
  switch (statusValue) {
    case 'on_track':
      return 'text-emerald-600 dark:text-emerald-400';
    case 'at_risk':
      return 'text-amber-600 dark:text-amber-400';
    case 'behind':
      return 'text-red-600 dark:text-red-400';
    case 'completed':
      return 'text-blue-600 dark:text-blue-400';
    default:
      return 'text-[var(--text-secondary)]';
  }
}

/**
 * Get Tailwind progress bar color class based on percent.
 * @param {number} percent
 */
export function getProgressColor(percent) {
  if (percent >= 100) return '[&>[data-slot=progress-indicator]]:bg-blue-500';
  if (percent >= 75) return '[&>[data-slot=progress-indicator]]:bg-emerald-500';
  if (percent >= 50) return '[&>[data-slot=progress-indicator]]:bg-amber-500';
  return '[&>[data-slot=progress-indicator]]:bg-red-500';
}
