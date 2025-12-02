<script>
	import { invalidateAll } from '$app/navigation';
	import { onMount, tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronDown,
		Eye,
		Expand,
		GripVertical,
		X,
		Building2,
		Target,
		DollarSign,
		Calendar,
		Percent,
		User,
		Briefcase,
		Globe,
		Check,
		Trash2
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Sheet from '$lib/components/ui/sheet/index.js';
	import { formatCurrency } from '$lib/utils/formatting.js';
	import { OPPORTUNITY_STAGES as stages, OPPORTUNITY_TYPES, OPPORTUNITY_SOURCES } from '$lib/constants/filters.js';

	const STORAGE_KEY = 'opportunities-notion-columns';

	// Stage options with colors
	const stageOptions = [
		{ value: 'PROSPECTING', label: 'Prospecting', color: 'bg-gray-100 text-gray-700' },
		{ value: 'QUALIFICATION', label: 'Qualification', color: 'bg-blue-100 text-blue-700' },
		{ value: 'PROPOSAL', label: 'Proposal', color: 'bg-purple-100 text-purple-700' },
		{ value: 'NEGOTIATION', label: 'Negotiation', color: 'bg-orange-100 text-orange-700' },
		{ value: 'CLOSED_WON', label: 'Won', color: 'bg-green-100 text-green-700' },
		{ value: 'CLOSED_LOST', label: 'Lost', color: 'bg-red-100 text-red-700' }
	];

	// Type options
	const typeOptions = OPPORTUNITY_TYPES.map(t => ({
		value: t.value,
		label: t.label,
		color: 'bg-slate-100 text-slate-700'
	}));

	// Column definitions
	const columns = [
		{ key: 'name', label: 'Opportunity', type: 'text', width: 'w-48' },
		{ key: 'account', label: 'Account', type: 'text', width: 'w-40' },
		{ key: 'stage', label: 'Stage', type: 'select', options: stageOptions, width: 'w-32' },
		{ key: 'amount', label: 'Amount', type: 'number', width: 'w-32' },
		{ key: 'probability', label: 'Probability', type: 'number', width: 'w-28' },
		{ key: 'opportunityType', label: 'Type', type: 'select', options: typeOptions, width: 'w-32' },
		{ key: 'closedOn', label: 'Close Date', type: 'date', width: 'w-36' },
		{ key: 'owner', label: 'Owner', type: 'text', width: 'w-36' }
	];

	/** @type {{ data: any }} */
	let { data } = $props();

	// Options for form
	const formOptions = $derived({
		accounts: data.options?.accounts || [],
		contacts: data.options?.contacts || [],
		tags: data.options?.tags || []
	});

	// State
	let searchQuery = $state('');
	let stageFilter = $state('ALL');

	// Column visibility state - all visible by default
	let visibleColumns = $state(columns.map(c => c.key));

	// Editing state
	/** @type {{ rowId: string, columnKey: string } | null} */
	let editingCell = $state(null);
	let editValue = $state('');

	// Row detail sheet state
	let sheetOpen = $state(false);
	/** @type {string | null} */
	let selectedRowId = $state(null);
	let isLoading = $state(false);

	// Drag-and-drop state
	/** @type {string | null} */
	let draggedRowId = $state(null);
	/** @type {string | null} */
	let dragOverRowId = $state(null);
	/** @type {'before' | 'after' | null} */
	let dropPosition = $state(null);

	// Computed values
	const opportunities = $derived(data.opportunities || []);
	const stats = $derived(data.stats || { total: 0, totalValue: 0, wonValue: 0, pipeline: 0 });

	const filteredOpportunities = $derived.by(() => {
		return opportunities
			.filter((/** @type {any} */ opp) => {
				const matchesSearch =
					searchQuery === '' ||
					opp.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
					opp.account?.name?.toLowerCase().includes(searchQuery.toLowerCase());
				const matchesStage = stageFilter === 'ALL' || opp.stage === stageFilter;
				return matchesSearch && matchesStage;
			});
	});

	const activeFiltersCount = $derived(stageFilter !== 'ALL' ? 1 : 0);

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
	function isColumnVisible(key) {
		return visibleColumns.includes(key);
	}

	/**
	 * @param {string} key
	 */
	function toggleColumn(key) {
		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter(k => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/**
	 * @param {string} rowId
	 * @param {string} columnKey
	 */
	async function startEditing(rowId, columnKey) {
		const row = filteredOpportunities.find((/** @type {any} */ r) => r.id === rowId);
		if (!row) return;

		editingCell = { rowId, columnKey };

		// Get the value based on column key
		let value = '';
		if (columnKey === 'account') {
			value = row.account?.name || '';
		} else if (columnKey === 'owner') {
			value = row.owner?.name || '';
		} else {
			value = row[columnKey]?.toString() ?? '';
		}
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
	 * @param {boolean} save
	 */
	async function stopEditing(save = true) {
		if (!editingCell) return;

		if (save) {
			const { rowId, columnKey } = editingCell;
			const column = columns.find(c => c.key === columnKey);

			// Save the value via API
			await saveFieldValue(rowId, columnKey, editValue, column?.type);
		}

		editingCell = null;
		editValue = '';
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
				amount: 'amount',
				probability: 'probability',
				stage: 'stage',
				opportunityType: 'opportunityType',
				closedOn: 'closedOn'
			});

			const apiField = fieldMapping[field];
			if (apiField) {
				// Convert value based on type
				let apiValue = value;
				if (fieldType === 'number') {
					apiValue = parseFloat(value) || 0;
				}
				form.append(apiField, apiValue?.toString() || '');

				// Need to send required fields too
				const opp = filteredOpportunities.find((/** @type {any} */ o) => o.id === rowId);
				if (opp) {
					if (field !== 'name') form.append('name', opp.name || '');
					if (field !== 'stage') form.append('stage', opp.stage || 'PROSPECTING');
				}

				const response = await fetch('?/update', { method: 'POST', body: form });
				const result = await response.json();

				if (result.type === 'success' || result.data?.success) {
					await invalidateAll();
				}
			}
		} catch (err) {
			console.error('Error saving field:', err);
			toast.error('Failed to save changes');
		}
	}

	/**
	 * @param {KeyboardEvent} e
	 */
	function handleKeydown(e) {
		if (e.key === 'Enter') {
			e.preventDefault();
			stopEditing(true);
		} else if (e.key === 'Escape') {
			e.preventDefault();
			stopEditing(false);
		}
	}

	/**
	 * @param {string} rowId
	 * @param {string} columnKey
	 * @param {string} value
	 */
	async function updateSelectValue(rowId, columnKey, value) {
		await saveFieldValue(rowId, columnKey, value);
	}

	/**
	 * @param {number | null} value
	 */
	function formatAmount(value) {
		if (!value) return '-';
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
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
		const option = options.find(o => o.value === value);
		return option?.color ?? 'bg-gray-100 text-gray-600';
	}

	/**
	 * @param {string} value
	 * @param {{ value: string, label: string, color: string }[]} options
	 */
	function getOptionLabel(value, options) {
		const option = options.find(o => o.value === value);
		return option?.label ?? value;
	}

	// Row detail sheet functions
	/**
	 * @param {string} rowId
	 */
	function openRowSheet(rowId) {
		selectedRowId = rowId;
		sheetOpen = true;
	}

	function closeRowSheet() {
		sheetOpen = false;
		selectedRowId = null;
	}

	/**
	 * @param {string} key
	 * @param {any} value
	 */
	async function updateSelectedRowField(key, value) {
		if (!selectedRowId) return;
		await saveFieldValue(selectedRowId, key, value);
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
				closeRowSheet();
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

	// Drag-and-drop handlers
	/**
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
	 * @param {DragEvent} e
	 * @param {string} rowId
	 */
	function handleRowDragOver(e, rowId) {
		e.preventDefault();
		if (draggedRowId === rowId) return;

		dragOverRowId = rowId;

		// Determine drop position based on mouse position
		const rect = /** @type {HTMLElement} */ (e.currentTarget).getBoundingClientRect();
		const midpoint = rect.top + rect.height / 2;
		dropPosition = e.clientY < midpoint ? 'before' : 'after';
	}

	function handleRowDragLeave() {
		dragOverRowId = null;
		dropPosition = null;
	}

	/**
	 * @param {DragEvent} e
	 * @param {string} targetRowId
	 */
	function handleRowDrop(e, targetRowId) {
		e.preventDefault();
		// Note: Actual reordering would require backend support
		// For now, just reset the drag state
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

	/**
	 * Clear all filters
	 */
	function clearFilters() {
		searchQuery = '';
		stageFilter = 'ALL';
	}

	// Create new opportunity
	async function addNewRow() {
		isLoading = true;
		try {
			const form = new FormData();
			form.append('name', 'New Opportunity');
			form.append('stage', 'PROSPECTING');
			form.append('amount', '0');
			form.append('probability', '50');

			const response = await fetch('?/create', { method: 'POST', body: form });
			const result = await response.json();

			if (result.type === 'success' || result.data?.success) {
				toast.success('Opportunity created');
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

	// Get selected row data
	const selectedRow = $derived(filteredOpportunities.find((/** @type {any} */ r) => r.id === selectedRowId));
</script>

<svelte:head>
	<title>Opportunities - BottleCRM</title>
</svelte:head>

<PageHeader title="Opportunities" subtitle="Pipeline: {formatCurrency(stats.pipeline)}">
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<!-- Column Visibility Dropdown -->
			<DropdownMenu.Root>
					<DropdownMenu.Trigger asChild>
						{#snippet child({ props })}
							<Button {...props} variant="outline" size="sm" class="gap-2">
								<Eye class="h-4 w-4" />
								Columns
								{#if visibleColumns.length < columns.length}
									<span class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700">
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
								checked={isColumnVisible(column.key)}
								onCheckedChange={() => toggleColumn(column.key)}
							>
								{column.label}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>

			<FilterPopover activeCount={activeFiltersCount} onClear={clearFilters}>
				{#snippet children()}
					<div>
						<label for="stage-filter" class="mb-1.5 block text-sm font-medium">Stage</label>
						<select
							id="stage-filter"
							bind:value={stageFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							{#each stages as stage}
								<option value={stage.value}>{stage.label}</option>
							{/each}
						</select>
					</div>
				{/snippet}
			</FilterPopover>

			<Button onclick={addNewRow} disabled={isLoading}>
				<Plus class="mr-2 h-4 w-4" />
				New
			</Button>
		</div>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Table View -->
	<div class="min-h-screen bg-white dark:bg-gray-950 rounded-lg border border-gray-200 dark:border-gray-800">
			<!-- Table -->
			<div class="overflow-x-auto">
				<table class="w-full border-collapse">
					<!-- Header -->
					<thead>
						<tr class="border-b border-gray-100/60 dark:border-gray-800/60">
							<!-- Drag handle column -->
							<th class="w-8 px-1"></th>
							<!-- Expand button column -->
							<th class="w-8 px-1"></th>
							{#each columns as column (column.key)}
								{#if isColumnVisible(column.key)}
									<th class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 dark:text-gray-500 {column.width}">
										{column.label}
									</th>
								{/if}
							{/each}
						</tr>
					</thead>

					<!-- Body -->
					<tbody>
						{#if filteredOpportunities.length === 0}
							<tr>
								<td colspan={visibleColumns.length + 2} class="py-16 text-center">
									<div class="flex flex-col items-center justify-center">
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
								</td>
							</tr>
						{:else}
							{#each filteredOpportunities as row (row.id)}
								<!-- Drop indicator line (before row) -->
								{#if dragOverRowId === row.id && dropPosition === 'before'}
									<tr class="h-0">
										<td colspan={visibleColumns.length + 2} class="p-0">
											<div class="h-0.5 bg-blue-400 rounded-full mx-4"></div>
										</td>
									</tr>
								{/if}

								<tr
									class="group hover:bg-gray-50/30 dark:hover:bg-gray-900/30 transition-all duration-100 ease-out {draggedRowId === row.id ? 'opacity-40 bg-gray-100 dark:bg-gray-900' : ''}"
									ondragover={(e) => handleRowDragOver(e, row.id)}
									ondragleave={handleRowDragLeave}
									ondrop={(e) => handleRowDrop(e, row.id)}
								>
									<!-- Drag Handle -->
									<td class="w-8 px-1 py-3">
										<div
											draggable="true"
											ondragstart={(e) => handleDragStart(e, row.id)}
											ondragend={handleDragEnd}
											class="flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-40 hover:!opacity-70 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all cursor-grab active:cursor-grabbing"
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
											onclick={() => openRowSheet(row.id)}
											class="flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all duration-75"
										>
											<Expand class="h-3.5 w-3.5 text-gray-500" />
										</button>
									</td>

									{#each columns as column (column.key)}
										{#if isColumnVisible(column.key)}
											<td class="px-4 py-3 {column.width}">
												<!-- Text cells -->
												{#if column.type === 'text'}
													{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
														<input
															type="text"
															bind:value={editValue}
															onkeydown={handleKeydown}
															onblur={() => stopEditing(true)}
															data-edit-input="{row.id}-{column.key}"
															class="w-full px-2 py-1.5 text-sm bg-white dark:bg-gray-900 rounded outline-none ring-1 ring-gray-200 dark:ring-gray-700 focus:ring-blue-300 dark:focus:ring-blue-600 shadow-sm transition-shadow duration-100"
														/>
													{:else}
														<button
															type="button"
															onclick={() => {
																if (column.key === 'account' || column.key === 'owner') {
																	// These are read-only, open sheet instead
																	openRowSheet(row.id);
																} else {
																	startEditing(row.id, column.key);
																}
															}}
															class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 dark:text-gray-100 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 cursor-text transition-colors duration-75"
														>
															{#if column.key === 'account'}
																{#if row.account?.name}
																	{row.account.name}
																{:else}
																	<span class="text-gray-400">-</span>
																{/if}
															{:else if column.key === 'owner'}
																{#if row.owner?.name}
																	{row.owner.name}
																{:else}
																	<span class="text-gray-400">-</span>
																{/if}
															{:else if row[column.key]}
																{row[column.key]}
															{:else}
																<span class="text-gray-400">Empty</span>
															{/if}
														</button>
													{/if}

												<!-- Number cells -->
												{:else if column.type === 'number'}
													{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
														<input
															type="number"
															bind:value={editValue}
															onkeydown={handleKeydown}
															onblur={() => stopEditing(true)}
															data-edit-input="{row.id}-{column.key}"
															class="w-full px-2 py-1.5 text-sm bg-white dark:bg-gray-900 rounded outline-none ring-1 ring-gray-200 dark:ring-gray-700 focus:ring-blue-300 dark:focus:ring-blue-600 shadow-sm transition-shadow duration-100"
														/>
													{:else}
														<button
															type="button"
															onclick={() => startEditing(row.id, column.key)}
															class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 dark:text-gray-100 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 cursor-text transition-colors duration-75"
														>
															{#if column.key === 'amount'}
																{formatAmount(row[column.key])}
															{:else if column.key === 'probability'}
																{row[column.key] != null ? `${row[column.key]}%` : '-'}
															{:else}
																{row[column.key] ?? '-'}
															{/if}
														</button>
													{/if}

												<!-- Date cells -->
												{:else if column.type === 'date'}
													{#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key}
														<input
															type="date"
															bind:value={editValue}
															onkeydown={handleKeydown}
															onblur={() => stopEditing(true)}
															data-edit-input="{row.id}-{column.key}"
															class="w-full px-2 py-1.5 text-sm bg-white dark:bg-gray-900 rounded outline-none ring-1 ring-gray-200 dark:ring-gray-700 focus:ring-blue-300 dark:focus:ring-blue-600 shadow-sm transition-shadow duration-100"
														/>
													{:else}
														<button
															type="button"
															onclick={() => startEditing(row.id, column.key)}
															class="w-full text-left px-2 py-1.5 -mx-2 -my-1.5 rounded text-sm text-gray-900 dark:text-gray-100 hover:bg-gray-100/50 dark:hover:bg-gray-800/50 cursor-text transition-colors duration-75"
														>
															{formatDate(row[column.key])}
														</button>
													{/if}

												<!-- Select cells (Stage, Type) -->
												{:else if column.type === 'select'}
													<DropdownMenu.Root>
														<DropdownMenu.Trigger asChild>
															{#snippet child({ props })}
																<button
																	{...props}
																	type="button"
																	class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium {getOptionStyle(row[column.key], column.options)} hover:opacity-80 transition-opacity"
																>
																	{getOptionLabel(row[column.key], column.options)}
																	<ChevronDown class="h-3 w-3 opacity-60" />
																</button>
															{/snippet}
														</DropdownMenu.Trigger>
														<DropdownMenu.Content align="start" class="w-36">
															{#each column.options as option (option.value)}
																<DropdownMenu.Item
																	onclick={() => updateSelectValue(row.id, column.key, option.value)}
																	class="flex items-center gap-2"
																>
																	<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
																	{option.label}
																	{#if row[column.key] === option.value}
																		<Check class="h-4 w-4 ml-auto" />
																	{/if}
																</DropdownMenu.Item>
															{/each}
														</DropdownMenu.Content>
													</DropdownMenu.Root>
												{/if}
											</td>
										{/if}
									{/each}
								</tr>

								<!-- Drop indicator line (after row) -->
								{#if dragOverRowId === row.id && dropPosition === 'after'}
									<tr class="h-0">
										<td colspan={visibleColumns.length + 2} class="p-0">
											<div class="h-0.5 bg-blue-400 rounded-full mx-4"></div>
										</td>
									</tr>
								{/if}
							{/each}
						{/if}
					</tbody>
				</table>
			</div>

			<!-- Add row button at bottom -->
			{#if filteredOpportunities.length > 0}
				<div class="border-t border-gray-100 dark:border-gray-800 px-4 py-2">
					<button
						type="button"
						onclick={addNewRow}
						disabled={isLoading}
						class="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900 rounded transition-colors disabled:opacity-50"
					>
						<Plus class="h-4 w-4" />
						New row
					</button>
				</div>
			{/if}
		</div>
</div>

<!-- Row Detail Sheet (Notion-style) -->
<Sheet.Root bind:open={sheetOpen} onOpenChange={(open) => !open && closeRowSheet()}>
	<Sheet.Content side="right" class="w-[440px] sm:max-w-[440px] p-0 overflow-hidden">
		{#if selectedRow}
			<div class="h-full flex flex-col">
				<!-- Header with close button -->
				<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800">
					<span class="text-sm text-gray-500">Opportunity</span>
					<button onclick={closeRowSheet} class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-75">
						<X class="h-4 w-4 text-gray-400" />
					</button>
				</div>

				<!-- Scrollable content -->
				<div class="flex-1 overflow-y-auto">
					<!-- Title section -->
					<div class="px-6 pt-6 pb-4">
						<input
							type="text"
							value={selectedRow.name}
							oninput={(e) => updateSelectedRowField('name', /** @type {HTMLInputElement} */ (e.target).value)}
							placeholder="Untitled"
							class="w-full text-2xl font-semibold bg-transparent border-0 outline-none focus:ring-0 placeholder:text-gray-300 dark:placeholder:text-gray-600 text-gray-900 dark:text-gray-100"
						/>
					</div>

					<!-- Properties section -->
					<div class="px-4 pb-6">
						<!-- Account property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Building2 class="h-4 w-4 text-gray-400" />
								Account
							</div>
							<div class="flex-1 min-w-0">
								<span class="px-2 py-1 text-sm text-gray-900 dark:text-gray-100">
									{selectedRow.account?.name || '-'}
								</span>
							</div>
						</div>

						<!-- Stage property (select) -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Target class="h-4 w-4 text-gray-400" />
								Stage
							</div>
							<div class="flex-1">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger asChild>
										{#snippet child({ props })}
											<button
												{...props}
												type="button"
												class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-sm {getOptionStyle(selectedRow.stage, stageOptions)} hover:opacity-90 transition-opacity"
											>
												<span class="w-2 h-2 rounded-full {getOptionStyle(selectedRow.stage, stageOptions).split(' ')[0]}"></span>
												{getOptionLabel(selectedRow.stage, stageOptions)}
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="start" class="w-36">
										{#each stageOptions as option (option.value)}
											<DropdownMenu.Item
												onclick={() => updateSelectedRowField('stage', option.value)}
												class="flex items-center gap-2"
											>
												<span class="w-2 h-2 rounded-full {option.color.split(' ')[0]}"></span>
												{option.label}
												{#if selectedRow.stage === option.value}
													<Check class="h-4 w-4 ml-auto" />
												{/if}
											</DropdownMenu.Item>
										{/each}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>

						<!-- Type property (select) -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Briefcase class="h-4 w-4 text-gray-400" />
								Type
							</div>
							<div class="flex-1">
								<DropdownMenu.Root>
									<DropdownMenu.Trigger asChild>
										{#snippet child({ props })}
											<button
												{...props}
												type="button"
												class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-sm {getOptionStyle(selectedRow.opportunityType, typeOptions)} hover:opacity-90 transition-opacity"
											>
												{getOptionLabel(selectedRow.opportunityType, typeOptions) || 'Select type'}
											</button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="start" class="w-40">
										{#each typeOptions as option (option.value)}
											<DropdownMenu.Item
												onclick={() => updateSelectedRowField('opportunityType', option.value)}
												class="flex items-center gap-2"
											>
												{option.label}
												{#if selectedRow.opportunityType === option.value}
													<Check class="h-4 w-4 ml-auto" />
												{/if}
											</DropdownMenu.Item>
										{/each}
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</div>
						</div>

						<!-- Amount property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<DollarSign class="h-4 w-4 text-gray-400" />
								Amount
							</div>
							<div class="flex-1 min-w-0">
								<div class="flex items-center">
									<span class="text-sm text-gray-500 mr-1">$</span>
									<input
										type="number"
										value={selectedRow.amount || 0}
										oninput={(e) => updateSelectedRowField('amount', parseFloat(/** @type {HTMLInputElement} */ (e.target).value) || 0)}
										placeholder="0"
										class="w-full px-1 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-900 rounded transition-colors placeholder:text-gray-400 text-gray-900 dark:text-gray-100"
									/>
								</div>
							</div>
						</div>

						<!-- Probability property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Percent class="h-4 w-4 text-gray-400" />
								Probability
							</div>
							<div class="flex-1 min-w-0">
								<div class="flex items-center">
									<input
										type="number"
										value={selectedRow.probability || 0}
										min="0"
										max="100"
										oninput={(e) => updateSelectedRowField('probability', parseInt(/** @type {HTMLInputElement} */ (e.target).value) || 0)}
										placeholder="0"
										class="w-20 px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-900 rounded transition-colors placeholder:text-gray-400 text-gray-900 dark:text-gray-100"
									/>
									<span class="text-sm text-gray-500">%</span>
								</div>
							</div>
						</div>

						<!-- Close Date property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<Calendar class="h-4 w-4 text-gray-400" />
								Close Date
							</div>
							<div class="flex-1 min-w-0">
								<input
									type="date"
									value={selectedRow.closedOn?.split('T')[0] || ''}
									oninput={(e) => updateSelectedRowField('closedOn', /** @type {HTMLInputElement} */ (e.target).value)}
									class="w-full px-2 py-1 text-sm bg-transparent border-0 outline-none focus:bg-gray-50 dark:focus:bg-gray-900 rounded transition-colors text-gray-900 dark:text-gray-100"
								/>
							</div>
						</div>

						<!-- Owner property -->
						<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
							<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
								<User class="h-4 w-4 text-gray-400" />
								Owner
							</div>
							<div class="flex-1 min-w-0">
								<span class="px-2 py-1 text-sm text-gray-900 dark:text-gray-100">
									{selectedRow.owner?.name || 'Unassigned'}
								</span>
							</div>
						</div>

						<!-- Lead Source property -->
						{#if selectedRow.leadSource}
							<div class="flex items-center min-h-[36px] px-2 -mx-2 rounded hover:bg-gray-50/60 dark:hover:bg-gray-900/60 transition-colors duration-75 group">
								<div class="w-28 shrink-0 flex items-center gap-2 text-[13px] text-gray-500">
									<Globe class="h-4 w-4 text-gray-400" />
									Source
								</div>
								<div class="flex-1 min-w-0">
									<span class="px-2 py-1 text-sm text-gray-900 dark:text-gray-100">
										{selectedRow.leadSource}
									</span>
								</div>
							</div>
						{/if}
					</div>
				</div>

				<!-- Footer with delete -->
				<div class="px-4 py-3 border-t border-gray-100 dark:border-gray-800 mt-auto">
					<button
						onclick={deleteSelectedRow}
						disabled={isLoading}
						class="flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors duration-75 disabled:opacity-50"
					>
						<Trash2 class="h-4 w-4" />
						Delete
					</button>
				</div>
			</div>
		{/if}
	</Sheet.Content>
</Sheet.Root>
