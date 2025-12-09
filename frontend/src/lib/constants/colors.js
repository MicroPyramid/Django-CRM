/**
 * Tag color palette constants
 * Matches backend COLOR_CHOICES in common/models.py
 * @module lib/constants/colors
 */

/**
 * @typedef {Object} TagColor
 * @property {string} value - Color key (matches backend)
 * @property {string} label - Display name
 * @property {string} class - Combined Tailwind classes for light/dark mode
 */

/** @type {TagColor[]} */
export const TAG_COLORS = [
  {
    value: 'gray',
    label: 'Gray',
    class: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
  },
  {
    value: 'red',
    label: 'Red',
    class: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  },
  {
    value: 'orange',
    label: 'Orange',
    class: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400'
  },
  {
    value: 'amber',
    label: 'Amber',
    class: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
  },
  {
    value: 'yellow',
    label: 'Yellow',
    class: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
  },
  {
    value: 'lime',
    label: 'Lime',
    class: 'bg-lime-100 text-lime-700 dark:bg-lime-900/30 dark:text-lime-400'
  },
  {
    value: 'green',
    label: 'Green',
    class: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
  },
  {
    value: 'emerald',
    label: 'Emerald',
    class: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
  },
  {
    value: 'teal',
    label: 'Teal',
    class: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400'
  },
  {
    value: 'cyan',
    label: 'Cyan',
    class: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400'
  },
  {
    value: 'sky',
    label: 'Sky',
    class: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400'
  },
  {
    value: 'blue',
    label: 'Blue',
    class: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
  },
  {
    value: 'indigo',
    label: 'Indigo',
    class: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400'
  },
  {
    value: 'violet',
    label: 'Violet',
    class: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
  },
  {
    value: 'purple',
    label: 'Purple',
    class: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
  },
  {
    value: 'fuchsia',
    label: 'Fuchsia',
    class: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/30 dark:text-fuchsia-400'
  },
  {
    value: 'pink',
    label: 'Pink',
    class: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400'
  },
  {
    value: 'rose',
    label: 'Rose',
    class: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'
  }
];

/**
 * Get Tailwind classes for a tag color
 * @param {string} color - Color value from TAG_COLORS
 * @returns {string} Combined Tailwind classes
 */
export function getTagColorClass(color) {
  const colorDef = TAG_COLORS.find((c) => c.value === color);
  return colorDef?.class || TAG_COLORS[11].class; // Default to blue
}
