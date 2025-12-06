<script>
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Circle, CheckCircle2, ChevronRight } from '@lucide/svelte';

	/**
	 * @typedef {Object} Task
	 * @property {string} id
	 * @property {string} subject
	 * @property {string} status
	 * @property {string} priority
	 * @property {string} [dueDate]
	 * @property {boolean} [isOverdue]
	 * @property {boolean} [isDueToday]
	 */

	/**
	 * @typedef {Object} Props
	 * @property {Task[]} [tasks] - All tasks
	 */

	/** @type {Props} */
	let { tasks = [] } = $props();

	/** @type {'all' | 'overdue' | 'today' | 'week'} */
	let filter = $state('all');

	const today = new Date();
	today.setHours(0, 0, 0, 0);

	const weekEnd = new Date(today);
	weekEnd.setDate(weekEnd.getDate() + 7);

	/**
	 * Check if a date is today
	 * @param {string} dateStr
	 */
	function isToday(dateStr) {
		if (!dateStr) return false;
		const date = new Date(dateStr);
		date.setHours(0, 0, 0, 0);
		return date.getTime() === today.getTime();
	}

	/**
	 * Check if a date is overdue
	 * @param {string} dateStr
	 */
	function isOverdue(dateStr) {
		if (!dateStr) return false;
		const date = new Date(dateStr);
		date.setHours(0, 0, 0, 0);
		return date.getTime() < today.getTime();
	}

	/**
	 * Check if a date is within this week
	 * @param {string} dateStr
	 */
	function isThisWeek(dateStr) {
		if (!dateStr) return false;
		const date = new Date(dateStr);
		date.setHours(0, 0, 0, 0);
		return date.getTime() >= today.getTime() && date.getTime() <= weekEnd.getTime();
	}

	const filteredTasks = $derived(() => {
		return tasks.filter((task) => {
			if (task.status === 'Completed') return false;
			if (filter === 'overdue') return isOverdue(task.dueDate);
			if (filter === 'today') return isToday(task.dueDate);
			if (filter === 'week') return isThisWeek(task.dueDate);
			return true;
		});
	});

	const overdueTasks = $derived(tasks.filter((t) => t.status !== 'Completed' && isOverdue(t.dueDate)));

	/**
	 * Get priority badge class
	 * @param {string} priority
	 */
	function getPriorityClass(priority) {
		const classes = /** @type {Record<string, string>} */ ({
			High: 'border-red-300 text-red-600 dark:border-red-700 dark:text-red-400',
			Medium: 'border-orange-300 text-orange-600 dark:border-orange-700 dark:text-orange-400',
			Low: 'border-gray-300 text-gray-600 dark:border-gray-600 dark:text-gray-400'
		});
		return classes[priority] || classes['Medium'];
	}

	/**
	 * Format date for display
	 * @param {string} dateStr
	 */
	function formatDate(dateStr) {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		if (isToday(dateStr)) return 'Today';
		if (isOverdue(dateStr)) {
			const days = Math.floor((today.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
			return days === 1 ? 'Yesterday' : `${days}d ago`;
		}
		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header class="flex-row items-center justify-between space-y-0 pb-3">
		<Card.Title class="text-foreground text-sm font-medium">My Tasks</Card.Title>
		<Button variant="ghost" size="sm" href="/tasks" class="text-xs">
			View all
			<ChevronRight class="ml-1 h-3 w-3" />
		</Button>
	</Card.Header>
	<div class="border-border/50 flex gap-1 border-b px-4 pb-2">
		<Button
			variant={filter === 'all' ? 'secondary' : 'ghost'}
			size="sm"
			class="h-7 px-2.5 text-xs"
			onclick={() => (filter = 'all')}
		>
			All
		</Button>
		<Button
			variant={filter === 'overdue' ? 'secondary' : 'ghost'}
			size="sm"
			class="h-7 px-2.5 text-xs {overdueTasks.length > 0 ? 'text-red-600 dark:text-red-400' : ''}"
			onclick={() => (filter = 'overdue')}
		>
			Overdue
			{#if overdueTasks.length > 0}
				<Badge variant="destructive" class="ml-1 h-4 px-1 text-[10px]">{overdueTasks.length}</Badge>
			{/if}
		</Button>
		<Button
			variant={filter === 'today' ? 'secondary' : 'ghost'}
			size="sm"
			class="h-7 px-2.5 text-xs"
			onclick={() => (filter = 'today')}
		>
			Today
		</Button>
		<Button
			variant={filter === 'week' ? 'secondary' : 'ghost'}
			size="sm"
			class="h-7 px-2.5 text-xs"
			onclick={() => (filter = 'week')}
		>
			Week
		</Button>
	</div>
	<Card.Content class="flex-1 overflow-auto p-0">
		{#if filteredTasks().length === 0}
			<div class="text-muted-foreground flex h-full items-center justify-center py-8 text-sm">
				No tasks found
			</div>
		{:else}
			<div class="divide-border/50 divide-y">
				{#each filteredTasks() as task (task.id)}
					<a
						href="/tasks/{task.id}"
						class="hover:bg-muted/50 group flex items-center gap-3 px-4 py-2.5 transition-colors"
					>
						<button class="text-muted-foreground hover:text-foreground flex-shrink-0">
							{#if task.status === 'Completed'}
								<CheckCircle2 class="h-4 w-4 text-green-500" />
							{:else}
								<Circle class="h-4 w-4" />
							{/if}
						</button>
						<div class="min-w-0 flex-1">
							<p
								class="text-foreground truncate text-sm font-medium {task.status === 'Completed'
									? 'text-muted-foreground line-through'
									: ''}"
							>
								{task.subject}
							</p>
							<p class="text-muted-foreground truncate text-xs">{task.status}</p>
						</div>
						<Badge variant="outline" class="flex-shrink-0 text-[10px] {getPriorityClass(task.priority)}">
							{task.priority}
						</Badge>
						{#if task.dueDate}
							<span
								class="flex-shrink-0 text-xs tabular-nums {isOverdue(task.dueDate)
									? 'font-medium text-red-500'
									: 'text-muted-foreground'}"
							>
								{formatDate(task.dueDate)}
							</span>
						{/if}
					</a>
				{/each}
			</div>
		{/if}
	</Card.Content>
</Card.Root>
