/**
 * Table helper utilities for CRM-style inline editing tables
 * @module lib/utils/table-helpers
 */

/**
 * @typedef {Object} SelectOption
 * @property {string} value - Option value
 * @property {string} label - Display label
 * @property {string} color - Tailwind CSS classes for styling
 */

/**
 * Get style classes for a select option
 * @param {string | null | undefined} value - Current value
 * @param {SelectOption[]} options - Available options
 * @returns {string} Tailwind CSS classes
 */
export function getOptionStyle(value, options) {
	const option = options.find((o) => o.value === value);
	return option?.color ?? 'bg-gray-100 text-gray-600';
}

/**
 * Get display label for a select option
 * @param {string | null | undefined} value - Current value
 * @param {SelectOption[]} options - Available options
 * @returns {string} Display label
 */
export function getOptionLabel(value, options) {
	const option = options.find((o) => o.value === value);
	return option?.label ?? value ?? '';
}

/**
 * Get the background color class (first part of color string)
 * @param {string | null | undefined} value - Current value
 * @param {SelectOption[]} options - Available options
 * @returns {string} Background color class
 */
export function getOptionBgColor(value, options) {
	const style = getOptionStyle(value, options);
	return style.split(' ')[0] ?? 'bg-gray-100';
}

/**
 * Create a column config for localStorage persistence
 * @param {string} key - Column key
 * @param {string} label - Column label
 * @param {boolean} [visible=true] - Whether column is visible
 * @param {boolean} [canHide=true] - Whether column can be hidden
 * @returns {{ key: string, label: string, visible: boolean, canHide: boolean }}
 */
export function createColumnConfig(key, label, visible = true, canHide = true) {
	return { key, label, visible, canHide };
}

/**
 * Load column config from localStorage
 * @param {string} storageKey - localStorage key
 * @param {{ key: string, label: string, visible: boolean, canHide: boolean }[]} defaultColumns - Default columns
 * @returns {{ key: string, label: string, visible: boolean, canHide: boolean }[]}
 */
export function loadColumnConfig(storageKey, defaultColumns) {
	if (typeof window === 'undefined') return defaultColumns;
	try {
		const saved = localStorage.getItem(storageKey);
		if (saved) {
			const parsed = JSON.parse(saved);
			return defaultColumns.map((def) => {
				const savedCol = parsed.find((/** @type {{ key: string }} */ p) => p.key === def.key);
				return savedCol ? { ...def, visible: savedCol.visible } : def;
			});
		}
	} catch (e) {
		console.error('Failed to load column config:', e);
	}
	return defaultColumns;
}

/**
 * Save column config to localStorage
 * @param {string} storageKey - localStorage key
 * @param {{ key: string, visible: boolean }[]} columns - Column config
 */
export function saveColumnConfig(storageKey, columns) {
	if (typeof window === 'undefined') return;
	try {
		localStorage.setItem(storageKey, JSON.stringify(columns));
	} catch (e) {
		console.error('Failed to save column config:', e);
	}
}

/**
 * Toggle column visibility
 * @param {{ key: string, visible: boolean, canHide: boolean }[]} columns - Current columns
 * @param {string} key - Column key to toggle
 * @returns {{ key: string, visible: boolean, canHide: boolean }[]}
 */
export function toggleColumnVisibility(columns, key) {
	return columns.map((col) => {
		if (col.key === key && col.canHide) {
			return { ...col, visible: !col.visible };
		}
		return col;
	});
}

/**
 * Get visible column count
 * @param {{ visible: boolean }[]} columns - Columns
 * @returns {{ visible: number, total: number }}
 */
export function getVisibleColumnCount(columns) {
	return {
		visible: columns.filter((c) => c.visible).length,
		total: columns.length
	};
}

