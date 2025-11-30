<script>
	import { Calendar, GripVertical } from '@lucide/svelte';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} Opportunity
	 * @property {string} id
	 * @property {string} name
	 * @property {number | null} amount
	 * @property {string} stage
	 * @property {number | null} probability
	 * @property {string | null} closedOn
	 * @property {{ id: string, name: string, email?: string } | null} account
	 * @property {{ id: string, name: string, email?: string } | null} owner
	 */

	/**
	 * @type {{
	 *   opportunity: Opportunity,
	 *   onclick?: () => void,
	 *   draggable?: boolean,
	 *   class?: string,
	 * }}
	 */
	let { opportunity, onclick, draggable = true, class: className } = $props();

	// Stage colors for left border and progress bar
	const stageColors =
		/** @type {{ [key: string]: { border: string, bg: string, text: string } }} */ ({
			PROSPECTING: { border: 'border-l-gray-500', bg: 'bg-gray-500', text: 'text-gray-600' },
			QUALIFICATION: { border: 'border-l-blue-500', bg: 'bg-blue-500', text: 'text-blue-600' },
			PROPOSAL: { border: 'border-l-purple-500', bg: 'bg-purple-500', text: 'text-purple-600' },
			NEGOTIATION: { border: 'border-l-orange-500', bg: 'bg-orange-500', text: 'text-orange-600' },
			CLOSED_WON: { border: 'border-l-green-500', bg: 'bg-green-500', text: 'text-green-600' },
			CLOSED_LOST: { border: 'border-l-red-500', bg: 'bg-red-500', text: 'text-red-600' }
		});

	const stageConfig = $derived(stageColors[opportunity.stage] || stageColors.PROSPECTING);

	/**
	 * Format currency
	 * @param {number | null} amount
	 */
	function formatCurrency(amount) {
		if (!amount) return '-';
		if (amount >= 1000000) {
			return '$' + (amount / 1000000).toFixed(1) + 'M';
		}
		if (amount >= 1000) {
			return '$' + (amount / 1000).toFixed(0) + 'k';
		}
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	/**
	 * Format date
	 * @param {string | null} date
	 */
	function formatDate(date) {
		if (!date) return null;
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
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

	// Progress percentage based on stage
	const stageProgress = /** @type {{ [key: string]: number }} */ ({
		PROSPECTING: 20,
		QUALIFICATION: 40,
		PROPOSAL: 60,
		NEGOTIATION: 80,
		CLOSED_WON: 100,
		CLOSED_LOST: 100
	});

	const progress = $derived(stageProgress[opportunity.stage] || 20);
</script>

<button
	type="button"
	class={cn(
		'group border-border bg-card relative w-full rounded-lg border p-3 text-left transition-all',
		'border-l-[3px]',
		stageConfig.border,
		'hover:border-border/80 hover:shadow-md',
		'focus:ring-ring focus:ring-2 focus:ring-offset-2 focus:outline-none',
		className
	)}
	{onclick}
	{draggable}
>
	<!-- Drag Handle -->
	{#if draggable}
		<div
			class="absolute top-1/2 left-1 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-50"
		>
			<GripVertical class="text-muted-foreground h-4 w-4" />
		</div>
	{/if}

	<!-- Card Content -->
	<div class="space-y-2">
		<!-- Title & Account -->
		<div>
			<h4 class="text-foreground line-clamp-1 text-sm font-semibold">
				{opportunity.name}
			</h4>
			{#if opportunity.account?.name}
				<p class="text-muted-foreground line-clamp-1 text-xs">
					{opportunity.account.name}
				</p>
			{/if}
		</div>

		<!-- Amount -->
		<p class="text-sm font-medium text-[var(--accent-primary)]">
			{formatCurrency(opportunity.amount)}
		</p>

		<!-- Progress Bar -->
		<div class="bg-muted h-1 w-full overflow-hidden rounded-full">
			<div
				class={cn('h-full rounded-full transition-all', stageConfig.bg)}
				style="width: {progress}%"
			></div>
		</div>

		<!-- Footer: Owner & Date -->
		<div class="flex items-center justify-between pt-1">
			<!-- Owner Avatar -->
			{#if opportunity.owner}
				<div
					class="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-[10px] font-medium text-white"
					title={opportunity.owner.name}
				>
					{getInitials(opportunity.owner.name)}
				</div>
			{:else}
				<div class="h-6 w-6"></div>
			{/if}

			<!-- Close Date -->
			{#if opportunity.closedOn}
				<div class="text-muted-foreground flex items-center gap-1 text-xs">
					<Calendar class="h-3 w-3" />
					<span>{formatDate(opportunity.closedOn)}</span>
				</div>
			{/if}
		</div>
	</div>
</button>
