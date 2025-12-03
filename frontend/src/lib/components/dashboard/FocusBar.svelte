<script>
	import { AlertCircle, Calendar, Phone, Flame } from '@lucide/svelte';

	/**
	 * @typedef {Object} Props
	 * @property {number} [overdueCount] - Number of overdue tasks
	 * @property {number} [todayCount] - Number of tasks due today
	 * @property {number} [followupsCount] - Number of follow-ups scheduled today
	 * @property {number} [hotLeadsCount] - Number of hot leads
	 */

	/** @type {Props} */
	let {
		overdueCount = 0,
		todayCount = 0,
		followupsCount = 0,
		hotLeadsCount = 0
	} = $props();

	const items = $derived([
		{
			href: '/tasks?filter=overdue',
			icon: AlertCircle,
			iconClass: 'text-red-500',
			count: overdueCount,
			label: 'Overdue',
			show: overdueCount > 0
		},
		{
			href: '/tasks?filter=today',
			icon: Calendar,
			iconClass: 'text-orange-500',
			count: todayCount,
			label: 'Due Today',
			show: true
		},
		{
			href: '/leads?filter=followup_today',
			icon: Phone,
			iconClass: 'text-blue-500',
			count: followupsCount,
			label: 'Follow-ups',
			show: true
		},
		{
			href: '/leads?rating=HOT',
			icon: Flame,
			iconClass: 'text-red-500',
			count: hotLeadsCount,
			label: 'Hot Leads',
			show: hotLeadsCount > 0
		}
	]);

	const visibleItems = $derived(items.filter((item) => item.show));
	const hasUrgentItems = $derived(overdueCount > 0);
</script>

{#if visibleItems.length > 0}
	<div
		class="flex items-center gap-2 overflow-x-auto rounded-lg border px-4 py-2.5 sm:gap-4 sm:px-6
			{hasUrgentItems
			? 'border-red-200 bg-red-50/50 dark:border-red-900/50 dark:bg-red-950/20'
			: 'border-border/50 bg-muted/30'}"
	>
		<span class="text-muted-foreground hidden text-xs font-medium uppercase tracking-wider sm:block"
			>Today's Focus</span
		>
		<div class="flex items-center gap-1 sm:gap-3">
			{#each visibleItems as item}
				<a
					href={item.href}
					class="hover:bg-muted/50 flex items-center gap-1.5 rounded-md px-2 py-1.5 transition-colors sm:gap-2 sm:px-3"
				>
					<item.icon class="h-4 w-4 {item.iconClass}" />
					<span class="text-foreground text-sm font-semibold tabular-nums">{item.count}</span>
					<span class="text-muted-foreground hidden text-xs sm:inline">{item.label}</span>
				</a>
			{/each}
		</div>
	</div>
{/if}
