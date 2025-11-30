<script>
	import {
		DollarSign,
		Building2,
		Calendar,
		Target,
		User,
		TrendingUp,
		Percent,
		Activity,
		Clock,
		Loader2,
		CheckCircle,
		XCircle,
		Tag,
		Users,
		Briefcase,
		Globe
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { EditableField } from '$lib/components/ui/editable-field/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { cn } from '$lib/utils.js';
	import {
		OPPORTUNITY_STAGES,
		OPPORTUNITY_TYPES,
		OPPORTUNITY_SOURCES,
		CURRENCY_CODES
	} from '$lib/constants/filters.js';

	/**
	 * @typedef {Object} Opportunity
	 * @property {string} [id]
	 * @property {string} name
	 * @property {number | null} [amount]
	 * @property {number | null} [expectedRevenue]
	 * @property {string} stage
	 * @property {string | null} [opportunityType]
	 * @property {string | null} [currency]
	 * @property {number | null} [probability]
	 * @property {string | null} [leadSource]
	 * @property {string | null} [description]
	 * @property {string | null} [closedOn]
	 * @property {string} [createdAt]
	 * @property {string | null} [createdOnArrow]
	 * @property {{ id: string, name: string, type?: string } | null} [account]
	 * @property {{ id: string, name: string, email?: string } | null} [owner]
	 * @property {Array<{ id: string, name: string, email?: string }>} [assignedTo]
	 * @property {Array<{ id: string, name: string }>} [teams]
	 * @property {Array<{ id: string, firstName: string, lastName: string, email?: string }>} [contacts]
	 * @property {Array<{ id: string, name: string, slug?: string }>} [tags]
	 * @property {{ id: string, name: string } | null} [closedBy]
	 * @property {{ tasks?: number, events?: number }} [_count]
	 */

	/**
	 * @typedef {Object} FormOptions
	 * @property {Array<{ id: string, name: string }>} accounts
	 * @property {Array<{ id: string, name: string, email?: string }>} contacts
	 * @property {Array<{ id: string, name: string }>} tags
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   opportunity?: Opportunity | null,
	 *   mode?: 'view' | 'create',
	 *   loading?: boolean,
	 *   options?: FormOptions,
	 *   initialStage?: string,
	 *   onSave?: (data: any) => Promise<void>,
	 *   onDelete?: () => void,
	 *   onMarkWon?: () => void,
	 *   onMarkLost?: () => void,
	 *   onCancel?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		opportunity = null,
		mode = 'view',
		loading = false,
		options = { accounts: [], contacts: [], tags: [] },
		initialStage = 'PROSPECTING',
		onSave,
		onDelete,
		onMarkWon,
		onMarkLost,
		onCancel
	} = $props();

	// Stage configurations
	const stageConfig =
		/** @type {{ [key: string]: { label: string, color: string, icon: any } }} */ ({
			PROSPECTING: {
				label: 'Prospecting',
				color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300',
				icon: Target
			},
			QUALIFICATION: {
				label: 'Qualification',
				color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
				icon: Target
			},
			PROPOSAL: {
				label: 'Proposal',
				color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
				icon: Target
			},
			NEGOTIATION: {
				label: 'Negotiation',
				color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
				icon: Target
			},
			CLOSED_WON: {
				label: 'Won',
				color: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
				icon: CheckCircle
			},
			CLOSED_LOST: {
				label: 'Lost',
				color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
				icon: XCircle
			}
		});

	// Filter out ALL from stages for form options
	const stageOptions = OPPORTUNITY_STAGES.filter((s) => s.value !== 'ALL').map((s) => ({
		value: s.value,
		label: s.label
	}));

	const typeOptions = OPPORTUNITY_TYPES.map((t) => ({ value: t.value, label: t.label }));
	const sourceOptions = OPPORTUNITY_SOURCES.map((s) => ({ value: s.value, label: s.label }));
	const currencyOptions = CURRENCY_CODES.map((c) => ({ value: c.value, label: c.label }));

	// Account options for select
	const accountOptions = $derived(
		options.accounts.map((a) => ({ value: a.id, label: a.name }))
	);

	// Create empty opportunity for create mode
	const emptyOpportunity = {
		name: '',
		amount: null,
		stage: 'PROSPECTING',
		opportunityType: '',
		currency: 'USD',
		probability: 50,
		leadSource: '',
		closedOn: '',
		accountId: '',
		description: ''
	};

	// Form data state - editable copy of opportunity
	let formData = $state(/** @type {any} */ ({ ...emptyOpportunity }));
	let originalData = $state(/** @type {any} */ ({ ...emptyOpportunity }));
	let isSubmitting = $state(false);

	// Reset form data when opportunity changes or drawer opens
	$effect(() => {
		if (open) {
			if (mode === 'create') {
				formData = { ...emptyOpportunity, stage: initialStage };
				originalData = { ...emptyOpportunity, stage: initialStage };
			} else if (opportunity) {
				const data = {
					name: opportunity.name || '',
					amount: opportunity.amount ?? null,
					stage: opportunity.stage || 'PROSPECTING',
					opportunityType: opportunity.opportunityType || '',
					currency: opportunity.currency || 'USD',
					probability: opportunity.probability ?? 50,
					leadSource: opportunity.leadSource || '',
					closedOn: opportunity.closedOn?.split('T')[0] || '',
					accountId: opportunity.account?.id || '',
					description: opportunity.description || ''
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

	// Check if opportunity is closed
	const isClosed = $derived(
		formData.stage === 'CLOSED_WON' || formData.stage === 'CLOSED_LOST'
	);

	// Current stage config
	const currentStageConfig = $derived(
		stageConfig[formData.stage] || stageConfig.PROSPECTING
	);

	// Validation
	const errors = $derived.by(() => {
		/** @type {Record<string, string>} */
		const errs = {};
		if (!formData.name?.trim()) {
			errs.name = 'Opportunity name is required';
		}
		if (formData.amount !== null && formData.amount !== '' && isNaN(Number(formData.amount))) {
			errs.amount = 'Please enter a valid amount';
		}
		if (formData.probability !== null && formData.probability !== '') {
			const prob = Number(formData.probability);
			if (isNaN(prob) || prob < 0 || prob > 100) {
				errs.probability = 'Probability must be between 0 and 100';
			}
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
			// Convert to API format (snake_case)
			const apiData = {
				name: formData.name,
				amount: formData.amount || null,
				probability: formData.probability || 0,
				stage: formData.stage,
				opportunity_type: formData.opportunityType || '',
				currency: formData.currency || 'USD',
				lead_source: formData.leadSource || '',
				closed_on: formData.closedOn || '',
				account_id: formData.accountId || '',
				description: formData.description || ''
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
	 * Format currency with symbol
	 * @param {number | null} amount
	 * @param {string | null | undefined} currencyCode
	 */
	function formatCurrency(amount, currencyCode) {
		if (!amount) return '-';
		const code = currencyCode || 'USD';
		try {
			return new Intl.NumberFormat('en-US', {
				style: 'currency',
				currency: code,
				minimumFractionDigits: 0,
				maximumFractionDigits: 0
			}).format(amount);
		} catch {
			return `${code} ${amount.toLocaleString()}`;
		}
	}

	/**
	 * Format date
	 * @param {string | null | undefined} date
	 */
	function formatDate(date) {
		if (!date) return '-';
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	/**
	 * Get initials
	 * @param {string | undefined} name
	 */
	function getInitials(name) {
		if (!name) return '?';
		return name
			.split(' ')
			.map((n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	const title = $derived(isCreateMode ? 'New Opportunity' : 'Opportunity');
</script>

<SideDrawer bind:open {onOpenChange} {title}>
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="space-y-2">
					<Skeleton class="h-6 w-48" />
					<Skeleton class="h-4 w-32" />
				</div>
				<div class="space-y-4">
					<Skeleton class="h-16 w-full" />
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
				<div class="mb-6">
					<div class="flex items-start justify-between gap-2">
						<div class="min-w-0 flex-1">
							<EditableField
								value={formData.name}
								placeholder="Opportunity name"
								required
								emptyText="Add opportunity name"
								onchange={(v) => updateField('name', v)}
								class="text-lg font-semibold"
							/>
							<div class="mt-2 flex items-center gap-1.5">
								<Building2 class="text-muted-foreground h-4 w-4 shrink-0" />
								<EditableField
									value={formData.accountId}
									type="select"
									options={accountOptions}
									placeholder="Select account"
									emptyText="Link account"
									onchange={(v) => updateField('accountId', v)}
									class="text-sm"
								/>
							</div>
						</div>
					</div>
				</div>

				<!-- Amount Card -->
				<div class="bg-muted/50 mb-6 rounded-lg p-4">
					<div class="flex items-center justify-between">
						<div class="flex-1">
							<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
								Deal Value
							</p>
							<div class="mt-1 flex items-center gap-2">
								<EditableField
									value={formData.currency}
									type="select"
									options={currencyOptions}
									placeholder="Currency"
									emptyText="USD"
									onchange={(v) => updateField('currency', v)}
									class="text-sm"
								/>
								<EditableField
									value={formData.amount?.toString() || ''}
									type="number"
									placeholder="0"
									emptyText="Add amount"
									min="0"
									onchange={(v) => updateField('amount', v ? Number(v) : null)}
									class="text-2xl font-bold text-[var(--accent-primary)]"
								/>
							</div>
						</div>
						<div
							class="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent-primary)]/10"
						>
							<DollarSign class="h-6 w-6 text-[var(--accent-primary)]" />
						</div>
					</div>
					{#if !isCreateMode && opportunity?.expectedRevenue}
						<div class="text-muted-foreground mt-2 flex items-center gap-1 text-sm">
							<TrendingUp class="h-3.5 w-3.5" />
							<span
								>Expected: {formatCurrency(opportunity.expectedRevenue, formData.currency)}</span
							>
						</div>
					{/if}
				</div>

				<!-- Stage & Type -->
				<div class="mb-6 grid grid-cols-2 gap-4">
					<div>
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Stage
						</p>
						<EditableField
							value={formData.stage}
							type="select"
							options={stageOptions}
							placeholder="Select stage"
							emptyText="Select stage"
							onchange={(v) => updateField('stage', v)}
						/>
					</div>
					<div>
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Type
						</p>
						<EditableField
							value={formData.opportunityType}
							type="select"
							options={typeOptions}
							placeholder="Select type"
							emptyText="Add type"
							onchange={(v) => updateField('opportunityType', v)}
						/>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Details Grid -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Details
					</p>
					<div class="grid grid-cols-2 gap-4">
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Percent class="h-3.5 w-3.5" />
								<span>Probability</span>
							</div>
							<div class="mt-0.5 flex items-center gap-1">
								<EditableField
									value={formData.probability?.toString() || ''}
									type="number"
									placeholder="50"
									emptyText="Add %"
									min="0"
									max="100"
									onchange={(v) => updateField('probability', v ? Number(v) : null)}
									class="text-sm font-medium"
								/>
								<span class="text-muted-foreground text-sm">%</span>
							</div>
						</div>
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Globe class="h-3.5 w-3.5" />
								<span>Source</span>
							</div>
							<div class="mt-0.5">
								<EditableField
									value={formData.leadSource}
									type="select"
									options={sourceOptions}
									placeholder="Select source"
									emptyText="Add source"
									onchange={(v) => updateField('leadSource', v)}
									class="text-sm font-medium"
								/>
							</div>
						</div>
						{#if !isCreateMode}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<User class="h-3.5 w-3.5" />
									<span>Owner</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{opportunity?.owner?.name || 'Unassigned'}
								</p>
							</div>
						{/if}
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Calendar class="h-3.5 w-3.5" />
								<span>Close Date</span>
							</div>
							<div class="mt-0.5">
								<EditableField
									value={formData.closedOn}
									type="date"
									placeholder="Select date"
									emptyText="Add date"
									onchange={(v) => updateField('closedOn', v)}
									class="text-sm font-medium"
								/>
							</div>
						</div>
						{#if !isCreateMode && opportunity?.createdAt}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Calendar class="h-3.5 w-3.5" />
									<span>Created</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{opportunity.createdOnArrow || formatDate(opportunity.createdAt)}
								</p>
							</div>
						{/if}
						{#if !isCreateMode && isClosed && opportunity?.closedBy}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<CheckCircle class="h-3.5 w-3.5" />
									<span>Closed By</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{opportunity.closedBy.name}
								</p>
							</div>
						{/if}
					</div>
				</div>

				<!-- Description -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
						Description
					</p>
					<EditableField
						value={formData.description}
						type="textarea"
						placeholder="Add notes about this opportunity..."
						emptyText="Add description..."
						onchange={(v) => updateField('description', v)}
					/>
				</div>

				{#if !isCreateMode}
					<Separator class="mb-6" />

					<!-- Tags -->
					{#if opportunity?.tags && opportunity.tags.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Tags
							</p>
							<div class="flex flex-wrap gap-1.5">
								{#each opportunity.tags as tag (tag.id)}
									<Badge variant="secondary" class="gap-1">
										<Tag class="h-3 w-3" />
										{tag.name}
									</Badge>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Teams -->
					{#if opportunity?.teams && opportunity.teams.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Teams
							</p>
							<div class="flex flex-wrap gap-1.5">
								{#each opportunity.teams as team (team.id)}
									<Badge variant="outline" class="gap-1">
										<Users class="h-3 w-3" />
										{team.name}
									</Badge>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Assigned Users -->
					{#if opportunity?.assignedTo && opportunity.assignedTo.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Assigned To
							</p>
							<div class="space-y-2">
								{#each opportunity.assignedTo as user (user.id)}
									<div class="bg-muted/50 flex items-center gap-3 rounded-lg px-3 py-2">
										<div
											class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-xs font-medium text-white"
										>
											{getInitials(user.name)}
										</div>
										<div>
											<p class="text-foreground text-sm font-medium">{user.name}</p>
											{#if user.email}
												<p class="text-muted-foreground text-xs">{user.email}</p>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}

					<!-- Contacts -->
					{#if opportunity?.contacts && opportunity.contacts.length > 0}
						<div class="mb-6">
							<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
								Contacts
							</p>
							<div class="space-y-2">
								{#each opportunity.contacts as contact (contact.id)}
									<div class="bg-muted/50 flex items-center gap-3 rounded-lg px-3 py-2">
										<div
											class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-purple-600 text-xs font-medium text-white"
										>
											{getInitials(`${contact.firstName} ${contact.lastName}`)}
										</div>
										<div>
											<p class="text-foreground text-sm font-medium">
												{contact.firstName}
												{contact.lastName}
											</p>
											{#if contact.email}
												<p class="text-muted-foreground text-xs">{contact.email}</p>
											{/if}
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}

					<Separator class="mb-6" />

					<!-- Activity Summary -->
					<div>
						<div class="mb-3 flex items-center gap-2">
							<Activity class="text-muted-foreground h-4 w-4" />
							<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
								Activity
							</p>
						</div>
						<div class="grid grid-cols-2 gap-3">
							<div class="bg-muted/50 flex items-center gap-3 rounded-lg px-3 py-2.5">
								<Clock class="text-muted-foreground h-5 w-5" />
								<div>
									<p class="text-foreground text-sm font-medium">
										{opportunity?._count?.tasks || 0}
									</p>
									<p class="text-muted-foreground text-xs">Tasks</p>
								</div>
							</div>
							<div class="bg-muted/50 flex items-center gap-3 rounded-lg px-3 py-2.5">
								<Calendar class="text-muted-foreground h-5 w-5" />
								<div>
									<p class="text-foreground text-sm font-medium">
										{opportunity?._count?.events || 0}
									</p>
									<p class="text-muted-foreground text-xs">Events</p>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		<div class="flex w-full items-center justify-between">
			<!-- Left side: Delete button (view mode only) -->
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

			<!-- Right side: Action buttons -->
			<div class="flex items-center gap-2">
				{#if !isCreateMode && !isClosed}
					<!-- Mark Won/Lost buttons for open opportunities -->
					{#if onMarkLost}
						<Button variant="outline" onclick={onMarkLost} disabled={isSubmitting}>
							<XCircle class="mr-2 h-4 w-4" />
							Mark Lost
						</Button>
					{/if}
					{#if onMarkWon}
						<Button variant="outline" onclick={onMarkWon} disabled={isSubmitting}>
							<CheckCircle class="mr-2 h-4 w-4" />
							Mark Won
						</Button>
					{/if}
				{/if}

				<Button variant="outline" onclick={handleCancel} disabled={isSubmitting}>
					Cancel
				</Button>

				{#if isDirty || isCreateMode}
					<Button onclick={handleSave} disabled={isSubmitting || !isValid}>
						{#if isSubmitting}
							<Loader2 class="mr-2 h-4 w-4 animate-spin" />
							{isCreateMode ? 'Creating...' : 'Saving...'}
						{:else}
							{isCreateMode ? 'Create Opportunity' : 'Save Changes'}
						{/if}
					</Button>
				{/if}
			</div>
		</div>
	{/snippet}
</SideDrawer>
