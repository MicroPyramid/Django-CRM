<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronDown,
		Phone,
		Mail,
		Building2,
		User,
		Calendar,
		GripVertical,
		Expand,
		X,
		Eye,
		Check,
		Trash2,
		Star,
		Globe,
		Briefcase
	} from '@lucide/svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { LeadDrawer } from '$lib/components/leads';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { cn } from '$lib/utils.js';
	import { formatRelativeDate, formatDate, getNameInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import {
		leadStatusOptions,
		leadRatingOptions,
		getOptionStyle,
		getOptionLabel,
		getOptionBgColor
	} from '$lib/utils/table-helpers.js';
	import {
		createDragState,
		calculateDropPosition,
		reorderItems,
		handleDragStart as dndDragStart,
		dragHandleClasses,
		expandButtonClasses,
		dropIndicatorClasses,
		draggedRowClasses
	} from '$lib/utils/drag-drop.js';

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
	const formOptions = $derived(data.formOptions || {});

	// Drawer state (simplified - single drawer, matching contacts page pattern)
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {any} */
	let selectedLead = $state(null);
	let drawerLoading = $state(false);

	// Sheet state (Notion-style row detail panel)
	let sheetOpen = $state(false);
	/** @type {string | null} */
	let selectedRowId = $state(null);

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

	// Dirty tracking for batch save
	/** @type {Map<string, Record<string, any>>} */
	let pendingChanges = $state(new Map());
	let saving = $state(false);

	// Derived: check if there are unsaved changes
	const hasUnsavedChanges = $derived(pendingChanges.size > 0);

	// Get selected row data for Sheet
	const selectedRow = $derived(leads.find((/** @type {any} */ l) => l.id === selectedRowId));

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

	/**
	 * Open row sheet
	 * @param {string} rowId
	 */
	function openRowSheet(rowId) {
		selectedRowId = rowId;
		sheetOpen = true;
	}

	/**
	 * Close row sheet
	 */
	function closeRowSheet() {
		sheetOpen = false;
		selectedRowId = null;
	}

	/**
	 * Update a field in the selected row (for Sheet edits)
	 * @param {string} field
	 * @param {any} value
	 */
	function updateSelectedRowField(field, value) {
		if (!selectedRowId) return;
		trackChange(selectedRowId, field, value);
	}

	/**
	 * Handle drag start
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleDragStart(e, rowId) {
		draggedRowId = rowId;
		dndDragStart(e, rowId);
	}

	/**
	 * Handle drag over a row
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleRowDragOver(e, rowId) {
		e.preventDefault();
		if (draggedRowId === rowId) return;
		dragOverRowId = rowId;
		dropPosition = calculateDropPosition(e);
	}

	/**
	 * Handle drag leave
	 */
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
		// Note: For now, drag-and-drop just reorders visually
		// In a real app, you'd persist this order
		resetDragState();
	}

	/**
	 * Handle drag end
	 */
	function handleDragEnd() {
		resetDragState();
	}

	/**
	 * Reset drag state
	 */
	function resetDragState() {
		draggedRowId = null;
		dragOverRowId = null;
		dropPosition = null;
	}

	/**
	 * Start editing a cell
	 * @param {string} rowId
	 * @param {string} columnKey
	 */
	async function startEditing(rowId, columnKey) {
		const row = leads.find((/** @type {any} */ l) => l.id === rowId);
		if (!row) return;

		// Get the current value (check pending changes first)
		const pending = pendingChanges.get(rowId);
		let currentValue = pending?.[columnKey] ?? row[columnKey];

		// Handle special cases
		if (columnKey === 'company') {
			currentValue = typeof row.company === 'object' ? row.company?.name || '' : row.company || '';
		}

		editingCell = { rowId, columnKey };
		editValue = currentValue?.toString() ?? '';

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
	 * Stop editing and optionally save
	 * @param {boolean} save
	 */
	function stopEditing(save = true) {
		if (!editingCell) return;

		if (save) {
			const { rowId, columnKey } = editingCell;
			trackChange(rowId, columnKey, editValue);
		}

		editingCell = null;
		editValue = '';
	}

	/**
	 * Handle keyboard events in edit mode
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
	 * Update a select value inline
	 * @param {string} rowId
	 * @param {string} columnKey
	 * @param {string} value
	 */
	function updateSelectValue(rowId, columnKey, value) {
		trackChange(rowId, columnKey, value);
	}

	/**
	 * Track a change to a field
	 * @param {string} rowId
	 * @param {string} field
	 * @param {any} value
	 */
	function trackChange(rowId, field, value) {
		const existing = pendingChanges.get(rowId) || {};
		pendingChanges.set(rowId, { ...existing, [field]: value });
		pendingChanges = new Map(pendingChanges); // Trigger reactivity
	}

	/**
	 * Get the display value for a field (pending change or original)
	 * @param {any} lead
	 * @param {string} field
	 */
	function getDisplayValue(lead, field) {
		const pending = pendingChanges.get(lead.id);
		if (pending && field in pending) {
			return pending[field];
		}
		return lead[field];
	}

	/**
	 * Save all pending changes
	 */
	async function saveAllChanges() {
		if (pendingChanges.size === 0) return;

		saving = true;

		try {
			// Process each changed row
			for (const [rowId, changes] of pendingChanges) {
				const lead = leads.find((/** @type {any} */ l) => l.id === rowId);
				if (!lead) continue;

				// Build form state with all lead data + changes
				const currentState = leadToFormState(lead);
				Object.assign(currentState, changes);

				// Copy to form state
				Object.assign(formState, currentState);

				await tick();
				updateForm.requestSubmit();

				// Wait a bit between requests to avoid overwhelming the server
				await new Promise((resolve) => setTimeout(resolve, 100));
			}

			pendingChanges.clear();
			pendingChanges = new Map(); // Trigger reactivity
			toast.success('Changes saved successfully');
		} catch (error) {
			toast.error('Failed to save some changes');
		} finally {
			saving = false;
		}
	}

	/**
	 * Discard all pending changes
	 */
	function discardChanges() {
		if (!confirm('Discard all unsaved changes?')) return;
		pendingChanges.clear();
		pendingChanges = new Map();
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

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;
	/** @type {HTMLFormElement} */
	let convertForm;
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
		formState.company = formData.company_name || '';
		formState.title = formData.title || '';
		formState.contactTitle = formData.job_title || '';
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

<div class="min-h-screen bg-white">
	<!-- Notion-style Header -->
	<div class="border-b border-gray-200 px-6 py-4">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-semibold text-gray-900">Leads</h1>
				<p class="mt-1 text-sm text-gray-500">{filteredLeads.length} leads</p>
			</div>
			<div class="flex items-center gap-2">
				<!-- Save Changes Button (shown when dirty) -->
				{#if hasUnsavedChanges}
					<Button variant="outline" size="sm" onclick={discardChanges} disabled={saving}>
						Discard
					</Button>
					<Button size="sm" onclick={saveAllChanges} disabled={saving}>
						{saving ? 'Saving...' : 'Save Changes'}
					</Button>
				{/if}

				<!-- Column Visibility (Notion-style) -->
				<DropdownMenu.Root>
					<DropdownMenu.Trigger asChild>
						{#snippet child({ props })}
							<Button {...props} variant="outline" size="sm" class="gap-2">
								<Eye class="h-4 w-4" />
								Columns
								{#if columnConfig.filter((c) => c.visible).length < columnConfig.length}
									<span
										class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700"
									>
										{columnConfig.filter((c) => c.visible).length}/{columnConfig.length}
									</span>
								{/if}
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="w-48">
						<DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
						<DropdownMenu.Separator />
						{#each columnConfig as column (column.key)}
							<DropdownMenu.CheckboxItem
								class=""
								checked={column.visible}
								disabled={!column.canHide}
								onCheckedChange={() => {
									if (column.canHide) {
										columnConfig = columnConfig.map((c) =>
											c.key === column.key ? { ...c, visible: !c.visible } : c
										);
									}
								}}
							>
								{column.label}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>

				<Button size="sm" class="gap-2" onclick={openCreate}>
					<Plus class="h-4 w-4" />
					New
				</Button>
			</div>
		</div>
	</div>

	<!-- Table -->
	{#if filteredLeads.length === 0}
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<User class="mb-4 h-12 w-12 text-gray-300" />
			<h3 class="text-lg font-medium text-gray-900">No leads found</h3>
			<p class="mt-1 text-sm text-gray-500">Create your first lead to get started.</p>
			<Button onclick={openCreate} class="mt-4" size="sm">
				<Plus class="mr-2 h-4 w-4" />
				New Lead
			</Button>
		</div>
	{:else}
		<!-- Desktop Table - Notion-style native HTML table -->
		<div class="hidden overflow-x-auto md:block">
			<table class="w-full border-collapse">
				<!-- Header -->
				<thead>
					<tr class="border-b border-gray-100/60">
						<!-- Drag handle column -->
						<th class="w-8 px-1"></th>
						<!-- Expand button column -->
						<th class="w-8 px-1"></th>
						{#if isColumnVisible('lead')}
							<th class="w-[250px] px-4 py-3 text-left text-[13px] font-normal text-gray-400"
								>Name</th
							>
						{/if}
						{#if isColumnVisible('company')}
							<th class="w-40 px-4 py-3 text-left text-[13px] font-normal text-gray-400">Company</th
							>
						{/if}
						{#if isColumnVisible('email')}
							<th class="w-52 px-4 py-3 text-left text-[13px] font-normal text-gray-400">Email</th>
						{/if}
						{#if isColumnVisible('phone')}
							<th class="w-36 px-4 py-3 text-left text-[13px] font-normal text-gray-400">Phone</th>
						{/if}
						{#if isColumnVisible('rating')}
							<th class="w-28 px-4 py-3 text-left text-[13px] font-normal text-gray-400">Rating</th>
						{/if}
						{#if isColumnVisible('status')}
							<th class="w-28 px-4 py-3 text-left text-[13px] font-normal text-gray-400">Status</th>
						{/if}
						{#if isColumnVisible('created')}
							<th class="w-36 px-4 py-3 text-left text-[13px] font-normal text-gray-400">
								Created
							</th>
						{/if}
					</tr>
				</thead>

				<!-- Body -->
				<tbody>
					{#each filteredLeads as lead, rowIndex (lead.id)}
						{@const displayRating = getDisplayValue(lead, 'rating') || lead.rating}
						{@const displayStatus = getDisplayValue(lead, 'status') || lead.status}
						{@const displayCompany =
							getDisplayValue(lead, 'company') ??
							(typeof lead.company === 'object' ? lead.company?.name : lead.company)}
						{@const displayEmail = getDisplayValue(lead, 'email') || lead.email}
						{@const displayPhone = getDisplayValue(lead, 'phone') || lead.phone}

						<!-- Drop indicator line (before row) -->
						{#if dragOverRowId === lead.id && dropPosition === 'before'}
							<tr class="h-0">
								<td colspan="10" class="p-0">
									<div class={dropIndicatorClasses}></div>
								</td>
							</tr>
						{/if}

						<tr
							class={cn(
								'group transition-all duration-100 ease-out hover:bg-gray-50/30',
								draggedRowId === lead.id && draggedRowClasses,
								pendingChanges.has(lead.id) && 'bg-amber-50/30'
							)}
							ondragover={(e) => handleRowDragOver(e, lead.id)}
							ondragleave={handleRowDragLeave}
							ondrop={(e) => handleRowDrop(e, lead.id)}
						>
							<!-- Drag Handle -->
							<td class="w-8 px-1 py-3">
								<div
									draggable="true"
									ondragstart={(e) => handleDragStart(e, lead.id)}
									ondragend={handleDragEnd}
									class={dragHandleClasses}
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
									onclick={() => openRowSheet(lead.id)}
									class={expandButtonClasses}
								>
									<Expand class="h-3.5 w-3.5 text-gray-500" />
								</button>
							</td>

							{#if isColumnVisible('lead')}
								<td class="w-48 px-4 py-3">
									{#if editingCell?.rowId === lead.id && editingCell?.columnKey === 'name'}
										<input
											type="text"
											bind:value={editValue}
											onkeydown={handleEditKeydown}
											onblur={() => stopEditing(true)}
											data-edit-input="{lead.id}-name"
											class="w-full rounded bg-white px-2 py-1.5 text-sm shadow-sm ring-1 ring-gray-200 transition-shadow duration-100 outline-none focus:ring-blue-300"
										/>
									{:else}
										<button
											type="button"
											onclick={() => openRowSheet(lead.id)}
											class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50"
										>
											{getFullName(lead) || 'Empty'}
										</button>
									{/if}
								</td>
							{/if}

							{#if isColumnVisible('company')}
								<td class="w-40 px-4 py-3">
									{#if editingCell?.rowId === lead.id && editingCell?.columnKey === 'company'}
										<input
											type="text"
											bind:value={editValue}
											onkeydown={handleEditKeydown}
											onblur={() => stopEditing(true)}
											data-edit-input="{lead.id}-company"
											class="w-full rounded bg-white px-2 py-1.5 text-sm shadow-sm ring-1 ring-gray-200 transition-shadow duration-100 outline-none focus:ring-blue-300"
										/>
									{:else}
										<button
											type="button"
											onclick={() => startEditing(lead.id, 'company')}
											class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50"
										>
											{displayCompany || ''}
										</button>
									{/if}
								</td>
							{/if}

							{#if isColumnVisible('email')}
								<td class="w-52 px-4 py-3">
									{#if editingCell?.rowId === lead.id && editingCell?.columnKey === 'email'}
										<input
											type="email"
											bind:value={editValue}
											onkeydown={handleEditKeydown}
											onblur={() => stopEditing(true)}
											data-edit-input="{lead.id}-email"
											class="w-full rounded bg-white px-2 py-1.5 text-sm shadow-sm ring-1 ring-gray-200 transition-shadow duration-100 outline-none focus:ring-blue-300"
										/>
									{:else}
										<button
											type="button"
											onclick={() => startEditing(lead.id, 'email')}
											class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50"
										>
											{displayEmail || ''}
										</button>
									{/if}
								</td>
							{/if}

							{#if isColumnVisible('phone')}
								<td class="w-36 px-4 py-3">
									{#if editingCell?.rowId === lead.id && editingCell?.columnKey === 'phone'}
										<input
											type="tel"
											bind:value={editValue}
											onkeydown={handleEditKeydown}
											onblur={() => stopEditing(true)}
											data-edit-input="{lead.id}-phone"
											class="w-full rounded bg-white px-2 py-1.5 text-sm shadow-sm ring-1 ring-gray-200 transition-shadow duration-100 outline-none focus:ring-blue-300"
										/>
									{:else}
										<button
											type="button"
											onclick={() => startEditing(lead.id, 'phone')}
											class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50"
										>
											{displayPhone || ''}
										</button>
									{/if}
								</td>
							{/if}

							{#if isColumnVisible('rating')}
								<td class="w-28 px-4 py-3">
									<DropdownMenu.Root>
										<DropdownMenu.Trigger asChild>
											{#snippet child({ props })}
												<button
													{...props}
													type="button"
													class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium {getOptionStyle(
														displayRating,
														leadRatingOptions
													)} transition-opacity hover:opacity-80"
												>
													{getOptionLabel(displayRating, leadRatingOptions) || ''}
													<ChevronDown class="h-3 w-3 opacity-60" />
												</button>
											{/snippet}
										</DropdownMenu.Trigger>
										<DropdownMenu.Content align="start" class="w-36">
											{#each leadRatingOptions as option (option.value)}
												<DropdownMenu.Item
													onclick={() => updateSelectValue(lead.id, 'rating', option.value)}
													class="flex items-center gap-2"
												>
													<span class="h-2 w-2 rounded-full {option.color.split(' ')[0]}"></span>
													{option.label}
													{#if displayRating === option.value}
														<Check class="ml-auto h-4 w-4" />
													{/if}
												</DropdownMenu.Item>
											{/each}
										</DropdownMenu.Content>
									</DropdownMenu.Root>
								</td>
							{/if}

							{#if isColumnVisible('status')}
								<td class="w-28 px-4 py-3">
									<DropdownMenu.Root>
										<DropdownMenu.Trigger asChild>
											{#snippet child({ props })}
												<button
													{...props}
													type="button"
													class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium {getOptionStyle(
														displayStatus,
														leadStatusOptions
													)} transition-opacity hover:opacity-80"
												>
													{getOptionLabel(displayStatus, leadStatusOptions) || ''}
													<ChevronDown class="h-3 w-3 opacity-60" />
												</button>
											{/snippet}
										</DropdownMenu.Trigger>
										<DropdownMenu.Content align="start" class="w-36">
											{#each leadStatusOptions as option (option.value)}
												<DropdownMenu.Item
													onclick={() => updateSelectValue(lead.id, 'status', option.value)}
													class="flex items-center gap-2"
												>
													<span class="h-2 w-2 rounded-full {option.color.split(' ')[0]}"></span>
													{option.label}
													{#if displayStatus === option.value}
														<Check class="ml-auto h-4 w-4" />
													{/if}
												</DropdownMenu.Item>
											{/each}
										</DropdownMenu.Content>
									</DropdownMenu.Root>
								</td>
							{/if}

							{#if isColumnVisible('created')}
								<td class="w-36 px-4 py-3">
									<button
										type="button"
										class="-mx-2 -my-1.5 rounded px-2 py-1.5 text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50"
									>
										{formatDate(lead.createdAt)}
									</button>
								</td>
							{/if}
						</tr>

						<!-- Drop indicator line (after row) -->
						{#if dragOverRowId === lead.id && dropPosition === 'after'}
							<tr class="h-0">
								<td colspan="10" class="p-0">
									<div class={dropIndicatorClasses}></div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>

			<!-- New row button (Notion-style) -->
			<div class="border-t border-gray-100/60 px-4 py-2">
				<button
					type="button"
					onclick={openCreate}
					class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
				>
					<Plus class="h-4 w-4" />
					New
				</button>
			</div>
		</div>

		<!-- Mobile Card View -->
		<div class="divide-y md:hidden">
			{#each filteredLeads as lead (lead.id)}
				<button
					type="button"
					class="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-gray-50/30"
					onclick={() => openRowSheet(lead.id)}
				>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<p class="text-sm font-medium text-gray-900">{getFullName(lead)}</p>
								{#if lead.company}
									<p class="text-sm text-gray-500">
										{typeof lead.company === 'object' ? lead.company.name : lead.company}
									</p>
								{/if}
							</div>
							<span
								class="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium {getOptionStyle(
									lead.status,
									leadStatusOptions
								)}"
							>
								{getOptionLabel(lead.status, leadStatusOptions)}
							</span>
						</div>
						<div class="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
							{#if lead.rating}
								<span
									class="rounded-full px-2 py-0.5 {getOptionStyle(lead.rating, leadRatingOptions)}"
								>
									{getOptionLabel(lead.rating, leadRatingOptions)}
								</span>
							{/if}
							<span>{formatRelativeDate(lead.createdAt)}</span>
						</div>
					</div>
				</button>
			{/each}

			<!-- Mobile new row button -->
			<button
				type="button"
				onclick={openCreate}
				class="flex w-full items-center gap-2 px-4 py-3 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
			>
				<Plus class="h-4 w-4" />
				New
			</button>
		</div>
	{/if}
</div>

<!-- Row Detail Sheet (Notion-style) -->
<Sheet.Root bind:open={sheetOpen} onOpenChange={(open) => !open && closeRowSheet()}>
	<Sheet.Content side="right" class="w-[440px] overflow-hidden p-0 sm:max-w-[440px]">
		{#if selectedRow}
			{@const displayFirstName = getDisplayValue(selectedRow, 'firstName') || selectedRow.firstName}
			{@const displayLastName = getDisplayValue(selectedRow, 'lastName') || selectedRow.lastName}
			{@const displayEmail = getDisplayValue(selectedRow, 'email') || selectedRow.email}
			{@const displayPhone = getDisplayValue(selectedRow, 'phone') || selectedRow.phone}
			{@const displayCompany =
				getDisplayValue(selectedRow, 'company') ??
				(typeof selectedRow.company === 'object' ? selectedRow.company?.name : selectedRow.company)}
			{@const displayStatus = getDisplayValue(selectedRow, 'status') || selectedRow.status}
			{@const displayRating = getDisplayValue(selectedRow, 'rating') || selectedRow.rating}
			{@const displayWebsite = getDisplayValue(selectedRow, 'website') || selectedRow.website}
			<div class="flex h-full flex-col">
				<!-- Header with close button -->
				<div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
					<span class="text-sm text-gray-500">Lead</span>
					<button
						onclick={closeRowSheet}
						class="rounded p-1 transition-colors duration-75 hover:bg-gray-100"
					>
						<X class="h-4 w-4 text-gray-400" />
					</button>
				</div>

				<!-- Scrollable content -->
				<div class="flex-1 overflow-y-auto">
					<!-- Title section -->
					<div class="px-6 pt-6 pb-4">
						<div class="mb-4 flex items-center gap-3">
							<div
								class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-lg font-medium text-white"
							>
								{getLeadInitials(selectedRow)}
							</div>
							<div>
								<input
									type="text"
									value="{displayFirstName} {displayLastName}"
									readonly
									placeholder="Untitled"
									class="w-full cursor-default border-0 bg-transparent text-xl font-semibold outline-none placeholder:text-gray-300 focus:ring-0"
								/>
							</div>
						</div>
					</div>

					<!-- Properties section -->
					<div class="space-y-1 px-4 pb-6">
						<!-- Email property -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Mail class="h-4 w-4 text-gray-400" />
								Email
							</div>
							<div class="min-w-0 flex-1">
								<input
									type="email"
									value={displayEmail || ''}
									oninput={(e) =>
										updateSelectedRowField(
											'email',
											/** @type {HTMLInputElement} */ (e.target).value
										)}
									placeholder="Add email"
									class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm transition-colors outline-none placeholder:text-gray-400 focus:bg-gray-50"
								/>
							</div>
						</div>

						<!-- Phone property -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Phone class="h-4 w-4 text-gray-400" />
								Phone
							</div>
							<div class="min-w-0 flex-1">
								<input
									type="tel"
									value={displayPhone || ''}
									oninput={(e) =>
										updateSelectedRowField(
											'phone',
											/** @type {HTMLInputElement} */ (e.target).value
										)}
									placeholder="Add phone"
									class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm transition-colors outline-none placeholder:text-gray-400 focus:bg-gray-50"
								/>
							</div>
						</div>

						<!-- Company property -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Building2 class="h-4 w-4 text-gray-400" />
								Company
							</div>
							<div class="min-w-0 flex-1">
								<input
									type="text"
									value={displayCompany || ''}
									oninput={(e) =>
										updateSelectedRowField(
											'company',
											/** @type {HTMLInputElement} */ (e.target).value
										)}
									placeholder="Add company"
									class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm transition-colors outline-none placeholder:text-gray-400 focus:bg-gray-50"
								/>
							</div>
						</div>

						<!-- Website property -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Globe class="h-4 w-4 text-gray-400" />
								Website
							</div>
							<div class="min-w-0 flex-1">
								<input
									type="url"
									value={displayWebsite || ''}
									oninput={(e) =>
										updateSelectedRowField(
											'website',
											/** @type {HTMLInputElement} */ (e.target).value
										)}
									placeholder="Add website"
									class="w-full rounded border-0 bg-transparent px-2 py-1 text-sm transition-colors outline-none placeholder:text-gray-400 focus:bg-gray-50"
								/>
							</div>
						</div>

						<!-- Status property (select) -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Briefcase class="h-4 w-4 text-gray-400" />
								Status
							</div>
							<div class="flex-1">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger asChild>
										{#snippet child({ props })}
											<button
												{...props}
												type="button"
												class="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-sm {getOptionStyle(
													displayStatus,
													leadStatusOptions
												)} transition-opacity hover:opacity-90"
											>
												<span
													class="h-2 w-2 rounded-full {getOptionBgColor(
														displayStatus,
														leadStatusOptions
													)}"
												></span>
												{getOptionLabel(displayStatus, leadStatusOptions) || 'Set status'}
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="start" class="w-36">
										{#each leadStatusOptions as option (option.value)}
											<DropdownMenu.Item
												onclick={() => updateSelectedRowField('status', option.value)}
												class="flex items-center gap-2"
											>
												<span class="h-2 w-2 rounded-full {option.color.split(' ')[0]}"></span>
												{option.label}
												{#if displayStatus === option.value}
													<Check class="ml-auto h-4 w-4" />
												{/if}
											</DropdownMenu.Item>
										{/each}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>

						<!-- Rating property (select) -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Star class="h-4 w-4 text-gray-400" />
								Rating
							</div>
							<div class="flex-1">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger asChild>
										{#snippet child({ props })}
											<button
												{...props}
												type="button"
												class="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-sm {getOptionStyle(
													displayRating,
													leadRatingOptions
												)} transition-opacity hover:opacity-90"
											>
												<span
													class="h-2 w-2 rounded-full {getOptionBgColor(
														displayRating,
														leadRatingOptions
													)}"
												></span>
												{getOptionLabel(displayRating, leadRatingOptions) || 'Set rating'}
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="start" class="w-36">
										{#each leadRatingOptions as option (option.value)}
											<DropdownMenu.Item
												onclick={() => updateSelectedRowField('rating', option.value)}
												class="flex items-center gap-2"
											>
												<span class="h-2 w-2 rounded-full {option.color.split(' ')[0]}"></span>
												{option.label}
												{#if displayRating === option.value}
													<Check class="ml-auto h-4 w-4" />
												{/if}
											</DropdownMenu.Item>
										{/each}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>

						<!-- Created date -->
						<div
							class="group -mx-2 flex min-h-[36px] items-center rounded px-2 transition-colors duration-75 hover:bg-gray-50/60"
						>
							<div class="flex w-28 shrink-0 items-center gap-2 text-[13px] text-gray-500">
								<Calendar class="h-4 w-4 text-gray-400" />
								Created
							</div>
							<div class="min-w-0 flex-1">
								<span class="px-2 py-1 text-sm text-gray-700">
									{formatDate(selectedRow.createdAt)}
								</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Footer with actions -->
				<div class="mt-auto flex items-center justify-between border-t border-gray-100 px-4 py-3">
					<button
						onclick={() => {
							closeRowSheet();
							handleRowDelete(selectedRow);
						}}
						class="flex items-center gap-2 rounded px-3 py-1.5 text-sm text-red-600 transition-colors duration-75 hover:bg-red-50"
					>
						<Trash2 class="h-4 w-4" />
						Delete
					</button>
					<Button
						size="sm"
						onclick={() => {
							closeRowSheet();
							openLead(selectedRow);
						}}
					>
						Open Full View
					</Button>
				</div>
			</div>
		{/if}
	</Sheet.Content>
</Sheet.Root>

<!-- Lead Drawer (unified view/create/edit) -->
<LeadDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	lead={selectedLead}
	mode={drawerMode}
	loading={drawerLoading}
	options={{
		statuses: [],
		sources: [],
		users: formOptions.users || [],
		teamsList: formOptions.teamsList || [],
		contactsList: formOptions.contactsList || [],
		tagsList: formOptions.tagsList || []
	}}
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

