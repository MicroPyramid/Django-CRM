<script>
	import { invalidateAll } from '$app/navigation';
	import {
		Mail,
		Phone,
		Building2,
		Briefcase,
		Calendar,
		Target,
		User,
		Star,
		MessageSquare,
		Activity,
		PlusCircle,
		Loader2,
		Copy,
		Check
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { cn } from '$lib/utils.js';

	/**
	 * @typedef {Object} Lead
	 * @property {string} id
	 * @property {string} firstName
	 * @property {string} lastName
	 * @property {string} [email]
	 * @property {string} [phone]
	 * @property {string | {id: string, name: string}} [company]
	 * @property {string} [title]
	 * @property {string} [contactTitle]
	 * @property {string} [website]
	 * @property {string} [linkedinUrl]
	 * @property {string} status
	 * @property {string} [leadSource]
	 * @property {string} [rating]
	 * @property {string} [industry]
	 * @property {string} [opportunityAmount]
	 * @property {number} [probability]
	 * @property {string} [closeDate]
	 * @property {string} [addressLine]
	 * @property {string} [city]
	 * @property {string} [state]
	 * @property {string} [postcode]
	 * @property {string} [country]
	 * @property {string} [lastContacted]
	 * @property {string} [nextFollowUp]
	 * @property {string} [description]
	 * @property {string} createdAt
	 * @property {{name: string, email?: string}} [owner]
	 * @property {Array<{id: string, body: string, createdAt: string, author?: {name: string}}>} [comments]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   lead?: Lead | null,
	 *   loading?: boolean,
	 *   onEdit?: () => void,
	 *   onConvert?: () => void,
	 *   onDelete?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		lead = null,
		loading = false,
		onEdit,
		onConvert,
		onDelete
	} = $props();

	let copiedField = $state('');

	/**
	 * Copy text to clipboard
	 * @param {string} text
	 * @param {string} field
	 */
	async function copyToClipboard(text, field) {
		await navigator.clipboard.writeText(text);
		copiedField = field;
		setTimeout(() => {
			copiedField = '';
		}, 2000);
	}

	/**
	 * Get full name
	 * @param {Lead} lead
	 */
	function getFullName(lead) {
		return `${lead.firstName} ${lead.lastName}`.trim();
	}

	/**
	 * Get initials for avatar
	 * @param {Lead} lead
	 */
	function getInitials(lead) {
		const first = lead.firstName?.[0] || '';
		const last = lead.lastName?.[0] || '';
		return (first + last).toUpperCase();
	}

	/**
	 * Get status badge classes
	 * @param {string} status
	 */
	function getStatusClass(status) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			ASSIGNED: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			IN_PROCESS: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			PENDING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			CONTACTED: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
			QUALIFIED: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
			CONVERTED: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
			RECYCLED: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
			CLOSED: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
		});
		return classes[status?.toUpperCase()] || classes.NEW;
	}

	/**
	 * Get rating config
	 * @param {string | undefined} rating
	 */
	function getRatingConfig(rating) {
		const configs = /** @type {{ [key: string]: { color: string, dots: number } }} */ ({
			HOT: { color: 'text-red-500', dots: 3 },
			WARM: { color: 'text-orange-500', dots: 2 },
			COLD: { color: 'text-blue-500', dots: 1 }
		});
		return configs[rating?.toUpperCase() || ''] || { color: 'text-gray-400', dots: 0 };
	}

	/**
	 * Format source for display
	 * @param {string | undefined} source
	 */
	function formatSource(source) {
		if (!source) return 'Unknown';
		return source
			.replace(/_/g, ' ')
			.toLowerCase()
			.replace(/\b\w/g, (l) => l.toUpperCase());
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
</script>

<SideDrawer bind:open {onOpenChange} title="Lead Details">
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="flex items-start gap-4">
					<Skeleton class="h-14 w-14 rounded-full" />
					<div class="flex-1 space-y-2">
						<Skeleton class="h-6 w-48" />
						<Skeleton class="h-4 w-32" />
					</div>
				</div>
				<div class="space-y-4">
					<Skeleton class="h-10 w-full" />
					<Skeleton class="h-10 w-full" />
				</div>
				<Separator class="" />
				<div class="grid grid-cols-2 gap-4">
					{#each { length: 6 } as _}
						<div class="space-y-1">
							<Skeleton class="h-3 w-16" />
							<Skeleton class="h-5 w-24" />
						</div>
					{/each}
				</div>
			</div>
		{:else if lead}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 text-lg font-semibold text-white"
					>
						{getInitials(lead)}
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<h3 class="text-foreground text-lg font-semibold">
									{getFullName(lead)}
								</h3>
								{#if lead.title}
									<p class="text-muted-foreground text-sm">{lead.title}</p>
								{/if}
							</div>
							{#if onEdit}
								<Button variant="ghost" size="sm" onclick={onEdit} disabled={false}>Edit</Button>
							{/if}
						</div>
						{#if lead.contactTitle}
							<p class="text-muted-foreground text-sm">{lead.contactTitle}</p>
						{/if}
						{#if lead.company}
							<div class="text-muted-foreground mt-2 flex items-center gap-1.5 text-sm">
								<Building2 class="h-4 w-4" />
								<span>{typeof lead.company === 'object' ? lead.company.name : lead.company}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Contact Info -->
				<div class="mb-6 space-y-2">
					{#if lead.email}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Mail class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href="mailto:{lead.email}"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{lead.email}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(lead.email || '', 'email')}
							>
								{#if copiedField === 'email'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
					{#if lead.phone}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Phone class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href="tel:{lead.phone}"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{lead.phone}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(lead.phone || '', 'phone')}
							>
								{#if copiedField === 'phone'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
				</div>

				<!-- Status -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
						Status
					</p>
					<span
						class={cn(
							'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
							getStatusClass(lead.status)
						)}
					>
						{lead.status}
					</span>
				</div>

				<Separator class="mb-6" />

				<!-- Contact Links -->
				{#if lead.website || lead.linkedinUrl}
					<div class="mb-6 space-y-2">
						{#if lead.website}
							<a
								href={lead.website}
								target="_blank"
								rel="noopener noreferrer"
								class="bg-muted/50 hover:bg-muted flex items-center gap-2 rounded-lg px-3 py-2 transition-colors"
							>
								<svg class="text-muted-foreground h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
								</svg>
								<span class="text-foreground truncate text-sm">{lead.website}</span>
							</a>
						{/if}
						{#if lead.linkedinUrl}
							<a
								href={lead.linkedinUrl}
								target="_blank"
								rel="noopener noreferrer"
								class="bg-muted/50 hover:bg-muted flex items-center gap-2 rounded-lg px-3 py-2 transition-colors"
							>
								<svg class="text-muted-foreground h-4 w-4" fill="currentColor" viewBox="0 0 24 24">
									<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
								</svg>
								<span class="text-foreground truncate text-sm">LinkedIn Profile</span>
							</a>
						{/if}
					</div>
				{/if}

				<Separator class="mb-6" />

				<!-- Details Grid -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Lead Details
					</p>
					<div class="grid grid-cols-2 gap-4">
						{#if lead.leadSource}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Target class="h-3.5 w-3.5" />
									<span>Source</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatSource(lead.leadSource)}
								</p>
							</div>
						{/if}
						{#if lead.rating}
							{@const ratingConfig = getRatingConfig(lead.rating)}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Star class="h-3.5 w-3.5" />
									<span>Rating</span>
								</div>
								<div class="mt-0.5 flex items-center gap-1">
									{#each { length: ratingConfig.dots } as _}
										<div
											class={cn('h-2 w-2 rounded-full', ratingConfig.color.replace('text-', 'bg-'))}
										></div>
									{/each}
									<span class={cn('text-sm font-medium', ratingConfig.color)}>
										{lead.rating}
									</span>
								</div>
							</div>
						{/if}
						{#if lead.industry}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Briefcase class="h-3.5 w-3.5" />
									<span>Industry</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium capitalize">
									{lead.industry.toLowerCase()}
								</p>
							</div>
						{/if}
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<User class="h-3.5 w-3.5" />
								<span>Owner</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{lead.owner?.name || 'Unassigned'}
							</p>
						</div>
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Calendar class="h-3.5 w-3.5" />
								<span>Created</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{formatDate(lead.createdAt)}
							</p>
						</div>
					</div>
				</div>

				<!-- Sales Pipeline Info -->
				{#if lead.opportunityAmount || lead.probability || lead.closeDate}
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Deal Information
						</p>
						<div class="grid grid-cols-2 gap-4">
							{#if lead.opportunityAmount}
								<div>
									<div class="text-muted-foreground text-xs">Deal Value</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										${parseFloat(lead.opportunityAmount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
									</p>
								</div>
							{/if}
							{#if lead.probability}
								<div>
									<div class="text-muted-foreground text-xs">Win Probability</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">{lead.probability}%</p>
								</div>
							{/if}
							{#if lead.closeDate}
								<div>
									<div class="text-muted-foreground text-xs">Expected Close Date</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">{formatDate(lead.closeDate)}</p>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Address -->
				{#if lead.addressLine || lead.city || lead.state || lead.country}
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Address
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm">
								{#if lead.addressLine}{lead.addressLine}<br />{/if}
								{#if lead.city || lead.state}
									{lead.city}{lead.city && lead.state ? ', ' : ''}{lead.state} {lead.postcode || ''}<br />
								{/if}
								{#if lead.country}{lead.country}{/if}
							</p>
						</div>
					</div>
				{/if}

				<!-- Activity Tracking -->
				{#if lead.lastContacted || lead.nextFollowUp}
					<div class="mb-6">
						<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
							Activity
						</p>
						<div class="grid grid-cols-2 gap-4">
							{#if lead.lastContacted}
								<div>
									<div class="text-muted-foreground text-xs">Last Contacted</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">{formatDate(lead.lastContacted)}</p>
								</div>
							{/if}
							{#if lead.nextFollowUp}
								<div>
									<div class="text-muted-foreground text-xs">Next Follow-up</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">{formatDate(lead.nextFollowUp)}</p>
								</div>
							{/if}
						</div>
					</div>
				{/if}

				<!-- Description -->
				{#if lead.description}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Description
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm whitespace-pre-wrap">
								{lead.description}
							</p>
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
					{#if lead.comments && lead.comments.length > 0}
						<div class="space-y-3">
							{#each lead.comments.slice(0, 5) as comment (comment.id)}
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
		{#if lead && lead.status !== 'CONVERTED'}
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
				{#if onConvert}
					<Button variant="default" onclick={onConvert} disabled={false}>
						<PlusCircle class="mr-2 h-4 w-4" />
						Convert to Deal
					</Button>
				{/if}
			</div>
		{:else if lead}
			<div class="flex w-full items-center justify-end">
				{#if onEdit}
					<Button variant="default" onclick={onEdit} disabled={false}>Edit Lead</Button>
				{/if}
			</div>
		{/if}
	{/snippet}
</SideDrawer>
