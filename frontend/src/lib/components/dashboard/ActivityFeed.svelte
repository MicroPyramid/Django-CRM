<script>
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import {
		Activity,
		Plus,
		Pencil,
		Trash2,
		Eye,
		MessageSquare,
		UserPlus,
		ChevronRight
	} from '@lucide/svelte';

	/**
	 * @typedef {Object} ActivityItem
	 * @property {string} id
	 * @property {string} [description]
	 * @property {string} [message]
	 * @property {string} [timestamp]
	 * @property {string} [createdAt]
	 * @property {string} [action]
	 * @property {string} [entityType]
	 * @property {string} [entityName]
	 * @property {{ name?: string }} [user]
	 */

	/**
	 * @typedef {Object} Props
	 * @property {ActivityItem[]} [activities=[]] - List of activity items
	 */

	/** @type {Props} */
	let { activities = [] } = $props();

	let showAll = $state(false);

	const actionIcons = /** @type {Record<string, typeof Activity>} */ ({
		CREATE: Plus,
		UPDATE: Pencil,
		DELETE: Trash2,
		VIEW: Eye,
		COMMENT: MessageSquare,
		ASSIGN: UserPlus
	});

	const actionColors = /** @type {Record<string, string>} */ ({
		CREATE: 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400',
		UPDATE: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
		DELETE: 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400',
		VIEW: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
		COMMENT: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400',
		ASSIGN: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
	});

	/**
	 * Get date category for grouping
	 * @param {string | undefined} dateStr
	 */
	function getDateCategory(dateStr) {
		if (!dateStr) return 'Earlier';
		const date = new Date(dateStr);
		const now = new Date();
		const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
		const yesterday = new Date(today);
		yesterday.setDate(yesterday.getDate() - 1);
		const weekAgo = new Date(today);
		weekAgo.setDate(weekAgo.getDate() - 7);

		if (date >= today) return 'Today';
		if (date >= yesterday) return 'Yesterday';
		if (date >= weekAgo) return 'This Week';
		return 'Earlier';
	}

	/**
	 * Format time only
	 * @param {string | undefined} dateStr
	 */
	function formatTime(dateStr) {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
	}

	/**
	 * Group activities by date category
	 * @param {ActivityItem[]} activities
	 */
	function groupByDate(activities) {
		const groups = /** @type {Record<string, ActivityItem[]>} */ ({});
		const order = ['Today', 'Yesterday', 'This Week', 'Earlier'];

		for (const activity of activities) {
			const category = getDateCategory(activity.timestamp || activity.createdAt);
			if (!groups[category]) groups[category] = [];
			groups[category].push(activity);
		}

		return order.filter((cat) => groups[cat]?.length > 0).map((cat) => ({
			category: cat,
			items: groups[cat]
		}));
	}

	const displayedActivities = $derived(showAll ? activities : activities.slice(0, 5));
	const groupedActivities = $derived(groupByDate(displayedActivities));
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header class="flex-row items-center justify-between space-y-0 pb-3">
		<div class="flex items-center gap-2">
			<Activity class="text-muted-foreground h-4 w-4" />
			<Card.Title class="text-foreground text-sm font-medium">Recent Activity</Card.Title>
		</div>
		<Button variant="ghost" size="sm" href="/activities" class="text-xs">
			View all
			<ChevronRight class="ml-1 h-3 w-3" />
		</Button>
	</Card.Header>
	<Card.Content class="flex-1 overflow-auto p-0 px-4 pb-4">
		{#if activities.length === 0}
			<div class="text-muted-foreground flex h-full flex-col items-center justify-center py-8 text-center">
				<Activity class="text-muted-foreground/30 mb-2 h-10 w-10" />
				<p class="text-sm">No recent activity</p>
			</div>
		{:else}
			<div class="space-y-4">
				{#each groupedActivities as group}
					<div>
						<p class="text-muted-foreground mb-2 text-xs font-medium uppercase tracking-wider">
							{group.category}
						</p>
						<div class="space-y-2">
							{#each group.items as activity (activity.id)}
								{@const Icon = actionIcons[activity.action || ''] || Activity}
								{@const colorClass = actionColors[activity.action || ''] || 'bg-muted text-muted-foreground'}
								<div class="hover:bg-muted/50 -mx-2 flex items-start gap-3 rounded-md px-2 py-1.5 transition-colors">
									<div class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full {colorClass}">
										<Icon class="h-3 w-3" />
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-foreground text-sm">
											{activity.description || activity.message || `${activity.action} ${activity.entityType}: ${activity.entityName}`}
										</p>
										<p class="text-muted-foreground text-xs">
											{activity.user?.name || 'System'} &middot; {formatTime(activity.timestamp || activity.createdAt)}
										</p>
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/each}
			</div>
			{#if activities.length > 5 && !showAll}
				<Button
					variant="ghost"
					size="sm"
					class="mt-3 w-full text-xs"
					onclick={() => (showAll = true)}
				>
					Show more ({activities.length - 5} more)
				</Button>
			{/if}
		{/if}
	</Card.Content>
</Card.Root>
