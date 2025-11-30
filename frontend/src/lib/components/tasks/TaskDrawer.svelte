<script>
	import {
		CheckSquare,
		Building2,
		Calendar,
		User,
		Clock,
		Flag,
		MessageSquare,
		Activity,
		Circle,
		CheckCircle2,
		PlayCircle,
		AlertCircle,
		Users,
		Loader2
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { EditableField, EditableMultiSelect } from '$lib/components/ui/editable-field/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { cn } from '$lib/utils.js';
	import { TASK_STATUSES, PRIORITIES } from '$lib/constants/filters.js';

	/**
	 * @typedef {Object} TaskItem
	 * @property {string} [id]
	 * @property {string} subject
	 * @property {string} [description]
	 * @property {string} status
	 * @property {string} [priority]
	 * @property {string} [dueDate]
	 * @property {string} [createdAt]
	 * @property {string} [updatedAt]
	 * @property {{id: string, name: string}} [createdBy]
	 * @property {Array<{id: string, name: string}>} [assignedTo]
	 * @property {{id: string, name: string}} [account]
	 * @property {Array<{id: string, name: string}>} [contacts]
	 * @property {Array<{id: string, name: string}>} [teams]
	 * @property {Array<{id: string, body: string, createdAt: string, author?: {name: string}}>} [comments]
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
	 *   task?: TaskItem | null,
	 *   mode?: 'view' | 'create',
	 *   loading?: boolean,
	 *   options?: FormOptions,
	 *   onSave?: (data: any) => Promise<void>,
	 *   onDelete?: () => void,
	 *   onComplete?: () => void,
	 *   onReopen?: () => void,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		task = null,
		mode = 'view',
		loading = false,
		options = { accounts: [], users: [], contacts: [], teams: [] },
		onSave,
		onDelete,
		onComplete,
		onReopen,
		onCancel
	} = $props();

	// Filter out the 'ALL' option from statuses and priorities for the form
	const statusOptions = TASK_STATUSES.filter((s) => s.value !== 'ALL').map((s) => ({
		value: s.value,
		label: s.label
	}));
	const priorityOptions = PRIORITIES.filter((p) => p.value !== 'ALL').map((p) => ({
		value: p.value,
		label: p.label
	}));

	// Account options for select
	const accountOptions = $derived([
		{ value: '', label: 'None' },
		...options.accounts.map((a) => ({ value: a.id, label: a.name }))
	]);

	// Empty task for create mode
	const emptyTask = {
		subject: '',
		description: '',
		status: 'New',
		priority: 'Medium',
		dueDate: '',
		accountId: '',
		assignedTo: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		contacts: /** @type {string[]} */ ([])
	};

	// Form data state
	let formData = $state({ ...emptyTask });
	let originalData = $state({ ...emptyTask });
	let isSubmitting = $state(false);

	// Reset form data when task changes or drawer opens
	$effect(() => {
		if (open) {
			if (mode === 'create') {
				formData = { ...emptyTask };
				originalData = { ...emptyTask };
			} else if (task) {
				const data = {
					subject: task.subject || '',
					description: task.description || '',
					status: task.status || 'New',
					priority: task.priority || 'Medium',
					dueDate: task.dueDate ? task.dueDate.split('T')[0] : '',
					accountId: task.account?.id || '',
					assignedTo: (task.assignedTo || []).map((a) => a.id),
					teams: (task.teams || []).map((t) => t.id),
					contacts: (task.contacts || []).map((c) => c.id)
				};
				formData = { ...data };
				originalData = { ...data };
			}
		}
	});

	// Check if form has changes
	const isDirty = $derived.by(() => {
		return JSON.stringify(formData) !== JSON.stringify(originalData);
	});

	// Check if it's create mode
	const isCreateMode = $derived(mode === 'create');

	// Check if task is completed
	const isCompleted = $derived(formData.status === 'Completed');

	// Check if task is overdue
	const isOverdue = $derived.by(() => {
		if (!formData.dueDate || isCompleted) return false;
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const due = new Date(formData.dueDate);
		due.setHours(0, 0, 0, 0);
		return due < today;
	});

	// Validation
	const errors = $derived.by(() => {
		/** @type {Record<string, string>} */
		const errs = {};
		if (!formData.subject?.trim()) {
			errs.subject = 'Task title is required';
		}
		return errs;
	});

	const isValid = $derived(Object.keys(errors).length === 0);

	/**
	 * Update a field in form data
	 * @param {string} field
	 * @param {any} value
	 */
	function updateField(field, value) {
		formData = { ...formData, [field]: value };
	}

	/**
	 * Handle save
	 */
	async function handleSave() {
		if (!isValid) return;

		isSubmitting = true;
		try {
			// Convert to API format
			const apiData = {
				subject: formData.subject,
				description: formData.description,
				status: formData.status,
				priority: formData.priority,
				dueDate: formData.dueDate || null,
				accountId: formData.accountId || null,
				assignedTo: formData.assignedTo,
				contacts: formData.contacts,
				teams: formData.teams
			};
			await onSave?.(apiData);
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
	 * Get status icon component
	 * @param {string} status
	 */
	function getStatusIcon(status) {
		const upperStatus = status?.toUpperCase();
		if (upperStatus === 'COMPLETED') return CheckCircle2;
		if (upperStatus === 'IN PROGRESS') return PlayCircle;
		return Circle;
	}

	/**
	 * Format date
	 * @param {string} date
	 */
	function formatDate(date) {
		if (!date) return '';
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	/**
	 * Format relative time
	 * @param {string} date
	 */
	function formatRelativeTime(date) {
		const now = new Date();
		const then = new Date(date);
		const diff = now.getTime() - then.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days} days ago`;
		if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
		return formatDate(date);
	}

	const StatusIcon = $derived(getStatusIcon(formData.status));
	const title = $derived(isCreateMode ? 'New Task' : 'Task');
</script>

<SideDrawer bind:open {onOpenChange} {title}>
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="flex items-start gap-4">
					<Skeleton class="h-12 w-12 rounded-lg" />
					<div class="flex-1 space-y-2">
						<Skeleton class="h-6 w-48" />
						<Skeleton class="h-4 w-32" />
					</div>
				</div>
				<div class="space-y-4">
					<Skeleton class="h-10 w-full" />
					<Skeleton class="h-10 w-full" />
				</div>
				<Separator />
				<div class="grid grid-cols-2 gap-4">
					{#each { length: 6 } as _}
						<div class="space-y-1">
							<Skeleton class="h-3 w-16" />
							<Skeleton class="h-5 w-24" />
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class={cn(
							'flex h-12 w-12 shrink-0 items-center justify-center rounded-lg',
							isCompleted
								? 'bg-gradient-to-br from-green-500 to-green-600'
								: 'bg-gradient-to-br from-purple-500 to-purple-600'
						)}
					>
						<CheckSquare class="h-6 w-6 text-white" />
					</div>
					<div class="min-w-0 flex-1">
						<!-- Editable Subject -->
						<EditableField
							value={formData.subject}
							placeholder="Task title"
							required
							emptyText="Enter task title"
							onchange={(v) => updateField('subject', v)}
							class={cn('text-lg font-semibold', isCompleted && 'line-through opacity-70')}
						/>
						{#if errors.subject}
							<p class="text-destructive mt-1 text-xs">{errors.subject}</p>
						{/if}
						<!-- Account display -->
						<div class="mt-1">
							<EditableField
								value={formData.accountId}
								type="select"
								options={accountOptions}
								placeholder="Select account"
								emptyText="No account"
								onchange={(v) => updateField('accountId', v)}
								class="text-muted-foreground text-sm"
							>
								{#snippet icon()}
									<Building2 class="h-4 w-4" />
								{/snippet}
							</EditableField>
						</div>
					</div>
				</div>

				<!-- Status, Priority and Due Date Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Status & Priority
					</p>
					<div class="space-y-3">
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<StatusIcon class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.status}
								type="select"
								options={statusOptions}
								placeholder="Select status"
								onchange={(v) => updateField('status', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							{#if formData.priority === 'High'}
								<AlertCircle class="h-4 w-4 shrink-0 text-red-500" />
							{:else}
								<Flag class="text-muted-foreground h-4 w-4 shrink-0" />
							{/if}
							<EditableField
								value={formData.priority}
								type="select"
								options={priorityOptions}
								placeholder="Select priority"
								onchange={(v) => updateField('priority', v)}
								class="flex-1"
							/>
						</div>
						<div
							class={cn(
								'flex items-center gap-3 rounded-lg px-3 py-2',
								isOverdue ? 'bg-red-100 dark:bg-red-900/20' : 'bg-muted/30'
							)}
						>
							<Calendar
								class={cn('h-4 w-4 shrink-0', isOverdue ? 'text-red-500' : 'text-muted-foreground')}
							/>
							<EditableField
								value={formData.dueDate}
								type="date"
								placeholder="Select due date"
								emptyText="No due date"
								onchange={(v) => updateField('dueDate', v)}
								class={cn('flex-1', isOverdue && 'text-red-600 dark:text-red-400')}
							/>
							{#if isOverdue}
								<span class="text-xs font-medium text-red-600 dark:text-red-400">Overdue</span>
							{/if}
						</div>
					</div>
				</div>

				<!-- Description Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Description
					</p>
					<EditableField
						value={formData.description}
						type="textarea"
						placeholder="Describe the task..."
						emptyText="Add description..."
						onchange={(v) => updateField('description', v)}
					/>
				</div>

				<Separator class="mb-6" />

				<!-- Assignment Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Assignment
					</p>
					<div class="space-y-3">
						<div>
							<p class="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs">
								<User class="h-3.5 w-3.5" />
								<span>Assigned To</span>
							</p>
							<EditableMultiSelect
								value={formData.assignedTo}
								options={options.users}
								emptyText="Unassigned"
								placeholder="Select users..."
								onchange={(v) => updateField('assignedTo', v)}
							/>
						</div>
						<div>
							<p class="text-muted-foreground mb-1.5 flex items-center gap-1.5 text-xs">
								<Users class="h-3.5 w-3.5" />
								<span>Teams</span>
							</p>
							<EditableMultiSelect
								value={formData.teams}
								options={options.teams}
								emptyText="No teams"
								placeholder="Select teams..."
								onchange={(v) => updateField('teams', v)}
							/>
						</div>
					</div>
				</div>

				<!-- Related Contacts Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Related Contacts
					</p>
					<EditableMultiSelect
						value={formData.contacts}
						options={options.contacts}
						emptyText="No contacts"
						placeholder="Select contacts..."
						onchange={(v) => updateField('contacts', v)}
					/>
				</div>

				{#if !isCreateMode && task}
					<Separator class="mb-6" />

					<!-- Read-only Details Section -->
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Details
						</p>
						<div class="grid grid-cols-2 gap-4">
							{#if task.createdBy}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<User class="h-3.5 w-3.5" />
										<span>Created By</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{task.createdBy.name}
									</p>
								</div>
							{/if}
							{#if task.createdAt}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<Clock class="h-3.5 w-3.5" />
										<span>Created</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{formatDate(task.createdAt)}
									</p>
								</div>
							{/if}
							{#if task.updatedAt}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<Clock class="h-3.5 w-3.5" />
										<span>Updated</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{formatRelativeTime(task.updatedAt)}
									</p>
								</div>
							{/if}
						</div>
					</div>

					<!-- Activity Timeline -->
					<div>
						<div class="mb-3 flex items-center gap-2">
							<Activity class="text-muted-foreground h-4 w-4" />
							<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
								Activity
							</p>
						</div>
						{#if task.comments && task.comments.length > 0}
							<div class="space-y-3">
								{#each task.comments.slice(0, 5) as comment (comment.id)}
									<div class="flex gap-3">
										<div
											class="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
										>
											<MessageSquare class="text-muted-foreground h-4 w-4" />
										</div>
										<div class="min-w-0 flex-1">
											<p class="text-foreground text-sm">
												<span class="font-medium">{comment.author?.name || 'Unknown'}</span>
												{' '}added a note
											</p>
											<p class="text-muted-foreground mt-0.5 text-xs">
												{formatRelativeTime(comment.createdAt)}
											</p>
											<p class="text-muted-foreground mt-1 line-clamp-2 text-sm">
												{comment.body}
											</p>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center py-6 text-center">
								<MessageSquare class="text-muted-foreground/50 mb-2 h-8 w-8" />
								<p class="text-muted-foreground text-sm">No activity yet</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-between">
			{#if !isCreateMode && onDelete}
				<Button
					variant="ghost"
					class="text-destructive hover:text-destructive"
					onclick={onDelete}
					disabled={isSubmitting}
				>
					Delete
				</Button>
			{:else}
				<div></div>
			{/if}
			<div class="flex items-center gap-2">
				{#if !isCreateMode && task}
					{#if isCompleted && onReopen}
						<Button variant="outline" onclick={onReopen} disabled={isSubmitting}>Reopen Task</Button
						>
					{:else if !isCompleted && onComplete}
						<Button variant="outline" onclick={onComplete} disabled={isSubmitting}>
							<CheckCircle2 class="mr-2 h-4 w-4" />
							Mark Complete
						</Button>
					{/if}
				{/if}
				<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>Cancel</Button>
				{#if isDirty || isCreateMode}
					<Button onclick={handleSave} disabled={isSubmitting || !isValid}>
						{#if isSubmitting}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							{isCreateMode ? 'Creating...' : 'Saving...'}
						{:else}
							{isCreateMode ? 'Create Task' : 'Save Changes'}
						{/if}
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</SideDrawer>
