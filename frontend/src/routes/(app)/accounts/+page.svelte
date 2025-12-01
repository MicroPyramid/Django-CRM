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
		MapPin
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { AccountDrawer } from '$lib/components/accounts';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { formatRelativeDate, formatCurrency, getInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import { ColumnCustomizer } from '$lib/components/ui/column-customizer/index.js';

	// Column visibility configuration
	const STORAGE_KEY = 'accounts-column-config';

	/**
	 * @typedef {Object} ColumnConfig
	 * @property {string} key
	 * @property {string} label
	 * @property {boolean} visible
	 * @property {boolean} [canHide]
	 */

	/** @type {ColumnConfig[]} */
	const defaultColumns = [
		{ key: 'account', label: 'Account', visible: true, canHide: false },
		{ key: 'industry', label: 'Industry', visible: true, canHide: true },
		{ key: 'contact', label: 'Contact Info', visible: true, canHide: true },
		{ key: 'revenue', label: 'Revenue', visible: true, canHide: true },
		{ key: 'relations', label: 'Relations', visible: true, canHide: true },
		{ key: 'created', label: 'Created', visible: true, canHide: true }
	];

	/**
	 * Load column config from localStorage
	 * @returns {typeof defaultColumns}
	 */
	function loadColumnConfig() {
		if (typeof window === 'undefined') return defaultColumns;
		try {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				return defaultColumns.map((def) => {
					const savedCol = parsed.find((/** @type {ColumnConfig} */ p) => p.key === def.key);
					return savedCol ? { ...def, visible: savedCol.visible } : def;
				});
			}
		} catch (e) {
			console.error('Failed to load column config:', e);
		}
		return defaultColumns;
	}

	let columnConfig = $state(defaultColumns);

	onMount(() => {
		columnConfig = loadColumnConfig();
	});

	// Save to localStorage when column config changes
	$effect(() => {
		if (typeof window !== 'undefined' && columnConfig !== defaultColumns) {
			localStorage.setItem(STORAGE_KEY, JSON.stringify(columnConfig));
		}
	});

	/**
	 * Check if a column is visible
	 * @param {string} key
	 */
	function isColumnVisible(key) {
		return columnConfig.find((c) => c.key === key)?.visible ?? true;
	}

	/**
	 * Handle column config change
	 * @param {ColumnConfig[]} newConfig
	 */
	function handleColumnChange(newConfig) {
		columnConfig = newConfig;
	}

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

	// Filtered and sorted accounts
	const filteredAccounts = $derived(list.filterAndSort(accounts));
	const activeFiltersCount = $derived(list.getActiveFilterCount());

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

