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
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { cn } from '$lib/utils.js';
	import { OPPORTUNITY_TYPES, CURRENCY_CODES } from '$lib/constants/filters.js';

	/**
	 * @typedef {Object} Opportunity
	 * @property {string} id
	 * @property {string} name
	 * @property {number | null} amount
	 * @property {number | null} expectedRevenue
	 * @property {string} stage
	 * @property {string | null} opportunityType
	 * @property {string | null} currency
	 * @property {number | null} probability
	 * @property {string | null} leadSource
	 * @property {string | null} description
	 * @property {string | null} closedOn
	 * @property {string} createdAt
	 * @property {string | null} createdOnArrow
	 * @property {{ id: string, name: string, type?: string } | null} account
	 * @property {{ id: string, name: string, email?: string } | null} owner
	 * @property {Array<{ id: string, name: string, email?: string }>} [assignedTo]
	 * @property {Array<{ id: string, name: string }>} [teams]
	 * @property {Array<{ id: string, firstName: string, lastName: string, email?: string }>} [contacts]
	 * @property {Array<{ id: string, name: string, slug?: string }>} [tags]
	 * @property {{ id: string, name: string } | null} [closedBy]
	 * @property {{ tasks?: number, events?: number }} [_count]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   opportunity?: Opportunity | null,
	 *   loading?: boolean,
	 *   onEdit?: () => void,
	 *   onMarkWon?: () => void,
	 *   onMarkLost?: () => void,
	 *   onDelete?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		opportunity = null,
		loading = false,
		onEdit,
		onMarkWon,
		onMarkLost,
		onDelete
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

	const currentStageConfig = $derived(
		stageConfig[opportunity?.stage || 'PROSPECTING'] || stageConfig.PROSPECTING
	);
	const isClosed = $derived(
		opportunity?.stage === 'CLOSED_WON' || opportunity?.stage === 'CLOSED_LOST'
	);

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
	 * Format source for display
	 * @param {string | null | undefined} source
	 */
	function formatSource(source) {
		if (!source) return '-';
		return source
			.replace(/_/g, ' ')
			.toLowerCase()
			.replace(/\b\w/g, (l) => l.toUpperCase());
	}

	/**
	 * Get opportunity type label
	 * @param {string | null | undefined} type
	 */
	function getOpportunityTypeLabel(type) {
		if (!type) return '-';
		const found = OPPORTUNITY_TYPES.find((t) => t.value === type);
		return found ? found.label : formatSource(type);
	}

	/**
	 * Get currency label
	 * @param {string | null | undefined} code
	 */
	function getCurrencyLabel(code) {
		if (!code) return '-';
		const found = CURRENCY_CODES.find((c) => c.value === code);
		return found ? found.label : code;
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
</script>

<SideDrawer bind:open {onOpenChange} title="Opportunity Details">
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
		{:else if opportunity}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6">
					<div class="flex items-start justify-between gap-2">
						<div>
							<h3 class="text-foreground text-lg font-semibold">
								{opportunity.name}
							</h3>
							{#if opportunity.account?.name}
								<div class="text-muted-foreground mt-1 flex items-center gap-1.5 text-sm">
									<Building2 class="h-4 w-4" />
									<span>{opportunity.account.name}</span>
								</div>
							{/if}
						</div>
						{#if onEdit && !isClosed}
							<Button variant="ghost" size="sm" onclick={onEdit} disabled={false}>Edit</Button>
						{/if}
					</div>
				</div>

				<!-- Amount Card -->
				<div class="bg-muted/50 mb-6 rounded-lg p-4">
					<div class="flex items-center justify-between">
						<div>
							<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
								Deal Value
							</p>
							<p class="mt-1 text-2xl font-bold text-[var(--accent-primary)]">
								{formatCurrency(opportunity.amount, opportunity.currency)}
							</p>
							{#if opportunity.currency}
								<p class="text-muted-foreground mt-0.5 text-xs">
									{getCurrencyLabel(opportunity.currency)}
								</p>
							{/if}
						</div>
						<div
							class="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent-primary)]/10"
						>
							<DollarSign class="h-6 w-6 text-[var(--accent-primary)]" />
						</div>
					</div>
					{#if opportunity.expectedRevenue}
						<div class="text-muted-foreground mt-2 flex items-center gap-1 text-sm">
							<TrendingUp class="h-3.5 w-3.5" />
							<span
								>Expected: {formatCurrency(opportunity.expectedRevenue, opportunity.currency)}</span
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
						{#if currentStageConfig}
							{@const StageIcon = currentStageConfig.icon}
							<span
								class={cn(
									'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium',
									currentStageConfig.color
								)}
							>
								<StageIcon class="h-4 w-4" />
								{currentStageConfig.label}
							</span>
						{/if}
					</div>
					<div>
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Type
						</p>
						{#if opportunity.opportunityType}
							<span
								class="inline-flex items-center gap-1.5 rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
							>
								<Briefcase class="h-4 w-4" />
								{getOpportunityTypeLabel(opportunity.opportunityType)}
							</span>
						{:else}
							<span class="text-muted-foreground text-sm">-</span>
						{/if}
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Details Grid -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Details
					</p>
					<div class="grid grid-cols-2 gap-4">
						{#if opportunity.probability != null}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Percent class="h-3.5 w-3.5" />
									<span>Probability</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{opportunity.probability}%
								</p>
							</div>
						{/if}
						{#if opportunity.leadSource}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Globe class="h-3.5 w-3.5" />
									<span>Source</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatSource(opportunity.leadSource)}
								</p>
							</div>
						{/if}
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<User class="h-3.5 w-3.5" />
								<span>Owner</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{opportunity.owner?.name || 'Unassigned'}
							</p>
						</div>
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Calendar class="h-3.5 w-3.5" />
								<span>Close Date</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{formatDate(opportunity.closedOn)}
							</p>
						</div>
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Calendar class="h-3.5 w-3.5" />
								<span>Created</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{opportunity.createdOnArrow || formatDate(opportunity.createdAt)}
							</p>
						</div>
						{#if isClosed && opportunity.closedBy}
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

				<!-- Tags -->
				{#if opportunity.tags && opportunity.tags.length > 0}
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
				{#if opportunity.teams && opportunity.teams.length > 0}
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
				{#if opportunity.assignedTo && opportunity.assignedTo.length > 0}
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
				{#if opportunity.contacts && opportunity.contacts.length > 0}
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

				<!-- Description -->
				{#if opportunity.description}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Description
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm whitespace-pre-wrap">
								{opportunity.description}
							</p>
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
									{opportunity._count?.tasks || 0}
								</p>
								<p class="text-muted-foreground text-xs">Tasks</p>
							</div>
						</div>
						<div class="bg-muted/50 flex items-center gap-3 rounded-lg px-3 py-2.5">
							<Calendar class="text-muted-foreground h-5 w-5" />
							<div>
								<p class="text-foreground text-sm font-medium">
									{opportunity._count?.events || 0}
								</p>
								<p class="text-muted-foreground text-xs">Events</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		{#if opportunity && !isClosed}
			<div class="flex w-full items-center justify-between">
				{#if onDelete}
					<Button
						variant="ghost"
						class="text-destructive hover:text-destructive"
						onclick={onDelete}
						disabled={false}
					>
						Delete
					</Button>
				{/if}
				<div class="flex items-center gap-2">
					{#if onMarkLost}
						<Button variant="outline" onclick={onMarkLost} disabled={false}>
							<XCircle class="mr-2 h-4 w-4" />
							Mark Lost
						</Button>
					{/if}
					{#if onMarkWon}
						<Button variant="default" onclick={onMarkWon} disabled={false}>
							<CheckCircle class="mr-2 h-4 w-4" />
							Mark Won
						</Button>
					{/if}
				</div>
			</div>
		{:else if opportunity}
			<div class="flex w-full items-center justify-between">
				{#if onDelete}
					<Button
						variant="ghost"
						class="text-destructive hover:text-destructive"
						onclick={onDelete}
						disabled={false}
					>
						Delete
					</Button>
				{/if}
				{#if onEdit}
					<Button variant="default" onclick={onEdit} disabled={false}>Edit Opportunity</Button>
				{/if}
			</div>
		{/if}
	{/snippet}
</SideDrawer>
