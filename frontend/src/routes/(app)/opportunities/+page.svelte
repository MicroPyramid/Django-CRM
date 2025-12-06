<script>
	import { invalidateAll, goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		Eye,
		Building2,
		Target,
		DollarSign,
		Calendar,
		Percent,
		User,
		Users,
		Briefcase,
		Globe,
		FileText,
		Trophy,
		XCircle,
		Banknote,
		Contact,
		Tags
	} from '@lucide/svelte';
	import { PageHeader } from '$lib/components/layout';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { CrmDrawer } from '$lib/components/ui/crm-drawer';
	import { CrmTable } from '$lib/components/ui/crm-table';
	import { FilterBar, SearchInput, SelectFilter, DateRangeFilter } from '$lib/components/ui/filter';
	import { formatCurrency, formatRelativeDate } from '$lib/utils/formatting.js';
	import {
		OPPORTUNITY_STAGES as stages,
		OPPORTUNITY_TYPES,
		OPPORTUNITY_SOURCES,
		CURRENCY_CODES
	} from '$lib/constants/filters.js';
	import { orgSettings } from '$lib/stores/org.js';

	const STORAGE_KEY = 'opportunities-crm-columns';

	// Stage options with colors
	const stageOptions = [
		{ value: 'PROSPECTING', label: 'Prospecting', color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300' },
		{ value: 'QUALIFICATION', label: 'Qualification', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' },
		{ value: 'PROPOSAL', label: 'Proposal', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' },
		{ value: 'NEGOTIATION', label: 'Negotiation', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
		{ value: 'CLOSED_WON', label: 'Won', color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
		{ value: 'CLOSED_LOST', label: 'Lost', color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' }
	];

	// Type options
	const typeOptions = OPPORTUNITY_TYPES.map((t) => ({
		value: t.value,
		label: t.label,
		color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
	}));

	// Source options
	const sourceOptions = OPPORTUNITY_SOURCES.map((s) => ({
		value: s.value,
		label: s.label,
		color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400'
	}));

	// Currency options
	const currencyOptions = CURRENCY_CODES.filter((c) => c.value).map((c) => ({
		value: c.value,
		label: c.label,
		color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
	}));


	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: any[], format?: (value: any) => string }} ColumnDef
	 */

	/** @type {ColumnDef[]} */
	const columns = [
		{
			key: 'name',
			label: 'Opportunity',
			type: 'text',
			width: 'w-48',
			canHide: false,
			emptyText: 'Untitled'
		},
		{
			key: 'account',
			label: 'Account',
			type: 'relation',
			width: 'w-40',
			relationIcon: 'building',
			editable: false,
			getValue: (row) => row.account?.name,
			emptyText: ''
		},
		{
			key: 'amount',
			label: 'Amount',
			type: 'number',
			width: 'w-32',
			format: (value, row) => formatAmount(value, row?.currency)
		},
		{ key: 'stage', label: 'Stage', type: 'select', options: stageOptions, width: 'w-32' },
		{ key: 'closedOn', label: 'Close Date', type: 'date', width: 'w-36' },
		{
			key: 'assignedTo',
			label: 'Assigned To',
			type: 'relation',
			width: 'w-40',
			relationIcon: 'user',
			editable: false,
			getValue: (row) => {
				const users = row.assignedTo || [];
				if (users.length === 0) return null;
				if (users.length === 1) return users[0].name;
				return `${users[0].name} +${users.length - 1}`;
			},
			emptyText: ''
		},
		// Hidden by default
		{
			key: 'probability',
			label: 'Probability',
			type: 'number',
			width: 'w-28',
			canHide: true,
			format: (value) => (value != null ? `${value}%` : '-')
		},
		{ key: 'opportunityType', label: 'Type', type: 'select', options: typeOptions, width: 'w-32', canHide: true }
	];

	// Default visible columns (excludes probability and type)
	const DEFAULT_VISIBLE_COLUMNS = ['name', 'account', 'amount', 'stage', 'closedOn', 'assignedTo'];

	/** @type {{ data: any }} */
	let { data } = $props();

	// Options for form
	const formOptions = $derived({
		accounts: data.options?.accounts || [],
		contacts: data.options?.contacts || [],
		tags: data.options?.tags || [],
		users: data.options?.users || [],
		teams: data.options?.teams || []
	});

	// Account options for select field
	const accountOptions = $derived(
		formOptions.accounts.map((a) => ({
			value: a.id,
			label: a.name
		}))
	);

	// Contact options for multiselect (uses id/name format)
	const contactOptions = $derived(
		formOptions.contacts.map((c) => ({
			id: c.id,
			name: c.name || c.email,
			email: c.email
		}))
	);

	// User options for assignedTo multiselect (uses id/name format)
	const userOptions = $derived(
		formOptions.users.map((u) => ({
			id: u.id,
			name: u.name || u.email,
			email: u.email
		}))
	);

	// Team options for teams multiselect (uses id/name format)
	const teamOptions = $derived(
		formOptions.teams.map((t) => ({
			id: t.id,
			name: t.name
		}))
	);

	// Tag options for tags multiselect (uses id/name format)
	const tagOptions = $derived(
		formOptions.tags.map((t) => ({
			id: t.id,
			name: t.name
		}))
	);

	// Drawer column definitions for CrmDrawer (derived since some options come from data)
	const drawerColumns = $derived([
		{ key: 'name', label: 'Name', type: 'text' },
		{
			key: 'account',
			label: 'Account',
			type: 'select',
			icon: Building2,
			options: accountOptions,
			placeholder: 'Select account'
		},
		{
			key: 'stage',
			label: 'Stage',
			type: 'select',
			icon: Target,
			options: stageOptions
		},
		{
			key: 'opportunityType',
			label: 'Type',
			type: 'select',
			icon: Briefcase,
			options: typeOptions,
			placeholder: 'Select type'
		},
		{
			key: 'amount',
			label: 'Amount',
			type: 'number',
			icon: DollarSign,
			placeholder: '0'
		},
		{
			key: 'currency',
			label: 'Currency',
			type: 'select',
			icon: Banknote,
			options: currencyOptions,
			placeholder: 'Select currency'
		},
		{
			key: 'probability',
			label: 'Probability',
			type: 'number',
			icon: Percent,
			placeholder: '0'
		},
		{
			key: 'closedOn',
			label: 'Close Date',
			type: 'date',
			icon: Calendar
		},
		{
			key: 'leadSource',
			label: 'Lead Source',
			type: 'select',
			icon: Globe,
			options: sourceOptions,
			placeholder: 'Select source'
		},
		{
			key: 'contacts',
			label: 'Contacts',
			type: 'multiselect',
			icon: Contact,
			options: contactOptions,
			placeholder: 'Select contacts'
		},
		{
			key: 'assignedTo',
			label: 'Assigned To',
			type: 'multiselect',
			icon: Users,
			options: userOptions,
			placeholder: 'Select users'
		},
		{
			key: 'teams',
			label: 'Teams',
			type: 'multiselect',
			icon: Users,
			options: teamOptions,
			placeholder: 'Select teams'
		},
		{
			key: 'tags',
			label: 'Tags',
			type: 'multiselect',
			icon: Tags,
			options: tagOptions,
			placeholder: 'Select tags'
		},
		{
			key: 'description',
			label: 'Notes',
			type: 'textarea',
			icon: FileText,
			placeholder: 'Add notes...'
		}
	]);

	// URL-based filter state from server
	const filters = $derived(data.filters || {});

	// Stage options for filter dropdown (includes ALL option)
	const stageFilterOptions = $derived([
		{ value: '', label: 'All Stages' },
		...stageOptions
	]);

	// Count active filters
	const activeFiltersCount = $derived.by(() => {
		let count = 0;
		if (filters.search) count++;
		if (filters.stage) count++;
		if (filters.account) count++;
		if (filters.assigned_to?.length > 0) count++;
		if (filters.tags?.length > 0) count++;
		if (filters.created_at_gte || filters.created_at_lte) count++;
		if (filters.closed_on_gte || filters.closed_on_lte) count++;
		return count;
	});

	/**
	 * Update URL with new filters
	 * @param {Record<string, any>} newFilters
	 */
	async function updateFilters(newFilters) {
		const url = new URL($page.url);
		// Clear existing filter params
		['search', 'stage', 'account', 'assigned_to', 'tags', 'created_at_gte', 'created_at_lte', 'closed_on_gte', 'closed_on_lte'].forEach((key) =>
			url.searchParams.delete(key)
		);
		// Set new params
		Object.entries(newFilters).forEach(([key, value]) => {
			if (Array.isArray(value)) {
				value.forEach((v) => url.searchParams.append(key, v));
			} else if (value && value !== 'ALL') {
				url.searchParams.set(key, value);
			}
		});
		await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
	}

	/**
	 * Clear all filters
	 */
	function clearFilters() {
		updateFilters({});
	}

	// Column visibility state - use defaults (excludes probability and type)
	let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);

	// Drawer state
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {string | null} */
	let selectedRowId = $state(null);
	let isLoading = $state(false);

	// Empty opportunity template for create mode
	const emptyOpportunity = {
		name: '',
		account: '',
		stage: 'PROSPECTING',
		opportunityType: '',
		amount: 0,
		currency: '',
		probability: 50,
		closedOn: '',
		leadSource: '',
		contacts: [],
		assignedTo: [],
		teams: [],
		tags: [],
		description: ''
	};

	// Drawer form data - mutable copy for editing
	let drawerFormData = $state({ ...emptyOpportunity });

	// Reset form data when opportunity changes or drawer opens
	$effect(() => {
		if (drawerOpen) {
			if (drawerMode === 'create') {
				drawerFormData = { ...emptyOpportunity, currency: $orgSettings.default_currency || 'USD' };
			} else if (selectedRow) {
				// Extract IDs for multiselect fields and account select
				drawerFormData = {
					...selectedRow,
					// Account ID for select
					account: selectedRow.account?.id || '',
					// Currency with fallback to org default
					currency: selectedRow.currency || $orgSettings.default_currency || 'USD',
					// Extract IDs for multiselect fields
					contacts: (selectedRow.contacts || []).map((/** @type {any} */ c) => c.id),
					assignedTo: (selectedRow.assignedTo || []).map((/** @type {any} */ u) => u.id),
					teams: (selectedRow.teams || []).map((/** @type {any} */ t) => t.id),
					tags: (selectedRow.tags || []).map((/** @type {any} */ t) => t.id)
				};
			}
		}
	});

	// Computed values - opportunities are already filtered server-side
	const opportunities = $derived(data.opportunities || []);
	const stats = $derived(data.stats || { total: 0, totalValue: 0, wonValue: 0, pipeline: 0 });

	// Status chip filter for quick filtering (client-side on top of server filters)
	let statusChipFilter = $state('ALL');

	// Status stages for filtering
	const openStages = ['PROSPECTING', 'QUALIFICATION', 'PROPOSAL', 'NEGOTIATION'];

	// Apply only status chip filter (all other filters are server-side)
	const filteredOpportunities = $derived.by(() => {
		return opportunities.filter((/** @type {any} */ opp) => {
			// Apply status chip filter
			if (statusChipFilter === 'open') {
				return openStages.includes(opp.stage);
			} else if (statusChipFilter === 'won') {
				return opp.stage === 'CLOSED_WON';
			} else if (statusChipFilter === 'lost') {
				return opp.stage === 'CLOSED_LOST';
			}
			return true;
		});
	});

	// Status counts for filter chips
	const openCount = $derived(opportunities.filter((/** @type {any} */ o) => openStages.includes(o.stage)).length);
	const wonCount = $derived(opportunities.filter((/** @type {any} */ o) => o.stage === 'CLOSED_WON').length);
	const lostCount = $derived(opportunities.filter((/** @type {any} */ o) => o.stage === 'CLOSED_LOST').length);

	// Load column visibility from localStorage
	onMount(() => {
		const saved = localStorage.getItem(STORAGE_KEY);
		if (saved) {
			try {
				visibleColumns = JSON.parse(saved);
			} catch (e) {
				console.error('Failed to parse saved columns:', e);
			}
		}
	});

	// Save column visibility when changed
	$effect(() => {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns));
	});

	/**
	 * @param {string} key
	 */
	function toggleColumn(key) {
		const col = columns.find((c) => c.key === key);
		if (col?.canHide === false) return;

		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/**
	 * Handle row change from NotionTable (inline editing)
	 * @param {any} row
	 * @param {string} field
	 * @param {any} value
	 */
	async function handleRowChange(row, field, value) {
		const column = columns.find((c) => c.key === field);
		await saveFieldValue(row.id, field, value, column?.type);
	}

	/**
	 * @param {string} rowId
	 * @param {string} field
	 * @param {any} value
	 * @param {string} [fieldType]
	 */
	async function saveFieldValue(rowId, field, value, fieldType) {
		try {
			const form = new FormData();
			form.append('opportunityId', rowId);

			// Map field names to API field names
			const fieldMapping = /** @type {Record<string, string>} */ ({
				name: 'name',
				account: 'accountId',
				amount: 'amount',
				currency: 'currency',
				probability: 'probability',
				stage: 'stage',
				opportunityType: 'opportunityType',
				closedOn: 'closedOn',
				leadSource: 'leadSource',
				description: 'description'
			});

			// Multi-select fields need special handling
			const multiSelectFields = ['contacts', 'assignedTo', 'teams', 'tags'];

			if (multiSelectFields.includes(field)) {
				// Send as JSON array
				form.append(field, JSON.stringify(Array.isArray(value) ? value : []));
			} else {
				const apiField = fieldMapping[field];
				if (apiField) {
					// Convert value based on type
					let apiValue = value;
					if (fieldType === 'number') {
						apiValue = parseFloat(value) || 0;
					}
					form.append(apiField, apiValue?.toString() || '');
				}
			}

			// Need to send required fields too
			const opp = filteredOpportunities.find((/** @type {any} */ o) => o.id === rowId);
			if (opp) {
				if (field !== 'name') form.append('name', opp.name || '');
				if (field !== 'stage') form.append('stage', opp.stage || 'PROSPECTING');
			}

			const response = await fetch('?/update', { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success('Changes saved');
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to save changes');
			}
		} catch (err) {
			console.error('Error saving field:', err);
			toast.error('Failed to save changes');
		}
	}

	/**
	 * @param {number | null} value
	 * @param {string} [currency='USD']
	 */
	function formatAmount(value, currency = 'USD') {
		if (!value) return '-';
		return formatCurrency(value, currency || 'USD');
	}

	/**
	 * @param {string | null} dateStr
	 */
	function formatDate(dateStr) {
		if (!dateStr) return '-';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
	}

	/**
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionStyle(value, options) {
		const option = options.find((o) => o.value === value);
		return option?.color ?? 'bg-gray-100 text-gray-600';
	}

	/**
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionLabel(value, options) {
		const option = options.find((o) => o.value === value);
		return option?.label ?? value;
	}

	// Drawer functions
	/**
	 * @param {string} rowId
	 */
	function openDrawer(rowId) {
		selectedRowId = rowId;
		drawerMode = 'view';
		drawerOpen = true;
	}

	function openCreate() {
		selectedRowId = null;
		drawerMode = 'create';
		drawerOpen = true;
	}

	function closeDrawer() {
		drawerOpen = false;
		selectedRowId = null;
	}

	/**
	 * Handle field change from CrmDrawer - just updates local state
	 * @param {string} field
	 * @param {any} value
	 */
	function handleDrawerFieldChange(field, value) {
		// Update local form data only - no auto-save
		drawerFormData = { ...drawerFormData, [field]: value };
	}

	/**
	 * Handle save for view/edit mode
	 */
	async function handleDrawerUpdate() {
		if (drawerMode !== 'view' || !selectedRowId) return;

		isLoading = true;
		try {
			const form = new FormData();
			form.append('opportunityId', selectedRowId);
			form.append('name', drawerFormData.name || 'Opportunity');
			form.append('stage', drawerFormData.stage || 'PROSPECTING');
			form.append('amount', drawerFormData.amount?.toString() || '0');
			form.append('probability', drawerFormData.probability?.toString() || '50');
			if (drawerFormData.account) {
				form.append('accountId', drawerFormData.account);
			}
			if (drawerFormData.opportunityType) {
				form.append('opportunityType', drawerFormData.opportunityType);
			}
			if (drawerFormData.currency) {
				form.append('currency', drawerFormData.currency);
			}
			if (drawerFormData.closedOn) {
				form.append('closedOn', drawerFormData.closedOn);
			}
			if (drawerFormData.leadSource) {
				form.append('leadSource', drawerFormData.leadSource);
			}
			if (drawerFormData.description) {
				form.append('description', drawerFormData.description);
			}
			// Multi-select fields - send as JSON arrays
			form.append('contacts', JSON.stringify(drawerFormData.contacts || []));
			form.append('assignedTo', JSON.stringify(drawerFormData.assignedTo || []));
			form.append('teams', JSON.stringify(drawerFormData.teams || []));
			form.append('tags', JSON.stringify(drawerFormData.tags || []));

			const response = await fetch('?/update', { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity updated');
				closeDrawer();
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to update opportunity');
			}
		} catch (err) {
			console.error('Update error:', err);
			toast.error('An error occurred');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Handle save for create mode
	 */
	async function handleDrawerSave() {
		if (drawerMode !== 'create') return;

		isLoading = true;
		try {
			const form = new FormData();
			form.append('name', drawerFormData.name || 'New Opportunity');
			form.append('stage', drawerFormData.stage || 'PROSPECTING');
			form.append('amount', drawerFormData.amount?.toString() || '0');
			form.append('probability', drawerFormData.probability?.toString() || '50');
			if (drawerFormData.account) {
				form.append('accountId', drawerFormData.account);
			}
			if (drawerFormData.opportunityType) {
				form.append('opportunityType', drawerFormData.opportunityType);
			}
			if (drawerFormData.currency) {
				form.append('currency', drawerFormData.currency);
			}
			if (drawerFormData.closedOn) {
				form.append('closedOn', drawerFormData.closedOn);
			}
			if (drawerFormData.leadSource) {
				form.append('leadSource', drawerFormData.leadSource);
			}
			if (drawerFormData.description) {
				form.append('description', drawerFormData.description);
			}
			// Multi-select fields - send as JSON arrays
			if (drawerFormData.contacts?.length > 0) {
				form.append('contacts', JSON.stringify(drawerFormData.contacts));
			}
			if (drawerFormData.assignedTo?.length > 0) {
				form.append('assignedTo', JSON.stringify(drawerFormData.assignedTo));
			}
			if (drawerFormData.teams?.length > 0) {
				form.append('teams', JSON.stringify(drawerFormData.teams));
			}
			if (drawerFormData.tags?.length > 0) {
				form.append('tags', JSON.stringify(drawerFormData.tags));
			}

			const response = await fetch('?/create', { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity created');
				closeDrawer();
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to create opportunity');
			}
		} catch (err) {
			console.error('Create error:', err);
			toast.error('An error occurred');
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Mark opportunity as won
	 */
	async function handleMarkWon() {
		if (!selectedRowId) return;
		await saveFieldValue(selectedRowId, 'stage', 'CLOSED_WON');
		toast.success('Opportunity marked as won!');
	}

	/**
	 * Mark opportunity as lost
	 */
	async function handleMarkLost() {
		if (!selectedRowId) return;
		await saveFieldValue(selectedRowId, 'stage', 'CLOSED_LOST');
		toast.success('Opportunity marked as lost');
	}

	async function deleteSelectedRow() {
		if (!selectedRowId) return;

		isLoading = true;
		try {
			const form = new FormData();
			form.append('opportunityId', selectedRowId);
			const response = await fetch('?/delete', { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity deleted');
				closeDrawer();
				await invalidateAll();
			} else {
				toast.error(result.data?.message || 'Failed to delete opportunity');
			}
		} catch (err) {
			console.error('Delete error:', err);
			toast.error('An error occurred while deleting');
		} finally {
			isLoading = false;
		}
	}

	// Open create drawer for new opportunity
	function addNewRow() {
		openCreate();
	}

	// Get selected row data
	const selectedRow = $derived(
		filteredOpportunities.find((/** @type {any} */ r) => r.id === selectedRowId)
	);

	// Check if opportunity is closed (won or lost)
	const isClosed = $derived(
		selectedRow?.stage === 'CLOSED_WON' || selectedRow?.stage === 'CLOSED_LOST'
	);
	const isWon = $derived(selectedRow?.stage === 'CLOSED_WON');
	const isLost = $derived(selectedRow?.stage === 'CLOSED_LOST');
</script>

<svelte:head>
	<title>Opportunities - BottleCRM</title>
</svelte:head>

<PageHeader title="Opportunities" subtitle="Pipeline: {formatCurrency(stats.pipeline)}">
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<!-- Status Filter Chips -->
			<div class="flex gap-1">
				<button
					type="button"
					onclick={() => (statusChipFilter = 'ALL')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter === 'ALL'
						? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					All
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'ALL'
							? 'bg-gray-700 text-gray-200 dark:bg-gray-200 dark:text-gray-700'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{opportunities.length}
					</span>
				</button>
				<button
					type="button"
					onclick={() => (statusChipFilter = 'open')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter === 'open'
						? 'bg-blue-600 text-white dark:bg-blue-500'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					Open
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'open'
							? 'bg-blue-700 text-blue-100 dark:bg-blue-600'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{openCount}
					</span>
				</button>
				<button
					type="button"
					onclick={() => (statusChipFilter = 'won')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter === 'won'
						? 'bg-emerald-600 text-white dark:bg-emerald-500'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					Won
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'won'
							? 'bg-emerald-700 text-emerald-100 dark:bg-emerald-600'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{wonCount}
					</span>
				</button>
				<button
					type="button"
					onclick={() => (statusChipFilter = 'lost')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter === 'lost'
						? 'bg-red-600 text-white dark:bg-red-500'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					Lost
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'lost'
							? 'bg-red-700 text-red-100 dark:bg-red-600'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{lostCount}
					</span>
				</button>
			</div>

			<div class="bg-border mx-1 h-6 w-px"></div>

			<!-- Column Visibility Dropdown -->
			<DropdownMenu.Root>
				<DropdownMenu.Trigger asChild>
					{#snippet child({ props })}
						<Button {...props} variant="outline" size="sm" class="gap-2">
							<Eye class="h-4 w-4" />
							Columns
							{#if visibleColumns.length < columns.length}
								<span
									class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
								>
									{visibleColumns.length}/{columns.length}
								</span>
							{/if}
						</Button>
					{/snippet}
				</DropdownMenu.Trigger>
				<DropdownMenu.Content align="end" class="w-48">
					<DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
					<DropdownMenu.Separator />
					{#each columns as column (column.key)}
						<DropdownMenu.CheckboxItem
							class=""
							checked={visibleColumns.includes(column.key)}
							onCheckedChange={() => toggleColumn(column.key)}
							disabled={column.canHide === false}
						>
							{column.label}
						</DropdownMenu.CheckboxItem>
					{/each}
				</DropdownMenu.Content>
			</DropdownMenu.Root>

			<Button onclick={addNewRow} disabled={isLoading}>
				<Plus class="mr-2 h-4 w-4" />
				New
			</Button>
		</div>
	{/snippet}
</PageHeader>

<!-- Filter Bar -->
<FilterBar activeCount={activeFiltersCount} onClear={clearFilters}>
	<SearchInput
		value={filters.search}
		onchange={(value) => updateFilters({ ...filters, search: value })}
		placeholder="Search opportunities..."
	/>
	<SelectFilter
		label="Stage"
		options={stageFilterOptions}
		value={filters.stage}
		onchange={(value) => updateFilters({ ...filters, stage: value })}
	/>
	<DateRangeFilter
		label="Close Date"
		startDate={filters.closed_on_gte}
		endDate={filters.closed_on_lte}
		onchange={(start, end) => updateFilters({ ...filters, closed_on_gte: start, closed_on_lte: end })}
	/>
	<DateRangeFilter
		label="Created"
		startDate={filters.created_at_gte}
		endDate={filters.created_at_lte}
		onchange={(start, end) => updateFilters({ ...filters, created_at_gte: start, created_at_lte: end })}
	/>
</FilterBar>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Table View -->
	{#if filteredOpportunities.length === 0}
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<Target class="text-muted-foreground/50 mb-4 h-12 w-12" />
			<h3 class="text-foreground text-lg font-medium">No opportunities found</h3>
			<p class="text-muted-foreground mt-1 text-sm">
				Try adjusting your search criteria or create a new deal.
			</p>
			<Button onclick={addNewRow} class="mt-4" disabled={isLoading}>
				<Plus class="mr-2 h-4 w-4" />
				Create New Deal
			</Button>
		</div>
	{:else}
		<CrmTable
			data={filteredOpportunities}
			{columns}
			bind:visibleColumns
			onRowChange={handleRowChange}
			onRowClick={(row) => openDrawer(row.id)}
		>
			{#snippet emptyState()}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<Target class="text-muted-foreground/50 mb-4 h-12 w-12" />
					<h3 class="text-foreground text-lg font-medium">No opportunities found</h3>
					<p class="text-muted-foreground mt-1 text-sm">
						Try adjusting your search criteria or create a new deal.
					</p>
					<Button onclick={addNewRow} class="mt-4" disabled={isLoading}>
						<Plus class="mr-2 h-4 w-4" />
						Create New Deal
					</Button>
				</div>
			{/snippet}
		</CrmTable>

		<!-- Add row button at bottom -->
		<div class="border-t border-gray-100 px-4 py-2 dark:border-gray-800">
			<button
				type="button"
				onclick={addNewRow}
				disabled={isLoading}
				class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 disabled:opacity-50 dark:hover:bg-gray-900 dark:hover:text-gray-300"
			>
				<Plus class="h-4 w-4" />
				New row
			</button>
		</div>
	{/if}
</div>

<!-- Opportunity Drawer -->
<CrmDrawer
	bind:open={drawerOpen}
	onOpenChange={(open) => !open && closeDrawer()}
	data={drawerFormData}
	columns={drawerColumns}
	titleKey="name"
	titlePlaceholder="Opportunity name"
	headerLabel="Opportunity"
	mode={drawerMode}
	loading={isLoading}
	onFieldChange={handleDrawerFieldChange}
	onDelete={deleteSelectedRow}
	onClose={closeDrawer}
>
	{#snippet activitySection()}
		<!-- Account and Owner info (view mode only) -->
		{#if drawerMode !== 'create' && selectedRow}
			<div class="mb-4">
				<p class="text-gray-500 dark:text-gray-400 mb-2 text-xs font-medium tracking-wider uppercase">Details</p>
				<div class="grid grid-cols-2 gap-3 text-sm">
					<div>
						<p class="text-gray-400 dark:text-gray-500 text-xs">Account</p>
						<p class="text-gray-900 dark:text-gray-100 font-medium">{selectedRow.account?.name || '-'}</p>
					</div>
					{#if selectedRow.createdAt}
						<div>
							<p class="text-gray-400 dark:text-gray-500 text-xs">Created</p>
							<p class="text-gray-900 dark:text-gray-100 font-medium">{formatRelativeDate(selectedRow.createdAt)}</p>
						</div>
					{/if}
					{#if isClosed && selectedRow.closedBy}
						<div>
							<p class="text-gray-400 dark:text-gray-500 text-xs">Closed By</p>
							<p class="text-gray-900 dark:text-gray-100 font-medium">{selectedRow.closedBy.name || '-'}</p>
						</div>
					{/if}
					{#if isClosed && selectedRow.closedOn}
						<div>
							<p class="text-gray-400 dark:text-gray-500 text-xs">Closed On</p>
							<p class="text-gray-900 dark:text-gray-100 font-medium">{formatDate(selectedRow.closedOn)}</p>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	{/snippet}

	{#snippet footerActions()}
		{#if drawerMode === 'create'}
			<Button onclick={handleDrawerSave} disabled={isLoading || !drawerFormData.name?.trim()}>
				{isLoading ? 'Creating...' : 'Create Opportunity'}
			</Button>
		{:else}
			{#if !isClosed}
				<Button
					variant="outline"
					class="text-green-600 hover:text-green-700 hover:bg-green-50 dark:text-green-400 dark:hover:text-green-300 dark:hover:bg-green-900/30"
					onclick={handleMarkWon}
					disabled={isLoading}
				>
					<Trophy class="mr-1.5 h-4 w-4" />
					Mark Won
				</Button>
				<Button
					variant="outline"
					class="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-900/30"
					onclick={handleMarkLost}
					disabled={isLoading}
				>
					<XCircle class="mr-1.5 h-4 w-4" />
					Mark Lost
				</Button>
			{/if}
			<Button onclick={handleDrawerUpdate} disabled={isLoading || !drawerFormData.name?.trim()}>
				{isLoading ? 'Saving...' : 'Save'}
			</Button>
		{/if}
	{/snippet}
</CrmDrawer>
