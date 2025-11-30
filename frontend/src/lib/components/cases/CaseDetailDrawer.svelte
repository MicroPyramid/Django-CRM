<script>
	import {
		Briefcase,
		Building2,
		Calendar,
		User,
		Clock,
		Flag,
		MessageSquare,
		Activity,
		AlertCircle,
		CheckCircle,
		RotateCcw,
		Users,
		Tag,
		Mail
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} CaseItem
	 * @property {string} id
	 * @property {string} subject
	 * @property {string} [description]
	 * @property {string} status
	 * @property {string} [priority]
	 * @property {string} [caseType]
	 * @property {string} [closedOn]
	 * @property {string} createdAt
	 * @property {string} [updatedAt]
	 * @property {boolean} [isActive]
	 * @property {{id: string, name: string}} [createdBy]
	 * @property {{id: string, name: string}} [owner]
	 * @property {Array<{id: string, name: string}>} [assignedTo]
	 * @property {{id: string, name: string}} [account]
	 * @property {Array<{id: string, name: string, email?: string}>} [contacts]
	 * @property {Array<{id: string, name: string}>} [teams]
	 * @property {Array<{id: string, body: string, createdAt: string, author?: {name: string}}>} [comments]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   caseItem?: CaseItem | null,
	 *   loading?: boolean,
	 *   onEdit?: () => void,
	 *   onClose?: () => void,
	 *   onReopen?: () => void,
	 *   onDelete?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		caseItem = null,
		loading = false,
		onEdit,
		onClose,
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
			ASSIGNED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			PENDING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			CLOSED: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
			REJECTED: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
			DUPLICATE: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
		});
		return classes[status?.toUpperCase()] || classes.NEW;
	}

	/**
	 * Get priority badge classes
	 * @param {string | undefined} priority
	 */
	function getPriorityClass(priority) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			URGENT: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
			HIGH: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
			NORMAL: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			MEDIUM: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			LOW: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
		});
		return classes[priority?.toUpperCase() || ''] || classes.NORMAL;
	}

	/**
	 * Get case type badge classes
	 * @param {string | undefined} caseType
	 */
	function getCaseTypeClass(caseType) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			QUESTION: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			INCIDENT: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
			PROBLEM: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
		});
		return classes[caseType?.toUpperCase() || ''] || 'bg-gray-100 text-gray-700';
	}

	/**
	 * Get status icon component
	 * @param {string} status
	 */
	function getStatusIcon(status) {
		const upperStatus = status?.toUpperCase();
		if (upperStatus === 'CLOSED') return CheckCircle;
		if (upperStatus === 'PENDING') return RotateCcw;
		return AlertCircle;
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

	/**
	 * Format status display
	 * @param {string} status
	 */
	function formatStatus(status) {
		return status?.replace(/_/g, ' ') || 'Unknown';
	}

	const StatusIcon = $derived(caseItem ? getStatusIcon(caseItem.status) : AlertCircle);
</script>

<SideDrawer bind:open {onOpenChange} title="Case Details">
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
		{:else if caseItem}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600"
					>
						<Briefcase class="h-6 w-6 text-white" />
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<h3 class="text-foreground text-lg font-semibold">
									{caseItem.subject}
								</h3>
							</div>
							{#if onEdit && caseItem.status !== 'Closed'}
								<Button variant="ghost" size="sm" onclick={onEdit} disabled={false}>Edit</Button>
							{/if}
						</div>
						{#if caseItem.account}
							<div class="text-muted-foreground mt-2 flex items-center gap-1.5 text-sm">
								<Building2 class="h-4 w-4" />
								<span>{caseItem.account.name}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Status, Priority and Type Badges -->
				<div class="mb-6 flex flex-wrap gap-3">
					<div>
						<p class="text-muted-foreground mb-1 text-xs font-medium tracking-wider uppercase">
							Status
						</p>
						<span
							class={cn(
								'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
								getStatusClass(caseItem.status)
							)}
						>
							<StatusIcon class="h-3.5 w-3.5" />
							{formatStatus(caseItem.status)}
						</span>
					</div>
					{#if caseItem.priority}
						<div>
							<p class="text-muted-foreground mb-1 text-xs font-medium tracking-wider uppercase">
								Priority
							</p>
							<span
								class={cn(
									'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
									getPriorityClass(caseItem.priority)
								)}
							>
								<Flag class="h-3.5 w-3.5" />
								{caseItem.priority}
							</span>
						</div>
					{/if}
					{#if caseItem.caseType}
						<div>
							<p class="text-muted-foreground mb-1 text-xs font-medium tracking-wider uppercase">
								Type
							</p>
							<span
								class={cn(
									'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
									getCaseTypeClass(caseItem.caseType)
								)}
							>
								<Tag class="h-3.5 w-3.5" />
								{caseItem.caseType}
							</span>
						</div>
					{/if}
				</div>

				<!-- Description -->
				{#if caseItem.description}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Description
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm whitespace-pre-wrap">
								{caseItem.description}
							</p>
						</div>
					</div>
				{/if}

				<Separator class="mb-6" />

				<!-- Details Grid -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Details
					</p>
					<div class="grid grid-cols-2 gap-4">
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Building2 class="h-3.5 w-3.5" />
								<span>Account</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{caseItem.account?.name || 'None'}
							</p>
						</div>
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Clock class="h-3.5 w-3.5" />
								<span>Created</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{formatDate(caseItem.createdAt)}
							</p>
						</div>
						{#if caseItem.closedOn}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Calendar class="h-3.5 w-3.5" />
									<span>Closed On</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatDate(caseItem.closedOn)}
								</p>
							</div>
						{/if}
						{#if caseItem.createdBy}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<User class="h-3.5 w-3.5" />
									<span>Created By</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{caseItem.createdBy.name}
								</p>
							</div>
						{/if}
					</div>
				</div>

				<!-- Assigned To Section -->
				{#if caseItem.assignedTo && caseItem.assignedTo.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Assigned To
						</p>
						<div class="flex flex-wrap gap-2">
							{#each caseItem.assignedTo as assignee}
								<Badge variant="secondary" class="gap-1">
									<User class="h-3 w-3" />
									{assignee.name}
								</Badge>
							{/each}
						</div>
					</div>
				{:else if caseItem.owner}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Assigned To
						</p>
						<Badge variant="secondary" class="gap-1">
							<User class="h-3 w-3" />
							{caseItem.owner.name}
						</Badge>
					</div>
				{/if}

				<!-- Teams Section -->
				{#if caseItem.teams && caseItem.teams.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Teams
						</p>
						<div class="flex flex-wrap gap-2">
							{#each caseItem.teams as team}
								<Badge variant="outline" class="gap-1">
									<Users class="h-3 w-3" />
									{team.name}
								</Badge>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Contacts Section -->
				{#if caseItem.contacts && caseItem.contacts.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Related Contacts
						</p>
						<div class="space-y-2">
							{#each caseItem.contacts as contact}
								<div class="bg-muted/50 flex items-center gap-2 rounded-lg p-2">
									<div
										class="bg-primary/10 text-primary flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium"
									>
										{contact.name.charAt(0).toUpperCase()}
									</div>
									<div class="min-w-0 flex-1">
										<p class="text-foreground text-sm font-medium">{contact.name}</p>
										{#if contact.email}
											<p class="text-muted-foreground flex items-center gap-1 text-xs">
												<Mail class="h-3 w-3" />
												{contact.email}
											</p>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<Separator class="mb-6" />

				<!-- Activity Timeline -->
				<div>
					<div class="mb-3 flex items-center gap-2">
						<Activity class="text-muted-foreground h-4 w-4" />
						<p class="text-muted-foreground text-xs font-medium tracking-wider uppercase">
							Activity
						</p>
					</div>
					{#if caseItem.comments && caseItem.comments.length > 0}
						<div class="space-y-3">
							{#each caseItem.comments.slice(0, 5) as comment (comment.id)}
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
		{#if caseItem}
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
					{#if caseItem.status === 'Closed' && onReopen}
						<Button variant="outline" onclick={onReopen} disabled={false}>Reopen Case</Button>
					{:else if caseItem.status !== 'Closed' && onClose}
						<Button variant="outline" onclick={onClose} disabled={false}>Close Case</Button>
					{/if}
					{#if onEdit && caseItem.status !== 'Closed'}
						<Button variant="default" onclick={onEdit} disabled={false}>Edit Case</Button>
					{/if}
				</div>
			</div>
		{/if}
	{/snippet}
</SideDrawer>
