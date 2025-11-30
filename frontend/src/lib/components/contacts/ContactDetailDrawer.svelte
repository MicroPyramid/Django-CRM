<script>
	import {
		Mail,
		Phone,
		Building2,
		Briefcase,
		Calendar,
		User,
		MapPin,
		MessageSquare,
		Activity,
		Loader2,
		Copy,
		Check,
		Linkedin,
		PhoneOff,
		Tag
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { cn } from '$lib/utils.js';
	import { getCountryName } from '$lib/constants/countries.js';

	/**
	 * @typedef {Object} Contact
	 * @property {string} id
	 * @property {string} firstName
	 * @property {string} lastName
	 * @property {string} [email]
	 * @property {string} [phone]
	 * @property {string} [organization]
	 * @property {string} [title]
	 * @property {string} [department]
	 * @property {boolean} [doNotCall]
	 * @property {string} [linkedInUrl]
	 * @property {string} [description]
	 * @property {string} [addressLine]
	 * @property {string} [city]
	 * @property {string} [state]
	 * @property {string} [postcode]
	 * @property {string} [country]
	 * @property {string} createdAt
	 * @property {{name: string, email?: string}} [owner]
	 * @property {Array<{account: {id: string, name: string}}>} [relatedAccounts]
	 * @property {Array<{id: string, name: string}>} [teams]
	 * @property {Array<{id: string, name: string}>} [tags]
	 * @property {{tasks: number, opportunities: number}} [_count]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   contact?: Contact | null,
	 *   loading?: boolean,
	 *   onEdit?: () => void,
	 *   onDelete?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		contact = null,
		loading = false,
		onEdit,
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
	 * @param {Contact} contact
	 */
	function getFullName(contact) {
		return `${contact.firstName} ${contact.lastName}`.trim();
	}

	/**
	 * Get initials for avatar
	 * @param {Contact} contact
	 */
	function getInitials(contact) {
		const first = contact.firstName?.[0] || '';
		const last = contact.lastName?.[0] || '';
		return (first + last).toUpperCase();
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
	 * Format phone for display
	 * @param {string} phone
	 */
	function formatPhone(phone) {
		if (!phone) return '';
		// Basic phone formatting
		return phone.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
	}

	/**
	 * Get formatted address
	 * @param {Contact} contact
	 */
	function getFormattedAddress(contact) {
		const parts = [];
		if (contact.addressLine) parts.push(contact.addressLine);

		const cityStateZip = [contact.city, contact.state, contact.postcode]
			.filter(Boolean)
			.join(', ');

		if (cityStateZip) parts.push(cityStateZip);
		if (contact.country) parts.push(getCountryName(contact.country));

		return parts.join('\n');
	}
</script>

<SideDrawer bind:open {onOpenChange} title="Contact Details">
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
				<Separator class="my-4" />
				<div class="grid grid-cols-2 gap-4">
					{#each { length: 6 } as _}
						<div class="space-y-1">
							<Skeleton class="h-3 w-16" />
							<Skeleton class="h-5 w-24" />
						</div>
					{/each}
				</div>
			</div>
		{:else if contact}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-lg font-semibold text-white"
					>
						{getInitials(contact)}
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<h3 class="text-foreground text-lg font-semibold">
									{getFullName(contact)}
								</h3>
								{#if contact.title}
									<p class="text-muted-foreground text-sm">{contact.title}</p>
								{/if}
							</div>
							{#if onEdit}
								<Button variant="ghost" size="sm" class="" onclick={onEdit} disabled={false}>
									Edit
								</Button>
							{/if}
						</div>
						{#if contact.organization}
							<div class="text-muted-foreground mt-2 flex items-center gap-1.5 text-sm">
								<Building2 class="h-4 w-4" />
								<span>{contact.organization}</span>
							</div>
						{/if}
						{#if contact.department}
							<div class="text-muted-foreground mt-1 flex items-center gap-1.5 text-sm">
								<Briefcase class="h-4 w-4" />
								<span>{contact.department}</span>
							</div>
						{/if}
						{#if contact.doNotCall}
							<Badge variant="destructive" class="mt-2">
								<PhoneOff class="mr-1 h-3 w-3" />
								Do Not Call
							</Badge>
						{/if}
					</div>
				</div>

				<!-- Contact Info -->
				<div class="mb-6 space-y-2">
					{#if contact.email}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Mail class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href="mailto:{contact.email}"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{contact.email}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(contact.email || '', 'email')}
							>
								{#if copiedField === 'email'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
					{#if contact.phone}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Phone class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href="tel:{contact.phone}"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{formatPhone(contact.phone)}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(contact.phone || '', 'phone')}
							>
								{#if copiedField === 'phone'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
					{#if contact.linkedInUrl}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Linkedin class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href={contact.linkedInUrl}
									target="_blank"
									rel="noopener noreferrer"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									LinkedIn Profile
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(contact.linkedInUrl || '', 'linkedin')}
							>
								{#if copiedField === 'linkedin'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
				</div>

				<!-- Related Accounts -->
				{#if contact.relatedAccounts && contact.relatedAccounts.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Accounts
						</p>
						<div class="space-y-2">
							{#each contact.relatedAccounts as rel}
								<a
									href="/accounts/{rel.account.id}"
									class="bg-muted/50 text-foreground hover:bg-muted flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors"
								>
									<Building2 class="text-muted-foreground h-4 w-4" />
									{rel.account.name}
								</a>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Tags -->
				{#if contact.tags && contact.tags.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Tags
						</p>
						<div class="flex flex-wrap gap-2">
							{#each contact.tags as tag}
								<Badge variant="secondary">
									<Tag class="mr-1 h-3 w-3" />
									{tag.name}
								</Badge>
							{/each}
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
						{#if contact.organization}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Building2 class="h-3.5 w-3.5" />
									<span>Company</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{contact.organization}
								</p>
							</div>
						{/if}
						{#if contact.department}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Briefcase class="h-3.5 w-3.5" />
									<span>Department</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{contact.department}
								</p>
							</div>
						{/if}
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<User class="h-3.5 w-3.5" />
								<span>Owner</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{contact.owner?.name || 'Unassigned'}
							</p>
						</div>
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Calendar class="h-3.5 w-3.5" />
								<span>Created</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{formatDate(contact.createdAt)}
							</p>
						</div>
						{#if contact._count}
							{#if contact._count.tasks > 0}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<Activity class="h-3.5 w-3.5" />
										<span>Tasks</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{contact._count.tasks}
									</p>
								</div>
							{/if}
							{#if contact._count.opportunities > 0}
								<div>
									<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
										<Activity class="h-3.5 w-3.5" />
										<span>Opportunities</span>
									</div>
									<p class="text-foreground mt-0.5 text-sm font-medium">
										{contact._count.opportunities}
									</p>
								</div>
							{/if}
						{/if}
					</div>
				</div>

				<!-- Teams -->
				{#if contact.teams && contact.teams.length > 0}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Teams
						</p>
						<div class="flex flex-wrap gap-2">
							{#each contact.teams as team}
								<Badge variant="outline">{team.name}</Badge>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Address -->
				{#if contact.addressLine || contact.city || contact.state || contact.postcode || contact.country}
					{@const address = getFormattedAddress(contact)}
					{#if address}
						<div class="mb-6">
							<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
								Address
							</p>
							<div class="bg-muted/50 flex items-start gap-2 rounded-lg p-3">
								<MapPin class="text-muted-foreground mt-0.5 h-4 w-4 shrink-0" />
								<p class="text-foreground text-sm whitespace-pre-line">
									{address}
								</p>
							</div>
						</div>
					{/if}
				{/if}

				<!-- Description -->
				{#if contact.description}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Notes
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm whitespace-pre-wrap">
								{contact.description}
							</p>
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		{#if contact}
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
				{:else}
					<div></div>
				{/if}
				{#if onEdit}
					<Button variant="default" class="" onclick={onEdit} disabled={false}>Edit Contact</Button>
				{/if}
			</div>
		{/if}
	{/snippet}
</SideDrawer>
