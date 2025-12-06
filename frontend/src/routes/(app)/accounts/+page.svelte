<script>
	import { enhance } from '$app/forms';
	import { invalidateAll, goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		Building2,
		Users,
		Target,
		Calendar,
		Eye,
		Globe,
		Phone,
		Mail,
		DollarSign,
		Briefcase,
		MapPin,
		FileText,
		Hash,
		Lock,
		Unlock,
		AlertTriangle,
		Tag,
		UserPlus,
		Contact,
		Banknote,
		Filter
	} from '@lucide/svelte';
	import { PageHeader } from '$lib/components/layout';
	import { CrmDrawer } from '$lib/components/ui/crm-drawer';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { CrmTable } from '$lib/components/ui/crm-table';
	import { FilterBar, SearchInput, SelectFilter, DateRangeFilter } from '$lib/components/ui/filter';
	import { Pagination } from '$lib/components/ui/pagination';
	import { formatRelativeDate, formatCurrency, getInitials } from '$lib/utils/formatting.js';
	import { COUNTRIES, getCountryName } from '$lib/constants/countries.js';
	import { CURRENCY_CODES } from '$lib/constants/filters.js';
	import { orgSettings } from '$lib/stores/org.js';

	// Column visibility configuration
	const STORAGE_KEY = 'accounts-column-config';

	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: any[], format?: (value: any) => string }} ColumnDef
	 */

	// Industry options for drawer
	const industryOptions = [
		{ value: 'ADVERTISING', label: 'Advertising' },
		{ value: 'AGRICULTURE', label: 'Agriculture' },
		{ value: 'APPAREL & ACCESSORIES', label: 'Apparel & Accessories' },
		{ value: 'AUTOMOTIVE', label: 'Automotive' },
		{ value: 'BANKING', label: 'Banking' },
		{ value: 'BIOTECHNOLOGY', label: 'Biotechnology' },
		{ value: 'BUILDING MATERIALS & EQUIPMENT', label: 'Building Materials & Equipment' },
		{ value: 'CHEMICAL', label: 'Chemical' },
		{ value: 'COMPUTER', label: 'Computer' },
		{ value: 'EDUCATION', label: 'Education' },
		{ value: 'ELECTRONICS', label: 'Electronics' },
		{ value: 'ENERGY', label: 'Energy' },
		{ value: 'ENTERTAINMENT & LEISURE', label: 'Entertainment & Leisure' },
		{ value: 'FINANCE', label: 'Finance' },
		{ value: 'FOOD & BEVERAGE', label: 'Food & Beverage' },
		{ value: 'GROCERY', label: 'Grocery' },
		{ value: 'HEALTHCARE', label: 'Healthcare' },
		{ value: 'INSURANCE', label: 'Insurance' },
		{ value: 'LEGAL', label: 'Legal' },
		{ value: 'MANUFACTURING', label: 'Manufacturing' },
		{ value: 'PUBLISHING', label: 'Publishing' },
		{ value: 'REAL ESTATE', label: 'Real Estate' },
		{ value: 'SERVICE', label: 'Service' },
		{ value: 'SOFTWARE', label: 'Software' },
		{ value: 'SPORTS', label: 'Sports' },
		{ value: 'TECHNOLOGY', label: 'Technology' },
		{ value: 'TELECOMMUNICATIONS', label: 'Telecommunications' },
		{ value: 'TELEVISION', label: 'Television' },
		{ value: 'TRANSPORTATION', label: 'Transportation' },
		{ value: 'VENTURE CAPITAL', label: 'Venture Capital' }
	];

	// Country options for drawer
	const countryOptions = COUNTRIES.map((c) => ({ value: c.code, label: c.name }));

	// Currency options for select
	const currencyOptions = CURRENCY_CODES.filter((c) => c.value).map((c) => ({
		value: c.value,
		label: c.label,
		color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
	}));

	// Base drawer columns (using $derived for dynamic currency symbol)
	const baseDrawerColumns = $derived([
		{ key: 'name', label: 'Name', type: 'text' },
		{
			key: 'industry',
			label: 'Industry',
			type: 'select',
			icon: Briefcase,
			options: industryOptions,
			placeholder: 'Select industry'
		},
		{
			key: 'website',
			label: 'Website',
			type: 'text',
			icon: Globe,
			placeholder: 'https://example.com'
		},
		{ key: 'phone', label: 'Phone', type: 'text', icon: Phone, placeholder: '+1 (555) 000-0000' },
		{
			key: 'email',
			label: 'Email',
			type: 'email',
			icon: Mail,
			placeholder: 'contact@company.com'
		},
		{
			key: 'annualRevenue',
			label: 'Revenue',
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
			key: 'numberOfEmployees',
			label: 'Employees',
			type: 'number',
			icon: Users,
			placeholder: '0'
		},
		{
			key: 'addressLine',
			label: 'Address',
			type: 'text',
			icon: MapPin,
			placeholder: 'Street address'
		},
		{ key: 'city', label: 'City', type: 'text', placeholder: 'City' },
		{ key: 'state', label: 'State', type: 'text', placeholder: 'State/Province' },
		{ key: 'postcode', label: 'Postal Code', type: 'text', placeholder: 'Postal code' },
		{
			key: 'country',
			label: 'Country',
			type: 'select',
			options: countryOptions,
			placeholder: 'Select country'
		},
		{
			key: 'description',
			label: 'Notes',
			type: 'textarea',
			icon: FileText,
			placeholder: 'Add notes about this account...'
		}
	]);

	/** @type {ColumnDef[]} */
	const columns = [
		{
			key: 'name',
			label: 'Account',
			type: 'text',
			width: 'w-60',
			canHide: false,
			emptyText: 'Untitled'
		},
		{ key: 'industry', label: 'Industry', type: 'text', width: 'w-40', emptyText: '' },
		{
			key: 'annualRevenue',
			label: 'Revenue',
			type: 'number',
			width: 'w-32',
			format: (value, row) => formatCurrency(value, row?.currency || 'USD', true)
		},
		{
			key: 'numberOfEmployees',
			label: 'Employees',
			type: 'number',
			width: 'w-28',
			emptyText: ''
		},
		{ key: 'phone', label: 'Phone', type: 'text', width: 'w-36', emptyText: '' },
		{
			key: 'createdAt',
			label: 'Created',
			type: 'date',
			width: 'w-36',
			editable: false
		},
		// Hidden by default
		{ key: 'website', label: 'Website', type: 'text', width: 'w-44', canHide: true, emptyText: '' }
	];

	// Default visible columns (excludes website; status removed - using tabs instead)
	const DEFAULT_VISIBLE_COLUMNS = [
		'name',
		'industry',
		'annualRevenue',
		'numberOfEmployees',
		'phone',
		'createdAt'
	];

	// Column visibility state - use defaults (excludes website)
	let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);

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
		if (typeof window !== 'undefined') {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns));
		}
	});

	/**
	 * Toggle column visibility
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

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	// Computed values from data
	const accounts = $derived(data.accounts || []);
	const pagination = $derived(data.pagination || { page: 1, limit: 10, total: 0, totalPages: 0 });

	// M2M options from API
	const userOptions = $derived((data.users || []).map((u) => ({ value: u.id, label: u.email })));
	const contactOptions = $derived(
		(data.contacts || []).map((c) => ({ value: c.id, label: c.name }))
	);
	const tagOptions = $derived((data.tags || []).map((t) => ({ value: t.id, label: t.name })));

	// Drawer columns with dynamic M2M options
	const drawerColumns = $derived([
		...baseDrawerColumns,
		{
			key: 'assignedTo',
			label: 'Assigned To',
			type: 'multiselect',
			icon: UserPlus,
			options: userOptions,
			placeholder: 'Select users',
			emptyText: 'Not assigned'
		},
		{
			key: 'contacts',
			label: 'Contacts',
			type: 'multiselect',
			icon: Contact,
			options: contactOptions,
			placeholder: 'Link contacts',
			emptyText: 'No contacts'
		},
		{
			key: 'tags',
			label: 'Tags',
			type: 'multiselect',
			icon: Tag,
			options: tagOptions,
			placeholder: 'Add tags',
			emptyText: 'No tags'
		}
	]);

	// Drawer state - simplified for unified drawer
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {any} */
	let selectedAccount = $state(null);
	let drawerLoading = $state(false);
	let isSubmitting = $state(false);

	// Empty account template for create mode
	const emptyAccount = {
		name: '',
		industry: '',
		website: '',
		phone: '',
		email: '',
		description: '',
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		annualRevenue: '',
		currency: '',
		numberOfEmployees: '',
		assignedTo: [],
		contacts: [],
		tags: []
	};

	// Drawer form data - mutable copy of selectedAccount for editing
	let drawerFormData = $state({ ...emptyAccount });

	// Reset form data when account changes or drawer opens
	$effect(() => {
		if (drawerOpen) {
			if (drawerMode === 'create') {
				drawerFormData = { ...emptyAccount, currency: $orgSettings.default_currency || 'USD' };
			} else if (selectedAccount) {
				drawerFormData = {
					...selectedAccount,
					currency: selectedAccount.currency || $orgSettings.default_currency || 'USD'
				};
			}
		}
	});

	// Check if account is closed (inactive)
	const isClosed = $derived(selectedAccount?.isActive === false);

	// URL sync for drawer state
	$effect(() => {
		const viewId = $page.url.searchParams.get('view');
		const action = $page.url.searchParams.get('action');

		if (action === 'create') {
			selectedAccount = null;
			drawerMode = 'create';
			drawerOpen = true;
		} else if (viewId && accounts.length > 0) {
			const account = accounts.find((a) => a.id === viewId);
			if (account) {
				selectedAccount = account;
				drawerMode = 'view';
				drawerOpen = true;
			}
		}
	});

	/**
	 * Update URL with drawer state
	 * @param {string | null} viewId
	 * @param {string | null} action
	 * @returns {Promise<void>}
	 */
	async function updateUrl(viewId, action) {
		const url = new URL($page.url);
		if (viewId) {
			url.searchParams.set('view', viewId);
			url.searchParams.delete('action');
		} else if (action) {
			url.searchParams.set('action', action);
			url.searchParams.delete('view');
		} else {
			url.searchParams.delete('view');
			url.searchParams.delete('action');
		}
		await goto(url.toString(), { replaceState: true, keepFocus: true });
	}

	/**
	 * Open account detail drawer
	 * @param {any} account
	 */
	function openAccount(account) {
		selectedAccount = account;
		drawerMode = 'view';
		drawerOpen = true;
		updateUrl(account.id, null);
	}

	/**
	 * Open create drawer
	 */
	function openCreate() {
		selectedAccount = null;
		drawerMode = 'create';
		drawerOpen = true;
		updateUrl(null, 'create');
	}

	/**
	 * Close drawer
	 * @returns {Promise<void>}
	 */
	async function closeDrawer() {
		drawerOpen = false;
		await updateUrl(null, null);
	}

	/**
	 * Handle drawer open change
	 * @param {boolean} open
	 */
	function handleDrawerChange(open) {
		drawerOpen = open;
		if (!open) {
			updateUrl(null, null);
		}
	}

	// Get unique industries from accounts for filter options
	const industries = $derived.by(() => {
		const uniqueIndustries = [...new Set(accounts.map((a) => a.industry).filter(Boolean))];
		return uniqueIndustries.sort();
	});

	// Industry options for filter
	const industryFilterOptions = $derived([
		{ value: '', label: 'All Industries' },
		...industries.map((ind) => ({ value: ind, label: ind }))
	]);

	// URL-based filter state from server
	const filters = $derived(data.filters);

	// Count active filters
	const activeFiltersCount = $derived.by(() => {
		let count = 0;
		if (filters.search) count++;
		if (filters.industry) count++;
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
		// Clear existing filter params (preserve view/action)
		['search', 'industry', 'assigned_to', 'tags', 'created_at_gte', 'created_at_lte'].forEach(
			(key) => url.searchParams.delete(key)
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

	// Accounts are already filtered server-side, apply chip filter for active/closed
	let statusChipFilter = $state('ALL');

	// Filter panel expansion state
	let filtersExpanded = $state(false);

	const filteredAccounts = $derived.by(() => {
		if (statusChipFilter === 'active') {
			return accounts.filter((a) => a.isActive !== false);
		} else if (statusChipFilter === 'closed') {
			return accounts.filter((a) => a.isActive === false);
		}
		return accounts;
	});

	// Visible column count for the toggle button
	const visibleColumnCount = $derived(visibleColumns.length);
	const totalColumnCount = $derived(columns.length);

	// Status counts for filter chips
	const activeCount = $derived(accounts.filter((a) => a.isActive !== false).length);
	const closedCount = $derived(accounts.filter((a) => a.isActive === false).length);

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;
	/** @type {HTMLFormElement} */
	let deactivateForm;
	/** @type {HTMLFormElement} */
	let activateForm;

	// Form data state - aligned with API fields
	let formState = $state({
		accountId: '',
		name: '',
		email: '',
		phone: '',
		website: '',
		industry: '',
		description: '',
		address_line: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		annual_revenue: '',
		currency: '',
		number_of_employees: '',
		assigned_to: '[]',
		contacts: '[]',
		tags: '[]'
	});

	/**
	 * Get initials for avatar
	 * @param {any} account
	 */
	function getAccountInitials(account) {
		return getInitials(account.name, 1);
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
		if (drawerMode !== 'view' || !selectedAccount || isClosed) return;

		isSubmitting = true;
		formState.accountId = selectedAccount.id;
		formState.name = drawerFormData.name || '';
		formState.email = drawerFormData.email || '';
		formState.phone = drawerFormData.phone || '';
		formState.website = drawerFormData.website || '';
		formState.industry = drawerFormData.industry || '';
		formState.description = drawerFormData.description || '';
		formState.address_line = drawerFormData.addressLine || '';
		formState.city = drawerFormData.city || '';
		formState.state = drawerFormData.state || '';
		formState.postcode = drawerFormData.postcode || '';
		formState.country = drawerFormData.country || '';
		formState.annual_revenue = drawerFormData.annualRevenue?.toString() || '';
		formState.currency = drawerFormData.currency || '';
		formState.number_of_employees = drawerFormData.numberOfEmployees?.toString() || '';
		formState.assigned_to = JSON.stringify(drawerFormData.assignedTo || []);
		formState.contacts = JSON.stringify(drawerFormData.contacts || []);
		formState.tags = JSON.stringify(drawerFormData.tags || []);

		await tick();
		updateForm.requestSubmit();
	}

	/**
	 * Handle save for create mode
	 */
	async function handleDrawerSave() {
		if (drawerMode !== 'create') return;

		isSubmitting = true;
		formState.name = drawerFormData.name || '';
		formState.email = drawerFormData.email || '';
		formState.phone = drawerFormData.phone || '';
		formState.website = drawerFormData.website || '';
		formState.industry = drawerFormData.industry || '';
		formState.description = drawerFormData.description || '';
		formState.address_line = drawerFormData.addressLine || '';
		formState.city = drawerFormData.city || '';
		formState.state = drawerFormData.state || '';
		formState.postcode = drawerFormData.postcode || '';
		formState.country = drawerFormData.country || '';
		formState.annual_revenue = drawerFormData.annualRevenue?.toString() || '';
		formState.currency = drawerFormData.currency || '';
		formState.number_of_employees = drawerFormData.numberOfEmployees?.toString() || '';
		formState.assigned_to = JSON.stringify(drawerFormData.assignedTo || []);
		formState.contacts = JSON.stringify(drawerFormData.contacts || []);
		formState.tags = JSON.stringify(drawerFormData.tags || []);

		await tick();
		createForm.requestSubmit();
	}

	/**
	 * Handle account delete
	 */
	async function handleDelete() {
		if (!selectedAccount) return;
		if (!confirm(`Are you sure you want to delete "${selectedAccount.name}"?`)) return;

		formState.accountId = selectedAccount.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Handle account close (deactivate)
	 */
	async function handleClose() {
		if (!selectedAccount) return;

		formState.accountId = selectedAccount.id;
		await tick();
		deactivateForm.requestSubmit();
	}

	/**
	 * Handle account reopen (activate)
	 */
	async function handleReopen() {
		if (!selectedAccount) return;

		formState.accountId = selectedAccount.id;
		await tick();
		activateForm.requestSubmit();
	}

	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 * @param {boolean} shouldCloseDrawer
	 */
	function createEnhanceHandler(successMessage, shouldCloseDrawer = false) {
		return () => {
			return async ({ result }) => {
				isSubmitting = false;
				if (result.type === 'success') {
					toast.success(successMessage);
					if (shouldCloseDrawer) {
						await closeDrawer();
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
	 * Navigate to add contact
	 */
	function handleAddContact() {
		if (selectedAccount) {
			goto(`/contacts?action=create&accountId=${selectedAccount.id}`);
		}
	}

	/**
	 * Navigate to add opportunity
	 */
	function handleAddOpportunity() {
		if (selectedAccount) {
			goto(`/opportunities/new?accountId=${selectedAccount.id}`);
		}
	}
</script>

<svelte:head>
	<title>Accounts - BottleCRM</title>
</svelte:head>

<PageHeader title="Accounts" subtitle="{filteredAccounts.length} of {accounts.length} accounts">
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
						{accounts.length}
					</span>
				</button>
				<button
					type="button"
					onclick={() => (statusChipFilter = 'active')}
					class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
					'active'
						? 'bg-emerald-600 text-white dark:bg-emerald-500'
						: 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
				>
					Active
					<span
						class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'active'
							? 'bg-emerald-700 text-emerald-100 dark:bg-emerald-600'
							: 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
					>
						{activeCount}
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

			<!-- Column Visibility Dropdown -->
			<DropdownMenu.Root>
				<DropdownMenu.Trigger asChild>
					{#snippet child({ props })}
						<Button {...props} variant="outline" size="sm" class="gap-2">
							<Eye class="h-4 w-4" />
							Columns
							{#if visibleColumnCount < totalColumnCount}
								<span
									class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
								>
									{visibleColumnCount}/{totalColumnCount}
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
			<Button onclick={openCreate} disabled={false}>
				<Plus class="mr-2 h-4 w-4" />
				New Account
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
			placeholder="Search accounts..."
		/>
		<SelectFilter
			label="Industry"
			options={industryFilterOptions}
			value={filters.industry}
			onchange={(value) => updateFilters({ ...filters, industry: value })}
		/>
		<DateRangeFilter
			label="Created"
			startDate={filters.created_at_gte}
			endDate={filters.created_at_lte}
			onchange={(start, end) =>
				updateFilters({ ...filters, created_at_gte: start, created_at_lte: end })}
		/>
	</FilterBar>
	<!-- Accounts Table -->
	{#if filteredAccounts.length === 0}
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<Building2 class="text-muted-foreground/50 mb-4 h-12 w-12" />
			<h3 class="text-foreground text-lg font-medium">No accounts found</h3>
			<p class="text-muted-foreground mt-1 text-sm">
				Try adjusting your search criteria or create a new account.
			</p>
			<Button onclick={openCreate} class="mt-4" disabled={false}>
				<Plus class="mr-2 h-4 w-4" />
				Create New Account
			</Button>
		</div>
	{:else}
		<!-- Desktop Table using CrmTable -->
		<div class="hidden md:block">
			<CrmTable
				data={filteredAccounts}
				{columns}
				bind:visibleColumns
				onRowClick={(row) => openAccount(row)}
			>
				{#snippet emptyState()}
					<div class="flex flex-col items-center justify-center py-16 text-center">
						<Building2 class="text-muted-foreground/50 mb-4 h-12 w-12" />
						<h3 class="text-foreground text-lg font-medium">No accounts found</h3>
					</div>
				{/snippet}
			</CrmTable>
		</div>

		<!-- Mobile Card View -->
		<div class="divide-y md:hidden dark:divide-gray-800">
			{#each filteredAccounts as account (account.id)}
				<button
					type="button"
					class="flex w-full items-start gap-4 p-4 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-800 {!account.isActive
						? 'opacity-60'
						: ''}"
					onclick={() => openAccount(account)}
				>
					<div
						class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-sm font-medium text-white"
					>
						{getAccountInitials(account)}
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<p class="font-medium text-gray-900 dark:text-gray-100">{account.name}</p>
								<div class="mt-1 flex items-center gap-1.5">
									{#if account.isActive !== false}
										<span
											class="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400"
										>
											Active
										</span>
									{:else}
										<span
											class="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400"
										>
											Closed
										</span>
									{/if}
								</div>
							</div>
						</div>
						<div
							class="mt-2 flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-gray-400"
						>
							{#if account.industry}
								<span>{account.industry}</span>
							{/if}
							<div class="flex items-center gap-1">
								<Users class="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />
								<span>{account.contactCount || 0}</span>
							</div>
							<div class="flex items-center gap-1">
								<Target class="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />
								<span>{account.opportunityCount || 0}</span>
							</div>
							<div class="flex items-center gap-1">
								<Calendar class="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />
								<span>{formatRelativeDate(account.createdAt)}</span>
							</div>
						</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}

	<!-- Pagination -->
	<Pagination
		page={pagination.page}
		limit={pagination.limit}
		total={pagination.total}
		onPageChange={handlePageChange}
		onLimitChange={handleLimitChange}
	/>
</div>

<!-- Account Drawer -->
<CrmDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	data={drawerFormData}
	columns={drawerColumns}
	titleKey="name"
	titlePlaceholder="Account name"
	headerLabel="Account"
	mode={drawerMode}
	loading={drawerLoading || isSubmitting}
	onFieldChange={handleDrawerFieldChange}
	onDelete={handleDelete}
	onClose={closeDrawer}
>
	{#snippet activitySection()}
		<!-- Closed account warning -->
		{#if isClosed && drawerMode !== 'create'}
			<div
				class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/30"
			>
				<div class="flex gap-2">
					<AlertTriangle class="mt-0.5 h-4 w-4 shrink-0 text-red-500 dark:text-red-400" />
					<div>
						<p class="text-sm font-medium text-red-700 dark:text-red-400">This account is closed</p>
						<p class="mt-0.5 text-xs text-red-600 dark:text-red-500">
							Reopen the account to make changes
						</p>
					</div>
				</div>
			</div>
		{/if}

		<!-- Related entity stats (view mode only) -->
		{#if drawerMode !== 'create' && selectedAccount}
			<div class="mb-4">
				<p
					class="mb-2 text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
				>
					Related
				</p>
				<div class="grid grid-cols-3 gap-2">
					<div class="rounded-lg bg-gray-50 p-2 text-center dark:bg-gray-800">
						<div class="flex items-center justify-center gap-1 text-gray-400 dark:text-gray-500">
							<Users class="h-3.5 w-3.5" />
						</div>
						<p class="mt-0.5 text-lg font-semibold text-gray-900 dark:text-gray-100">
							{selectedAccount.contactCount || 0}
						</p>
						<p class="text-[10px] text-gray-500 dark:text-gray-400">Contacts</p>
					</div>
					<div class="rounded-lg bg-gray-50 p-2 text-center dark:bg-gray-800">
						<div class="flex items-center justify-center gap-1 text-gray-400 dark:text-gray-500">
							<Target class="h-3.5 w-3.5" />
						</div>
						<p class="mt-0.5 text-lg font-semibold text-gray-900 dark:text-gray-100">
							{selectedAccount.opportunityCount || 0}
						</p>
						<p class="text-[10px] text-gray-500 dark:text-gray-400">Opportunities</p>
					</div>
					<div class="rounded-lg bg-gray-50 p-2 text-center dark:bg-gray-800">
						<div class="flex items-center justify-center gap-1 text-gray-400 dark:text-gray-500">
							<AlertTriangle class="h-3.5 w-3.5" />
						</div>
						<p class="mt-0.5 text-lg font-semibold text-gray-900 dark:text-gray-100">
							{selectedAccount.caseCount || 0}
						</p>
						<p class="text-[10px] text-gray-500 dark:text-gray-400">Cases</p>
					</div>
				</div>
			</div>

			<!-- Quick actions (for active accounts only) -->
			{#if !isClosed}
				<div class="mb-4">
					<p
						class="mb-2 text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
					>
						Quick Actions
					</p>
					<div class="flex gap-2">
						<Button variant="outline" size="sm" onclick={handleAddContact} class="flex-1">
							<Users class="mr-1.5 h-3.5 w-3.5" />
							Add Contact
						</Button>
						<Button variant="outline" size="sm" onclick={handleAddOpportunity} class="flex-1">
							<Target class="mr-1.5 h-3.5 w-3.5" />
							Add Opportunity
						</Button>
					</div>
				</div>
			{/if}

			<!-- Metadata -->
			<div>
				<p
					class="mb-2 text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
				>
					Details
				</p>
				<div class="grid grid-cols-2 gap-3 text-sm">
					<div>
						<p class="text-xs text-gray-400 dark:text-gray-500">Owner</p>
						<p class="font-medium text-gray-900 dark:text-gray-100">
							{selectedAccount.owner?.name || 'Unassigned'}
						</p>
					</div>
					<div>
						<p class="text-xs text-gray-400 dark:text-gray-500">Created</p>
						<p class="font-medium text-gray-900 dark:text-gray-100">
							{formatRelativeDate(selectedAccount.createdAt)}
						</p>
					</div>
				</div>
			</div>
		{/if}
	{/snippet}

	{#snippet footerActions()}
		{#if drawerMode === 'create'}
			<Button variant="outline" onclick={closeDrawer} disabled={isSubmitting}>Cancel</Button>
			<Button onclick={handleDrawerSave} disabled={isSubmitting || !drawerFormData.name?.trim()}>
				{isSubmitting ? 'Creating...' : 'Create Account'}
			</Button>
		{:else if isClosed}
			<Button variant="outline" onclick={closeDrawer} disabled={isSubmitting}>Cancel</Button>
			<Button
				variant="outline"
				class="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300"
				onclick={handleReopen}
				disabled={isSubmitting}
			>
				<Unlock class="mr-1.5 h-4 w-4" />
				Reopen Account
			</Button>
		{:else}
			<Button variant="outline" onclick={closeDrawer} disabled={isSubmitting}>Cancel</Button>
			<Button
				variant="ghost"
				class="text-orange-600 hover:text-orange-700 dark:text-orange-400 dark:hover:text-orange-300"
				onclick={handleClose}
				disabled={isSubmitting}
			>
				<Lock class="mr-1.5 h-4 w-4" />
				Close Account
			</Button>
			<Button onclick={handleDrawerUpdate} disabled={isSubmitting || !drawerFormData.name?.trim()}>
				{isSubmitting ? 'Saving...' : 'Save'}
			</Button>
		{/if}
	{/snippet}
</CrmDrawer>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Account created successfully', true)}
	class="hidden"
>
	<input type="hidden" name="name" value={formState.name} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="website" value={formState.website} />
	<input type="hidden" name="industry" value={formState.industry} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="address_line" value={formState.address_line} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<input type="hidden" name="annual_revenue" value={formState.annual_revenue} />
	<input type="hidden" name="currency" value={formState.currency} />
	<input type="hidden" name="number_of_employees" value={formState.number_of_employees} />
	<input type="hidden" name="assigned_to" value={formState.assigned_to} />
	<input type="hidden" name="contacts" value={formState.contacts} />
	<input type="hidden" name="tags" value={formState.tags} />
</form>

<form
	method="POST"
	action="?/update"
	bind:this={updateForm}
	use:enhance={createEnhanceHandler('Account updated successfully', true)}
	class="hidden"
>
	<input type="hidden" name="accountId" value={formState.accountId} />
	<input type="hidden" name="name" value={formState.name} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="website" value={formState.website} />
	<input type="hidden" name="industry" value={formState.industry} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="address_line" value={formState.address_line} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<input type="hidden" name="annual_revenue" value={formState.annual_revenue} />
	<input type="hidden" name="currency" value={formState.currency} />
	<input type="hidden" name="number_of_employees" value={formState.number_of_employees} />
	<input type="hidden" name="assigned_to" value={formState.assigned_to} />
	<input type="hidden" name="contacts" value={formState.contacts} />
	<input type="hidden" name="tags" value={formState.tags} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Account deleted successfully', true)}
	class="hidden"
>
	<input type="hidden" name="accountId" value={formState.accountId} />
</form>

<form
	method="POST"
	action="?/deactivate"
	bind:this={deactivateForm}
	use:enhance={createEnhanceHandler('Account closed successfully', true)}
	class="hidden"
>
	<input type="hidden" name="accountId" value={formState.accountId} />
</form>

<form
	method="POST"
	action="?/activate"
	bind:this={activateForm}
	use:enhance={createEnhanceHandler('Account reopened successfully')}
	class="hidden"
>
	<input type="hidden" name="accountId" value={formState.accountId} />
</form>
