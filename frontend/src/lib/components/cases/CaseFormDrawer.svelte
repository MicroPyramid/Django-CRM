<script>
	import { Loader2 } from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { cn } from '$lib/utils.js';
	import { CASE_STATUSES, CASE_TYPES, PRIORITIES } from '$lib/constants/filters.js';

	/**
	 * @typedef {Object} CaseFormData
	 * @property {string} [id]
	 * @property {string} title
	 * @property {string} description
	 * @property {string} accountId
	 * @property {string[]} assignedTo
	 * @property {string[]} contacts
	 * @property {string[]} teams
	 * @property {string} priority
	 * @property {string} caseType
	 * @property {string} dueDate
	 * @property {string} status
	 */

	/**
	 * @typedef {Object} FormOptions
	 * @property {Array<{id: string, name: string}>} accounts
	 * @property {Array<{id: string, name: string}>} users
	 * @property {Array<{id: string, name: string, email?: string}>} contacts
	 * @property {Array<{id: string, name: string}>} teams
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   mode?: 'create' | 'edit',
	 *   initialData?: Partial<CaseFormData> | null,
	 *   options?: FormOptions,
	 *   loading?: boolean,
	 *   onSubmit?: (data: CaseFormData) => Promise<void>,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		mode = 'create',
		initialData = null,
		options = { accounts: [], users: [], contacts: [], teams: [] },
		loading = false,
		onSubmit,
		onCancel
	} = $props();

	// Filter out the 'ALL' option from statuses and priorities for the form
	const statuses = CASE_STATUSES.filter((s) => s.value !== 'ALL');
	const caseTypes = CASE_TYPES;
	const priorities = PRIORITIES.filter((p) => p.value !== 'ALL');

	/** @type {CaseFormData} */
	let formData = $state({
		title: '',
		description: '',
		accountId: '',
		assignedTo: [],
		contacts: [],
		teams: [],
		priority: 'Normal',
		caseType: '',
		dueDate: '',
		status: 'New'
	});

	/** @type {Record<string, string>} */
	let errors = $state({});

	let isSubmitting = $state(false);

	// Reset form when drawer opens with new data
	$effect(() => {
		if (open) {
			if (initialData) {
				formData = {
					title: initialData.title || '',
					description: initialData.description || '',
					accountId: initialData.accountId || '',
					assignedTo: initialData.assignedTo || [],
					contacts: initialData.contacts || [],
					teams: initialData.teams || [],
					priority: initialData.priority || 'Normal',
					caseType: initialData.caseType || '',
					dueDate: initialData.dueDate || '',
					status: initialData.status || 'New'
				};
			} else {
				formData = {
					title: '',
					description: '',
					accountId: '',
					assignedTo: [],
					contacts: [],
					teams: [],
					priority: 'Normal',
					caseType: '',
					dueDate: '',
					status: 'New'
				};
			}
			errors = {};
		}
	});

	/**
	 * Validate form
	 */
	function validateForm() {
		errors = {};
		let isValid = true;

		if (!formData.title?.trim()) {
			errors.title = 'Case title is required';
			isValid = false;
		}

		return isValid;
	}

	/**
	 * Handle form submission
	 */
	async function handleSubmit() {
		if (!validateForm()) return;

		isSubmitting = true;
		try {
			await onSubmit?.(formData);
		} finally {
			isSubmitting = false;
		}
	}

	/**
	 * Handle cancel
	 */
	function handleCancel() {
		if (onCancel) {
			onCancel();
		} else {
			onOpenChange?.(false);
		}
	}

	/**
	 * Toggle assigned user selection
	 * @param {string} userId
	 */
	function toggleAssignedUser(userId) {
		if (formData.assignedTo.includes(userId)) {
			formData.assignedTo = formData.assignedTo.filter((id) => id !== userId);
		} else {
			formData.assignedTo = [...formData.assignedTo, userId];
		}
	}

	/**
	 * Toggle contact selection
	 * @param {string} contactId
	 */
	function toggleContact(contactId) {
		if (formData.contacts.includes(contactId)) {
			formData.contacts = formData.contacts.filter((id) => id !== contactId);
		} else {
			formData.contacts = [...formData.contacts, contactId];
		}
	}

	/**
	 * Toggle team selection
	 * @param {string} teamId
	 */
	function toggleTeam(teamId) {
		if (formData.teams.includes(teamId)) {
			formData.teams = formData.teams.filter((id) => id !== teamId);
		} else {
			formData.teams = [...formData.teams, teamId];
		}
	}

	const title = $derived(mode === 'create' ? 'New Case' : 'Edit Case');
</script>

