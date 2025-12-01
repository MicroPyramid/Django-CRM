<script>
	import { enhance } from '$app/forms';
	import { invalidateAll, goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronDown,
		ChevronUp,
		Phone,
		Globe,
		Building2,
		Users,
		Target,
		Calendar,
		DollarSign,
		MapPin,
		GripVertical,
		Expand,
		Eye
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { AccountDrawer } from '$lib/components/accounts';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { formatRelativeDate, formatCurrency, getInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import { reorderItems } from '$lib/utils/drag-drop.js';

	// Column visibility configuration
	const STORAGE_KEY = 'accounts-column-config';

	// Column definitions
	const columns = [
		{ key: 'account', label: 'Account', type: 'text', width: 'w-60', canHide: false },
		{ key: 'industry', label: 'Industry', type: 'text', width: 'w-40', canHide: true },
		{ key: 'contact', label: 'Contact Info', type: 'custom', width: 'w-48', canHide: true },
		{ key: 'revenue', label: 'Revenue', type: 'number', width: 'w-32', canHide: true },
		{ key: 'relations', label: 'Relations', type: 'custom', width: 'w-28', canHide: true },
		{ key: 'created', label: 'Created', type: 'date', width: 'w-36', canHide: true }
	];

	// Column visibility state - simple array of visible keys
	let visibleColumns = $state(columns.map((c) => c.key));

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
	 * Check if a column is visible
	 * @param {string} key
	 */
	function isColumnVisible(key) {
		return visibleColumns.includes(key);
	}

	/**
	 * Toggle column visibility
	 * @param {string} key
	 */
	function toggleColumn(key) {
		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	// Drag-and-drop state
	/** @type {string | null} */
	let draggedRowId = $state(null);
	/** @type {string | null} */
	let dragOverRowId = $state(null);
	/** @type {'before' | 'after' | null} */
	let dropPosition = $state(null);

	// Inline editing state
	/** @type {{ rowId: string, columnKey: string } | null} */
	let editingCell = $state(null);
	let editValue = $state('');

	// Local accounts state for drag-drop reordering
	let localAccounts = $state(/** @type {any[]} */ ([]));

	// Sync local accounts with data
	$effect(() => {
		if (data.accounts) {
			localAccounts = [...data.accounts];
		}
	});

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	// Computed values from data
	const accounts = $derived(data.accounts || []);
	const pagination = $derived(data.pagination || { page: 1, limit: 10, total: 0, totalPages: 0 });

	// Drawer state - simplified for unified drawer
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {any} */
	let selectedAccount = $state(null);
	let drawerLoading = $state(false);

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
	 */
	function updateUrl(viewId, action) {
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
		goto(url.toString(), { replaceState: true, keepFocus: true });
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
	 */
	function closeDrawer() {
		drawerOpen = false;
		updateUrl(null, null);
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

	// Get unique industries from accounts for filter
	const industries = $derived.by(() => {
		const uniqueIndustries = [...new Set(accounts.map((a) => a.industry).filter(Boolean))];
		return uniqueIndustries.sort();
	});

	// Filter/search/sort state
	const list = useListFilters({
		searchFields: ['name', 'industry', 'website', 'phone'],
		filters: [
			{
				key: 'statusFilter',
				defaultValue: 'ALL',
				match: (item, value) =>
					value === 'ALL' ||
					(value === 'active' && item.isActive !== false) ||
					(value === 'closed' && item.isActive === false)
			},
			{
				key: 'industryFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.industry === value
			}
		],
		defaultSortColumn: 'createdAt',
		defaultSortDirection: 'desc'
	});

	// Filtered and sorted accounts - use localAccounts for drag-drop support
	const filteredAccounts = $derived(list.filterAndSort(localAccounts));
	const activeFiltersCount = $derived(list.getActiveFilterCount());

	// Visible column count for the toggle button
	const visibleColumnCount = $derived(visibleColumns.length);
	const totalColumnCount = $derived(columns.length);

	// Stats
	const stats = $derived.by(() => ({
		total: accounts.length,
		active: accounts.filter((a) => a.isActive !== false).length,
		totalContacts: accounts.reduce((sum, a) => sum + (a.contactCount || 0), 0),
		totalOpportunities: accounts.reduce((sum, a) => sum + (a.opportunityCount || 0), 0)
	}));

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
		number_of_employees: ''
	});

	/**
	 * Get initials for avatar
	 * @param {any} account
	 */
	function getAccountInitials(account) {
		return getInitials(account.name, 1);
	}

	// ===== Drag-and-drop handlers =====
	/**
	 * Handle drag start
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleDragStart(e, rowId) {
		draggedRowId = rowId;
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
			e.dataTransfer.setData('text/plain', rowId);
		}
	}

	/**
	 * Handle drag over row
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleRowDragOver(e, rowId) {
		e.preventDefault();
		if (draggedRowId === rowId) return;

		dragOverRowId = rowId;

		const rect = /** @type {HTMLElement} */ (e.currentTarget).getBoundingClientRect();
		const midpoint = rect.top + rect.height / 2;
		dropPosition = e.clientY < midpoint ? 'before' : 'after';
	}

	function handleRowDragLeave() {
		dragOverRowId = null;
		dropPosition = null;
	}

	/**
	 * Handle row drop
	 * @param {DragEvent} e
	 * @param {string} targetRowId
	 */
	function handleRowDrop(e, targetRowId) {
		e.preventDefault();
		if (!draggedRowId || draggedRowId === targetRowId || !dropPosition) {
			resetDragState();
			return;
		}

		localAccounts = reorderItems(
			localAccounts,
			draggedRowId,
			targetRowId,
			dropPosition,
			(/** @type {any} */ item) => item.id
		);

		resetDragState();
	}

	function handleDragEnd() {
		resetDragState();
	}

	function resetDragState() {
		draggedRowId = null;
		dragOverRowId = null;
		dropPosition = null;
	}

	// ===== Inline editing handlers =====
	/**
	 * Start editing a cell
	 * @param {string} rowId
	 * @param {string} columnKey
	 */
	async function startEditing(rowId, columnKey) {
		const account = localAccounts.find((a) => a.id === rowId);
		if (!account) return;

		// Map column key to account field
		let value = '';
		if (columnKey === 'name') value = account.name || '';
		else if (columnKey === 'industry') value = account.industry || '';

		editingCell = { rowId, columnKey };
		editValue = value;
		await tick();

		const input = document.querySelector(`[data-edit-input="${rowId}-${columnKey}"]`);
		if (input) {
			// @ts-ignore
			input.focus();
			// @ts-ignore
			if (input.select) input.select();
		}
	}

	/**
	 * Commit the current edit
	 * @param {boolean} save
	 */
	async function stopEditing(save = true) {
		if (!editingCell) return;

		if (save) {
			const { rowId, columnKey } = editingCell;
			const account = localAccounts.find((a) => a.id === rowId);
			if (account) {
				// Update local state
				let fieldName = columnKey;
				if (columnKey === 'name') fieldName = 'name';
				else if (columnKey === 'industry') fieldName = 'industry';

				// Update locally and trigger server update
				const updatedAccount = { ...account, [fieldName]: editValue };
				localAccounts = localAccounts.map((a) => (a.id === rowId ? updatedAccount : a));

				// Submit update to server
				formState.accountId = rowId;
				formState.name = updatedAccount.name || '';
				formState.email = updatedAccount.email || '';
				formState.phone = updatedAccount.phone || '';
				formState.website = updatedAccount.website || '';
				formState.industry = updatedAccount.industry || '';
				formState.description = updatedAccount.description || '';
				formState.address_line = updatedAccount.addressLine || '';
				formState.city = updatedAccount.city || '';
				formState.state = updatedAccount.state || '';
				formState.postcode = updatedAccount.postcode || '';
				formState.country = updatedAccount.country || '';
				formState.annual_revenue = updatedAccount.annualRevenue?.toString() || '';
				formState.number_of_employees = updatedAccount.numberOfEmployees?.toString() || '';

				await tick();
				updateForm.requestSubmit();
			}
		}

		editingCell = null;
		editValue = '';
	}

	/**
	 * Handle keyboard events during editing
	 * @param {KeyboardEvent} e
	 */
	function handleEditKeydown(e) {
		if (e.key === 'Enter') {
			e.preventDefault();
			stopEditing(true);
		} else if (e.key === 'Escape') {
			e.preventDefault();
			stopEditing(false);
		}
	}

	/**
	 * Handle form submit from drawer
	 * @param {any} formData
	 */
	async function handleFormSubmit(formData) {
		// Populate form state with all API fields
		formState.name = formData.name || '';
		formState.email = formData.email || '';
		formState.phone = formData.phone || '';
		formState.website = formData.website || '';
		formState.industry = formData.industry || '';
		formState.description = formData.description || '';
		formState.address_line = formData.address_line || '';
		formState.city = formData.city || '';
		formState.state = formData.state || '';
		formState.postcode = formData.postcode || '';
		formState.country = formData.country || '';
		formState.annual_revenue = formData.annual_revenue || '';
		formState.number_of_employees = formData.number_of_employees || '';

		await tick();

		if (drawerMode === 'view' && selectedAccount) {
			formState.accountId = selectedAccount.id;
			await tick();
			updateForm.requestSubmit();
		} else {
			createForm.requestSubmit();
		}
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
				if (result.type === 'success') {
					toast.success(successMessage);
					if (shouldCloseDrawer) {
						closeDrawer();
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

<PageHeader title="Accounts" subtitle="{filteredAccounts.length} of {localAccounts.length} accounts">
	{#snippet actions()}
		<!-- Column Visibility Dropdown -->
		<DropdownMenu.Root>
			<DropdownMenu.Trigger asChild>
				{#snippet child({ props })}
					<Button {...props} variant="outline" size="sm" class="gap-2">
						<Eye class="h-4 w-4" />
						Columns
						{#if visibleColumnCount < totalColumnCount}
							<span class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700">
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
					{#if column.canHide}
						<DropdownMenu.CheckboxItem
							class=""
							checked={isColumnVisible(column.key)}
							onCheckedChange={() => toggleColumn(column.key)}
						>
							{column.label}
						</DropdownMenu.CheckboxItem>
					{/if}
				{/each}
			</DropdownMenu.Content>
		</DropdownMenu.Root>
		<FilterPopover activeCount={activeFiltersCount} onClear={list.clearFilters}>
			{#snippet children()}
				<div class="space-y-3">
					<div>
						<label for="status-filter" class="mb-1.5 block text-sm font-medium">Status</label>
						<select
							id="status-filter"
							bind:value={list.filters.statusFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							<option value="ALL">All Status</option>
							<option value="active">Active</option>
							<option value="closed">Closed</option>
						</select>
					</div>
					<div>
						<label for="industry-filter" class="mb-1.5 block text-sm font-medium">Industry</label>
						<select
							id="industry-filter"
							bind:value={list.filters.industryFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							<option value="ALL">All Industries</option>
							{#each industries as industry}
								<option value={industry}>{industry}</option>
							{/each}
						</select>
					</div>
				</div>
			{/snippet}
		</FilterPopover>
		<Button onclick={openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Account
		</Button>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Stats Cards -->
	<div class="grid grid-cols-2 gap-4 md:grid-cols-4">
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30"
					>
						<Building2 class="h-5 w-5 text-blue-600 dark:text-blue-400" />
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Total Accounts</p>
						<p class="text-2xl font-bold">{stats.total}</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
					>
						<Target class="h-5 w-5 text-green-600 dark:text-green-400" />
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Active</p>
						<p class="text-2xl font-bold">{stats.active}</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/30"
					>
						<Users class="h-5 w-5 text-orange-600 dark:text-orange-400" />
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Contacts</p>
						<p class="text-2xl font-bold">{stats.totalContacts}</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
		<Card.Root>
			<Card.Content class="p-4">
				<div class="flex items-center gap-3">
					<div
						class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30"
					>
						<DollarSign class="h-5 w-5 text-purple-600 dark:text-purple-400" />
					</div>
					<div>
						<p class="text-muted-foreground text-sm">Opportunities</p>
						<p class="text-2xl font-bold">{stats.totalOpportunities}</p>
					</div>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Accounts Table -->
	<Card.Root class="border-0 shadow-sm">
		<Card.Content class="p-0">
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
				<!-- Desktop Table (Notion-style) -->
				<div class="hidden md:block overflow-x-auto">
					<table class="w-full border-collapse">
						<!-- Header -->
						<thead>
							<tr class="border-b border-gray-100/60">
								<!-- Drag handle column -->
								<th class="w-8 px-1"></th>
								<!-- Expand button column -->
								<th class="w-8 px-1"></th>
								{#if isColumnVisible('account')}
									<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 w-60">Account</th>
								{/if}
								{#if isColumnVisible('industry')}
									<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 w-40">Industry</th>
								{/if}
								{#if isColumnVisible('contact')}
									<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 w-48">Contact Info</th>
								{/if}
								{#if isColumnVisible('revenue')}
									<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 w-32">Revenue</th>
								{/if}
								{#if isColumnVisible('relations')}
									<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 w-28">Relations</th>
								{/if}
								{#if isColumnVisible('created')}
									<th
										class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 w-36 cursor-pointer hover:bg-gray-50 rounded transition-colors"
										onclick={() => list.toggleSort('createdAt')}
									>
										<div class="flex items-center gap-1">
											Created
											{#if list.sortColumn === 'createdAt'}
												{#if list.sortDirection === 'asc'}
													<ChevronUp class="h-3.5 w-3.5" />
												{:else}
													<ChevronDown class="h-3.5 w-3.5" />
												{/if}
											{/if}
										</div>
									</th>
								{/if}
							</tr>
						</thead>

						<!-- Body -->
						<tbody>
							{#each filteredAccounts as account (account.id)}
								<!-- Drop indicator line (before row) -->
								{#if dragOverRowId === account.id && dropPosition === 'before'}
									<tr class="h-0">
										<td colspan={visibleColumnCount + 2} class="p-0">
											<div class="h-0.5 bg-blue-400 rounded-full mx-4"></div>
										</td>
									</tr>
								{/if}

								<tr
									class="group hover:bg-gray-50/30 transition-all duration-100 ease-out {draggedRowId === account.id ? 'opacity-40 bg-gray-100' : ''} {!account.isActive ? 'opacity-60' : ''}"
									ondragover={(e) => handleRowDragOver(e, account.id)}
									ondragleave={handleRowDragLeave}
									ondrop={(e) => handleRowDrop(e, account.id)}
								>
									<!-- Drag Handle -->
									<td class="w-8 px-1 py-3">
										<div
											draggable="true"
											ondragstart={(e) => handleDragStart(e, account.id)}
											ondragend={handleDragEnd}
											class="flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-40 hover:!opacity-70 hover:bg-gray-200 transition-all cursor-grab active:cursor-grabbing"
											role="button"
											tabindex="0"
											aria-label="Drag to reorder"
										>
											<GripVertical class="h-4 w-4 text-gray-400" />
										</div>
									</td>

									<!-- Expand button -->
									<td class="w-8 px-1 py-3">
										<button
											type="button"
											onclick={() => openAccount(account)}
											class="flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 transition-all duration-75"
										>
											<Expand class="h-3.5 w-3.5 text-gray-500" />
										</button>
									</td>

									{#if isColumnVisible('account')}
										<td class="px-4 py-3 w-60">
											<div class="flex items-center gap-3">
												<div
													class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-sm font-medium text-white"
												>
													{getAccountInitials(account)}
												</div>
												<div class="min-w-0 flex-1">
													<!-- Editable name -->
													{#if editingCell?.rowId === account.id && editingCell?.columnKey === 'name'}
														<input
															type="text"
															bind:value={editValue}
															onkeydown={handleEditKeydown}
															onblur={() => stopEditing(true)}
															data-edit-input="{account.id}-name"
															class="w-full px-2 py-1.5 text-sm bg-white rounded outline-none ring-1 ring-gray-200 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
														/>
													{:else}
														<button
															type="button"
															onclick={(e) => { e.stopPropagation(); startEditing(account.id, 'name'); }}
															class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 hover:bg-gray-100/50 cursor-text transition-colors duration-75"
														>
															{account.name || 'Untitled'}
														</button>
													{/if}
													<div class="mt-1 flex items-center gap-1.5">
														{#if account.isActive !== false}
															<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
																Active
															</span>
														{:else}
															<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
																Closed
															</span>
														{/if}
													</div>
												</div>
											</div>
										</td>
									{/if}
									{#if isColumnVisible('industry')}
										<td class="px-4 py-3 w-40">
											<!-- Editable industry -->
											{#if editingCell?.rowId === account.id && editingCell?.columnKey === 'industry'}
												<input
													type="text"
													bind:value={editValue}
													onkeydown={handleEditKeydown}
													onblur={() => stopEditing(true)}
													data-edit-input="{account.id}-industry"
													class="w-full px-2 py-1.5 text-sm bg-white rounded outline-none ring-1 ring-gray-200 focus:ring-blue-300 shadow-sm transition-shadow duration-100"
												/>
											{:else}
												<button
													type="button"
													onclick={(e) => { e.stopPropagation(); startEditing(account.id, 'industry'); }}
													class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 hover:bg-gray-100/50 cursor-text transition-colors duration-75"
												>
													{#if account.industry}
														{account.industry}
													{:else}
														<span class="text-gray-400">Empty</span>
													{/if}
												</button>
											{/if}
										</td>
									{/if}
									{#if isColumnVisible('contact')}
										<td class="px-4 py-3 w-48">
											<div class="space-y-1">
												{#if account.website}
													<div class="flex items-center gap-1.5 text-sm text-gray-700">
														<Globe class="h-3.5 w-3.5 text-gray-400" />
														<span class="max-w-[140px] truncate">
															{account.website.replace(/^https?:\/\//, '')}
														</span>
													</div>
												{/if}
												{#if account.phone}
													<div class="flex items-center gap-1.5 text-sm text-gray-500">
														<Phone class="h-3.5 w-3.5 text-gray-400" />
														<span>{account.phone}</span>
													</div>
												{/if}
												{#if account.city || account.state}
													<div class="flex items-center gap-1.5 text-sm text-gray-500">
														<MapPin class="h-3.5 w-3.5 text-gray-400" />
														<span class="truncate">
															{[account.city, account.state].filter(Boolean).join(', ')}
														</span>
													</div>
												{/if}
												{#if !account.website && !account.phone && !account.city}
													<span class="text-gray-400 text-sm">-</span>
												{/if}
											</div>
										</td>
									{/if}
									{#if isColumnVisible('revenue')}
										<td class="px-4 py-3 w-32">
											<span class="text-sm font-medium text-gray-900">
												{formatCurrency(account.annualRevenue, 'USD', true)}
											</span>
										</td>
									{/if}
									{#if isColumnVisible('relations')}
										<td class="px-4 py-3 w-28">
											<div class="flex items-center gap-3">
												<div class="flex items-center gap-1">
													<Users class="h-4 w-4 text-gray-400" />
													<span class="text-sm font-medium text-gray-700">{account.contactCount || 0}</span>
												</div>
												<div class="flex items-center gap-1">
													<Target class="h-4 w-4 text-gray-400" />
													<span class="text-sm font-medium text-gray-700">{account.opportunityCount || 0}</span>
												</div>
											</div>
										</td>
									{/if}
									{#if isColumnVisible('created')}
										<td class="px-4 py-3 w-36">
											<div class="flex items-center gap-1.5 text-sm text-gray-500">
												<Calendar class="h-3.5 w-3.5 text-gray-400" />
												<span>{formatRelativeDate(account.createdAt)}</span>
											</div>
										</td>
									{/if}
								</tr>

								<!-- Drop indicator line (after row) -->
								{#if dragOverRowId === account.id && dropPosition === 'after'}
									<tr class="h-0">
										<td colspan={visibleColumnCount + 2} class="p-0">
											<div class="h-0.5 bg-blue-400 rounded-full mx-4"></div>
										</td>
									</tr>
								{/if}
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Mobile Card View -->
				<div class="divide-y md:hidden">
					{#each filteredAccounts as account (account.id)}
						<button
							type="button"
							class="hover:bg-gray-50 flex w-full items-start gap-4 p-4 text-left transition-colors {!account.isActive
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
										<p class="font-medium text-gray-900">{account.name}</p>
										<div class="mt-1 flex items-center gap-1.5">
											{#if account.isActive !== false}
												<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
													Active
												</span>
											{:else}
												<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
													Closed
												</span>
											{/if}
										</div>
									</div>
								</div>
								<div class="mt-2 flex flex-wrap items-center gap-3 text-sm text-gray-500">
									{#if account.industry}
										<span>{account.industry}</span>
									{/if}
									<div class="flex items-center gap-1">
										<Users class="h-3.5 w-3.5 text-gray-400" />
										<span>{account.contactCount || 0}</span>
									</div>
									<div class="flex items-center gap-1">
										<Target class="h-3.5 w-3.5 text-gray-400" />
										<span>{account.opportunityCount || 0}</span>
									</div>
									<div class="flex items-center gap-1">
										<Calendar class="h-3.5 w-3.5 text-gray-400" />
										<span>{formatRelativeDate(account.createdAt)}</span>
									</div>
								</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Pagination -->
	{#if pagination.totalPages > 1}
		<div class="flex items-center justify-between">
			<p class="text-muted-foreground text-sm">
				Showing {filteredAccounts.length} of {pagination.total} accounts
			</p>
			<div class="flex items-center gap-2">
				<Button variant="outline" size="sm" disabled={pagination.page === 1}>Previous</Button>
				<span class="text-sm">
					Page {pagination.page} of {pagination.totalPages}
				</span>
				<Button variant="outline" size="sm" disabled={pagination.page === pagination.totalPages}>
					Next
				</Button>
			</div>
		</div>
	{/if}
</div>

<!-- Account Drawer (unified) -->
<AccountDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	account={selectedAccount}
	mode={drawerMode}
	loading={drawerLoading}
	onSave={handleFormSubmit}
	onDelete={handleDelete}
	onClose={handleClose}
	onReopen={handleReopen}
	onAddContact={handleAddContact}
	onAddOpportunity={handleAddOpportunity}
	onCancel={closeDrawer}
/>

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
	<input type="hidden" name="number_of_employees" value={formState.number_of_employees} />
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
	<input type="hidden" name="number_of_employees" value={formState.number_of_employees} />
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
