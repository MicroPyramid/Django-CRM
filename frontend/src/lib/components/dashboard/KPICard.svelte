<script>
	import { cn } from '$lib/utils.js';
	import { TrendingUp, TrendingDown } from '@lucide/svelte';
	import * as Card from '$lib/components/ui/card/index.js';

	/**
	 * @typedef {Object} Props
	 * @property {string} label - The metric label (e.g., "Active Leads")
	 * @property {string | number} value - The metric value
	 * @property {import('svelte').Snippet} [icon] - Icon snippet to display
	 * @property {number} [trend] - Percentage change (positive or negative)
	 * @property {string} [trendLabel] - Label for trend (e.g., "vs last month")
	 * @property {string} [iconBgClass] - Background class for icon container
	 * @property {string} [iconClass] - Class for the icon
	 * @property {string} [class] - Additional classes
	 */

	/** @type {Props & Record<string, any>} */
	let {
		label,
		value,
		icon,
		trend,
		trendLabel,
		iconBgClass = 'bg-blue-100 dark:bg-blue-900/30',
		iconClass = 'text-blue-600 dark:text-blue-400',
		class: className,
		...restProps
	} = $props();

	const hasTrend = $derived(trend !== undefined && trend !== null);
	const isPositive = $derived(trend !== undefined && trend >= 0);
</script>

<Card.Root class={cn('px-5 py-4', className)} {...restProps}>
	<div class="flex items-start justify-between gap-4">
		<div class="flex min-w-0 flex-col gap-1">
			<p class="text-muted-foreground truncate text-xs font-medium tracking-wider uppercase">
				{label}
			</p>
			<p class="text-foreground truncate text-2xl font-semibold">
				{value}
			</p>
			{#if hasTrend}
				<div class="mt-1 flex items-center gap-1">
					{#if isPositive}
						<TrendingUp class="h-3.5 w-3.5 text-[var(--status-success)]" />
						<span class="text-xs font-medium text-[var(--status-success)]">
							+{trend}%
						</span>
					{:else}
						<TrendingDown class="h-3.5 w-3.5 text-[var(--status-danger)]" />
						<span class="text-xs font-medium text-[var(--status-danger)]">
							{trend}%
						</span>
					{/if}
					{#if trendLabel}
						<span class="text-muted-foreground text-xs">{trendLabel}</span>
					{/if}
				</div>
			{/if}
		</div>
		{#if icon}
			<div
				class={cn(
					'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg',
					iconBgClass
				)}
			>
				<div class={iconClass}>
					{@render icon()}
				</div>
			</div>
		{/if}
	</div>
</Card.Root>
