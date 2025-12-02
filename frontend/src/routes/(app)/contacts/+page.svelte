<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { page } from '$app/stores';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		ChevronDown,
		ChevronUp,
		Eye,
		Expand,
		GripVertical,
		User
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { ContactDrawer } from '$lib/components/contacts';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { formatRelativeDate, formatPhone, getNameInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import { goto } from '$app/navigation';

	// Column visibility configuration
	const STORAGE_KEY = 'contacts-column-config';

	// Column definitions
	const columns = [
		{ key: 'contact', label: 'Contact', width: 'w-48' },
		{ key: 'title', label: 'Title', width: 'w-36' },
		{ key: 'email', label: 'Email', width: 'w-52' },
		{ key: 'phone', label: 'Phone', width: 'w-36' },
		{ key: 'company', label: 'Company', width: 'w-40' },
		{ key: 'owner', label: 'Owner', width: 'w-36' },
		{ key: 'created', label: 'Created', width: 'w-32' }
	];

	// Column visibility state
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
		if (key === 'contact') return; // Don't allow hiding contact column
		if (visibleColumns.includes(key)) {
			visibleColumns = visibleColumns.filter((k) => k !== key);
		} else {
			visibleColumns = [...visibleColumns, key];
		}
	}

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	// Computed values from data
	const contacts = $derived(data.contacts || []);
	const owners = $derived(data.owners || []);

	// Drawer state (simplified - single drawer)
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {any} */
	let selectedContact = $state(null);
	let drawerLoading = $state(false);


	// Drag-and-drop state
	let draggedRowId = $state(null);
	let dragOverRowId = $state(null);
	/** @type {'before' | 'after' | null} */
	let dropPosition = $state(null);

	// URL sync
	$effect(() => {
		const viewId = $page.url.searchParams.get('view');
		const action = $page.url.searchParams.get('action');

		if (action === 'create') {
			selectedContact = null;
			drawerMode = 'create';
			drawerOpen = true;
		} else if (viewId && contacts.length > 0) {
			const contact = contacts.find((c) => c.id === viewId);
			if (contact) {
				selectedContact = contact;
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
	 * Open drawer for viewing/editing a contact
	 * @param {any} contact
	 */
	function openContact(contact) {
		selectedContact = contact;
		drawerMode = 'view';
		drawerOpen = true;
		updateUrl(contact.id, null);
	}

	/**
	 * Open drawer for creating a new contact
	 */
	function openCreate() {
		selectedContact = null;
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
		// Note: For contacts, we'd need to implement reordering via API
		// For now, just reset drag state
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

	// Filter/search/sort state
	const list = useListFilters({
		searchFields: ['firstName', 'lastName', 'email', 'phone', 'title', 'organization'],
		filters: [
			{
				key: 'ownerFilter',
				defaultValue: 'ALL',
				match: (item, value) => value === 'ALL' || item.owner?.id === value
			}
		],
		defaultSortColumn: 'createdAt',
		defaultSortDirection: 'desc'
	});

	// Filtered and sorted contacts
	const filteredContacts = $derived(list.filterAndSort(contacts));
	const activeFiltersCount = $derived(list.getActiveFilterCount());

	// Form references for server actions
	/** @type {HTMLFormElement} */
	let createForm;
	/** @type {HTMLFormElement} */
	let updateForm;
	/** @type {HTMLFormElement} */
	let deleteForm;

	// Form data state
	let formState = $state({
		contactId: '',
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		organization: '',
		title: '',
		department: '',
		doNotCall: false,
		linkedInUrl: '',
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		description: '',
		ownerId: ''
	});

	/**
	 * Get full name
	 * @param {any} contact
	 */
	function getFullName(contact) {
		return `${contact.firstName} ${contact.lastName}`.trim();
	}

	/**
	 * Get initials for contact
	 * @param {any} contact
	 */
	function getContactInitials(contact) {
		return getNameInitials(contact.firstName, contact.lastName);
	}

	/**
	 * Handle form submit from drawer
	 * @param {any} formData
	 */
	async function handleFormSubmit(formData) {
		// Populate form state
		formState.firstName = formData.first_name || '';
		formState.lastName = formData.last_name || '';
		formState.email = formData.email || '';
		formState.phone = formData.phone || '';
		formState.organization = formData.organization || '';
		formState.title = formData.title || '';
		formState.department = formData.department || '';
		formState.doNotCall = formData.do_not_call || false;
		formState.linkedInUrl = formData.linkedin_url || '';
		formState.addressLine = formData.address_line || '';
		formState.city = formData.city || '';
		formState.state = formData.state || '';
		formState.postcode = formData.postcode || '';
		formState.country = formData.country || '';
		formState.description = formData.description || '';
		formState.ownerId = formData.owner_id || '';

		await tick();

		if (drawerMode === 'view' && selectedContact) {
			// Edit mode
			formState.contactId = selectedContact.id;
			await tick();
			updateForm.requestSubmit();
		} else {
			// Create mode
			createForm.requestSubmit();
		}
	}

	/**
	 * Handle contact delete
	 */
	async function handleDelete() {
		if (!selectedContact) return;
		if (!confirm(`Are you sure you want to delete ${getFullName(selectedContact)}?`)) return;

		formState.contactId = selectedContact.id;
		await tick();
		deleteForm.requestSubmit();
	}


	/**
	 * Create enhance handler for form actions
	 * @param {string} successMessage
	 * @param {boolean} closeOnSuccess
	 */
	function createEnhanceHandler(successMessage, closeOnSuccess = true) {
		return () => {
			return async ({ result }) => {
				if (result.type === 'success') {
					toast.success(successMessage);
					if (closeOnSuccess) {
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
</script>

<svelte:head>
	<title>Contacts - BottleCRM</title>
</svelte:head>

<div class="min-h-screen bg-white">
	<!-- Header -->
	<div class="border-b border-gray-200 px-6 py-4">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-semibold text-gray-900">Contacts</h1>
				<p class="mt-1 text-sm text-gray-500">
					{filteredContacts.length} of {contacts.length} contacts
				</p>
			</div>
			<div class="flex items-center gap-2">
				<!-- Filter Popover -->
				<FilterPopover activeCount={activeFiltersCount} onClear={list.clearFilters}>
					{#snippet children()}
						<div>
							<label for="owner-filter" class="mb-1.5 block text-sm font-medium">Owner</label>
							<select
								id="owner-filter"
								bind:value={list.filters.ownerFilter}
								class="border-input bg-background w-full rounded-md border px-3 py-2 text-sm"
							>
								<option value="ALL">All Owners</option>
								{#each owners as owner}
									<option value={owner.id}>{owner.name || owner.email}</option>
								{/each}
							</select>
						</div>
					{/snippet}
				</FilterPopover>

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
								checked={isColumnVisible(column.key)}
								onCheckedChange={() => toggleColumn(column.key)}
								disabled={column.key === 'contact'}
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
	<div class="overflow-x-auto">
		{#if filteredContacts.length === 0}
			<div class="flex flex-col items-center justify-center py-16 text-center">
				<User class="text-muted-foreground/50 mb-4 h-12 w-12" />
				<h3 class="text-foreground text-lg font-medium">No contacts found</h3>
				<p class="text-muted-foreground mt-1 text-sm">
					Try adjusting your search criteria or create a new contact.
				</p>
				<Button onclick={openCreate} class="mt-4">
					<Plus class="mr-2 h-4 w-4" />
					Create New Contact
				</Button>
			</div>
		{:else}
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
									{#if column.key === 'created'}
										<button
											type="button"
											class="flex items-center gap-1 rounded px-1 -mx-1 hover:bg-gray-100 transition-colors"
											onclick={() => list.toggleSort('createdAt')}
										>
											{column.label}
											{#if list.sortColumn === 'createdAt'}
												{#if list.sortDirection === 'asc'}
													<ChevronUp class="h-3.5 w-3.5" />
												{:else}
													<ChevronDown class="h-3.5 w-3.5" />
												{/if}
											{/if}
										</button>
									{:else}
										{column.label}
									{/if}
								</th>
							{/if}
						{/each}
					</tr>
				</thead>

				<!-- Body -->
				<tbody>
					{#each filteredContacts as contact (contact.id)}
						<!-- Drop indicator line (before row) -->
						{#if dragOverRowId === contact.id && dropPosition === 'before'}
							<tr class="h-0">
								<td colspan={visibleColumns.length + 2} class="p-0">
									<div class="mx-4 h-0.5 rounded-full bg-blue-400"></div>
								</td>
							</tr>
						{/if}

						<tr
							class="group transition-all duration-100 ease-out hover:bg-gray-50/30 {draggedRowId ===
							contact.id
								? 'bg-gray-100 opacity-40'
								: ''}"
							ondragover={(e) => handleRowDragOver(e, contact.id)}
							ondragleave={handleRowDragLeave}
							ondrop={(e) => handleRowDrop(e, contact.id)}
						>
							<!-- Drag Handle -->
							<td class="w-8 px-1 py-3">
								<div
									draggable="true"
									ondragstart={(e) => handleDragStart(e, contact.id)}
									ondragend={handleDragEnd}
									class="flex h-6 w-6 cursor-grab items-center justify-center rounded opacity-0 transition-all group-hover:opacity-40 hover:!opacity-70 hover:bg-gray-200 active:cursor-grabbing"
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
									onclick={() => openContact(contact)}
									class="flex h-6 w-6 items-center justify-center rounded opacity-0 transition-all duration-75 group-hover:opacity-100 hover:bg-gray-200"
								>
									<Expand class="h-3.5 w-3.5 text-gray-500" />
								</button>
							</td>

							<!-- Contact -->
							{#if isColumnVisible('contact')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'contact')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 flex w-full cursor-pointer items-center gap-3 rounded px-2 py-1.5 text-left transition-colors duration-75 hover:bg-gray-100/50"
									>
										<div
											class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-medium text-white"
										>
											{getContactInitials(contact)}
										</div>
										<span class="truncate text-sm text-gray-900">
											{getFullName(contact)}
										</span>
									</button>
								</td>
							{/if}

							<!-- Title -->
							{#if isColumnVisible('title')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'title')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm transition-colors duration-75 hover:bg-gray-100/50"
									>
										{#if contact.title}
											<span class="text-gray-900">{contact.title}</span>
										{:else}
											<span class="text-gray-400">Empty</span>
										{/if}
									</button>
								</td>
							{/if}

							<!-- Email -->
							{#if isColumnVisible('email')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'email')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm transition-colors duration-75 hover:bg-gray-100/50"
									>
										{#if contact.email}
											<span class="truncate text-gray-900">{contact.email}</span>
										{:else}
											<span class="text-gray-400">Empty</span>
										{/if}
									</button>
								</td>
							{/if}

							<!-- Phone -->
							{#if isColumnVisible('phone')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'phone')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm transition-colors duration-75 hover:bg-gray-100/50"
									>
										{#if contact.phone}
											<span class="text-gray-900">{formatPhone(contact.phone)}</span>
										{:else}
											<span class="text-gray-400">Empty</span>
										{/if}
									</button>
								</td>
							{/if}

							<!-- Company -->
							{#if isColumnVisible('company')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'company')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm transition-colors duration-75 hover:bg-gray-100/50"
									>
										{#if contact.organization}
											<span class="truncate text-gray-900">{contact.organization}</span>
										{:else}
											<span class="text-gray-400">Empty</span>
										{/if}
									</button>
								</td>
							{/if}

							<!-- Owner -->
							{#if isColumnVisible('owner')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'owner')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm transition-colors duration-75 hover:bg-gray-100/50"
									>
										{#if contact.owner?.name || contact.owner?.email}
											<span class="text-gray-900"
												>{contact.owner.name || contact.owner.email}</span
											>
										{:else}
											<span class="text-gray-400">Empty</span>
										{/if}
									</button>
								</td>
							{/if}

							<!-- Created -->
							{#if isColumnVisible('created')}
								<td class="px-4 py-3 {columns.find((c) => c.key === 'created')?.width}">
									<button
										type="button"
										onclick={() => openContact(contact)}
										class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm transition-colors duration-75 hover:bg-gray-100/50"
									>
										<span class="text-gray-900">{formatRelativeDate(contact.createdAt)}</span>
									</button>
								</td>
							{/if}
						</tr>

						<!-- Drop indicator line (after row) -->
						{#if dragOverRowId === contact.id && dropPosition === 'after'}
							<tr class="h-0">
								<td colspan={visibleColumns.length + 2} class="p-0">
									<div class="mx-4 h-0.5 rounded-full bg-blue-400"></div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		{/if}
	</div>

	<!-- Add row button at bottom -->
	{#if filteredContacts.length > 0}
		<div class="border-t border-gray-100 px-4 py-2">
			<button
				type="button"
				onclick={openCreate}
				class="flex items-center gap-2 rounded px-2 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
			>
				<Plus class="h-4 w-4" />
				New contact
			</button>
		</div>
	{/if}
</div>

<!-- Contact Drawer -->
<ContactDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	contact={selectedContact}
	mode={drawerMode}
	loading={drawerLoading}
	onSave={handleFormSubmit}
	onDelete={handleDelete}
	onCancel={closeDrawer}
/>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Contact created successfully')}
	class="hidden"
>
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="organization" value={formState.organization} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="department" value={formState.department} />
	<input type="hidden" name="doNotCall" value={formState.doNotCall} />
	<input type="hidden" name="linkedInUrl" value={formState.linkedInUrl} />
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="ownerId" value={formState.ownerId} />
</form>

<form
	method="POST"
	action="?/update"
	bind:this={updateForm}
	use:enhance={createEnhanceHandler('Contact updated successfully')}
	class="hidden"
>
	<input type="hidden" name="contactId" value={formState.contactId} />
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<input type="hidden" name="organization" value={formState.organization} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="department" value={formState.department} />
	<input type="hidden" name="doNotCall" value={formState.doNotCall} />
	<input type="hidden" name="linkedInUrl" value={formState.linkedInUrl} />
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<input type="hidden" name="description" value={formState.description} />
	<input type="hidden" name="ownerId" value={formState.ownerId} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Contact deleted successfully')}
	class="hidden"
>
	<input type="hidden" name="contactId" value={formState.contactId} />
</form>
