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
		Phone,
		Mail,
		Building2,
		User,
		Calendar,
		Briefcase
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { ContactDrawer } from '$lib/components/contacts';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { formatRelativeDate, formatPhone, getNameInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import { goto } from '$app/navigation';
	import { ColumnCustomizer } from '$lib/components/ui/column-customizer/index.js';

	// Column visibility configuration
	const STORAGE_KEY = 'contacts-column-config';

	/**
	 * @typedef {Object} ColumnConfig
	 * @property {string} key
	 * @property {string} label
	 * @property {boolean} visible
	 * @property {boolean} [canHide]
	 */

	/** @type {ColumnConfig[]} */
	const defaultColumns = [
		{ key: 'contact', label: 'Contact', visible: true, canHide: false },
		{ key: 'title', label: 'Title & Department', visible: true, canHide: true },
		{ key: 'email', label: 'Email', visible: true, canHide: true },
		{ key: 'phone', label: 'Phone', visible: true, canHide: true },
		{ key: 'company', label: 'Company', visible: true, canHide: true },
		{ key: 'owner', label: 'Owner', visible: true, canHide: true },
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
	const contacts = $derived(data.contacts || []);
	const owners = $derived(data.owners || []);

	// Drawer state (simplified - single drawer)
	let drawerOpen = $state(false);
	/** @type {'view' | 'create'} */
	let drawerMode = $state('view');
	/** @type {any} */
	let selectedContact = $state(null);
	let drawerLoading = $state(false);

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
		formState.linkedInUrl = formData.linked_in_url || '';
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

<PageHeader title="Contacts" subtitle="{filteredContacts.length} of {contacts.length} contacts">
	{#snippet actions()}
		<ColumnCustomizer columns={columnConfig} onchange={handleColumnChange} />
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
		<Button class="" onclick={openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Contact
		</Button>
	{/snippet}
</PageHeader>

<div class="flex-1 space-y-4 p-4 md:p-6">
	<!-- Contacts Table -->
	<Card.Root class="border-0 shadow-sm">
		<Card.Content class="p-0">
			{#if filteredContacts.length === 0}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<User class="text-muted-foreground/50 mb-4 h-12 w-12" />
					<h3 class="text-foreground text-lg font-medium">No contacts found</h3>
					<p class="text-muted-foreground mt-1 text-sm">
						Try adjusting your search criteria or create a new contact.
					</p>
					<Button onclick={openCreate} class="mt-4" disabled={false}>
						<Plus class="mr-2 h-4 w-4" />
						Create New Contact
					</Button>
				</div>
			{:else}
				<!-- Desktop Table -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row class="border-b border-border/40 hover:bg-transparent">
								{#if isColumnVisible('contact')}
									<Table.Head class="w-[250px] py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Contact</Table.Head>
								{/if}
								{#if isColumnVisible('title')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Title & Department</Table.Head>
								{/if}
								{#if isColumnVisible('email')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Email</Table.Head>
								{/if}
								{#if isColumnVisible('phone')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Phone</Table.Head>
								{/if}
								{#if isColumnVisible('company')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Company</Table.Head>
								{/if}
								{#if isColumnVisible('owner')}
									<Table.Head class="py-2.5 px-4 text-xs font-normal uppercase tracking-wide text-muted-foreground/70">Owner</Table.Head>
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
							{#each filteredContacts as contact (contact.id)}
								<Table.Row
									class="group relative h-[52px] border-b border-border/30 hover:bg-muted/20 cursor-pointer transition-all duration-150 ease-out"
									onclick={() => openContact(contact)}
								>
									{#if isColumnVisible('contact')}
										<Table.Cell class="py-2 px-4">
											<div class="flex items-center gap-3">
												<div
													class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-sm font-medium text-white"
												>
													{getContactInitials(contact)}
												</div>
												<div class="min-w-0">
													<p class="text-foreground truncate font-medium">
														{getFullName(contact)}
													</p>
												</div>
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('title')}
										<Table.Cell class="py-2 px-4">
											<div class="space-y-1">
												{#if contact.title}
													<p class="text-foreground text-sm">{contact.title}</p>
												{/if}
												{#if contact.department}
													<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
														<Briefcase class="h-3.5 w-3.5" />
														<span>{contact.department}</span>
													</div>
												{/if}
												{#if !contact.title && !contact.department}
													<span class="text-muted-foreground">-</span>
												{/if}
											</div>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('email')}
										<Table.Cell class="py-2 px-4">
											{#if contact.email}
												<div class="flex items-center gap-1.5 text-sm">
													<Mail class="text-muted-foreground h-3.5 w-3.5" />
													<span class="max-w-[200px] truncate">{contact.email}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
									{/if}
									{#if isColumnVisible('phone')}
										<Table.Cell class="py-2 px-4">
											{#if contact.phone}
												<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
													<Phone class="h-3.5 w-3.5" />
													<span>{formatPhone(contact.phone)}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
									{/if}
									{#if isColumnVisible('company')}
										<Table.Cell class="py-2 px-4">
											{#if contact.organization}
												<div class="flex items-center gap-1.5 text-sm">
													<Building2 class="text-muted-foreground h-4 w-4" />
													<span class="truncate">{contact.organization}</span>
												</div>
											{:else}
												<span class="text-muted-foreground">-</span>
											{/if}
										</Table.Cell>
									{/if}
									{#if isColumnVisible('owner')}
										<Table.Cell class="py-2 px-4">
											<span class="text-foreground text-sm">
												{contact.owner?.name || contact.owner?.email || '-'}
											</span>
										</Table.Cell>
									{/if}
									{#if isColumnVisible('created')}
										<Table.Cell class="py-2 px-4">
											<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
												<Calendar class="h-3.5 w-3.5" />
												<span>{formatRelativeDate(contact.createdAt)}</span>
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
					{#each filteredContacts as contact (contact.id)}
						<button
							type="button"
							class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left"
							onclick={() => openContact(contact)}
						>
							<div
								class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-sm font-medium text-white"
							>
								{getContactInitials(contact)}
							</div>
							<div class="min-w-0 flex-1">
								<div class="flex items-start justify-between gap-2">
									<div>
										<p class="text-foreground font-medium">{getFullName(contact)}</p>
										{#if contact.title}
											<p class="text-muted-foreground text-sm">{contact.title}</p>
										{/if}
									</div>
								</div>
								<div class="text-muted-foreground mt-2 flex flex-wrap items-center gap-3 text-sm">
									{#if contact.email}
										<div class="flex items-center gap-1">
											<Mail class="h-3.5 w-3.5" />
											<span class="max-w-[150px] truncate">{contact.email}</span>
										</div>
									{/if}
									{#if contact.organization}
										<div class="flex items-center gap-1">
											<Building2 class="h-3.5 w-3.5" />
											<span>{contact.organization}</span>
										</div>
									{/if}
									<div class="flex items-center gap-1">
										<Calendar class="h-3.5 w-3.5" />
										<span>{formatRelativeDate(contact.createdAt)}</span>
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

<!-- Unified Contact Drawer -->
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
