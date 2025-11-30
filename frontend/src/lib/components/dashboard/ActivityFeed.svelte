<script>
	import * as Card from '$lib/components/ui/card/index.js';
	import { Activity, Clock } from '@lucide/svelte';

	/**
	 * @typedef {Object} ActivityItem
	 * @property {string} id
	 * @property {string} message
	 * @property {string} createdAt
	 * @property {string} [type]
	 */

	/**
	 * @typedef {Object} Props
	 * @property {ActivityItem[]} [activities=[]] - List of activity items
	 */

	/** @type {Props} */
	let { activities = [] } = $props();

	/**
	 * Format relative time
	 * @param {string} date
	 */
	function formatRelativeTime(date) {
		const now = new Date();
		const then = new Date(date);
		const diff = Math.floor((now.getTime() - then.getTime()) / 1000);

		if (diff < 60) return 'Just now';
		if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
		if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
		if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
		return then.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<Card.Root>
	<Card.Header class="flex flex-row items-center gap-2 space-y-0 pb-2">
		<div class="bg-muted text-muted-foreground flex h-8 w-8 items-center justify-center rounded-lg">
			<Activity class="h-5 w-5" />
		</div>
		<Card.Title class="text-base font-semibold">Recent Activity</Card.Title>
	</Card.Header>
	<Card.Content>
		{#if activities.length === 0}
			<div class="flex flex-col items-center justify-center py-8 text-center">
				<Activity class="text-muted-foreground/50 mb-2 h-10 w-10" />
				<p class="text-muted-foreground text-sm">No recent activity</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each activities as activity (activity.id)}
					<div class="flex items-start gap-3">
						<div class="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
							<Activity class="text-muted-foreground h-4 w-4" />
						</div>
						<div class="min-w-0 flex-1">
							<p class="text-foreground text-sm">{activity.message}</p>
							<div class="text-muted-foreground mt-1 flex items-center gap-1 text-xs">
								<Clock class="h-3 w-3" />
								<span>{formatRelativeTime(activity.createdAt)}</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</Card.Content>
</Card.Root>
