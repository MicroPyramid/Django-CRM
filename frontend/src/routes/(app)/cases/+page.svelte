<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Search,
		Filter,
		Plus,
		ChevronDown,
		ChevronUp,
		Briefcase,
		Building2,
		User,
		Calendar,
		Flag,
		MoreHorizontal,
		Eye,
		AlertCircle,
		CheckCircle,
		RotateCcw,
		Tag
	} from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { CaseDrawer } from '$lib/components/cases';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
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

	/** @type {{ data: any }} */
	let { data } = $props();

	// Computed values
	const cases = $derived(data.cases || []);
	const accounts = $derived(data.allAccounts || []);
	const users = $derived(data.allUsers || []);
	const contacts = $derived(data.allContacts || []);
	const teams = $derived(data.allTeams || []);

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
	const filteredCases = $derived(list.filterAndSort(cases));
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
</script>

<svelte:head>
	<title>Cases - BottleCRM</title>
</svelte:head>

<PageHeader title="Cases" subtitle="{filteredCases.length} of {cases.length} cases">
	{#snippet actions()}
		<Button onclick={drawer.openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Case
		</Button>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Search and Filters -->
	<Card.Root>
		<Card.Content class="p-4">
			<div class="flex flex-col gap-4 sm:flex-row">
				<div class="relative flex-1">
					<Search class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
					<Input
						type="text"
						placeholder="Search by subject, description, or account..."
						bind:value={list.searchQuery}
						class="pl-9"
					/>
				</div>
				<Button
					variant="outline"
					onclick={() => (list.showFilters = !list.showFilters)}
					class="shrink-0"
					disabled={false}
				>
					<Filter class="mr-2 h-4 w-4" />
					Filters
					{#if activeFiltersCount > 0}
						<Badge variant="secondary" class="ml-2">{activeFiltersCount}</Badge>
					{/if}
					{#if list.showFilters}
						<ChevronUp class="ml-2 h-4 w-4" />
					{:else}
						<ChevronDown class="ml-2 h-4 w-4" />
					{/if}
				</Button>
			</div>

			{#if list.showFilters}
				<div class="bg-muted/50 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 sm:grid-cols-4">
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
					<div class="flex items-end">
						<Button variant="ghost" onclick={list.clearFilters} class="w-full" disabled={false}>
							Clear Filters
						</Button>
					</div>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Cases Table -->
	<Card.Root>
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
				<!-- Desktop Table -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head class="w-[300px]">Case</Table.Head>
								<Table.Head>Account</Table.Head>
								<Table.Head>Type</Table.Head>
								<Table.Head>Assigned To</Table.Head>
								<Table.Head>Priority</Table.Head>
								<Table.Head>Status</Table.Head>
								<Table.Head
									class="hover:bg-muted/50 cursor-pointer"
									onclick={() => list.toggleSort('createdAt')}
								>
									<div class="flex items-center gap-1">
										Created
										{#if list.sortColumn === 'createdAt'}
											{#if list.sortDirection === 'asc'}
												<ChevronUp class="h-4 w-4" />
											{:else}
												<ChevronDown class="h-4 w-4" />
											{/if}
										{/if}
									</div>
								</Table.Head>
								<Table.Head class="w-[80px]">Actions</Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each filteredCases as caseItem (caseItem.id)}
								{@const StatusIcon = getStatusIcon(caseItem.status)}
								<Table.Row
									class="hover:bg-muted/50 cursor-pointer"
									onclick={() => drawer.openDetail(caseItem)}
								>
									<Table.Cell>
										<div class="flex items-center gap-3">
											<div
												class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600"
											>
												<Briefcase class="h-4 w-4 text-white" />
											</div>
											<div class="min-w-0">
												<p class="text-foreground truncate font-medium">
													{caseItem.subject}
												</p>
												{#if caseItem.description}
													<p class="text-muted-foreground line-clamp-1 text-sm">
														{caseItem.description}
													</p>
												{/if}
											</div>
										</div>
									</Table.Cell>
									<Table.Cell>
										{#if caseItem.account}
											<div class="flex items-center gap-1.5 text-sm">
												<Building2 class="text-muted-foreground h-4 w-4" />
												<span class="truncate">{caseItem.account.name}</span>
											</div>
										{:else}
											<span class="text-muted-foreground">-</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
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
										{:else}
											<span class="text-muted-foreground">-</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
										{#if caseItem.owner}
											<div class="flex items-center gap-1.5 text-sm">
												<User class="text-muted-foreground h-4 w-4" />
												<span class="truncate">{caseItem.owner.name}</span>
											</div>
										{:else}
											<span class="text-muted-foreground">Unassigned</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
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
										{:else}
											<span class="text-muted-foreground">-</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
										<span
											class={cn(
												'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
												getCaseStatusClass(caseItem.status)
											)}
										>
											<StatusIcon class="h-3 w-3" />
											{formatStatusDisplay(caseItem.status)}
										</span>
									</Table.Cell>
									<Table.Cell>
										<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
											<Calendar class="h-3.5 w-3.5" />
											<span>{formatRelativeDate(caseItem.createdAt)}</span>
										</div>
									</Table.Cell>
									<Table.Cell onclick={(e) => e.stopPropagation()}>
										<DropdownMenu.Root>
											<DropdownMenu.Trigger>
												<Button variant="ghost" size="icon" class="h-8 w-8" disabled={false}>
													<MoreHorizontal class="h-4 w-4" />
												</Button>
											</DropdownMenu.Trigger>
											<DropdownMenu.Content align="end">
												<DropdownMenu.Item onclick={() => drawer.openDetail(caseItem)}>
													<Eye class="mr-2 h-4 w-4" />
													View Details
												</DropdownMenu.Item>
												<DropdownMenu.Item
													onclick={() => {
														drawer.selected = caseItem;
														drawer.openEdit();
													}}
												>
													Edit
												</DropdownMenu.Item>
												<DropdownMenu.Separator />
												<DropdownMenu.Item class="text-destructive">Delete</DropdownMenu.Item>
											</DropdownMenu.Content>
										</DropdownMenu.Root>
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
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
