<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { page } from '$app/stores';
	import { tick } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Search,
		Filter,
		Plus,
		ChevronDown,
		ChevronUp,
		Phone,
		Mail,
		Building2,
		User,
		Calendar,
		Eye,
		MoreHorizontal,
		Briefcase
	} from '@lucide/svelte';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { ContactDetailDrawer, ContactFormDrawer } from '$lib/components/contacts';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { formatRelativeDate, formatPhone, getNameInitials } from '$lib/utils/formatting.js';
	import { useDrawerState, useListFilters } from '$lib/hooks';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	// Computed values from data
	const contacts = $derived(data.contacts || []);
	const owners = $derived(data.owners || []);

	// Drawer state with URL sync
	const drawer = useDrawerState({
		page: $page,
		syncUrl: true
	});

	// Initialize URL sync when contacts change
	$effect(() => {
		drawer.initUrlSync(contacts);
	});

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
		// Core fields
		firstName: '',
		lastName: '',
		email: '',
		phone: '',
		// Professional info
		organization: '',
		title: '',
		department: '',
		// Communication preferences
		doNotCall: false,
		linkedInUrl: '',
		// Address fields
		addressLine: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		// Notes
		description: '',
		// Assignment
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
		// Populate form state - Core fields
		formState.firstName = formData.first_name || '';
		formState.lastName = formData.last_name || '';
		formState.email = formData.email || '';
		formState.phone = formData.phone || '';
		// Professional info
		formState.organization = formData.organization || '';
		formState.title = formData.title || '';
		formState.department = formData.department || '';
		// Communication preferences
		formState.doNotCall = formData.do_not_call || false;
		formState.linkedInUrl = formData.linked_in_url || '';
		// Address fields
		formState.addressLine = formData.address_line || '';
		formState.city = formData.city || '';
		formState.state = formData.state || '';
		formState.postcode = formData.postcode || '';
		formState.country = formData.country || '';
		// Notes
		formState.description = formData.description || '';
		// Assignment
		formState.ownerId = formData.owner_id || '';

		await tick();

		if (drawer.mode === 'edit' && drawer.selected) {
			formState.contactId = drawer.selected.id;
			await tick();
			updateForm.requestSubmit();
		} else {
			createForm.requestSubmit();
		}
	}

	/**
	 * Handle contact delete
	 */
	async function handleDelete() {
		if (!drawer.selected) return;
		if (!confirm(`Are you sure you want to delete ${getFullName(drawer.selected)}?`)) return;

		formState.contactId = drawer.selected.id;
		await tick();
		deleteForm.requestSubmit();
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
</script>

<svelte:head>
	<title>Contacts - BottleCRM</title>
</svelte:head>

<PageHeader title="Contacts" subtitle="{filteredContacts.length} of {contacts.length} contacts">
	{#snippet actions()}
		<Button class="" onclick={drawer.openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Contact
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
						placeholder="Search by name, email, phone, title, or company..."
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
					<div class="flex items-end sm:col-start-4">
						<Button variant="ghost" onclick={list.clearFilters} class="w-full" disabled={false}>
							Clear Filters
						</Button>
					</div>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Contacts Table -->
	<Card.Root>
		<Card.Content class="p-0">
			{#if filteredContacts.length === 0}
				<div class="flex flex-col items-center justify-center py-16 text-center">
					<User class="text-muted-foreground/50 mb-4 h-12 w-12" />
					<h3 class="text-foreground text-lg font-medium">No contacts found</h3>
					<p class="text-muted-foreground mt-1 text-sm">
						Try adjusting your search criteria or create a new contact.
					</p>
					<Button onclick={drawer.openCreate} class="mt-4" disabled={false}>
						<Plus class="mr-2 h-4 w-4" />
						Create New Contact
					</Button>
				</div>
			{:else}
				<!-- Desktop Table -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head class="w-[250px]">Contact</Table.Head>
								<Table.Head>Title & Department</Table.Head>
								<Table.Head>Contact Info</Table.Head>
								<Table.Head>Company</Table.Head>
								<Table.Head>Owner</Table.Head>
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
							{#each filteredContacts as contact (contact.id)}
								<Table.Row
									class="hover:bg-muted/50 cursor-pointer"
									onclick={() => drawer.openDetail(contact)}
								>
									<Table.Cell>
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
									<Table.Cell>
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
									<Table.Cell>
										<div class="space-y-1">
											{#if contact.email}
												<div class="flex items-center gap-1.5 text-sm">
													<Mail class="text-muted-foreground h-3.5 w-3.5" />
													<span class="max-w-[150px] truncate">{contact.email}</span>
												</div>
											{/if}
											{#if contact.phone}
												<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
													<Phone class="h-3.5 w-3.5" />
													<span>{formatPhone(contact.phone)}</span>
												</div>
											{/if}
											{#if !contact.email && !contact.phone}
												<span class="text-muted-foreground">-</span>
											{/if}
										</div>
									</Table.Cell>
									<Table.Cell>
										{#if contact.organization}
											<div class="flex items-center gap-1.5 text-sm">
												<Building2 class="text-muted-foreground h-4 w-4" />
												<span class="truncate">{contact.organization}</span>
											</div>
										{:else}
											<span class="text-muted-foreground">-</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
										<span class="text-foreground text-sm">
											{contact.owner?.name || contact.owner?.email || '-'}
										</span>
									</Table.Cell>
									<Table.Cell>
										<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
											<Calendar class="h-3.5 w-3.5" />
											<span>{formatRelativeDate(contact.createdAt)}</span>
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
												<DropdownMenu.Item onclick={() => drawer.openDetail(contact)}>
													<Eye class="mr-2 h-4 w-4" />
													View Details
												</DropdownMenu.Item>
												<DropdownMenu.Item
													onclick={() => {
														drawer.selected = contact;
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
					{#each filteredContacts as contact (contact.id)}
						<button
							type="button"
							class="hover:bg-muted/50 flex w-full items-start gap-4 p-4 text-left"
							onclick={() => drawer.openDetail(contact)}
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

<!-- Contact Detail Drawer -->
<ContactDetailDrawer
	bind:open={drawer.detailOpen}
	onOpenChange={drawer.handleDetailChange}
	contact={drawer.selected}
	loading={drawer.loading}
	onEdit={drawer.openEdit}
	onDelete={handleDelete}
/>

<!-- Contact Form Drawer -->
<ContactFormDrawer
	bind:open={drawer.formOpen}
	onOpenChange={drawer.handleFormChange}
	mode={drawer.mode}
	initialData={drawer.selected
		? {
				first_name: drawer.selected.firstName,
				last_name: drawer.selected.lastName,
				email: drawer.selected.email,
				phone: drawer.selected.phone,
				organization: drawer.selected.organization,
				title: drawer.selected.title,
				department: drawer.selected.department,
				do_not_call: drawer.selected.doNotCall,
				linked_in_url: drawer.selected.linkedInUrl,
				address_line: drawer.selected.addressLine,
				city: drawer.selected.city,
				state: drawer.selected.state,
				postcode: drawer.selected.postcode,
				country: drawer.selected.country,
				description: drawer.selected.description
			}
		: null}
	onSubmit={handleFormSubmit}
/>

<!-- Hidden forms for server actions -->
<form
	method="POST"
	action="?/create"
	bind:this={createForm}
	use:enhance={createEnhanceHandler('Contact created successfully')}
	class="hidden"
>
	<!-- Core fields -->
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<!-- Professional info -->
	<input type="hidden" name="organization" value={formState.organization} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="department" value={formState.department} />
	<!-- Communication preferences -->
	<input type="hidden" name="doNotCall" value={formState.doNotCall} />
	<input type="hidden" name="linkedInUrl" value={formState.linkedInUrl} />
	<!-- Address fields -->
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<!-- Notes -->
	<input type="hidden" name="description" value={formState.description} />
	<!-- Assignment -->
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
	<!-- Core fields -->
	<input type="hidden" name="firstName" value={formState.firstName} />
	<input type="hidden" name="lastName" value={formState.lastName} />
	<input type="hidden" name="email" value={formState.email} />
	<input type="hidden" name="phone" value={formState.phone} />
	<!-- Professional info -->
	<input type="hidden" name="organization" value={formState.organization} />
	<input type="hidden" name="title" value={formState.title} />
	<input type="hidden" name="department" value={formState.department} />
	<!-- Communication preferences -->
	<input type="hidden" name="doNotCall" value={formState.doNotCall} />
	<input type="hidden" name="linkedInUrl" value={formState.linkedInUrl} />
	<!-- Address fields -->
	<input type="hidden" name="addressLine" value={formState.addressLine} />
	<input type="hidden" name="city" value={formState.city} />
	<input type="hidden" name="state" value={formState.state} />
	<input type="hidden" name="postcode" value={formState.postcode} />
	<input type="hidden" name="country" value={formState.country} />
	<!-- Notes -->
	<input type="hidden" name="description" value={formState.description} />
	<!-- Assignment -->
	<input type="hidden" name="ownerId" value={formState.ownerId} />
</form>

<form
	method="POST"
	action="?/delete"
	bind:this={deleteForm}
	use:enhance={createEnhanceHandler('Contact deleted successfully', true)}
	class="hidden"
>
	<input type="hidden" name="contactId" value={formState.contactId} />
</form>
