<script>
	import {
		Briefcase,
		Building2,
		Calendar,
		User,
		Clock,
		Flag,
		MessageSquare,
		Activity,
		AlertCircle,
		CheckCircle,
		RotateCcw,
		Users,
		Tag,
		Loader2
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { EditableField, EditableMultiSelect } from '$lib/components/ui/editable-field/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { CASE_STATUSES, CASE_TYPES, PRIORITIES } from '$lib/constants/filters.js';

	/**
	 * @typedef {Object} CaseItem
	 * @property {string} [id]
	 * @property {string} subject
	 * @property {string} [description]
	 * @property {string} status
	 * @property {string} [priority]
	 * @property {string} [caseType]
	 * @property {string} [closedOn]
	 * @property {string} [createdAt]
	 * @property {string} [updatedAt]
	 * @property {boolean} [isActive]
	 * @property {{id: string, name: string}} [createdBy]
	 * @property {{id: string, name: string}} [owner]
	 * @property {Array<{id: string, name: string}>} [assignedTo]
	 * @property {{id: string, name: string}} [account]
	 * @property {Array<{id: string, name: string, email?: string}>} [contacts]
	 * @property {Array<{id: string, name: string}>} [teams]
	 * @property {Array<{id: string, body: string, createdAt: string, author?: {name: string}}>} [comments]
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
	 *   caseItem?: CaseItem | null,
	 *   mode?: 'view' | 'create',
	 *   loading?: boolean,
	 *   options?: FormOptions,
	 *   onSave?: (data: any) => Promise<void>,
	 *   onDelete?: () => void,
	 *   onClose?: () => void,
	 *   onReopen?: () => void,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		caseItem = null,
		mode = 'view',
		loading = false,
		options = { accounts: [], users: [], contacts: [], teams: [] },
		onSave,
		onDelete,
		onClose,
		onReopen,
		onCancel
	} = $props();

	// Filter out the 'ALL' option from statuses and priorities for the form
	const statusOptions = CASE_STATUSES.filter((s) => s.value !== 'ALL').map((s) => ({
		value: s.value,
		label: s.label
	}));
	const caseTypeOptions = CASE_TYPES.map((t) => ({ value: t.value, label: t.label }));
	const priorityOptions = PRIORITIES.filter((p) => p.value !== 'ALL').map((p) => ({
		value: p.value,
		label: p.label
	}));

	// Account options for select
	const accountOptions = $derived([
		{ value: '', label: 'None' },
		...options.accounts.map((a) => ({ value: a.id, label: a.name }))
	]);

	// Empty case for create mode
	const emptyCase = {
		subject: '',
		description: '',
		status: 'New',
		priority: 'Normal',
		caseType: '',
		accountId: '',
		closedOn: '',
		assignedTo: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		contacts: /** @type {string[]} */ ([])
	};

	// Form data state
	let formData = $state({ ...emptyCase });
	let originalData = $state({ ...emptyCase });
	let isSubmitting = $state(false);

	// Reset form data when case changes or drawer opens
	$effect(() => {
		if (open) {
			if (mode === 'create') {
				formData = { ...emptyCase };
				originalData = { ...emptyCase };
			} else if (caseItem) {
				const data = {
					subject: caseItem.subject || '',
					description: caseItem.description || '',
					status: caseItem.status || 'New',
					priority: caseItem.priority || 'Normal',
					caseType: caseItem.caseType || '',
					accountId: caseItem.account?.id || '',
					closedOn: caseItem.closedOn ? caseItem.closedOn.split('T')[0] : '',
					assignedTo: (caseItem.assignedTo || []).map((a) => a.id),
					teams: (caseItem.teams || []).map((t) => t.id),
					contacts: (caseItem.contacts || []).map((c) => c.id)
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

	// Validation
	const errors = $derived.by(() => {
		/** @type {Record<string, string>} */
		const errs = {};
		if (!formData.subject?.trim()) {
			errs.subject = 'Case title is required';
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
				name: formData.subject,
				case_type: formData.caseType,
				description: formData.description,
				account: formData.accountId || null,
				priority: formData.priority,
				status: formData.status,
				closed_on: formData.closedOn || null,
				assigned_to: formData.assignedTo,
				teams: formData.teams,
				contacts: formData.contacts
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
	 * Get status badge classes
	 * @param {string} status
	 */
	function getStatusClass(status) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			ASSIGNED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			PENDING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			CLOSED: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
			REJECTED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
			DUPLICATE: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
		});
		return classes[status?.toUpperCase()] || classes.NEW;
	}

	/**
	 * Get priority badge classes
	 * @param {string | undefined} priority
	 */
	function getPriorityClass(priority) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			URGENT: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
			HIGH: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
			NORMAL: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
		});
		return classes[priority?.toUpperCase() || ''] || classes.NORMAL;
	}

	/**
	 * Get case type badge classes
	 * @param {string | undefined} caseType
	 */
	function getCaseTypeClass(caseType) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			QUESTION: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			INCIDENT: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
			PROBLEM: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
		});
		return classes[caseType?.toUpperCase() || ''] || 'bg-gray-100 text-gray-700';
	}

	/**
	 * Get status icon component
	 * @param {string} status
	 */
	function getStatusIcon(status) {
		const upperStatus = status?.toUpperCase();
		if (upperStatus === 'CLOSED') return CheckCircle;
		if (upperStatus === 'PENDING') return RotateCcw;
		return AlertCircle;
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

	/**
	 * Format status display
	 * @param {string} status
	 */
	function formatStatus(status) {
		return status?.replace(/_/g, ' ') || 'Unknown';
	}

	const StatusIcon = $derived(getStatusIcon(formData.status));
	const title = $derived(isCreateMode ? 'New Case' : 'Case');
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
						class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600"
					>
						<Briefcase class="h-6 w-6 text-white" />
					</div>
					<div class="min-w-0 flex-1">
						<!-- Editable Subject -->
						<EditableField
							value={formData.subject}
							placeholder="Case title"
							required
							emptyText="Enter case title"
							onchange={(v) => updateField('subject', v)}
							class="text-lg font-semibold"
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

				<!-- Status, Priority and Type Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Status & Classification
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
							<Flag class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.priority}
								type="select"
								options={priorityOptions}
								placeholder="Select priority"
								onchange={(v) => updateField('priority', v)}
								class="flex-1"
							/>
						</div>
						<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
							<Tag class="text-muted-foreground h-4 w-4 shrink-0" />
							<EditableField
								value={formData.caseType}
								type="select"
								options={caseTypeOptions}
								placeholder="Select case type"
								emptyText="No type"
								onchange={(v) => updateField('caseType', v)}
								class="flex-1"
							/>
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
						placeholder="Describe the case..."
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

				<Separator class="mb-6" />

				<!-- Dates Section -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Dates
					</p>
					<div class="bg-muted/30 flex items-center gap-3 rounded-lg px-3 py-2">
						<Calendar class="text-muted-foreground h-4 w-4 shrink-0" />
						<EditableField
							value={formData.closedOn}
							type="date"
							placeholder="Select close date"
							emptyText="No close date"
							onchange={(v) => updateField('closedOn', v)}
							class="flex-1"
						/>
					</div>
				</div>

				{#if !isCreateMode && caseItem}
					<Separator class="mb-6" />

					<!-- Read-only Details Section -->
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Details
						</p>
						<div class="grid grid-cols-2 gap-4">
							{#if caseItem.createdBy}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<User class="h-3.5 w-3.5" />
										<span>Created By</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{caseItem.createdBy.name}
									</p>
								</div>
							{/if}
							{#if caseItem.createdAt}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<Clock class="h-3.5 w-3.5" />
										<span>Created</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{formatDate(caseItem.createdAt)}
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
						{#if caseItem.comments && caseItem.comments.length > 0}
							<div class="space-y-3">
								{#each caseItem.comments.slice(0, 5) as comment (comment.id)}
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
				{#if !isCreateMode && caseItem}
					{#if formData.status === 'Closed' && onReopen}
						<Button variant="outline" onclick={onReopen} disabled={isSubmitting}>Reopen Case</Button
						>
					{:else if formData.status !== 'Closed' && onClose}
						<Button variant="outline" onclick={onClose} disabled={isSubmitting}>Close Case</Button>
					{/if}
				{/if}
				<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>Cancel</Button>
				{#if isDirty || isCreateMode}
					<Button onclick={handleSave} disabled={isSubmitting || !isValid}>
						{#if isSubmitting}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							{isCreateMode ? 'Creating...' : 'Saving...'}
						{:else}
							{isCreateMode ? 'Create Case' : 'Save Changes'}
						{/if}
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</SideDrawer>
