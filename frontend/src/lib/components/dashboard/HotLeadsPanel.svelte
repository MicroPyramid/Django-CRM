<script>
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Flame, Phone, Mail, ChevronRight, Calendar } from '@lucide/svelte';

	/**
	 * @typedef {Object} Lead
	 * @property {string} id
	 * @property {string} [first_name]
	 * @property {string} [last_name]
	 * @property {string} [company]
	 * @property {string} [rating]
	 * @property {string} [next_follow_up]
	 * @property {string} [last_contacted]
	 */

	/**
	 * @typedef {Object} Props
	 * @property {Lead[]} [leads] - Hot leads
	 */

	/** @type {Props} */
	let { leads = [] } = $props();

	const ratingConfig = /** @type {Record<string, { color: string }>} */ ({
		HOT: { color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
		WARM: { color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
		COLD: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' }
	});

	/**
	 * Format date for display
	 * @param {string | null | undefined} dateStr
	 */
	function formatFollowUp(dateStr) {
		if (!dateStr) return 'No follow-up set';
		const date = new Date(dateStr);
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const tomorrow = new Date(today);
		tomorrow.setDate(tomorrow.getDate() + 1);

		const dateOnly = new Date(date);
		dateOnly.setHours(0, 0, 0, 0);

		if (dateOnly.getTime() === today.getTime()) return 'Today';
		if (dateOnly.getTime() === tomorrow.getTime()) return 'Tomorrow';
		if (dateOnly.getTime() < today.getTime()) {
			const days = Math.floor((today.getTime() - dateOnly.getTime()) / (1000 * 60 * 60 * 24));
			return `${days}d overdue`;
		}
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	/**
	 * Check if follow-up is overdue
	 * @param {string | null | undefined} dateStr
	 */
	function isOverdue(dateStr) {
		if (!dateStr) return false;
		const date = new Date(dateStr);
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		return date < today;
	}

	/**
	 * Get lead name
	 * @param {Lead} lead
	 */
	function getLeadName(lead) {
		const parts = [lead.first_name, lead.last_name].filter(Boolean);
		return parts.length > 0 ? parts.join(' ') : 'Unnamed Lead';
	}
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header class="flex-row items-center justify-between space-y-0 pb-3">
		<div class="flex items-center gap-2">
			<Flame class="h-4 w-4 text-red-500" />
			<Card.Title class="text-foreground text-sm font-medium">Hot Leads</Card.Title>
		</div>
		<Button variant="ghost" size="sm" href="/leads?rating=HOT" class="text-xs">
			View all
			<ChevronRight class="ml-1 h-3 w-3" />
		</Button>
	</Card.Header>
	<Card.Content class="flex-1 overflow-auto p-0">
		{#if leads.length === 0}
			<div class="text-muted-foreground flex h-full flex-col items-center justify-center py-8 text-center">
				<Flame class="text-muted-foreground/30 mb-2 h-10 w-10" />
				<p class="text-sm">No hot leads</p>
				<p class="text-muted-foreground/70 text-xs">Mark leads as "Hot" to see them here</p>
			</div>
		{:else}
			<div class="divide-border/50 divide-y">
				{#each leads as lead (lead.id)}
					<a
						href="/leads/{lead.id}"
						class="hover:bg-muted/50 group flex items-center gap-3 px-4 py-2.5 transition-colors"
					>
						<div class="min-w-0 flex-1">
							<p class="text-foreground truncate text-sm font-medium">
								{getLeadName(lead)}
							</p>
							<p class="text-muted-foreground truncate text-xs">
								{lead.company || 'No company'}
							</p>
						</div>
						<Badge class="{ratingConfig[lead.rating || 'HOT']?.color} flex-shrink-0 gap-1 text-[10px]">
							<Flame class="h-3 w-3" />
							{lead.rating || 'HOT'}
						</Badge>
						{#if lead.next_follow_up}
							<div class="flex flex-shrink-0 items-center gap-1">
								<Calendar class="text-muted-foreground h-3 w-3" />
								<span
									class="text-xs tabular-nums {isOverdue(lead.next_follow_up)
										? 'font-medium text-red-500'
										: 'text-muted-foreground'}"
								>
									{formatFollowUp(lead.next_follow_up)}
								</span>
							</div>
						{/if}
						<!-- Hover actions -->
						<div class="flex flex-shrink-0 gap-1 opacity-0 transition-opacity group-hover:opacity-100">
							<Button variant="ghost" size="icon" class="h-7 w-7" title="Call">
								<Phone class="h-3.5 w-3.5" />
							</Button>
							<Button variant="ghost" size="icon" class="h-7 w-7" title="Email">
								<Mail class="h-3.5 w-3.5" />
							</Button>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</Card.Content>
</Card.Root>
