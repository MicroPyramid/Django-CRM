<script>
	import { Loader2, X, Check, ChevronDown, ChevronUp } from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} TaskFormData
	 * @property {string} [id]
	 * @property {string} subject
	 * @property {string} description
	 * @property {string} status
	 * @property {string} priority
	 * @property {string} dueDate
	 * @property {string[]} assignedTo
	 * @property {string[]} contacts
	 * @property {string[]} teams
	 * @property {string} accountId
	 */

	/**
	 * @typedef {Object} FormOptions
	 * @property {Array<{id: string, name: string}>} accounts
	 * @property {Array<{id: string, name: string}>} users
	 * @property {Array<{id: string, name: string}>} contacts
	 * @property {Array<{id: string, name: string}>} teams
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   mode?: 'create' | 'edit',
	 *   initialData?: Partial<TaskFormData> | null,
	 *   options?: FormOptions,
	 *   loading?: boolean,
	 *   onSubmit?: (data: TaskFormData) => Promise<void>,
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

	/** @type {TaskFormData} */
	let formData = $state({
		subject: '',
		description: '',
		status: 'New',
		priority: 'Medium',
		dueDate: '',
		assignedTo: [],
		contacts: [],
		teams: [],
		accountId: ''
	});

	/** @type {Record<string, string>} */
	let errors = $state({});

	let isSubmitting = $state(false);

	// Collapsible states for multi-selects
	let assignedToExpanded = $state(false);
	let contactsExpanded = $state(false);
	let teamsExpanded = $state(false);

	// Reset form when drawer opens with new data
	$effect(() => {
		if (open) {
			if (initialData) {
				formData = {
					subject: initialData.subject || '',
					description: initialData.description || '',
					status: initialData.status || 'New',
					priority: initialData.priority || 'Medium',
					dueDate: initialData.dueDate || '',
					assignedTo: initialData.assignedTo || [],
					contacts: initialData.contacts || [],
					teams: initialData.teams || [],
					accountId: initialData.accountId || ''
				};
			} else {
				formData = {
					subject: '',
					description: '',
					status: 'New',
					priority: 'Medium',
					dueDate: '',
					assignedTo: [],
					contacts: [],
					teams: [],
					accountId: ''
				};
			}
			errors = {};
			// Collapse all by default
			assignedToExpanded = false;
			contactsExpanded = false;
			teamsExpanded = false;
		}
	});

	/**
	 * Validate form
	 */
	function validateForm() {
		errors = {};
		let isValid = true;

		if (!formData.subject?.trim()) {
			errors.subject = 'Task subject is required';
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
	 * Toggle item in array
	 * @param {string[]} arr
	 * @param {string} id
	 */
	function toggleItem(arr, id) {
		const idx = arr.indexOf(id);
		if (idx === -1) {
			return [...arr, id];
		} else {
			return arr.filter((x) => x !== id);
		}
	}

	/**
	 * Get display text for multi-select
	 * @param {string[]} selectedIds
	 * @param {Array<{id: string, name: string}>} opts
	 * @param {string} placeholder
	 */
	function getMultiSelectDisplay(selectedIds, opts, placeholder) {
		if (selectedIds.length === 0) return placeholder;
		if (selectedIds.length === 1) {
			const item = opts.find((o) => o.id === selectedIds[0]);
			return item?.name || placeholder;
		}
		return `${selectedIds.length} selected`;
	}

	const title = $derived(mode === 'create' ? 'New Task' : 'Edit Task');
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
				<!-- Task Details Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Task Details
					</p>
					<div class="space-y-4">
						<div>
							<Label for="subject" class="text-sm">Title *</Label>
							<Input
								id="subject"
								type="text"
								bind:value={formData.subject}
								placeholder="What needs to be done?"
								class={cn('mt-1.5', errors.subject && 'border-destructive')}
							/>
							{#if errors.subject}
								<p class="text-destructive mt-1 text-xs">{errors.subject}</p>
							{/if}
						</div>

						<div>
							<Label for="description" class="text-sm">Description</Label>
							<Textarea
								id="description"
								bind:value={formData.description}
								placeholder="Add more details about this task..."
								rows={4}
								class="mt-1.5"
							/>
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Status & Priority Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Status & Priority
					</p>
					<div class="grid grid-cols-2 gap-3">
						<div>
							<Label for="status" class="text-sm">Status</Label>
							<select
								id="status"
								bind:value={formData.status}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="New">New</option>
								<option value="In Progress">In Progress</option>
								<option value="Completed">Completed</option>
							</select>
						</div>

						<div>
							<Label for="priority" class="text-sm">Priority</Label>
							<select
								id="priority"
								bind:value={formData.priority}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="High">High</option>
								<option value="Medium">Medium</option>
								<option value="Low">Low</option>
							</select>
						</div>
					</div>

					<div class="mt-4">
						<Label for="dueDate" class="text-sm">Due Date</Label>
						<Input id="dueDate" type="date" bind:value={formData.dueDate} class="mt-1.5" />
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
						<div>
							<button
								type="button"
								class="border-input bg-background hover:bg-muted/50 flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition-colors"
								onclick={() => (assignedToExpanded = !assignedToExpanded)}
							>
								<span class={formData.assignedTo.length === 0 ? 'text-muted-foreground' : ''}>
									{getMultiSelectDisplay(formData.assignedTo, options.users, 'Select users...')}
								</span>
								{#if assignedToExpanded}
									<ChevronUp class="text-muted-foreground h-4 w-4" />
								{:else}
									<ChevronDown class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
							{#if assignedToExpanded}
								<div class="border-input mt-1 max-h-40 overflow-auto rounded-md border p-1">
									{#if options.users.length === 0}
										<p class="text-muted-foreground p-2 text-center text-sm">No users available</p>
									{:else}
										{#each options.users as user}
											<button
												type="button"
												class="hover:bg-muted flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm"
												onclick={() =>
													(formData.assignedTo = toggleItem(formData.assignedTo, user.id))}
											>
												<div
													class={cn(
														'border-primary flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border',
														formData.assignedTo.includes(user.id)
															? 'bg-primary text-primary-foreground'
															: 'opacity-50'
													)}
												>
													{#if formData.assignedTo.includes(user.id)}
														<Check class="h-3 w-3" />
													{/if}
												</div>
												<span>{user.name}</span>
											</button>
										{/each}
									{/if}
								</div>
							{/if}
							{#if formData.assignedTo.length > 0}
								<div class="mt-2 flex flex-wrap gap-1">
									{#each formData.assignedTo as userId}
										{@const user = options.users.find((u) => u.id === userId)}
										{#if user}
											<span
												class="bg-secondary text-secondary-foreground inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
											>
												{user.name}
												<button
													type="button"
													onclick={() =>
														(formData.assignedTo = formData.assignedTo.filter(
															(id) => id !== userId
														))}
													class="hover:text-destructive"
												>
													<X class="h-3 w-3" />
												</button>
											</span>
										{/if}
									{/each}
								</div>
							{/if}
						</div>

						<!-- Teams (Multi-select) -->
						<div>
							<Label class="text-sm">Teams</Label>
							<button
								type="button"
								class="border-input bg-background hover:bg-muted/50 mt-1.5 flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition-colors"
								onclick={() => (teamsExpanded = !teamsExpanded)}
							>
								<span class={formData.teams.length === 0 ? 'text-muted-foreground' : ''}>
									{getMultiSelectDisplay(formData.teams, options.teams, 'Select teams...')}
								</span>
								{#if teamsExpanded}
									<ChevronUp class="text-muted-foreground h-4 w-4" />
								{:else}
									<ChevronDown class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
							{#if teamsExpanded}
								<div class="border-input mt-1 max-h-40 overflow-auto rounded-md border p-1">
									{#if options.teams.length === 0}
										<p class="text-muted-foreground p-2 text-center text-sm">No teams available</p>
									{:else}
										{#each options.teams as team}
											<button
												type="button"
												class="hover:bg-muted flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm"
												onclick={() => (formData.teams = toggleItem(formData.teams, team.id))}
											>
												<div
													class={cn(
														'border-primary flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border',
														formData.teams.includes(team.id)
															? 'bg-primary text-primary-foreground'
															: 'opacity-50'
													)}
												>
													{#if formData.teams.includes(team.id)}
														<Check class="h-3 w-3" />
													{/if}
												</div>
												<span>{team.name}</span>
											</button>
										{/each}
									{/if}
								</div>
							{/if}
							{#if formData.teams.length > 0}
								<div class="mt-2 flex flex-wrap gap-1">
									{#each formData.teams as teamId}
										{@const team = options.teams.find((t) => t.id === teamId)}
										{#if team}
											<span
												class="bg-secondary text-secondary-foreground inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
											>
												{team.name}
												<button
													type="button"
													onclick={() =>
														(formData.teams = formData.teams.filter((id) => id !== teamId))}
													class="hover:text-destructive"
												>
													<X class="h-3 w-3" />
												</button>
											</span>
										{/if}
									{/each}
								</div>
							{/if}
						</div>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Related Records Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Related Records
					</p>
					<div class="space-y-4">
						<!-- Account -->
						<div>
							<Label for="accountId" class="text-sm">Account</Label>
							<select
								id="accountId"
								bind:value={formData.accountId}
								class="border-input bg-background ring-offset-background focus:ring-ring mt-1.5 w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
							>
								<option value="">No account</option>
								{#each options.accounts as account}
									<option value={account.id}>{account.name}</option>
								{/each}
							</select>
						</div>

						<!-- Contacts (Multi-select) -->
						<div>
							<Label class="text-sm">Contacts</Label>
							<button
								type="button"
								class="border-input bg-background hover:bg-muted/50 mt-1.5 flex w-full items-center justify-between rounded-md border px-3 py-2 text-left text-sm transition-colors"
								onclick={() => (contactsExpanded = !contactsExpanded)}
							>
								<span class={formData.contacts.length === 0 ? 'text-muted-foreground' : ''}>
									{getMultiSelectDisplay(formData.contacts, options.contacts, 'Select contacts...')}
								</span>
								{#if contactsExpanded}
									<ChevronUp class="text-muted-foreground h-4 w-4" />
								{:else}
									<ChevronDown class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
							{#if contactsExpanded}
								<div class="border-input mt-1 max-h-40 overflow-auto rounded-md border p-1">
									{#if options.contacts.length === 0}
										<p class="text-muted-foreground p-2 text-center text-sm">
											No contacts available
										</p>
									{:else}
										{#each options.contacts as contact}
											<button
												type="button"
												class="hover:bg-muted flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm"
												onclick={() =>
													(formData.contacts = toggleItem(formData.contacts, contact.id))}
											>
												<div
													class={cn(
														'border-primary flex h-4 w-4 shrink-0 items-center justify-center rounded-sm border',
														formData.contacts.includes(contact.id)
															? 'bg-primary text-primary-foreground'
															: 'opacity-50'
													)}
												>
													{#if formData.contacts.includes(contact.id)}
														<Check class="h-3 w-3" />
													{/if}
												</div>
												<span>{contact.name}</span>
											</button>
										{/each}
									{/if}
								</div>
							{/if}
							{#if formData.contacts.length > 0}
								<div class="mt-2 flex flex-wrap gap-1">
									{#each formData.contacts as contactId}
										{@const contact = options.contacts.find((c) => c.id === contactId)}
										{#if contact}
											<span
												class="bg-secondary text-secondary-foreground inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
											>
												{contact.name}
												<button
													type="button"
													onclick={() =>
														(formData.contacts = formData.contacts.filter(
															(id) => id !== contactId
														))}
													class="hover:text-destructive"
												>
													<X class="h-3 w-3" />
												</button>
											</span>
										{/if}
									{/each}
								</div>
							{/if}
						</div>
					</div>
				</div>
			</form>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-end gap-2">
			<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>Cancel</Button>
			<Button onclick={handleSubmit} disabled={isSubmitting || loading}>
				{#if isSubmitting}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
					{mode === 'create' ? 'Creating...' : 'Saving...'}
				{:else}
					{mode === 'create' ? 'Create Task' : 'Save Changes'}
				{/if}
			</Button>
		</div>
	{/snippet}
</SideDrawer>