<PageHeader title="Accounts" subtitle="{filteredAccounts.length} of {accounts.length} accounts">
	{#snippet actions()}
		<ColumnCustomizer columns={columnConfig} onchange={handleColumnChange} />
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
				<!-- Desktop Table -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row class="border-b border-border/40 hover:bg-transparent">
								{#if isColumnVisible('account')}
									<Table.Head class="w-[250px] py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Account</Table.Head>
								{/if}
								{#if isColumnVisible('industry')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Industry</Table.Head>
								{/if}
								{#if isColumnVisible('contact')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Contact Info</Table.Head>
								{/if}
								{#if isColumnVisible('revenue')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Revenue</Table.Head>
								{/if}
								{#if isColumnVisible('relations')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Relations</Table.Head>
								{/if}
								{#if isColumnVisible('created')}
									<Table.Head
										class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70 hover:bg-muted/30 cursor-pointer rounded transition-colors"
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
									</Table.Head>
								{/if}
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each filteredAccounts as account (account.id)}
								<Table.Row
									class="group relative h-[52px] border-b border-border/30 hover:bg-muted/20 cursor-pointer transition-all duration-150 ease-out {!account.isActive ? 'opacity-60' : ''}"
									onclick={() => openAccount(account)}
								>
									{#if isColumnVisible('account')}
										<Table.Cell class="py-2 px-4">
											<div class="flex items-center gap-3">
												<div
													class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-sm font-medium text-white"
												>
													{getAccountInitials(account)}
												</div>
												<div class="min-w-0">
													<p class="text-foreground truncate font-medium">{account.name}</p>
													<div class="mt-0.5 flex items-center gap-1.5">
														{#if account.isActive !== false}
															<Badge
																variant="default"
																class="bg-green-500/10 px-1.5 py-0 text-xs text-green-600 hover:bg-green-500/20"
															>
																Active
															</Badge>
														{:else}
															<Badge variant="secondary" class="px-1.5 py-0 text-xs">Closed</Badge>
														{/if}
													</div>
												</div>
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('industry')}
										<Table.Cell class="py-2 px-4">
											<span class="text-foreground text-sm">{account.industry || '-'}</span>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('contact')}
										<Table.Cell class="py-2 px-4">
											<div class="space-y-1">
												{#if account.website}
													<div class="flex items-center gap-1.5 text-sm">
														<Globe class="text-muted-foreground h-3.5 w-3.5" />
														<span class="max-w-[140px] truncate">
															{account.website.replace(/^https?:\/\//, '')}
														</span>
													</div>
												{/if}
												{#if account.phone}
													<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
														<Phone class="h-3.5 w-3.5" />
														<span>{account.phone}</span>
													</div>
												{/if}
												{#if account.city || account.state}
													<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
														<MapPin class="h-3.5 w-3.5" />
														<span class="truncate">
															{[account.city, account.state].filter(Boolean).join(', ')}
														</span>
													</div>
												{/if}
												{#if !account.website && !account.phone && !account.city}
													<span class="text-muted-foreground">-</span>
												{/if}
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('revenue')}
										<Table.Cell class="py-2 px-4">
											<span class="text-foreground text-sm font-medium">
												{formatCurrency(account.annualRevenue, 'USD', true)}
											</span>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('relations')}
										<Table.Cell class="py-2 px-4">
											<div class="flex items-center gap-3">
												<div class="flex items-center gap-1">
													<Users class="text-muted-foreground h-4 w-4" />
													<span class="text-sm font-medium">{account.contactCount || 0}</span>
												</div>
												<div class="flex items-center gap-1">
													<Target class="text-muted-foreground h-4 w-4" />
													<span class="text-sm font-medium">{account.opportunityCount || 0}</span>
												</div>
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('created')}
										<Table.Cell class="py-2 px-4">
											<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
												<Calendar class="h-3.5 w-3.5" />
												<span>{formatRelativeDate(account.createdAt)}</span>
											</div>
										</Table.Cell>
									{/if}
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Mobile Card View -->
				<div class="divide-y md:hidden">
					{#each filteredAccounts as account (account.id)}
						<button
							type="button"
							class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left {!account.isActive
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
										<p class="text-foreground font-medium">{account.name}</p>
										<div class="mt-0.5 flex items-center gap-1.5">
											{#if account.isActive !== false}
												<Badge
													variant="default"
													class="bg-green-500/10 px-1.5 py-0 text-xs text-green-600"
												>
													Active
												</Badge>
											{:else}
												<Badge variant="secondary" class="px-1.5 py-0 text-xs">Closed</Badge>
											{/if}
										</div>
									</div>
								</div>
								<div class="text-muted-foreground mt-2 flex flex-wrap items-center gap-3 text-sm">
									{#if account.industry}
										<span>{account.industry}</span>
									{/if}
									<div class="flex items-center gap-1">
										<Users class="h-3.5 w-3.5" />
										<span>{account.contactCount || 0}</span>
									</div>
									<div class="flex items-center gap-1">
										<Target class="h-3.5 w-3.5" />
										<span>{account.opportunityCount || 0}</span>
									</div>
									<div class="flex items-center gap-1">
										<Calendar class="h-3.5 w-3.5" />
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