// Common status options for CRM entities
export const leadStatusOptions = [
	{ value: 'NEW', label: 'New', color: 'bg-blue-100 text-blue-700' },
	{ value: 'ASSIGNED', label: 'Assigned', color: 'bg-blue-100 text-blue-700' },
	{ value: 'IN_PROCESS', label: 'In Process', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'CONTACTED', label: 'Contacted', color: 'bg-green-100 text-green-700' },
	{ value: 'QUALIFIED', label: 'Qualified', color: 'bg-purple-100 text-purple-700' },
	{ value: 'CONVERTED', label: 'Converted', color: 'bg-emerald-100 text-emerald-700' },
	{ value: 'RECYCLED', label: 'Recycled', color: 'bg-orange-100 text-orange-700' },
	{ value: 'CLOSED', label: 'Closed', color: 'bg-gray-100 text-gray-600' }
];

export const leadRatingOptions = [
	{ value: 'HOT', label: 'Hot', color: 'bg-red-100 text-red-700' },
	{ value: 'WARM', label: 'Warm', color: 'bg-orange-100 text-orange-700' },
	{ value: 'COLD', label: 'Cold', color: 'bg-blue-100 text-blue-700' }
];

export const priorityOptions = [
	{ value: 'URGENT', label: 'Urgent', color: 'bg-red-100 text-red-700' },
	{ value: 'HIGH', label: 'High', color: 'bg-orange-100 text-orange-700' },
	{ value: 'NORMAL', label: 'Normal', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'MEDIUM', label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'LOW', label: 'Low', color: 'bg-green-100 text-green-700' }
];

export const taskStatusOptions = [
	{ value: 'NOT STARTED', label: 'Not Started', color: 'bg-blue-100 text-blue-700' },
	{ value: 'IN PROGRESS', label: 'In Progress', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'PENDING', label: 'Pending', color: 'bg-orange-100 text-orange-700' },
	{ value: 'COMPLETED', label: 'Completed', color: 'bg-green-100 text-green-700' },
	{ value: 'DEFERRED', label: 'Deferred', color: 'bg-gray-100 text-gray-600' }
];

export const caseStatusOptions = [
	{ value: 'New', label: 'New', color: 'bg-blue-100 text-blue-700' },
	{ value: 'Assigned', label: 'Assigned', color: 'bg-blue-100 text-blue-700' },
	{ value: 'Pending', label: 'Pending', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'Closed', label: 'Closed', color: 'bg-gray-100 text-gray-600' },
	{ value: 'Rejected', label: 'Rejected', color: 'bg-red-100 text-red-700' },
	{ value: 'Duplicate', label: 'Duplicate', color: 'bg-orange-100 text-orange-700' }
];

export const caseTypeOptions = [
	{ value: 'Question', label: 'Question', color: 'bg-blue-100 text-blue-700' },
	{ value: 'Incident', label: 'Incident', color: 'bg-orange-100 text-orange-700' },
	{ value: 'Problem', label: 'Problem', color: 'bg-red-100 text-red-700' }
];

export const casePriorityOptions = [
	{ value: 'Low', label: 'Low', color: 'bg-green-100 text-green-700' },
	{ value: 'Normal', label: 'Normal', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'High', label: 'High', color: 'bg-orange-100 text-orange-700' },
	{ value: 'Urgent', label: 'Urgent', color: 'bg-red-100 text-red-700' }
];

export const accountStatusOptions = [
	{ value: 'ACTIVE', label: 'Active', color: 'bg-green-100 text-green-700' },
	{ value: 'INACTIVE', label: 'Inactive', color: 'bg-gray-100 text-gray-600' },
	{ value: 'PENDING', label: 'Pending', color: 'bg-yellow-100 text-yellow-700' }
];

export const opportunityStageOptions = [
	{ value: 'PROSPECTING', label: 'Prospecting', color: 'bg-blue-100 text-blue-700' },
	{ value: 'QUALIFICATION', label: 'Qualification', color: 'bg-purple-100 text-purple-700' },
	{ value: 'PROPOSAL', label: 'Proposal', color: 'bg-yellow-100 text-yellow-700' },
	{ value: 'NEGOTIATION', label: 'Negotiation', color: 'bg-orange-100 text-orange-700' },
	{ value: 'CLOSED_WON', label: 'Closed Won', color: 'bg-green-100 text-green-700' },
	{ value: 'CLOSED_LOST', label: 'Closed Lost', color: 'bg-red-100 text-red-700' }
];
