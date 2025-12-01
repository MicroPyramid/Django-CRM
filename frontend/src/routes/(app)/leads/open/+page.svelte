<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronDown,
		ChevronUp,
		Phone,
		Mail,
		Building2,
		User,
		Calendar,
		GripVertical
	} from '@lucide/svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { LeadDrawer, RowActions } from '$lib/components/leads';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { InlineEditableCell } from '$lib/components/ui/inline-editable-cell/index.js';
	import { ColumnCustomizer } from '$lib/components/ui/column-customizer/index.js';
	import { cn } from '$lib/utils.js';
	import { formatRelativeDate, getNameInitials } from '$lib/utils/formatting.js';
	import { getLeadStatusClass, getRatingConfig } from '$lib/utils/ui-helpers.js';
	import {
		LEAD_STATUSES as statuses,
		LEAD_SOURCES as sources,
		LEAD_RATINGS as ratings
	} from '$lib/constants/filters.js';
	import { useListFilters } from '$lib/hooks';

	// Column visibility configuration
	const STORAGE_KEY = 'leads-column-config';

	/**
	 * @typedef {Object} ColumnConfig
	 * @property {string} key
	 * @property {string} label
	 * @property {boolean} visible
	 * @property {boolean} [canHide]
	 */

	/** @type {ColumnConfig[]} */
	const defaultColumns = [
		{ key: 'lead', label: 'Lead', visible: true, canHide: false },
		{ key: 'company', label: 'Company', visible: true, canHide: true },
		{ key: 'email', label: 'Email', visible: true, canHide: true },
		{ key: 'phone', label: 'Phone', visible: false, canHide: true },
		{ key: 'rating', label: 'Rating', visible: true, canHide: true },
		{ key: 'status', label: 'Status', visible: true, canHide: true },
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
				// Merge with defaults to handle new columns
				return defaultColumns.map((def) => {
					const saved = parsed.find((p) => p.key === def.key);
					return saved ? { ...def, visible: saved.visible } : def;
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

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	const leads = $derived(data.leads || []);

	// Drawer state (simplified - single drawer, matching contacts page pattern)
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {any} */
	let selectedLead = $state(null);
	let drawerLoading = $state(false);

	// URL sync
	$effect(() => {
		const viewId = $page.url.searchParams.get('view');
		const action = $page.url.searchParams.get('action');

		if (action === 'create') {
			selectedLead = null;
			drawerMode = 'create';
			drawerOpen = true;
		} else if (viewId && leads.length > 0) {
			const lead = leads.find((l) => l.id === viewId);
			if (lead) {
				selectedLead = lead;
				drawerMode = 'view';
				drawerOpen = true;
			}
		}
	});

	/**
	 * Update URL
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
		goto(url.toString(), { replaceState: true, noScroll: true });
	}

	/**
	 * Open drawer for viewing/editing a lead
	 * @param {any} lead
	 */
	function openLead(lead) {
		selectedLead = lead;
		drawerMode = 'view';
		drawerOpen = true;
		updateUrl(lead.id, null);
	}

	/**
	 * Open drawer for creating a new lead
	 */
	function openCreate() {
		selectedLead = null;
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
		if (!open) updateUrl(null, null);
	}

	// Filter/search/sort state
	const list = useListFilters({
		searchFields: ['firstName', 'lastName', 'company', 'email'],
		filters: [
			{
				key: 'statusFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.status === value
			},
			{
				key: 'sourceFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.leadSource === value
			},
			{
				key: 'ratingFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.rating === value
			}
		],
		defaultSortColumn: 'createdAt',
		defaultSortDirection: 'desc'
	});

	// Filtered and sorted leads
	const filteredLeads = $derived(list.filterAndSort(leads));
	const activeFiltersCount = $derived(list.getActiveFilterCount());

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;
	/** @type {HTMLFormElement} */
	let convertForm;
	/** @type {HTMLFormElement} */
	let duplicateForm;

	// Cell navigation for inline editing
	const editableColumns = ['company', 'email', 'phone', 'rating', 'status'];

	/** @type {Record<string, any>} */
	let cellRefs = {};

	/**
	 * Register a cell reference for navigation
	 * @param {string} rowId
	 * @param {string} column
	 * @param {any} ref
	 */
	function registerCell(rowId, column, ref) {
		cellRefs[`${rowId}-${column}`] = ref;
	}

	/**
	 * Focus a specific cell
	 * @param {string} rowId
	 * @param {string} column
	 */
	function focusCell(rowId, column) {
		const ref = cellRefs[`${rowId}-${column}`];
		ref?.startEditing();
	}

	/**
	 * Move to next cell (Tab)
	 * @param {string} rowId
	 * @param {string} currentColumn
	 */
	function handleCellNext(rowId, currentColumn) {
		const visibleColumns = editableColumns.filter(col => isColumnVisible(col));
		const idx = visibleColumns.indexOf(currentColumn);
		if (idx < visibleColumns.length - 1) {
			focusCell(rowId, visibleColumns[idx + 1]);
		}
	}

	/**
	 * Move to previous cell (Shift+Tab)
	 * @param {string} rowId
	 * @param {string} currentColumn
	 */
	function handleCellPrev(rowId, currentColumn) {
		const visibleColumns = editableColumns.filter(col => isColumnVisible(col));
		const idx = visibleColumns.indexOf(currentColumn);
		if (idx > 0) {
			focusCell(rowId, visibleColumns[idx - 1]);
		}
	}

	/**
	 * Move to cell below (Enter)
	 * @param {number} currentRowIndex
	 * @param {string} column
	 */
	function handleCellDown(currentRowIndex, column) {
		if (currentRowIndex < filteredLeads.length - 1) {
			const nextRow = filteredLeads[currentRowIndex + 1];
			focusCell(nextRow.id, column);
		}
	}

	// Rating options for quick edit
	const ratingOptions = [
		{ value: 'HOT', label: 'Hot' },
		{ value: 'WARM', label: 'Warm' },
		{ value: 'COLD', label: 'Cold' }
	];

	// Status options for quick edit
	const statusOptions = [
		{ value: 'assigned', label: 'Assigned' },
		{ value: 'in process', label: 'In Process' },
		{ value: 'converted', label: 'Converted' },
		{ value: 'recycled', label: 'Recycled' },
		{ value: 'closed', label: 'Closed' }
	];

	// Form data state
	let formState = $state({
		leadId: '',
		// Core Information
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		company: '',
		title: '',
		contactTitle: '',
		website: '',
		linkedinUrl: '',
		// Sales Pipeline
		status: '',
		source: '',
		industry: '',
		rating: '',
		opportunityAmount: '',
		probability: '',
		closeDate: '',
		// Address
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		// Activity
		lastContacted: '',
		nextFollowUp: '',
		description: '',
		ownerId: ''
	});

	/**
	 * Get full name
	 * @param {any} lead
	 */
	function getFullName(lead) {
		return `${lead.firstName} ${lead.lastName}`.trim();
	}

	/**
	 * Get initials for lead
	 * @param {any} lead
	 */
	function getLeadInitials(lead) {
		return getNameInitials(lead.firstName, lead.lastName);
	}

	/**
	 * Handle form submit from drawer
	 * @param {any} formData
	 */
	async function handleFormSubmit(formData) {
		// Populate form state
		// Core Information
		formState.firstName = formData.first_name || '';
		formState.lastName = formData.last_name || '';
		formState.email = formData.email || '';
		formState.phone = formData.phone || '';
		formState.company = formData.company || '';
		formState.title = formData.title || '';
		formState.contactTitle = formData.contact_title || '';
		formState.website = formData.website || '';
		formState.linkedinUrl = formData.linkedin_url || '';
		// Sales Pipeline
		formState.status = formData.status || '';
		formState.source = formData.source || '';
		formState.industry = formData.industry || '';
		formState.rating = formData.rating || '';
		formState.opportunityAmount = formData.opportunity_amount || '';
		formState.probability = formData.probability || '';
		formState.closeDate = formData.close_date || '';
		// Address
		formState.addressLine = formData.address_line || '';
		formState.city = formData.city || '';
		formState.state = formData.state || '';
		formState.postcode = formData.postcode || '';
		formState.country = formData.country || '';
		// Activity
		formState.lastContacted = formData.last_contacted || '';
		formState.nextFollowUp = formData.next_follow_up || '';
		formState.description = formData.description || '';

		await tick();

		if (drawerMode === 'view' && selectedLead) {
			// Edit mode
			formState.leadId = selectedLead.id;
			// Use existing owner when editing (form doesn't have owner selection)
			formState.ownerId = selectedLead.owner?.id || '';
			await tick();
			updateForm.requestSubmit();
		} else {
			// Create mode
			formState.ownerId = '';
			createForm.requestSubmit();
		}
	}

	/**
	 * Handle lead delete
	 */
	async function handleDelete() {
		if (!selectedLead) return;
		if (!confirm(`Are you sure you want to delete ${getFullName(selectedLead)}?`)) return;

		formState.leadId = selectedLead.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Handle lead convert
	 */
	async function handleConvert() {
		if (!selectedLead) return;

		formState.leadId = selectedLead.id;
		await tick();
		convertForm.requestSubmit();
	}

	/**
	 * Handle lead duplicate
	 * @param {any} lead
	 */
	async function handleDuplicate(lead) {
		formState.leadId = lead.id;
		await tick();
		duplicateForm.requestSubmit();
	}

	/**
	 * Handle lead delete from row action
	 * @param {any} lead
	 */
	async function handleRowDelete(lead) {
		if (!confirm(`Are you sure you want to delete ${getFullName(lead)}?`)) return;

		formState.leadId = lead.id;
		await tick();
		deleteForm.requestSubmit();
	}

	/**
	 * Convert lead to form state for quick edit
	 * @param {any} lead
	 */
	function leadToFormState(lead) {
		return {
			leadId: lead.id,
			firstName: lead.firstName || '',
			lastName: lead.lastName || '',
			email: lead.email || '',
			phone: lead.phone || '',
			company: typeof lead.company === 'object' ? lead.company?.id || '' : lead.company || '',
			title: lead.title || '',
			contactTitle: lead.contactTitle || '',
			website: lead.website || '',
			linkedinUrl: lead.linkedinUrl || '',
			status: lead.status?.toLowerCase().replace('_', ' ') || '',
			source: lead.leadSource || '',
			industry: lead.industry || '',
			rating: lead.rating || '',
			opportunityAmount: lead.opportunityAmount || '',
			probability: lead.probability || '',
			closeDate: lead.closeDate || '',
			addressLine: lead.addressLine || '',
			city: lead.city || '',
			state: lead.state || '',
			postcode: lead.postcode || '',
			country: lead.country || '',
			lastContacted: lead.lastContacted || '',
			nextFollowUp: lead.nextFollowUp || '',
			description: lead.description || '',
			ownerId: lead.owner?.id || ''
		};
	}

	/**
	 * Handle quick edit from cell
	 * @param {any} lead
	 * @param {string} field
	 * @param {string} value
	 */
	async function handleQuickEdit(lead, field, value) {
		// Populate form state with current lead data
		const currentState = leadToFormState(lead);

		// Update the specific field
		currentState[field] = value;

		// Copy to form state
		Object.assign(formState, currentState);

		await tick();
		updateForm.requestSubmit();
	}

	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 */
	function createEnhanceHandler(successMessage) {
		return () => {
			return async ({ result }) => {
				if (result.type === 'success') {
					toast.success(successMessage);
					closeDrawer();
					await invalidateAll();
				} else if (result.type === 'failure') {
					toast.error(result.data?.error || 'Operation failed');
				} else if (result.type === 'error') {
					toast.error('An unexpected error occurred');
				}
			};
		};
	}
</script>

<svelte:head>
	<title>Leads - BottleCRM</title>
</svelte:head>

<PageHeader title="Leads" subtitle="{filteredLeads.length} of {leads.length} leads">
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
							{#each statuses as status}
								<option value={status.value}>{status.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label for="source-filter" class="mb-1.5 block text-sm font-medium">Source</label>
						<select
							id="source-filter"
							bind:value={list.filters.sourceFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							{#each sources as source}
								<option value={source.value}>{source.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label for="rating-filter" class="mb-1.5 block text-sm font-medium">Rating</label>
						<select
							id="rating-filter"
							bind:value={list.filters.ratingFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							{#each ratings as rating}
								<option value={rating.value}>{rating.label}</option>
							{/each}
						</select>
					</div>
				</div>
			{/snippet}
		</FilterPopover>
		<Button onclick={openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Lead
		</Button>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Leads Table -->
	<Card.Root class="border-0 shadow-sm">
		<Card.Content class="p-0">
			{#if filteredLeads.length === 0}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<User class="text-muted-foreground/50 mb-4 h-12 w-12" />
					<h3 class="text-foreground text-lg font-medium">No leads found</h3>
					<p class="text-muted-foreground mt-1 text-sm">
						Try adjusting your search criteria or create a new lead.
					</p>
					<Button onclick={openCreate} class="mt-4" disabled={false}>
						<Plus class="mr-2 h-4 w-4" />
						Create New Lead
					</Button>
				</div>
			{:else}
				<!-- Desktop Table - Notion-like styling -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row class="border-b border-border/40 hover:bg-transparent">
								<!-- Drag handle column -->
								<Table.Head class="w-8 py-2.5 px-0"></Table.Head>
								{#if isColumnVisible('lead')}
									<Table.Head class="w-[250px] py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Lead</Table.Head>
								{/if}
								{#if isColumnVisible('company')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Company</Table.Head>
								{/if}
								{#if isColumnVisible('email')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Email</Table.Head>
								{/if}
								{#if isColumnVisible('phone')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Phone</Table.Head>
								{/if}
								{#if isColumnVisible('rating')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Rating</Table.Head>
								{/if}
								{#if isColumnVisible('status')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Status</Table.Head>
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
								<!-- Extra space for row actions -->
								<Table.Head class="w-[120px]"></Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each filteredLeads as lead, rowIndex (lead.id)}
								{@const ratingConfig = getRatingConfig(lead.rating)}
								<Table.Row
									class="group relative h-[52px] border-b border-border/30 hover:bg-muted/20 cursor-pointer transition-all duration-150 ease-out"
									onclick={() => openLead(lead)}
								>
									<!-- Drag Handle -->
									<Table.Cell class="w-8 py-2 px-0">
										<div
											class="flex items-center justify-center opacity-0 group-hover:opacity-40 hover:!opacity-70 transition-opacity duration-150 cursor-grab active:cursor-grabbing"
											onmousedown={(e) => e.stopPropagation()}
											onclick={(e) => e.stopPropagation()}
										>
											<GripVertical class="h-4 w-4 text-muted-foreground" />
										</div>
									</Table.Cell>
									{#if isColumnVisible('lead')}
										<Table.Cell class="py-2 px-4">
											<div class="flex items-center gap-3">
												<div
													class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-sm font-medium text-white"
												>
													{getLeadInitials(lead)}
												</div>
												<div class="min-w-0">
													<p class="text-foreground truncate font-medium">
														{getFullName(lead)}
													</p>
													{#if lead.title}
														<p class="text-muted-foreground truncate text-sm">
															{lead.title}
														</p>
													{/if}
												</div>
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('company')}
										<Table.Cell class="py-2 px-4">
											<InlineEditableCell
												bind:this={cellRefs[`${lead.id}-company`]}
												value={typeof lead.company === 'object' ? lead.company?.name || '' : lead.company || ''}
												type="text"
												placeholder="Add company"
												onchange={(val) => handleQuickEdit(lead, 'company', val)}
												onnext={() => handleCellNext(lead.id, 'company')}
												onprev={() => handleCellPrev(lead.id, 'company')}
												ondown={() => handleCellDown(rowIndex, 'company')}
											>
												{#if lead.company}
													<div class="flex items-center gap-1.5 text-sm">
														<Building2 class="text-muted-foreground h-4 w-4 shrink-0" />
														<span class="truncate">{typeof lead.company === 'object' ? lead.company.name : lead.company}</span>
													</div>
												{:else}
													<span class="text-muted-foreground text-sm italic">Add company</span>
												{/if}
											</InlineEditableCell>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('email')}
										<Table.Cell class="py-2 px-4">
											<InlineEditableCell
												bind:this={cellRefs[`${lead.id}-email`]}
												value={lead.email || ''}
												type="email"
												placeholder="Add email"
												onchange={(val) => handleQuickEdit(lead, 'email', val)}
												onnext={() => handleCellNext(lead.id, 'email')}
												onprev={() => handleCellPrev(lead.id, 'email')}
												ondown={() => handleCellDown(rowIndex, 'email')}
											>
												{#if lead.email}
													<div class="flex items-center gap-1.5 text-sm">
														<Mail class="text-muted-foreground h-3.5 w-3.5 shrink-0" />
														<span class="max-w-[180px] truncate">{lead.email}</span>
													</div>
												{:else}
													<span class="text-muted-foreground text-sm italic">Add email</span>
												{/if}
											</InlineEditableCell>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('phone')}
										<Table.Cell class="py-2 px-4">
											<InlineEditableCell
												bind:this={cellRefs[`${lead.id}-phone`]}
												value={lead.phone || ''}
												type="phone"
												placeholder="Add phone"
												onchange={(val) => handleQuickEdit(lead, 'phone', val)}
												onnext={() => handleCellNext(lead.id, 'phone')}
												onprev={() => handleCellPrev(lead.id, 'phone')}
												ondown={() => handleCellDown(rowIndex, 'phone')}
											>
												{#if lead.phone}
													<div class="flex items-center gap-1.5 text-sm">
														<Phone class="text-muted-foreground h-3.5 w-3.5 shrink-0" />
														<span>{lead.phone}</span>
													</div>
												{:else}
													<span class="text-muted-foreground text-sm italic">Add phone</span>
												{/if}
											</InlineEditableCell>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('rating')}
										<Table.Cell class="py-2 px-4">
											<InlineEditableCell
												bind:this={cellRefs[`${lead.id}-rating`]}
												value={lead.rating || ''}
												type="select"
												options={ratingOptions}
												placeholder="Set rating"
												onchange={(val) => handleQuickEdit(lead, 'rating', val)}
												onnext={() => handleCellNext(lead.id, 'rating')}
												onprev={() => handleCellPrev(lead.id, 'rating')}
												ondown={() => handleCellDown(rowIndex, 'rating')}
											>
												{#if lead.rating}
													<div class="flex items-center gap-1.5">
														{#each { length: ratingConfig.dots } as _}
															<div class={cn('h-2 w-2 rounded-full', ratingConfig.bgColor)}></div>
														{/each}
														<span class={cn('text-sm font-medium', ratingConfig.color)}>
															{lead.rating}
														</span>
													</div>
												{:else}
													<span class="text-muted-foreground text-sm italic">Set rating</span>
												{/if}
											</InlineEditableCell>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('status')}
										<Table.Cell class="py-2 px-4">
											<InlineEditableCell
												bind:this={cellRefs[`${lead.id}-status`]}
												value={lead.status?.toLowerCase().replace('_', ' ') || ''}
												type="select"
												options={statusOptions}
												placeholder="Set status"
												onchange={(val) => handleQuickEdit(lead, 'status', val)}
												onnext={() => handleCellNext(lead.id, 'status')}
												onprev={() => handleCellPrev(lead.id, 'status')}
												ondown={() => handleCellDown(rowIndex, 'status')}
											>
												<span
													class={cn(
														'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
														getLeadStatusClass(lead.status)
													)}
												>
													{lead.status || 'Set status'}
												</span>
											</InlineEditableCell>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('created')}
										<Table.Cell class="py-2 px-4">
											<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
												<Calendar class="h-3.5 w-3.5" />
												<span>{formatRelativeDate(lead.createdAt)}</span>
											</div>
										</Table.Cell>
									{/if}
									<!-- Row Actions -->
									<Table.Cell class="py-2 px-4">
										<RowActions
											onEdit={() => openLead(lead)}
											onDelete={() => handleRowDelete(lead)}
											onDuplicate={() => handleDuplicate(lead)}
										/>
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Mobile Card View -->
				<div class="divide-y md:hidden">
					{#each filteredLeads as lead (lead.id)}
						{@const ratingConfig = getRatingConfig(lead.rating)}
						<button
							type="button"
							class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left"
							onclick={() => openLead(lead)}
						>
							<div
								class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-sm font-medium text-white"
							>
								{getLeadInitials(lead)}
							</div>
							<div class="min-w-0 flex-1">
								<div class="flex items-start justify-between gap-2">
									<div>
										<p class="text-foreground font-medium">{getFullName(lead)}</p>
										{#if lead.company}
											<p class="text-muted-foreground text-sm">{typeof lead.company === 'object' ? lead.company.name : lead.company}</p>
										{/if}
									</div>
									<span
										class={cn(
											'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
											getLeadStatusClass(lead.status)
										)}
									>
										{lead.status}
									</span>
								</div>
								<div class="text-muted-foreground mt-2 flex flex-wrap items-center gap-3 text-sm">
									{#if lead.rating}
										<div class="flex items-center gap-1">
											{#each { length: ratingConfig.dots } as _}
												<div class={cn('h-1.5 w-1.5 rounded-full', ratingConfig.bgColor)}></div>
											{/each}
											<span class={ratingConfig.color}>{lead.rating}</span>
										</div>
									{/if}
									<div class="flex items-center gap-1">
										<Calendar class="h-3.5 w-3.5" />
										<span>{formatRelativeDate(lead.createdAt)}</span>
									</div>
								</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</Card.Content>
	</Card.Root>
</div>

<!-- Lead Drawer (unified view/create/edit) -->
<LeadDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	lead={selectedLead}
	mode={drawerMode}
	loading={drawerLoading}
	onSave={handleFormSubmit}
	onConvert={handleConvert}
	onDelete={handleDelete}
	onCancel={closeDrawer}
/>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Lead created successfully')}
	class="hidden"
>
	<!-- Core Information -->
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="company" value={formState.company} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="contactTitle" value={formState.contactTitle} />
	<input type="hidden" name="website" value={formState.website} />
	<input type="hidden" name="linkedinUrl" value={formState.linkedinUrl} />
	<!-- Sales Pipeline -->
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="source" value={formState.source} />
	<input type="hidden" name="industry" value={formState.industry} />
	<input type="hidden" name="rating" value={formState.rating} />
	<input type="hidden" name="opportunityAmount" value={formState.opportunityAmount} />
	<input type="hidden" name="probability" value={formState.probability} />
	<input type="hidden" name="closeDate" value={formState.closeDate} />
	<!-- Address -->
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<!-- Activity -->
	<input type="hidden" name="lastContacted" value={formState.lastContacted} />
	<input type="hidden" name="nextFollowUp" value={formState.nextFollowUp} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="ownerId" value={formState.ownerId} />
</form>

<form
	method="POST"
	action="?/update"
	bind:this={updateForm}
	use:enhance={createEnhanceHandler('Lead updated successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
	<!-- Core Information -->
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="company" value={formState.company} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="contactTitle" value={formState.contactTitle} />
	<input type="hidden" name="website" value={formState.website} />
	<input type="hidden" name="linkedinUrl" value={formState.linkedinUrl} />
	<!-- Sales Pipeline -->
	<input type="hidden" name="status" value={formState.status} />
	<input type="hidden" name="source" value={formState.source} />
	<input type="hidden" name="industry" value={formState.industry} />
	<input type="hidden" name="rating" value={formState.rating} />
	<input type="hidden" name="opportunityAmount" value={formState.opportunityAmount} />
	<input type="hidden" name="probability" value={formState.probability} />
	<input type="hidden" name="closeDate" value={formState.closeDate} />
	<!-- Address -->
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<!-- Activity -->
	<input type="hidden" name="lastContacted" value={formState.lastContacted} />
	<input type="hidden" name="nextFollowUp" value={formState.nextFollowUp} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="ownerId" value={formState.ownerId} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Lead deleted successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
</form>

<form
	method="POST"
	action="?/convert"
	bind:this={convertForm}
	use:enhance={createEnhanceHandler('Lead converted successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
</form>

<form
	method="POST"
	action="?/duplicate"
	bind:this={duplicateForm}
	use:enhance={createEnhanceHandler('Lead duplicated successfully')}
	class="hidden"
>
	<input type="hidden" name="leadId" value={formState.leadId} />
</form>