<SideDrawer bind:open {onOpenChange} {title}>
	{#snippet children()}
		{#if loading}
			<div class="flex items-center justify-center py-20">
				<Loader2 class="text-muted-foreground h-8 w-8 animate-spin" />
			</div>
		{:else}
			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleSubmit();
				}}
				class="p-6"
			>
				<!-- Case Details Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Case Details
					</p>
					<div class="space-y-4">
						<div>
							<Label for="title" class="text-sm">Case Title *</Label>
							<Input
								id="title"
								type="text"
								bind:value={formData.title}
								placeholder="Brief description of the issue..."
								class={cn('mt-1.5', errors.title && 'border-destructive')}
							/>
							{#if errors.title}
								<p class="text-destructive mt-1 text-xs">{errors.title}</p>
							{/if}
						</div>

						<div>
							<Label for="caseType" class="text-sm">Case Type</Label>
							<select
								id="caseType"
								bind:value={formData.caseType}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								{#each caseTypes as caseType}
									<option value={caseType.value}>{caseType.label}</option>
								{/each}
							</select>
						</div>

						<div>
							<Label for="description" class="text-sm">Description</Label>
							<Textarea
								id="description"
								bind:value={formData.description}
								placeholder="Detailed description of the case..."
								rows={4}
								class="mt-1.5"
							/>
						</div>

						<div>
							<Label for="accountId" class="text-sm">Account</Label>
							<select
								id="accountId"
								bind:value={formData.accountId}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="">Select an account...</option>
								{#each options.accounts as account}
									<option value={account.id}>{account.name}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Assignment Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Assignment
					</p>
					<div class="space-y-4">
						<!-- Assigned To (Multi-select) -->
						{#if options.users && options.users.length > 0}
							<div>
								<Label class="text-sm">Assign To</Label>
								<div
									class="border-input mt-1.5 max-h-32 space-y-1 overflow-y-auto rounded-md border p-2"
								>
									{#each options.users as user}
										<label class="hover:bg-muted flex cursor-pointer items-center gap-2 rounded p-1">
											<input
												type="checkbox"
												checked={formData.assignedTo.includes(user.id)}
												onchange={() => toggleAssignedUser(user.id)}
												class="rounded"
											/>
											<span class="text-sm">{user.name}</span>
										</label>
									{/each}
								</div>
								{#if formData.assignedTo.length > 0}
									<p class="text-muted-foreground mt-1 text-xs">
										{formData.assignedTo.length} user(s) selected
									</p>
								{/if}
							</div>
						{/if}

						<!-- Teams (Multi-select) -->
						{#if options.teams && options.teams.length > 0}
							<div>
								<Label class="text-sm">Teams</Label>
								<div
									class="border-input mt-1.5 max-h-32 space-y-1 overflow-y-auto rounded-md border p-2"
								>
									{#each options.teams as team}
										<label class="hover:bg-muted flex cursor-pointer items-center gap-2 rounded p-1">
											<input
												type="checkbox"
												checked={formData.teams.includes(team.id)}
												onchange={() => toggleTeam(team.id)}
												class="rounded"
											/>
											<span class="text-sm">{team.name}</span>
										</label>
									{/each}
								</div>
								{#if formData.teams.length > 0}
									<p class="text-muted-foreground mt-1 text-xs">
										{formData.teams.length} team(s) selected
									</p>
								{/if}
							</div>
						{/if}
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Contacts Section -->
				{#if options.contacts && options.contacts.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Related Contacts
						</p>
						<div>
							<Label class="text-sm">Contacts</Label>
							<div
								class="border-input mt-1.5 max-h-32 space-y-1 overflow-y-auto rounded-md border p-2"
							>
								{#each options.contacts as contact}
									<label class="hover:bg-muted flex cursor-pointer items-center gap-2 rounded p-1">
										<input
											type="checkbox"
											checked={formData.contacts.includes(contact.id)}
											onchange={() => toggleContact(contact.id)}
											class="rounded"
										/>
										<span class="text-sm">{contact.name}</span>
										{#if contact.email}
											<span class="text-muted-foreground text-xs">({contact.email})</span>
										{/if}
									</label>
								{/each}
							</div>
							{#if formData.contacts.length > 0}
								<p class="text-muted-foreground mt-1 text-xs">
									{formData.contacts.length} contact(s) selected
								</p>
							{/if}
						</div>
					</div>

					<Separator class="mb-6" />
				{/if}

				<!-- Priority & Status Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Priority & Status
					</p>
					<div class="space-y-4">
						<div class="grid grid-cols-2 gap-3">
							<div>
								<Label for="priority" class="text-sm">Priority</Label>
								<select
									id="priority"
									bind:value={formData.priority}
									class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
								>
									{#each priorities as priority}
										<option value={priority.value}>{priority.label}</option>
									{/each}
								</select>
							</div>

							<div>
								<Label for="dueDate" class="text-sm">Close Date</Label>
								<Input id="dueDate" type="date" bind:value={formData.dueDate} class="mt-1.5" />
							</div>
						</div>

						{#if mode === 'edit'}
							<div>
								<Label for="status" class="text-sm">Status</Label>
								<select
									id="status"
									bind:value={formData.status}
									class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
								>
									{#each statuses as status}
										<option value={status.value}>{status.label}</option>
									{/each}
								</select>
							</div>
						{/if}
					</div>
				</div>
			</form>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-end gap-2">
			<Button variant="outline" onclick={handleCancel} disabled={isSubmitting || false}>
				Cancel
			</Button>
			<Button onclick={handleSubmit} disabled={isSubmitting || loading || false}>
				{#if isSubmitting}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					{mode === 'create' ? 'Creating...' : 'Saving...'}
				{:else}
					{mode === 'create' ? 'Create Case' : 'Save Changes'}
				{/if}
			</Button>
		</div>
	{/snippet}
</SideDrawer>
