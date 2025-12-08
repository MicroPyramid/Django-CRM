<script>
	import { enhance } from '$app/forms';
	import { invalidateAll, goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		Briefcase,
		Building2,
		User,
		Users,
		Flag,
		Tag,
		Circle,
		Calendar,
		FileText,
		MessageSquare,
		Activity,
		Loader2,
		Eye,
		Filter
	} from '@lucide/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { PageHeader } from '$lib/components/layout';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { CrmTable } from '$lib/components/ui/crm-table';
	import { CrmDrawer } from '$lib/components/ui/crm-drawer';
	import { FilterBar, SearchInput, SelectFilter, DateRangeFilter } from '$lib/components/ui/filter';
	import { Pagination } from '$lib/components/ui/pagination';
	import {
		caseStatusOptions,
		caseTypeOptions,
		casePriorityOptions
	} from '$lib/utils/table-helpers.js';
	import { useDrawerState } from '$lib/hooks';

	// Account from URL param (for quick action from account page)
	let accountFromUrl = $state(false);
	let accountName = $state('');
	let accountIdFromUrl = $state('');

	/**
	 * @typedef {Object} ColumnDef
	 * @property {string} key
	 * @property {string} label
	 * @property {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} [type]
	 * @property {string} [width]
	 * @property {{ value: string, label: string, color: string }[]} [options]
	 * @property {boolean} [editable]
	 * @property {boolean} [canHide]
	 * @property {string} [relationIcon]
	 * @property {(row: any) => any} [getValue]
	 */

	// NotionTable column configuration - reordered for scanning priority
	/** @type {ColumnDef[]} */
	const columns = [
		{ key: 'subject', label: 'Case', type: 'text', width: 'w-[250px]', canHide: false },
		{
			key: 'account',
			label: 'Account',
			type: 'relation',
			relationIcon: 'building',
			width: 'w-40',
			getValue: (/** @type {any} */ row) => row.account
		},
		{
			key: 'priority',
			label: 'Priority',
			type: 'select',
			options: casePriorityOptions,
			width: 'w-28'
		},
		{ key: 'status', label: 'Status', type: 'select', options: caseStatusOptions, width: 'w-28' },
		{ key: 'caseType', label: 'Type', type: 'select', options: caseTypeOptions, width: 'w-28' },
		{
			key: 'owner',
			label: 'Assigned To',
			type: 'relation',
			relationIcon: 'user',
			width: 'w-36',
			getValue: (/** @type {any} */ row) => row.owner
		},
		{ key: 'createdAt', label: 'Created', type: 'date', width: 'w-32', editable: false }
	];

	// Column visibility state
	const STORAGE_KEY = 'cases-column-config';
	let visibleColumns = $state(columns.map((c) => c.key));

	// Load column visibility from localStorage
	onMount(() => {
		const saved = localStorage.getItem(STORAGE_KEY);
		if (saved) {
			try {
				const parsed = JSON.parse(saved);
				visibleColumns = parsed.filter((/** @type {string} */ key) =>
					columns.some((c) => c.key === key)
				);
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
	function isColumnVisible(key) {
		return visibleColumns.includes(key);
	}

	/**
	 * @param {string} key
	 */
	function toggleColumn(key) {
		const column = columns.find((c) => c.key === key);
		// @ts-ignore
		if (column?.canHide === false) return;

		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	const columnCounts = $derived({
		visible: visibleColumns.length,
		total: columns.length
	});

	// Drawer local form state
	let drawerFormData = $state({
		subject: '',
		description: '',
		accountId: '',
		accountName: '', // Read-only display for edit mode
		assignedTo: /** @type {string[]} */ ([]),
		contacts: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		tags: /** @type {string[]} */ ([]),
		priority: 'Normal',
		caseType: '',
		status: 'New',
		closedOn: ''
	});

	// Track if drawer form has been modified
	let isDrawerDirty = $state(false);
	let isSubmitting = $state(false);

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	let casesData = $derived(data.cases || []);
	const pagination = $derived(data.pagination || { page: 1, limit: 10, total: 0, totalPages: 0 });

	// Dropdown options from server (loaded with page data)
	const formOptions = $derived(data.formOptions || {});
	const accounts = $derived(formOptions.accounts || []);
	const users = $derived(formOptions.users || []);
	const contacts = $derived(formOptions.contacts || []);
	const teams = $derived(formOptions.teams || []);
	const tags = $derived(formOptions.tags || []);

	/**
	 * Get account name from server-provided accounts list
	 * @param {string} id
	 */
	function fetchAccountName(id) {
		const account = accounts.find((a) => a.id === id);
		if (account) {
			accountName = account.name;
		} else {
			accountName = 'Unknown Account';
		}
	}

	/**
	 * Clear URL params for accountId and action
	 */
	function clearUrlParams() {
		const url = new URL($page.url);
		url.searchParams.delete('action');
		url.searchParams.delete('accountId');
		goto(url.pathname, { replaceState: true, invalidateAll: true });
		accountFromUrl = false;
		accountName = '';
		accountIdFromUrl = '';
	}

	// Drawer state using hook
	const drawer = useDrawerState();

	// URL sync for accountId and action params (quick action from account page)
	$effect(() => {
		const action = $page.url.searchParams.get('action');
		const accountIdParam = $page.url.searchParams.get('accountId');

		if (action === 'create' && !drawer.detailOpen) {
			// Handle account pre-fill from URL BEFORE opening drawer
			if (accountIdParam) {
				accountIdFromUrl = accountIdParam;
				accountFromUrl = true;
				fetchAccountName(accountIdParam);
			}

			drawer.openCreate();

			// Set account in form data after drawer opens
			if (accountIdParam) {
				drawerFormData.accountId = accountIdParam;
			}
		}
	});

	// Account options for drawer select
	const accountOptions = $derived([
		{ value: '', label: 'None', color: 'bg-gray-100 text-gray-600' },
		...accounts.map((/** @type {any} */ a) => ({
			value: a.id,
			label: a.name,
			color: 'bg-blue-100 text-blue-700'
		}))
	]);

	// Drawer columns configuration (with icons and multiselect)
	// Account is only editable on create (and not when pre-filled from URL), read-only on edit
	const drawerColumns = $derived([
		{ key: 'subject', label: 'Case Title', type: 'text' },
		// Account field: readonly when pre-filled from URL or in edit mode
		drawer.mode === 'create' && !accountFromUrl
			? {
					key: 'accountId',
					label: 'Account',
					type: 'select',
					icon: Building2,
					options: accountOptions,
					emptyText: 'No account'
				}
			: accountFromUrl
				? {
						key: 'accountDisplay',
						label: 'Account',
						type: 'readonly',
						icon: Building2,
						getValue: () => accountName || 'Loading...'
					}
				: {
						key: 'accountName',
						label: 'Account',
						type: 'readonly',
						icon: Building2,
						emptyText: 'No account'
					},
		{
			key: 'caseType',
			label: 'Type',
			type: 'select',
			icon: Tag,
			options: caseTypeOptions,
			emptyText: 'Select type'
		},
		{
			key: 'status',
			label: 'Status',
			type: 'select',
			icon: Circle,
			options: caseStatusOptions
		},
		{
			key: 'priority',
			label: 'Priority',
			type: 'select',
			icon: Flag,
			options: casePriorityOptions
		},
		{
			key: 'description',
			label: 'Description',
			type: 'textarea',
			icon: FileText,
			placeholder: 'Describe the case...',
			emptyText: 'No description'
		},
		{
			key: 'assignedTo',
			label: 'Assigned To',
			type: 'multiselect',
			icon: User,
			options: users.map((/** @type {any} */ u) => ({ id: u.id, name: u.name })),
			emptyText: 'Unassigned'
		},
		{
			key: 'teams',
			label: 'Teams',
			type: 'multiselect',
			icon: Users,
			options: teams.map((/** @type {any} */ t) => ({ id: t.id, name: t.name })),
			emptyText: 'No teams'
		},
		{
			key: 'contacts',
			label: 'Contacts',
			type: 'multiselect',
			icon: User,
			options: contacts.map((/** @type {any} */ c) => ({ id: c.id, name: c.name, email: c.email })),
			emptyText: 'No contacts'
		},
		{
			key: 'tags',
			label: 'Tags',
			type: 'multiselect',
			icon: Tag,
			options: tags.map((/** @type {any} */ t) => ({ id: t.id, name: t.name })),
			emptyText: 'No tags'
		},
		{
			key: 'closedOn',
			label: 'Close Date',
			type: 'date',
			icon: Calendar,
			emptyText: 'Not set'
		}
	]);

	// Reset drawer form when case changes or drawer opens
	$effect(() => {
		if (drawer.detailOpen) {
			if (drawer.mode === 'create') {
				drawerFormData = {
					subject: '',
					description: '',
					accountId: accountIdFromUrl || '', // Preserve account from URL if present
					accountName: '',
					assignedTo: [],
					contacts: [],
					teams: [],
					tags: [],
					priority: 'Normal',
					caseType: '',
					status: 'New',
					closedOn: ''
				};
			} else if (drawer.selected) {
				const caseItem = drawer.selected;
				drawerFormData = {
					subject: caseItem.subject || '',
					description: caseItem.description || '',
					accountId: caseItem.account?.id || '',
					accountName: caseItem.account?.name || '', // Read-only display
					assignedTo: (caseItem.assignedTo || []).map((/** @type {any} */ a) => a.id),
					contacts: (caseItem.contacts || []).map((/** @type {any} */ c) => c.id),
					teams: (caseItem.teams || []).map((/** @type {any} */ t) => t.id),
					tags: (caseItem.tags || []).map((/** @type {any} */ t) => t.id),
					priority: caseItem.priority || 'Normal',
					caseType: caseItem.caseType || '',
					status: caseItem.status || 'New',
					closedOn: caseItem.closedOn ? caseItem.closedOn.split('T')[0] : ''
				};
			}
			isDrawerDirty = false;
		}
	});

	/**
	 * Handle field change from drawer
	 * @param {string} field
	 * @param {any} value
	 */
	function handleDrawerFieldChange(field, value) {
		drawerFormData = { ...drawerFormData, [field]: value };
		isDrawerDirty = true;
	}

	// URL-based filter state from server
	const filters = $derived(data.filters || {});

	// Status options for filter dropdown
	const statusFilterOptions = $derived([
		{ value: '', label: 'All Statuses' },
		...caseStatusOptions
	]);

	// Priority options for filter dropdown
	const priorityFilterOptions = $derived([
		{ value: '', label: 'All Priorities' },
		...casePriorityOptions
	]);

	// Type options for filter dropdown
	const typeFilterOptions = $derived([{ value: '', label: 'All Types' }, ...caseTypeOptions]);

	// Count active filters (excluding status since it's handled via chips in header)
	const activeFiltersCount = $derived.by(() => {
		let count = 0;
		if (filters.search) count++;
		if (filters.priority) count++;
		if (filters.case_type) count++;
		if (filters.assigned_to?.length > 0) count++;
		if (filters.tags?.length > 0) count++;
		if (filters.created_at_gte || filters.created_at_lte) count++;
		return count;
	});

	/**
	 * Update URL with new filters
	 * @param {Record<string, any>} newFilters
	 */
	async function updateFilters(newFilters) {
		const url = new URL($page.url);
		// Clear existing filter params
		[
			'search',
			'status',
			'priority',
			'case_type',
			'assigned_to',
			'tags',
			'created_at_gte',
			'created_at_lte'
		].forEach((key) => url.searchParams.delete(key));
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

	/**
	 * Handle page change
	 * @param {number} newPage
	 */
	async function handlePageChange(newPage) {
		const url = new URL($page.url);
		url.searchParams.set('page', newPage.toString());
		await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
	}

	/**
	 * Handle limit change
	 * @param {number} newLimit
	 */
	async function handleLimitChange(newLimit) {
		const url = new URL($page.url);
		url.searchParams.set('limit', newLimit.toString());
		url.searchParams.set('page', '1'); // Reset to first page
		await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
	}

	// Status counts for filter chips
	const openStatuses = ['New', 'Open', 'Pending', 'Assigned'];
	const openCount = $derived(
		casesData.filter((/** @type {any} */ c) => openStatuses.includes(c.status)).length
	);
	const closedCount = $derived(
		casesData.filter((/** @type {any} */ c) => c.status === 'Closed').length
	);

	// Status chip filter state (client-side quick filter on top of server filters)
	let statusChipFilter = $state('ALL');

	// Filter panel expansion state
	let filtersExpanded = $state(false);

	// Filtered cases - server already applies main filters, just apply status chip
	const filteredCases = $derived.by(() => {
		let filtered = casesData;
		if (statusChipFilter === 'open') {
			filtered = filtered.filter((/** @type {any} */ c) => openStatuses.includes(c.status));
		} else if (statusChipFilter === 'closed') {
			filtered = filtered.filter((/** @type {any} */ c) => c.status === 'Closed');
		}
		return filtered;
	});

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;
	/** @type {HTMLFormElement} */
	let closeForm;
	/** @type {HTMLFormElement} */
	let reopenForm;

	// Form data state
	let formState = $state({
		title: '',
		description: '',
		accountId: '',
		assignedTo: /** @type {string[]} */ ([]),
		contacts: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		tags: /** @type {string[]} */ ([]),
		priority: 'Normal',
		caseType: '',
		status: 'New',
		dueDate: '',
		caseId: ''
	});

	/**
	 * Handle save from drawer
	 */
	async function handleSave() {
		if (!drawerFormData.subject?.trim()) {
			toast.error('Case title is required');
			return;
		}

		isSubmitting = true;

		// Convert drawer form data to form state
		formState.title = drawerFormData.subject || '';
		formState.description = drawerFormData.description || '';
		formState.accountId = drawerFormData.accountId || '';
		formState.assignedTo = drawerFormData.assignedTo || [];
		formState.contacts = drawerFormData.contacts || [];
		formState.teams = drawerFormData.teams || [];
		formState.tags = drawerFormData.tags || [];
		formState.priority = drawerFormData.priority || 'Normal';
		formState.caseType = drawerFormData.caseType || '';
		formState.status = drawerFormData.status || 'New';
		formState.dueDate = drawerFormData.closedOn || '';

		await tick();

		if (drawer.mode === 'edit' && drawer.selected) {
			formState.caseId = drawer.selected.id;
			await tick();
			updateForm.requestSubmit();
		} else {
			createForm.requestSubmit();
		}
	}

	/**
	 * Handle case delete
	 */
	async function handleDelete() {
		if (!drawer.selected) return;
		if (!confirm(`Are you sure you want to delete "${drawer.selected.subject}"?`)) return;

		formState.caseId = drawer.selected.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Handle case close
	 */
	async function handleClose() {
		if (!drawer.selected) return;

		formState.caseId = drawer.selected.id;
		await tick();
		closeForm.requestSubmit();
	}

	/**
	 * Handle case reopen
	 */
	async function handleReopen() {
		if (!drawer.selected) return;

		formState.caseId = drawer.selected.id;
		await tick();
		reopenForm.requestSubmit();
	}

	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 * @param {boolean} closeDetailDrawer
	 */
	function createEnhanceHandler(successMessage, closeDetailDrawer = false) {
		return () => {
			return async ({ result }) => {
				isSubmitting = false;
				if (result.type === 'success') {
					toast.success(successMessage);
					isDrawerDirty = false;
					if (closeDetailDrawer) {
						drawer.closeDetail();
					} else {
						drawer.closeAll();
					}
					// Clear account URL params if they were set
					if (accountFromUrl) {
						clearUrlParams();
					}
					await invalidateAll();
				} else if (result.type === 'failure') {
					toast.error(result.data?.error || 'Operation failed');
				} else if (result.type === 'error') {
					toast.error('An unexpected error occurred');
				}
			};
		};
	}

	/**
	 * Convert case to form state for inline editing
	 * @param {any} caseItem
	 */
	function caseToFormState(caseItem) {
		return {
			caseId: caseItem.id,
			title: caseItem.subject || '',
			description: caseItem.description || '',
			accountId: caseItem.account?.id || '',
			assignedTo: (caseItem.assignedTo || []).map((/** @type {any} */ a) => a.id),
			contacts: (caseItem.contacts || []).map((/** @type {any} */ c) => c.id),
			teams: (caseItem.teams || []).map((/** @type {any} */ t) => t.id),
			tags: (caseItem.tags || []).map((/** @type {any} */ t) => t.id),
			priority: caseItem.priority || 'Normal',
			caseType: caseItem.caseType || '',
			status: caseItem.status || 'New',
			dueDate: caseItem.closedOn ? caseItem.closedOn.split('T')[0] : ''
		};
	}

	/**
	 * Handle inline cell edits - persists to API
	 * @param {any} caseItem
	 * @param {string} field
	 * @param {any} value
	 */
	async function handleQuickEdit(caseItem, field, value) {
		// Map frontend field names to form state field names
		const fieldMapping = {
			subject: 'title',
			caseType: 'caseType',
			priority: 'priority',
			status: 'status',
			closedOn: 'dueDate'
		};

		// Populate form state with current case data
		const currentState = caseToFormState(caseItem);

		// Update the specific field (use mapped name if exists)
		const formField = fieldMapping[field] || field;
		currentState[formField] = value;

		// Copy to form state
		Object.assign(formState, currentState);

		await tick();
		updateForm.requestSubmit();
	}

	/**
	 * Handle row change from CrmTable (inline editing)
	 * @param {any} row
	 * @param {string} field
	 * @param {any} value
	 */
	async function handleRowChange(row, field, value) {
		await handleQuickEdit(row, field, value);
	}
</script>

<svelte:head>
	<title>Cases - BottleCRM</title>
</svelte:head>

<PageHeader title="Cases" subtitle="{filteredCases.length} of {casesData.length} cases">
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<!-- Status Filter Chips -->
			<div class="flex gap-1">
				<button
					type="button"
					onclick={() => (statusChipFilter = 'ALL')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
					'ALL'
						? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					All
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'ALL'
							? 'bg-gray-700 text-gray-200 dark:bg-gray-200 dark:text-gray-700'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{casesData.length}
					</span>
				</button>
				<button
					type="button"
					onclick={() => (statusChipFilter = 'open')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
					'open'
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
					onclick={() => (statusChipFilter = 'closed')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
					'closed'
						? 'bg-gray-600 text-white dark:bg-gray-500'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					Closed
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'closed'
							? 'bg-gray-700 text-gray-200 dark:bg-gray-600'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{closedCount}
					</span>
				</button>
			</div>

			<div class="bg-border mx-1 h-6 w-px"></div>

			<!-- Filter Toggle Button -->
			<Button
				variant={filtersExpanded ? 'secondary' : 'outline'}
				size="sm"
				class="gap-2"
				onclick={() => (filtersExpanded = !filtersExpanded)}
			>
				<Filter class="h-4 w-4" />
				Filters
				{#if activeFiltersCount > 0}
					<span
						class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
					>
						{activeFiltersCount}
					</span>
				{/if}
			</Button>

			<DropdownMenu.Root>
				<DropdownMenu.Trigger>
					{#snippet child({ props })}
						<Button {...props} variant="outline" size="sm" class="gap-2">
							<Eye class="h-4 w-4" />
							Columns
							{#if columnCounts.visible < columnCounts.total}
								<span
									class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
								>
									{columnCounts.visible}/{columnCounts.total}
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
							checked={isColumnVisible(column.key)}
							onCheckedChange={() => toggleColumn(column.key)}
							disabled={column.canHide === false}
						>
							{column.label}
						</DropdownMenu.CheckboxItem>
					{/each}
				</DropdownMenu.Content>
			</DropdownMenu.Root>

			<Button onclick={drawer.openCreate}>
				<Plus class="mr-2 h-4 w-4" />
				New Case
			</Button>
		</div>
	{/snippet}
</PageHeader>

<div class="flex-1">
	<!-- Collapsible Filter Bar -->
	<FilterBar
		minimal={true}
		expanded={filtersExpanded}
		activeCount={activeFiltersCount}
		onClear={clearFilters}
		class="pb-4"
	>
		<SearchInput
			value={filters.search}
			onchange={(value) => updateFilters({ ...filters, search: value })}
			placeholder="Search cases..."
		/>
		<SelectFilter
			label="Priority"
			options={priorityFilterOptions}
			value={filters.priority}
			onchange={(value) => updateFilters({ ...filters, priority: value })}
		/>
		<SelectFilter
			label="Type"
			options={typeFilterOptions}
			value={filters.case_type}
			onchange={(value) => updateFilters({ ...filters, case_type: value })}
		/>
		<DateRangeFilter
			label="Created"
			startDate={filters.created_at_gte}
			endDate={filters.created_at_lte}
			onchange={(start, end) =>
				updateFilters({ ...filters, created_at_gte: start, created_at_lte: end })}
		/>
	</FilterBar>
	<CrmTable
		data={filteredCases}
		{columns}
		bind:visibleColumns
		onRowChange={handleRowChange}
		onRowClick={(row) => drawer.openDetail(row)}
	>
		{#snippet emptyState()}
			<div class="flex flex-col items-center justify-center py-16 text-center">
				<Briefcase class="text-muted-foreground/50 mb-4 h-12 w-12" />
				<h3 class="text-foreground text-lg font-medium">No cases found</h3>
			</div>
		{/snippet}
	</CrmTable>

	<!-- Pagination -->
	<Pagination
		page={pagination.page}
		limit={pagination.limit}
		total={pagination.total}
		onPageChange={handlePageChange}
		onLimitChange={handleLimitChange}
	/>
</div>

<!-- Case Drawer -->
<CrmDrawer
	bind:open={drawer.detailOpen}
	onOpenChange={(open) => {
		if (!open) {
			drawer.closeAll();
			if (accountFromUrl) {
				clearUrlParams();
			}
		}
	}}
	data={drawerFormData}
	columns={drawerColumns}
	titleKey="subject"
	titlePlaceholder="Case title"
	headerLabel={drawer.mode === 'create' ? 'New Case' : 'Case'}
	onFieldChange={handleDrawerFieldChange}
	onDelete={handleDelete}
	onClose={() => drawer.closeAll()}
	loading={drawer.loading}
	mode={drawer.mode === 'create' ? 'create' : 'view'}
>
	{#snippet activitySection()}
		{#if drawer.mode !== 'create' && drawer.selected?.comments?.length > 0}
			<div class="space-y-3">
				<div class="mb-3 flex items-center gap-2">
					<Activity class="h-4 w-4 text-gray-400 dark:text-gray-500" />
					<p class="text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400">
						Activity
					</p>
				</div>
				{#each drawer.selected.comments.slice(0, 5) as comment (comment.id)}
					<div class="flex gap-3">
						<div
							class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800"
						>
							<MessageSquare class="h-4 w-4 text-gray-400 dark:text-gray-500" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-sm text-gray-900 dark:text-gray-100">
								<span class="font-medium">{comment.author?.name || 'Unknown'}</span>
								{' '}added a note
							</p>
							<p class="mt-0.5 text-xs text-gray-500">
								{new Date(comment.createdAt).toLocaleDateString('en-US', {
									month: 'short',
									day: 'numeric',
									year: 'numeric'
								})}
							</p>
							<p class="mt-1 line-clamp-2 text-sm text-gray-500">{comment.body}</p>
						</div>
					</div>
				{/each}
			</div>
		{:else if drawer.mode !== 'create'}
			<div class="flex flex-col items-center justify-center py-6 text-center">
				<MessageSquare class="mb-2 h-8 w-8 text-gray-300 dark:text-gray-600" />
				<p class="text-sm text-gray-500 dark:text-gray-400">No activity yet</p>
			</div>
		{/if}
	{/snippet}

	{#snippet footerActions()}
		{#if drawer.mode !== 'create' && drawer.selected}
			{#if drawerFormData.status === 'Closed'}
				<Button variant="outline" onclick={handleReopen} disabled={isSubmitting}>Reopen</Button>
			{:else}
				<Button variant="outline" onclick={handleClose} disabled={isSubmitting}>Close Case</Button>
			{/if}
		{/if}
		<Button variant="outline" onclick={() => drawer.closeAll()} disabled={isSubmitting}>
			Cancel
		</Button>
		{#if isDrawerDirty || drawer.mode === 'create'}
			<Button onclick={handleSave} disabled={isSubmitting}>
				{#if isSubmitting}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					{drawer.mode === 'create' ? 'Creating...' : 'Saving...'}
				{:else}
					{drawer.mode === 'create' ? 'Create Case' : 'Save Changes'}
				{/if}
			</Button>
		{/if}
	{/snippet}
</CrmDrawer>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Case created successfully')}
	class="hidden"
>
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="accountId" value={formState.accountId} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
	<input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
	<input type="hidden" name="priority" value={formState.priority} />
	<input type="hidden" name="caseType" value={formState.caseType} />
	<input type="hidden" name="dueDate" value={formState.dueDate} />
</form>

<form
	method="POST"
	action="?/update"
	bind:this={updateForm}
	use:enhance={createEnhanceHandler('Case updated successfully')}
	class="hidden"
>
	<input type="hidden" name="caseId" value={formState.caseId} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
	<input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
	<input type="hidden" name="priority" value={formState.priority} />
	<input type="hidden" name="caseType" value={formState.caseType} />
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="dueDate" value={formState.dueDate} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Case deleted successfully', true)}
	class="hidden"
>
	<input type="hidden" name="caseId" value={formState.caseId} />
</form>

<form
	method="POST"
	action="?/close"
	bind:this={closeForm}
	use:enhance={createEnhanceHandler('Case closed successfully')}
	class="hidden"
>
	<input type="hidden" name="caseId" value={formState.caseId} />
</form>

<form
	method="POST"
	action="?/reopen"
	bind:this={reopenForm}
	use:enhance={createEnhanceHandler('Case reopened successfully')}
	class="hidden"
>
	<input type="hidden" name="caseId" value={formState.caseId} />
</form>
