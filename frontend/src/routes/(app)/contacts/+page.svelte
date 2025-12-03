<script>
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { page } from '$app/stores';
	import { tick, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		Plus,
		Eye,
		User,
		Mail,
		Phone,
		Building2,
		Briefcase,
		MapPin,
		FileText,
		Linkedin,
		PhoneOff,
		Calendar
	} from '@lucide/svelte';
	import { PageHeader, FilterPopover } from '$lib/components/layout';
	import { CrmDrawer } from '$lib/components/ui/crm-drawer';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { CrmTable } from '$lib/components/ui/crm-table';
	import { formatRelativeDate, formatPhone, getNameInitials } from '$lib/utils/formatting.js';
	import { useListFilters } from '$lib/hooks';
	import { goto } from '$app/navigation';
	import { COUNTRIES, getCountryName } from '$lib/constants/countries.js';

	// Column visibility configuration
	const STORAGE_KEY = 'contacts-column-config';

	/**
	 * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
	 * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string }} ColumnDef
	 */

	/** @type {ColumnDef[]} */
	const columns = [
		{
			key: 'name',
			label: 'Contact',
			type: 'text',
			width: 'w-48',
			editable: false,
			canHide: false,
			getValue: (row) => `${row.firstName || ''} ${row.lastName || ''}`.trim(),
			emptyText: 'Unnamed'
		},
		{ key: 'title', label: 'Title', type: 'text', width: 'w-36', emptyText: 'Empty' },
		{ key: 'email', label: 'Email', type: 'email', width: 'w-52', emptyText: '' },
		{ key: 'phone', label: 'Phone', type: 'text', width: 'w-36', emptyText: '' },
		{
			key: 'organization',
			label: 'Company',
			type: 'text',
			width: 'w-40',
			emptyText: ''
		},
		{
			key: 'owner',
			label: 'Owner',
			type: 'relation',
			width: 'w-36',
			relationIcon: 'user',
			getValue: (row) => row.owner?.name || row.owner?.email,
			emptyText: ''
		},
		{
			key: 'createdAt',
			label: 'Created',
			type: 'date',
			width: 'w-32',
			editable: false
		}
	];

	// Country options for drawer
	const countryOptions = COUNTRIES.map((c) => ({ value: c.code, label: c.name }));

	// Drawer column definitions for NotionDrawer
	const drawerColumns = [
		{ key: 'firstName', label: 'First Name', type: 'text', icon: User, placeholder: 'First name' },
		{ key: 'lastName', label: 'Last Name', type: 'text', placeholder: 'Last name' },
		{ key: 'email', label: 'Email', type: 'email', icon: Mail, placeholder: 'email@example.com' },
		{ key: 'phone', label: 'Phone', type: 'text', icon: Phone, placeholder: '+1 (555) 000-0000' },
		{
			key: 'organization',
			label: 'Company',
			type: 'text',
			icon: Building2,
			placeholder: 'Company name'
		},
		{ key: 'title', label: 'Job Title', type: 'text', icon: Briefcase, placeholder: 'Job title' },
		{ key: 'department', label: 'Department', type: 'text', placeholder: 'Department' },
		{
			key: 'doNotCall',
			label: 'Do Not Call',
			type: 'checkbox',
			icon: PhoneOff
		},
		{
			key: 'linkedInUrl',
			label: 'LinkedIn',
			type: 'text',
			icon: Linkedin,
			placeholder: 'https://linkedin.com/in/...'
		},
		{
			key: 'addressLine',
			label: 'Address',
			type: 'text',
			icon: MapPin,
			placeholder: 'Street address'
		},
		{ key: 'city', label: 'City', type: 'text', placeholder: 'City' },
		{ key: 'state', label: 'State', type: 'text', placeholder: 'State/Province' },
		{ key: 'postcode', label: 'Postal Code', type: 'text', placeholder: 'Postal code' },
		{
			key: 'country',
			label: 'Country',
			type: 'select',
			options: countryOptions,
			placeholder: 'Select country'
		},
		{
			key: 'description',
			label: 'Notes',
			type: 'textarea',
			icon: FileText,
			placeholder: 'Add notes about this contact...'
		}
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
	function toggleColumn(key) {
		const col = columns.find((c) => c.key === key);
		if (col?.canHide === false) return;

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
	let isSubmitting = $state(false);

	// Empty contact template for create mode
	const emptyContact = {
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
		description: ''
	};

	// Drawer form data - mutable copy for editing
	let drawerFormData = $state({ ...emptyContact });

	// Reset form data when contact changes or drawer opens
	$effect(() => {
		if (drawerOpen) {
			if (drawerMode === 'create') {
				drawerFormData = { ...emptyContact };
			} else if (selectedContact) {
				drawerFormData = { ...selectedContact };
			}
		}
	});

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
	 * Handle field change from NotionDrawer
	 * @param {string} field
	 * @param {any} value
	 */
	async function handleDrawerFieldChange(field, value) {
		// Update local form data
		drawerFormData = { ...drawerFormData, [field]: value };

		// For view mode (editing), auto-save changes
		if (drawerMode === 'view' && selectedContact) {
			formState.contactId = selectedContact.id;
			formState.firstName = field === 'firstName' ? value : drawerFormData.firstName || '';
			formState.lastName = field === 'lastName' ? value : drawerFormData.lastName || '';
			formState.email = field === 'email' ? value : drawerFormData.email || '';
			formState.phone = field === 'phone' ? value : drawerFormData.phone || '';
			formState.organization =
				field === 'organization' ? value : drawerFormData.organization || '';
			formState.title = field === 'title' ? value : drawerFormData.title || '';
			formState.department = field === 'department' ? value : drawerFormData.department || '';
			formState.doNotCall = field === 'doNotCall' ? value : drawerFormData.doNotCall || false;
			formState.linkedInUrl = field === 'linkedInUrl' ? value : drawerFormData.linkedInUrl || '';
			formState.addressLine = field === 'addressLine' ? value : drawerFormData.addressLine || '';
			formState.city = field === 'city' ? value : drawerFormData.city || '';
			formState.state = field === 'state' ? value : drawerFormData.state || '';
			formState.postcode = field === 'postcode' ? value : drawerFormData.postcode || '';
			formState.country = field === 'country' ? value : drawerFormData.country || '';
			formState.description = field === 'description' ? value : drawerFormData.description || '';

			await tick();
			updateForm.requestSubmit();
		}
	}

	/**
	 * Handle save for create mode
	 */
	async function handleDrawerSave() {
		if (drawerMode !== 'create') return;

		isSubmitting = true;
		formState.firstName = drawerFormData.firstName || '';
		formState.lastName = drawerFormData.lastName || '';
		formState.email = drawerFormData.email || '';
		formState.phone = drawerFormData.phone || '';
		formState.organization = drawerFormData.organization || '';
		formState.title = drawerFormData.title || '';
		formState.department = drawerFormData.department || '';
		formState.doNotCall = drawerFormData.doNotCall || false;
		formState.linkedInUrl = drawerFormData.linkedInUrl || '';
		formState.addressLine = drawerFormData.addressLine || '';
		formState.city = drawerFormData.city || '';
		formState.state = drawerFormData.state || '';
		formState.postcode = drawerFormData.postcode || '';
		formState.country = drawerFormData.country || '';
		formState.description = drawerFormData.description || '';

		await tick();
		createForm.requestSubmit();
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
				isSubmitting = false;
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
								class=""
								checked={visibleColumns.includes(column.key)}
								onCheckedChange={() => toggleColumn(column.key)}
								disabled={column.canHide === false}
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
		<CrmTable
			data={filteredContacts}
			{columns}
			bind:visibleColumns
			onRowClick={(row) => openContact(row)}
		>
			{#snippet emptyState()}
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
			{/snippet}
		</CrmTable>

		<!-- Add row button at bottom -->
		<div class="border-t border-gray-100/60 px-4 py-2">
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
<CrmDrawer
	bind:open={drawerOpen}
	onOpenChange={handleDrawerChange}
	data={drawerFormData}
	columns={drawerColumns}
	titleKey="firstName"
	titlePlaceholder="First name"
	headerLabel="Contact"
	mode={drawerMode}
	loading={drawerLoading || isSubmitting}
	onFieldChange={handleDrawerFieldChange}
	onDelete={handleDelete}
	onClose={closeDrawer}
>
	{#snippet activitySection()}
		<!-- Metadata (view mode only) -->
		{#if drawerMode !== 'create' && selectedContact}
			<div>
				<p class="text-gray-500 mb-2 text-xs font-medium tracking-wider uppercase">Details</p>
				<div class="grid grid-cols-2 gap-3 text-sm">
					<div>
						<p class="text-gray-400 text-xs">Owner</p>
						<p class="text-gray-900 font-medium">{selectedContact.owner?.name || 'Unassigned'}</p>
					</div>
					<div>
						<p class="text-gray-400 text-xs">Created</p>
						<p class="text-gray-900 font-medium">{formatRelativeDate(selectedContact.createdAt)}</p>
					</div>
				</div>
			</div>
		{/if}
	{/snippet}

	{#snippet footerActions()}
		{#if drawerMode === 'create'}
			<Button variant="outline" onclick={closeDrawer} disabled={isSubmitting}>Cancel</Button>
			<Button
				onclick={handleDrawerSave}
				disabled={isSubmitting || !drawerFormData.firstName?.trim()}
			>
				{isSubmitting ? 'Creating...' : 'Create Contact'}
			</Button>
		{/if}
	{/snippet}
</CrmDrawer>

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
	use:enhance={createEnhanceHandler('Contact updated successfully', false)}
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
