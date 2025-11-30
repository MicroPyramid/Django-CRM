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
		Phone,
		Mail,
		Building2,
		User,
		Calendar
	} from '@lucide/svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import PageHeader from '$lib/components/layout/PageHeader.svelte';
	import { LeadDrawer } from '$lib/components/leads';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { formatRelativeDate, getNameInitials } from '$lib/utils/formatting.js';
	import { getLeadStatusClass, getRatingConfig } from '$lib/utils/ui-helpers.js';
	import {
		LEAD_STATUSES as statuses,
		LEAD_SOURCES as sources,
		LEAD_RATINGS as ratings
	} from '$lib/constants/filters.js';
	import { useListFilters } from '$lib/hooks';

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
		<Button onclick={openCreate} disabled={false}>
			<Plus class="mr-2 h-4 w-4" />
			New Lead
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
						placeholder="Search by name, company, or email..."
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
					<div class="flex items-end">
						<Button variant="ghost" onclick={list.clearFilters} class="w-full" disabled={false}>
							Clear Filters
						</Button>
					</div>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Leads Table -->
	<Card.Root>
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
				<!-- Desktop Table -->
				<div class="hidden md:block">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								<Table.Head class="w-[250px]">Lead</Table.Head>
								<Table.Head>Company</Table.Head>
								<Table.Head>Contact</Table.Head>
								<Table.Head>Rating</Table.Head>
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
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each filteredLeads as lead (lead.id)}
								{@const ratingConfig = getRatingConfig(lead.rating)}
								<Table.Row
									class="hover:bg-muted/50 cursor-pointer"
									onclick={() => openLead(lead)}
								>
									<Table.Cell>
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
									<Table.Cell>
										{#if lead.company}
											<div class="flex items-center gap-1.5 text-sm">
												<Building2 class="text-muted-foreground h-4 w-4" />
												<span class="truncate">{typeof lead.company === 'object' ? lead.company.name : lead.company}</span>
											</div>
										{:else}
											<span class="text-muted-foreground">-</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
										<div class="space-y-1">
											{#if lead.email}
												<div class="flex items-center gap-1.5 text-sm">
													<Mail class="text-muted-foreground h-3.5 w-3.5" />
													<span class="max-w-[150px] truncate">{lead.email}</span>
												</div>
											{/if}
											{#if lead.phone}
												<div class="flex items-center gap-1.5 text-sm">
													<Phone class="text-muted-foreground h-3.5 w-3.5" />
													<span>{lead.phone}</span>
												</div>
											{/if}
											{#if !lead.email && !lead.phone}
												<span class="text-muted-foreground">-</span>
											{/if}
										</div>
									</Table.Cell>
									<Table.Cell>
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
											<span class="text-muted-foreground">-</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
										<span
											class={cn(
												'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
												getLeadStatusClass(lead.status)
											)}
										>
											{lead.status}
										</span>
									</Table.Cell>
									<Table.Cell>
										<div class="text-muted-foreground flex items-center gap-1.5 text-sm">
											<Calendar class="h-3.5 w-3.5" />
											<span>{formatRelativeDate(lead.createdAt)}</span>
										</div>
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
