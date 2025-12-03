<script>
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { ChevronRight } from '@lucide/svelte';

	/**
	 * @typedef {Object} StageData
	 * @property {number} count - Number of opportunities in this stage
	 * @property {number} value - Total value of opportunities in this stage
	 * @property {string} label - Display label for the stage
	 */

	/**
	 * @typedef {Object} Props
	 * @property {Record<string, StageData>} [pipelineData] - Pipeline data by stage
	 */

	/** @type {Props} */
	let { pipelineData = {} } = $props();

	const stages = [
		{ id: 'PROSPECTING', color: 'bg-gray-500' },
		{ id: 'QUALIFICATION', color: 'bg-blue-500' },
		{ id: 'PROPOSAL', color: 'bg-purple-500' },
		{ id: 'NEGOTIATION', color: 'bg-orange-500' },
		{ id: 'CLOSED_WON', color: 'bg-green-500' },
		{ id: 'CLOSED_LOST', color: 'bg-red-500' }
	];

	/**
	 * Format currency values compactly
	 * @param {number} amount
	 */
	function formatCurrency(amount) {
		if (amount >= 1000000) return '$' + (amount / 1000000).toFixed(1) + 'M';
		if (amount >= 1000) return '$' + Math.round(amount / 1000) + 'k';
		if (amount > 0) return '$' + Math.round(amount);
		return '$0';
	}
</script>

<div class="overflow-x-auto">
	<div class="flex min-w-max items-center gap-1">
		{#each stages as stage, index}
			{@const data = pipelineData[stage.id] || { count: 0, value: 0, label: stage.id }}
			<a
				href="/opportunities?stage={stage.id}"
				class="group flex min-w-[120px] flex-col rounded-lg border border-transparent bg-muted/30 px-3 py-2.5 transition-all hover:border-border/50 hover:bg-muted/50"
			>
				<div class="mb-1 flex items-center gap-1.5">
					<div class="h-2 w-2 rounded-full {stage.color}"></div>
					<span class="text-foreground text-xs font-medium">{data.label || stage.id}</span>
					<Badge variant="secondary" class="ml-auto h-5 px-1.5 text-[10px]">{data.count}</Badge>
				</div>
				<p class="text-foreground text-base font-semibold tabular-nums">
					{formatCurrency(data.value)}
				</p>
			</a>
			{#if index < stages.length - 1 && index !== 3}
				<ChevronRight class="text-muted-foreground/50 h-4 w-4 flex-shrink-0" />
			{/if}
			{#if index === 3}
				<div class="bg-border mx-1 h-8 w-px flex-shrink-0"></div>
			{/if}
		{/each}
	</div>
</div>
