<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
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
		Eye
	} from '@lucide/svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { NotionTable } from '$lib/components/ui/notion-table';
	import { NotionDrawer } from '$lib/components/ui/notion-drawer';
	import {
		caseStatusOptions,
		caseTypeOptions,
		priorityOptions
	} from '$lib/utils/table-helpers.js';
	import { useDrawerState, useListFilters } from '$lib/hooks';

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

	// NotionTable column configuration
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
		{ key: 'caseType', label: 'Type', type: 'select', options: caseTypeOptions, width: 'w-28' },
		{
			key: 'owner',
			label: 'Assigned To',
			type: 'relation',
			relationIcon: 'user',
			width: 'w-36',
			getValue: (/** @type {any} */ row) => row.owner
		},
		{ key: 'priority', label: 'Priority', type: 'select', options: priorityOptions, width: 'w-28' },
		{ key: 'status', label: 'Status', type: 'select', options: caseStatusOptions, width: 'w-28' },
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
	let casesData = $state(data.cases || []);
	const accounts = $derived(data.allAccounts || []);
	const users = $derived(data.allUsers || []);
	const contacts = $derived(data.allContacts || []);
	const teams = $derived(data.allTeams || []);
	const tags = $derived(data.allTags || []);

	// Sync casesData when data changes
	$effect(() => {
		casesData = data.cases || [];
	});

	// Drawer state using hook
	const drawer = useDrawerState();

	// Account options for drawer select
	const accountOptions = $derived([
		{ value: '', label: 'None', color: 'bg-gray-100 text-gray-600' },
		...accounts.map((/** @type {any} */ a) => ({ value: a.id, label: a.name, color: 'bg-blue-100 text-blue-700' }))
	]);

	// Drawer columns configuration (with icons and multiselect)
	const drawerColumns = $derived([
		{ key: 'subject', label: 'Case Title', type: 'text' },
		{
			key: 'accountId',
			label: 'Account',
			type: 'select',
			icon: Building2,
			options: accountOptions,
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
			options: priorityOptions
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
					accountId: '',
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
					await invalidateAll();
				} else if (result.type === 'failure') {
					toast.error(result.data?.error || 'Operation failed');
				} else if (result.type === 'error') {
					toast.error('An unexpected error occurred');
				}
			};
		};
	}

	// NotionTable callbacks
	/**
	 * Handle inline cell edits (client-side only for now)
	 * @param {any} row
	 * @param {string} field
	 * @param {any} value
	 */
	function handleRowChange(row, field, value) {
		const index = casesData.findIndex((/** @type {any} */ c) => c.id === row.id);
		if (index !== -1) {
			casesData[index] = { ...casesData[index], [field]: value };
		}
	}
</script>

<svelte:head>
	<title>Cases - BottleCRM</title>
</svelte:head>

<div class="min-h-screen rounded-lg border border-border/40 bg-white dark:bg-gray-950">
	<!-- Header -->
	<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-800">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">Cases</h1>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{filteredCases.length} items</p>
			</div>
			<div class="flex items-center gap-2">
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button {...props} variant="outline" size="sm" class="gap-2">
								<Eye class="h-4 w-4" />
								Columns
								{#if columnCounts.visible < columnCounts.total}
									<span
										class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700"
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

				<Button size="sm" class="gap-2" onclick={drawer.openCreate}>
					<Plus class="h-4 w-4" />
					New
				</Button>
			</div>
		</div>
	</div>

	<!-- Table -->
	<div class="overflow-x-auto">
		<NotionTable
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
					<p class="text-muted-foreground mt-1 text-sm">Create a new case to get started.</p>
					<Button onclick={drawer.openCreate} class="mt-4">
						<Plus class="mr-2 h-4 w-4" />
						Create New Case
					</Button>
				</div>
			{/snippet}
		</NotionTable>
	</div>

	<!-- Add row button at bottom -->
	{#if filteredCases.length > 0}
		<div class="border-t border-gray-100 px-4 py-2 dark:border-gray-800">
			<button
				type="button"
				onclick={drawer.openCreate}
				class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-300"
			>
				<Plus class="h-4 w-4" />
				New row
			</button>
		</div>
	{/if}
</div>

<!-- Case Drawer (using NotionDrawer) -->
<NotionDrawer
	bind:open={drawer.detailOpen}
	onOpenChange={(open) => !open && drawer.closeAll()}
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
				<div class="flex items-center gap-2 mb-3">
					<Activity class="h-4 w-4 text-gray-400" />
					<p class="text-xs font-medium tracking-wider uppercase text-gray-500">Activity</p>
				</div>
				{#each drawer.selected.comments.slice(0, 5) as comment (comment.id)}
					<div class="flex gap-3">
						<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-gray-800">
							<MessageSquare class="h-4 w-4 text-gray-400" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-sm text-gray-900 dark:text-gray-100">
								<span class="font-medium">{comment.author?.name || 'Unknown'}</span>
								{' '}added a note
							</p>
							<p class="text-xs text-gray-500 mt-0.5">
								{new Date(comment.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
							</p>
							<p class="text-sm text-gray-500 mt-1 line-clamp-2">{comment.body}</p>
						</div>
					</div>
				{/each}
			</div>
		{:else if drawer.mode !== 'create'}
			<div class="flex flex-col items-center justify-center py-6 text-center">
				<MessageSquare class="h-8 w-8 text-gray-300 mb-2" />
				<p class="text-sm text-gray-500">No activity yet</p>
			</div>
		{/if}
	{/snippet}

	{#snippet footerActions()}
		{#if drawer.mode !== 'create' && drawer.selected}
			{#if drawerFormData.status === 'Closed'}
				<Button variant="outline" onclick={handleReopen} disabled={isSubmitting}>
					Reopen
				</Button>
			{:else}
				<Button variant="outline" onclick={handleClose} disabled={isSubmitting}>
					Close Case
				</Button>
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
</NotionDrawer>

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
	<input type="hidden" name="accountId" value={formState.accountId} />
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
