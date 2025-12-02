<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		Eye,
		Expand,
		GripVertical,
		ChevronDown,
		Check,
		Briefcase,
		Building2,
		User,
		Calendar,
		Flag,
		AlertCircle,
		CheckCircle,
		RotateCcw,
		Tag
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { CaseDrawer } from '$lib/components/cases';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { cn } from '$lib/utils.js';
	import { formatRelativeDate } from '$lib/utils/formatting.js';
	import {
		getCaseStatusClass,
		getPriorityClass,
		getCaseTypeClass,
		formatStatusDisplay
	} from '$lib/utils/ui-helpers.js';
	import {
		CASE_STATUSES as statuses,
		CASE_TYPES as caseTypes,
		PRIORITIES as priorities
	} from '$lib/constants/filters.js';
	import { useDrawerState, useListFilters } from '$lib/hooks';

	// Column visibility configuration
	const STORAGE_KEY = 'cases-column-config';

	// Column definitions
	const columns = [
		{ key: 'case', label: 'Case', width: 'w-[300px]' },
		{ key: 'account', label: 'Account', width: 'w-40' },
		{ key: 'type', label: 'Type', width: 'w-28' },
		{ key: 'assignedTo', label: 'Assigned To', width: 'w-36' },
		{ key: 'priority', label: 'Priority', width: 'w-28' },
		{ key: 'status', label: 'Status', width: 'w-28' },
		{ key: 'created', label: 'Created', width: 'w-32' }
	];

	// Column visibility state - all columns visible by default
	let visibleColumns = $state(columns.map((c) => c.key));

	// Drag-and-drop state
	let draggedRowId = $state(null);
	let dragOverRowId = $state(null);
	/** @type {'before' | 'after' | null} */
	let dropPosition = $state(null);

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
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	let casesData = $state(data.cases || []);
	const accounts = $derived(data.allAccounts || []);
	const users = $derived(data.allUsers || []);
	const contacts = $derived(data.allContacts || []);
	const teams = $derived(data.allTeams || []);

	// Sync casesData when data changes
	$effect(() => {
		casesData = data.cases || [];
	});

	// Drawer state using hook
	const drawer = useDrawerState();

	// Filter/search/sort state using hook
	const list = useListFilters({
		searchFields: ['subject', 'description', 'account.name'],
		filters: [
			{
				key: 'statusFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.status === value
			},
			{
				key: 'priorityFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.priority === value
			},
			{
				key: 'accountFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.account?.id === value
			}
		],
		defaultSortColumn: 'createdAt',
		defaultSortDirection: 'desc'
	});

	// Filtered and sorted cases
	const filteredCases = $derived(list.filterAndSort(casesData));
	const activeFiltersCount = $derived(list.getActiveFilterCount());

	const accountOptions = $derived([
		{ value: 'ALL', label: 'All Accounts' },
		...accounts.map((/** @type {any} */ acc) => ({ value: acc.id, label: acc.name }))
	]);

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
		priority: 'Normal',
		caseType: '',
		status: 'New',
		dueDate: '',
		caseId: ''
	});

	/**
	 * Get status icon
	 * @param {string} status
	 */
	function getStatusIcon(status) {
		const upperStatus = status?.toUpperCase();
		if (upperStatus === 'CLOSED') return CheckCircle;
		if (upperStatus === 'IN_PROGRESS' || upperStatus === 'IN PROGRESS') return RotateCcw;
		return AlertCircle;
	}

	/**
	 * Handle save from drawer (receives API-formatted data)
	 * @param {any} apiData
	 */
	async function handleSave(apiData) {
		// Convert API format to form state
		formState.title = apiData.name || '';
		formState.description = apiData.description || '';
		formState.accountId = apiData.account || '';
		formState.assignedTo = apiData.assigned_to || [];
		formState.contacts = apiData.contacts || [];
		formState.teams = apiData.teams || [];
		formState.priority = apiData.priority || 'Normal';
		formState.caseType = apiData.case_type || '';
		formState.status = apiData.status || drawer.selected?.status || 'New';
		formState.dueDate = apiData.closed_on || '';

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
				if (result.type === 'success') {
					toast.success(successMessage);
					if (closeDetailDrawer) {
						drawer.closeDetail();
					} else {
						drawer.closeForm();
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

	// Form options for drawers
	const formOptions = $derived({
		accounts: accounts.map((/** @type {any} */ acc) => ({ id: acc.id, name: acc.name })),
		users: users.map((/** @type {any} */ user) => ({ id: user.id, name: user.name })),
		contacts: contacts.map((/** @type {any} */ contact) => ({
			id: contact.id,
			name: contact.name,
			email: contact.email
		})),
		teams: teams.map((/** @type {any} */ team) => ({ id: team.id, name: team.name }))
	});

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
		if (!draggedRowId || draggedRowId === targetRowId) {
			resetDragState();
			return;
		}

		const draggedIndex = casesData.findIndex((/** @type {any} */ r) => r.id === draggedRowId);
		const targetIndex = casesData.findIndex((/** @type {any} */ r) => r.id === targetRowId);

		if (draggedIndex === -1 || targetIndex === -1) {
			resetDragState();
			return;
		}

		// Create new array and reorder
		const newData = [...casesData];
		const [draggedItem] = newData.splice(draggedIndex, 1);

		// Calculate insert position
		let insertIndex = targetIndex;
		if (dropPosition === 'after') {
			insertIndex = draggedIndex < targetIndex ? targetIndex : targetIndex + 1;
		} else {
			insertIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
		}

		newData.splice(insertIndex, 0, draggedItem);
		casesData = newData;

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
</script>

<svelte:head>
	<title>Cases - BottleCRM</title>
</svelte:head>

<PageHeader title="Cases" subtitle="{filteredCases.length} of {casesData.length} cases">
	{#snippet actions()}
		<!-- Column Visibility Dropdown -->
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Button {...props} variant="outline" size="sm" class="gap-2">
						<Eye class="h-4 w-4" />
						Columns
						{#if visibleColumns.length < columns.length}
							<span
								class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700"
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
						checked={isColumnVisible(column.key)}
						onCheckedChange={() => toggleColumn(column.key)}
					>
						{column.label}
					</DropdownMenu.CheckboxItem>
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
							{#each statuses as status}
								<option value={status.value}>{status.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label for="priority-filter" class="mb-1.5 block text-sm font-medium">Priority</label>
						<select
							id="priority-filter"
							bind:value={list.filters.priorityFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							{#each priorities as priority}
								<option value={priority.value}>{priority.label}</option>
							{/each}
						</select>
					</div>
					<div>
						<label for="account-filter" class="mb-1.5 block text-sm font-medium">Account</label>
						<select
							id="account-filter"
							bind:value={list.filters.accountFilter}
							class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
						>
							{#each accountOptions as account}
								<option value={account.value}>{account.label}</option>
							{/each}
						</select>
					</div>
				</div>
			{/snippet}
		</FilterPopover>
		<Button onclick={drawer.openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Case
		</Button>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Cases Table -->
	<Card.Root class="border-0 shadow-sm">
		<Card.Content class="p-0">
			{#if filteredCases.length === 0}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<Briefcase class="text-muted-foreground/50 mb-4 h-12 w-12" />
					<h3 class="text-foreground text-lg font-medium">No cases found</h3>
					<p class="text-muted-foreground mt-1 text-sm">
						Try adjusting your search criteria or create a new case.
					</p>
					<Button onclick={drawer.openCreate} class="mt-4" disabled={false}>
						<Plus class="mr-2 h-4 w-4" />
						Create New Case
					</Button>
				</div>
			{:else}
				<!-- Desktop Table - Notion Style -->
				<div class="hidden md:block">
					<div class="overflow-x-auto">
						<table class="w-full border-collapse">
							<!-- Header -->
							<thead>
								<tr class="border-b border-gray-100/60">
									<!-- Drag handle column -->
									<th class="w-8 px-1"></th>
									<!-- Expand button column -->
									<th class="w-8 px-1"></th>
									{#each columns as column (column.key)}
										{#if isColumnVisible(column.key)}
											<th
												class="px-4 py-3 text-left text-[13px] font-normal text-gray-400 {column.width}"
											>
												{column.label}
											</th>
										{/if}
									{/each}
								</tr>
							</thead>

							<!-- Body -->
							<tbody>
								{#each filteredCases as caseItem (caseItem.id)}
									{@const StatusIcon = getStatusIcon(caseItem.status)}

									<!-- Drop indicator line (before row) -->
									{#if dragOverRowId === caseItem.id && dropPosition === 'before'}
										<tr class="h-0">
											<td colspan={visibleColumns.length + 2} class="p-0">
												<div class="mx-4 h-0.5 rounded-full bg-blue-400"></div>
											</td>
										</tr>
									{/if}

									<tr
										class="group transition-all duration-100 ease-out hover:bg-gray-50/30 {draggedRowId ===
										caseItem.id
											? 'bg-gray-100 opacity-40'
											: ''}"
										ondragover={(e) => handleRowDragOver(e, caseItem.id)}
										ondragleave={handleRowDragLeave}
										ondrop={(e) => handleRowDrop(e, caseItem.id)}
									>
										<!-- Drag Handle -->
										<td class="w-8 px-1 py-3">
											<div
												draggable="true"
												ondragstart={(e) => handleDragStart(e, caseItem.id)}
												ondragend={handleDragEnd}
												class="flex h-6 w-6 cursor-grab items-center justify-center rounded opacity-0 transition-all hover:bg-gray-200 hover:!opacity-70 group-hover:opacity-40 active:cursor-grabbing"
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
												onclick={() => drawer.openDetail(caseItem)}
												class="flex h-6 w-6 items-center justify-center rounded opacity-0 transition-all duration-75 hover:bg-gray-200 group-hover:opacity-100"
											>
												<Expand class="h-3.5 w-3.5 text-gray-500" />
											</button>
										</td>

										{#if isColumnVisible('case')}
											<td class="w-[300px] px-4 py-3">
												<button
													type="button"
													onclick={() => drawer.openDetail(caseItem)}
													class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left transition-colors duration-75 hover:bg-gray-100/50"
												>
													<div class="flex items-center gap-3">
														<div
															class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600"
														>
															<Briefcase class="h-4 w-4 text-white" />
														</div>
														<div class="min-w-0">
															<p class="text-foreground truncate text-sm font-medium">
																{caseItem.subject}
															</p>
															{#if caseItem.description}
																<p class="text-muted-foreground line-clamp-1 text-xs">
																	{caseItem.description}
																</p>
															{/if}
														</div>
													</div>
												</button>
											</td>
										{/if}

										{#if isColumnVisible('account')}
											<td class="w-40 px-4 py-3">
												{#if caseItem.account}
													<div class="flex items-center gap-1.5 text-sm">
														<Building2 class="text-muted-foreground h-4 w-4" />
														<span class="truncate">{caseItem.account.name}</span>
													</div>
												{:else}
													<span class="text-gray-400">Empty</span>
												{/if}
											</td>
										{/if}

										{#if isColumnVisible('type')}
											<td class="w-28 px-4 py-3">
												{#if caseItem.caseType}
													<span
														class={cn(
															'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
															getCaseTypeClass(caseItem.caseType)
														)}
													>
														{caseItem.caseType}
													</span>
												{:else}
													<span class="text-gray-400">Empty</span>
												{/if}
											</td>
										{/if}

										{#if isColumnVisible('assignedTo')}
											<td class="w-36 px-4 py-3">
												{#if caseItem.owner}
													<div class="flex items-center gap-1.5 text-sm">
														<User class="text-muted-foreground h-4 w-4" />
														<span class="truncate">{caseItem.owner.name}</span>
													</div>
												{:else}
													<span class="text-gray-400">Unassigned</span>
												{/if}
											</td>
										{/if}

										{#if isColumnVisible('priority')}
											<td class="w-28 px-4 py-3">
												{#if caseItem.priority}
													<span
														class={cn(
															'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
															getPriorityClass(caseItem.priority)
														)}
													>
														{caseItem.priority}
													</span>
												{:else}
													<span class="text-gray-400">Empty</span>
												{/if}
											</td>
										{/if}

										{#if isColumnVisible('status')}
											<td class="w-28 px-4 py-3">
												<span
													class={cn(
														'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
														getCaseStatusClass(caseItem.status)
													)}
												>
													<StatusIcon class="h-3 w-3" />
													{formatStatusDisplay(caseItem.status)}
												</span>
											</td>
										{/if}

										{#if isColumnVisible('created')}
											<td class="w-32 px-4 py-3">
												<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
													<Calendar class="h-3.5 w-3.5" />
													<span>{formatRelativeDate(caseItem.createdAt)}</span>
												</div>
											</td>
										{/if}
									</tr>

									<!-- Drop indicator line (after row) -->
									{#if dragOverRowId === caseItem.id && dropPosition === 'after'}
										<tr class="h-0">
											<td colspan={visibleColumns.length + 2} class="p-0">
												<div class="mx-4 h-0.5 rounded-full bg-blue-400"></div>
											</td>
										</tr>
									{/if}
								{/each}
							</tbody>
						</table>
					</div>
				</div>

				<!-- Add row button at bottom -->
				<div class="hidden border-t border-gray-100 px-4 py-2 md:block">
					<button
						type="button"
						onclick={drawer.openCreate}
						class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
					>
						<Plus class="h-4 w-4" />
						New row
					</button>
				</div>

				<!-- Mobile Card View -->
				<div class="divide-y md:hidden">
					{#each filteredCases as caseItem (caseItem.id)}
						{@const StatusIcon = getStatusIcon(caseItem.status)}
						<button
							type="button"
							class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left"
							onclick={() => drawer.openDetail(caseItem)}
						>
							<div
								class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600"
							>
								<Briefcase class="h-5 w-5 text-white" />
							</div>
							<div class="min-w-0 flex-1">
								<div class="flex items-start justify-between gap-2">
									<div>
										<p class="text-foreground font-medium">{caseItem.subject}</p>
										{#if caseItem.account}
											<p class="text-muted-foreground text-sm">{caseItem.account.name}</p>
										{/if}
									</div>
									<span
										class={cn(
											'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
											getCaseStatusClass(caseItem.status)
										)}
									>
										{formatStatusDisplay(caseItem.status)}
									</span>
								</div>
								<div class="text-muted-foreground mt-2 flex flex-wrap items-center gap-3 text-sm">
									{#if caseItem.caseType}
										<span
											class={cn(
												'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
												getCaseTypeClass(caseItem.caseType)
											)}
										>
											<Tag class="h-3 w-3" />
											{caseItem.caseType}
										</span>
									{/if}
									{#if caseItem.priority}
										<span
											class={cn(
												'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
												getPriorityClass(caseItem.priority)
											)}
										>
											<Flag class="h-3 w-3" />
											{caseItem.priority}
										</span>
									{/if}
									<div class="flex items-center gap-1">
										<Calendar class="h-3.5 w-3.5" />
										<span>{formatRelativeDate(caseItem.createdAt)}</span>
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

<!-- Case Drawer (unified view/create/edit) -->
<CaseDrawer
	bind:open={drawer.detailOpen}
	caseItem={drawer.selected}
	mode={drawer.mode === 'create' ? 'create' : 'view'}
	loading={drawer.loading}
	options={formOptions}
	onSave={handleSave}
	onDelete={handleDelete}
	onClose={handleClose}
	onReopen={handleReopen}
	onCancel={() => drawer.closeAll()}
/>

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
	<input type="hidden" name="accountId" value={formState.accountId} />
	<input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
	<input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
	<input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
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
