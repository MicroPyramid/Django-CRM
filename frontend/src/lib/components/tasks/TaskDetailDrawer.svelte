<script>
	import {
		CheckSquare,
		Building2,
		Calendar,
		User,
		Users,
		Clock,
		Flag,
		MessageSquare,
		Activity,
		Circle,
		CheckCircle2,
		PlayCircle,
		AlertCircle,
		Contact,
		UsersRound
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} TaskItem
	 * @property {string} id
	 * @property {string} subject
	 * @property {string} [description]
	 * @property {string} status
	 * @property {string} [priority]
	 * @property {string} [dueDate]
	 * @property {string} createdAt
	 * @property {string} [updatedAt]
	 * @property {Array<{id: string, name: string}>} [assignedTo]
	 * @property {Array<{id: string, name: string}>} [contacts]
	 * @property {Array<{id: string, name: string}>} [teams]
	 * @property {{id: string, name: string}} [account]
	 * @property {{id: string, name: string}} [createdBy]
	 * @property {Array<{id: string, body: string, createdAt: string, author?: {name: string}}>} [comments]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   task?: TaskItem | null,
	 *   loading?: boolean,
	 *   onEdit?: () => void,
	 *   onComplete?: () => void,
	 *   onReopen?: () => void,
	 *   onDelete?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		task = null,
		loading = false,
		onEdit,
		onComplete,
		onReopen,
		onDelete
	} = $props();

	/**
	 * Get status badge classes
	 * @param {string} status
	 */
	function getStatusClass(status) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			'IN PROGRESS': 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			COMPLETED: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
		});
		return classes[status?.toUpperCase()] || classes.NEW;
	}

	/**
	 * Get priority badge classes
	 * @param {string | undefined} priority
	 */
	function getPriorityClass(priority) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			HIGH: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
			MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
		});
		return classes[priority?.toUpperCase() || ''] || classes.MEDIUM;
	}

	/**
	 * Get status icon component
	 * @param {string} status
	 */
	function getStatusIcon(status) {
		const upperStatus = status?.toUpperCase();
		if (upperStatus === 'COMPLETED') return CheckCircle2;
		if (upperStatus === 'IN PROGRESS') return PlayCircle;
		return Circle;
	}

	/**
	 * Get priority icon component
	 * @param {string | undefined} priority
	 */
	function getPriorityIcon(priority) {
		const upperPriority = priority?.toUpperCase();
		if (upperPriority === 'HIGH') return AlertCircle;
		return Flag;
	}

	/**
	 * Check if task is overdue
	 * @param {string | undefined} dueDate
	 * @param {string} status
	 */
	function isOverdue(dueDate, status) {
		if (!dueDate || status?.toUpperCase() === 'COMPLETED') return false;
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const due = new Date(dueDate);
		due.setHours(0, 0, 0, 0);
		return due < today;
	}

	/**
	 * Format date
	 * @param {string} date
	 */
	function formatDate(date) {
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	/**
	 * Format relative time
	 * @param {string} date
	 */
	function formatRelativeTime(date) {
		const now = new Date();
		const then = new Date(date);
		const diff = now.getTime() - then.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days} days ago`;
		if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
		return formatDate(date);
	}

	const StatusIcon = $derived(task ? getStatusIcon(task.status) : Circle);
	const PriorityIcon = $derived(task ? getPriorityIcon(task.priority) : Flag);
	const taskOverdue = $derived(task ? isOverdue(task.dueDate, task.status) : false);
</script>

<SideDrawer bind:open {onOpenChange} title="Task Details">
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="flex items-start gap-4">
					<Skeleton class="h-12 w-12 rounded-lg" />
					<div class="flex-1 space-y-2">
						<Skeleton class="h-6 w-48" />
						<Skeleton class="h-4 w-32" />
					</div>
				</div>
				<div class="space-y-4">
					<Skeleton class="h-10 w-full" />
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
		{:else if task}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class={cn(
							'flex h-12 w-12 shrink-0 items-center justify-center rounded-lg',
							task.status?.toUpperCase() === 'COMPLETED'
								? 'bg-gradient-to-br from-green-500 to-green-600'
								: 'bg-gradient-to-br from-blue-500 to-blue-600'
						)}
					>
						<CheckSquare class="h-6 w-6 text-white" />
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<h3
									class={cn(
										'text-foreground text-lg font-semibold',
										task.status?.toUpperCase() === 'COMPLETED' && 'line-through opacity-70'
									)}
								>
									{task.subject}
								</h3>
							</div>
							{#if onEdit && task.status?.toUpperCase() !== 'COMPLETED'}
								<Button variant="ghost" size="sm" onclick={onEdit}>Edit</Button>
							{/if}
						</div>
						{#if task.account}
							<div class="text-muted-foreground mt-2 flex items-center gap-1.5 text-sm">
								<Building2 class="h-4 w-4" />
								<span>{task.account.name}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Status and Priority -->
				<div class="mb-6 flex flex-wrap gap-3">
					<div>
						<p class="text-muted-foreground mb-1 text-xs font-medium tracking-wider uppercase">
							Status
						</p>
						<span
							class={cn(
								'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
								getStatusClass(task.status)
							)}
						>
							<StatusIcon class="h-3.5 w-3.5" />
							{task.status}
						</span>
					</div>
					{#if task.priority}
						<div>
							<p class="text-muted-foreground mb-1 text-xs font-medium tracking-wider uppercase">
								Priority
							</p>
							<span
								class={cn(
									'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
									getPriorityClass(task.priority)
								)}
							>
								<PriorityIcon class="h-3.5 w-3.5" />
								{task.priority}
							</span>
						</div>
					{/if}
					{#if task.dueDate}
						<div>
							<p class="text-muted-foreground mb-1 text-xs font-medium tracking-wider uppercase">
								Due Date
							</p>
							<span
								class={cn(
									'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
									taskOverdue
										? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
										: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
								)}
							>
								<Calendar class="h-3.5 w-3.5" />
								{formatDate(task.dueDate)}
								{#if taskOverdue}
									<span class="text-xs">(Overdue)</span>
								{/if}
							</span>
						</div>
					{/if}
				</div>

				<!-- Description -->
				{#if task.description}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Description
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm whitespace-pre-wrap">
								{task.description}
							</p>
						</div>
					</div>
				{/if}

				<Separator class="mb-6" />

				<!-- Assignment Details -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Assignment
					</p>
					<div class="space-y-4">
						<!-- Assigned To -->
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Users class="h-3.5 w-3.5" />
								<span>Assigned To</span>
							</div>
							{#if task.assignedTo && task.assignedTo.length > 0}
								<div class="mt-1.5 flex flex-wrap gap-1">
									{#each task.assignedTo as user}
										<span
											class="bg-secondary text-secondary-foreground inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
										>
											<User class="h-3 w-3" />
											{user.name}
										</span>
									{/each}
								</div>
							{:else}
								<p class="text-foreground mt-0.5 text-sm font-medium">Unassigned</p>
							{/if}
						</div>

						<!-- Teams -->
						{#if task.teams && task.teams.length > 0}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<UsersRound class="h-3.5 w-3.5" />
									<span>Teams</span>
								</div>
								<div class="mt-1.5 flex flex-wrap gap-1">
									{#each task.teams as team}
										<span
											class="bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
										>
											{team.name}
										</span>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Related Records -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Related Records
					</p>
					<div class="grid grid-cols-2 gap-4">
						<!-- Account -->
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Building2 class="h-3.5 w-3.5" />
								<span>Account</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{task.account?.name || 'None'}
							</p>
						</div>

						<!-- Created By -->
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<User class="h-3.5 w-3.5" />
								<span>Created By</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{task.createdBy?.name || 'Unknown'}
							</p>
						</div>

						<!-- Created At -->
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Clock class="h-3.5 w-3.5" />
								<span>Created</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{formatDate(task.createdAt)}
							</p>
						</div>

						<!-- Updated At -->
						{#if task.updatedAt}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Clock class="h-3.5 w-3.5" />
									<span>Updated</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatRelativeTime(task.updatedAt)}
								</p>
							</div>
						{/if}
					</div>

					<!-- Contacts -->
					{#if task.contacts && task.contacts.length > 0}
						<div class="mt-4">
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Contact class="h-3.5 w-3.5" />
								<span>Related Contacts</span>
							</div>
							<div class="mt-1.5 flex flex-wrap gap-1">
								{#each task.contacts as contact}
									<span
										class="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs"
									>
										{contact.name}
									</span>
								{/each}
							</div>
						</div>
					{/if}
				</div>

				<Separator class="mb-6" />

				<!-- Activity Timeline -->
				<div>
					<div class="mb-3 flex items-center gap-2">
						<Activity class="text-muted-foreground h-4 w-4" />
						<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
							Activity
						</p>
					</div>
					{#if task.comments && task.comments.length > 0}
						<div class="space-y-3">
							{#each task.comments.slice(0, 5) as comment (comment.id)}
								<div class="flex gap-3">
									<div
										class="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
									>
										<MessageSquare class="text-muted-foreground h-4 w-4" />
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-foreground text-sm">
											<span class="font-medium">{comment.author?.name || 'Unknown'}</span>
											{' '}added a note
										</p>
										<p class="text-muted-foreground mt-0.5 text-xs">
											{formatRelativeTime(comment.createdAt)}
										</p>
										<p class="text-muted-foreground mt-1 line-clamp-2 text-sm">
											{comment.body}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<div class="flex flex-col items-center justify-center py-6 text-center">
							<MessageSquare class="text-muted-foreground/50 mb-2 h-8 w-8" />
							<p class="text-muted-foreground text-sm">No activity yet</p>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		{#if task}
			<div class="flex w-full items-center justify-between">
				{#if onDelete}
					<Button
						variant="ghost"
						class="text-destructive hover:text-destructive"
						onclick={onDelete}
					>
						Delete
					</Button>
				{/if}
				<div class="flex items-center gap-2">
					{#if task.status?.toUpperCase() === 'COMPLETED' && onReopen}
						<Button variant="outline" onclick={onReopen}>Reopen Task</Button>
					{:else if task.status?.toUpperCase() !== 'COMPLETED' && onComplete}
						<Button variant="outline" onclick={onComplete}>
							<CheckCircle2 class="mr-2 h-4 w-4" />
							Mark Complete
						</Button>
					{/if}
					{#if onEdit && task.status?.toUpperCase() !== 'COMPLETED'}
						<Button variant="default" onclick={onEdit}>Edit Task</Button>
					{/if}
				</div>
			</div>
		{/if}
	{/snippet}
</SideDrawer>
