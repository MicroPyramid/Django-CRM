<script>
	import {
		Globe,
		Phone,
		Mail,
		MapPin,
		Calendar,
		Users,
		Target,
		DollarSign,
		Briefcase,
		Copy,
		Check,
		Lock,
		Unlock,
		AlertTriangle
	} from '@lucide/svelte';
	import SideDrawer from '$lib/components/layout/SideDrawer.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';

	/**
	 * @typedef {Object} Account
	 * @property {string} id
	 * @property {string} name
	 * @property {string} [industry]
	 * @property {string} [website]
	 * @property {string} [phone]
	 * @property {string} [email]
	 * @property {string} [description]
	 * @property {string} [addressLine]
	 * @property {string} [city]
	 * @property {string} [state]
	 * @property {string} [postcode]
	 * @property {string} [country]
	 * @property {number} [annualRevenue]
	 * @property {number} [numberOfEmployees]
	 * @property {boolean} [isActive]
	 * @property {string} [closedAt]
	 * @property {string} [closureReason]
	 * @property {string} createdAt
	 * @property {string} [updatedAt]
	 * @property {{name: string, email?: string}} [owner]
	 * @property {number} [contactCount]
	 * @property {number} [opportunityCount]
	 * @property {number} [caseCount]
	 * @property {Array<{id: string, name: string}>} [tags]
	 * @property {Array<{id: string, name: string}>} [teams]
	 */

	/**
	 * @type {{
	 *   open?: boolean,
	 *   onOpenChange?: (open: boolean) => void,
	 *   account?: Account | null,
	 *   loading?: boolean,
	 *   onEdit?: () => void,
	 *   onClose?: () => void,
	 *   onReopen?: () => void,
	 *   onAddContact?: () => void,
	 *   onAddOpportunity?: () => void,
	 * }}
	 */
	let {
		open = $bindable(false),
		onOpenChange,
		account = null,
		loading = false,
		onEdit,
		onClose,
		onReopen,
		onAddContact,
		onAddOpportunity
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
	 * Get initials for avatar
	 * @param {Account} account
	 */
	function getInitials(account) {
		return (account.name?.[0] || 'A').toUpperCase();
	}

	/**
	 * Format date
	 * @param {string | null | undefined} date
	 */
	function formatDate(date) {
		if (!date) return '-';
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	/**
	 * Format currency
	 * @param {number | null | undefined} value
	 */
	function formatCurrency(value) {
		if (!value) return '-';
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
	}

	/**
	 * Format number
	 * @param {number | null | undefined} value
	 */
	function formatNumber(value) {
		if (!value) return '-';
		return new Intl.NumberFormat('en-US').format(value);
	}

	/**
	 * Get formatted address
	 * @param {Account} account
	 */
	function getFormattedAddress(account) {
		const parts = [];
		if (account.addressLine) parts.push(account.addressLine);

		const cityStateZip = [account.city, account.state, account.postcode]
			.filter(Boolean)
			.join(', ');

		if (cityStateZip) parts.push(cityStateZip);
		if (account.country) parts.push(account.country);

		return parts.join('\n');
	}

	/**
	 * Format website URL for display
	 * @param {string} website
	 */
	function formatWebsite(website) {
		return website.replace(/^https?:\/\//, '');
	}

	/**
	 * Get full website URL
	 * @param {string} website
	 */
	function getWebsiteUrl(website) {
		return website.startsWith('http') ? website : `https://${website}`;
	}
</script>

<SideDrawer bind:open {onOpenChange} title="Account Details">
	{#snippet children()}
		{#if loading}
			<!-- Loading skeleton -->
			<div class="space-y-6 p-6">
				<div class="flex items-start gap-4">
					<Skeleton class="h-14 w-14 rounded-lg" />
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
		{:else if account}
			<div class="p-6">
				<!-- Primary Info Section -->
				<div class="mb-6 flex items-start gap-4">
					<div
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 text-lg font-semibold text-white"
					>
						{getInitials(account)}
					</div>
					<div class="min-w-0 flex-1">
						<div class="flex items-start justify-between gap-2">
							<div>
								<h3 class="text-foreground text-lg font-semibold">
									{account.name}
								</h3>
								<div class="mt-1 flex flex-wrap items-center gap-2">
									{#if account.isActive !== false}
										<Badge variant="default" class="bg-green-500 hover:bg-green-600">Active</Badge>
									{:else}
										<Badge variant="secondary" class="bg-gray-500">Closed</Badge>
									{/if}
								</div>
							</div>
							{#if onEdit && !account.closedAt}
								<Button variant="ghost" size="sm" onclick={onEdit} disabled={false}>Edit</Button>
							{/if}
						</div>
						{#if account.industry}
							<div class="text-muted-foreground mt-2 flex items-center gap-1.5 text-sm">
								<Briefcase class="h-4 w-4" />
								<span>{account.industry}</span>
							</div>
						{/if}
					</div>
				</div>

				<!-- Closure Warning -->
				{#if account.closedAt}
					<div class="border-destructive/50 bg-destructive/10 mb-6 rounded-lg border p-4">
						<div class="flex gap-3">
							<AlertTriangle class="text-destructive h-5 w-5 shrink-0" />
							<div>
								<p class="text-destructive font-medium">
									Account closed on {formatDate(account.closedAt)}
								</p>
								{#if account.closureReason}
									<p class="text-muted-foreground mt-1 text-sm">
										Reason: {account.closureReason}
									</p>
								{/if}
							</div>
						</div>
					</div>
				{/if}

				<!-- Contact Info -->
				<div class="mb-6 space-y-2">
					{#if account.website}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Globe class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href={getWebsiteUrl(account.website)}
									target="_blank"
									rel="noopener noreferrer"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{formatWebsite(account.website)}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(account.website || '', 'website')}
							>
								{#if copiedField === 'website'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
					{#if account.phone}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Phone class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href="tel:{account.phone}"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{account.phone}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(account.phone || '', 'phone')}
							>
								{#if copiedField === 'phone'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
					{#if account.email}
						<div class="group bg-muted/50 flex items-center justify-between rounded-lg px-3 py-2">
							<div class="flex min-w-0 items-center gap-2">
								<Mail class="text-muted-foreground h-4 w-4 shrink-0" />
								<a
									href="mailto:{account.email}"
									class="text-foreground truncate text-sm hover:text-[var(--accent-primary)]"
								>
									{account.email}
								</a>
							</div>
							<button
								class="shrink-0 p-1 opacity-0 transition-opacity group-hover:opacity-100"
								onclick={() => copyToClipboard(account.email || '', 'email')}
							>
								{#if copiedField === 'email'}
									<Check class="h-4 w-4 text-[var(--status-success)]" />
								{:else}
									<Copy class="text-muted-foreground h-4 w-4" />
								{/if}
							</button>
						</div>
					{/if}
				</div>

				<!-- Related Entities Stats -->
				<div class="mb-6 grid grid-cols-3 gap-3">
					<div class="bg-muted/50 rounded-lg p-3 text-center">
						<div class="text-muted-foreground flex items-center justify-center gap-1.5">
							<Users class="h-4 w-4" />
						</div>
						<p class="text-foreground mt-1 text-xl font-semibold">
							{account.contactCount || 0}
						</p>
						<p class="text-muted-foreground text-xs">Contacts</p>
					</div>
					<div class="bg-muted/50 rounded-lg p-3 text-center">
						<div class="text-muted-foreground flex items-center justify-center gap-1.5">
							<Target class="h-4 w-4" />
						</div>
						<p class="text-foreground mt-1 text-xl font-semibold">
							{account.opportunityCount || 0}
						</p>
						<p class="text-muted-foreground text-xs">Opportunities</p>
					</div>
					<div class="bg-muted/50 rounded-lg p-3 text-center">
						<div class="text-muted-foreground flex items-center justify-center gap-1.5">
							<AlertTriangle class="h-4 w-4" />
						</div>
						<p class="text-foreground mt-1 text-xl font-semibold">
							{account.caseCount || 0}
						</p>
						<p class="text-muted-foreground text-xs">Cases</p>
					</div>
				</div>

				<Separator class="mb-6" />

				<!-- Details Grid -->
				<div class="mb-6">
					<p class="text-muted-foreground mb-3 text-xs font-medium tracking-wider uppercase">
						Details
					</p>
					<div class="grid grid-cols-2 gap-4">
						{#if account.annualRevenue}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<DollarSign class="h-3.5 w-3.5" />
									<span>Annual Revenue</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatCurrency(account.annualRevenue)}
								</p>
							</div>
						{/if}
						{#if account.numberOfEmployees}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Users class="h-3.5 w-3.5" />
									<span>Employees</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatNumber(account.numberOfEmployees)}
								</p>
							</div>
						{/if}
						<div>
							<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
								<Calendar class="h-3.5 w-3.5" />
								<span>Created</span>
							</div>
							<p class="text-foreground mt-0.5 text-sm font-medium">
								{formatDate(account.createdAt)}
							</p>
						</div>
						{#if account.updatedAt}
							<div>
								<div class="text-muted-foreground flex items-center gap-1.5 text-xs">
									<Calendar class="h-3.5 w-3.5" />
									<span>Updated</span>
								</div>
								<p class="text-foreground mt-0.5 text-sm font-medium">
									{formatDate(account.updatedAt)}
								</p>
							</div>
						{/if}
					</div>
				</div>

				<!-- Address -->
				{#if account.addressLine || account.city || account.state || account.postcode || account.country}
					{@const address = getFormattedAddress(account)}
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
				{#if account.description}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Description
						</p>
						<div class="bg-muted/50 rounded-lg p-3">
							<p class="text-foreground text-sm whitespace-pre-wrap">
								{account.description}
							</p>
						</div>
					</div>
				{/if}

				<!-- Quick Actions -->
				{#if !account.closedAt && (onAddContact || onAddOpportunity)}
					<div class="mb-6">
						<p class="text-muted-foreground mb-2 text-xs font-medium tracking-wider uppercase">
							Quick Actions
						</p>
						<div class="flex gap-2">
							{#if onAddContact}
								<Button
									variant="outline"
									size="sm"
									onclick={onAddContact}
									class="flex-1"
									disabled={false}
								>
									<Users class="mr-1.5 h-4 w-4" />
									Add Contact
								</Button>
							{/if}
							{#if onAddOpportunity}
								<Button
									variant="outline"
									size="sm"
									onclick={onAddOpportunity}
									class="flex-1"
									disabled={false}
								>
									<Target class="mr-1.5 h-4 w-4" />
									Add Opportunity
								</Button>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	{/snippet}

	{#snippet footer()}
		{#if account}
			<div class="flex w-full items-center justify-between">
				{#if account.closedAt}
					{#if onReopen}
						<Button
							variant="outline"
							class="text-green-600 hover:text-green-700"
							onclick={onReopen}
							disabled={false}
						>
							<Unlock class="mr-2 h-4 w-4" />
							Reopen Account
						</Button>
					{:else}
						<div></div>
					{/if}
				{:else if onClose}
					<Button
						variant="ghost"
						class="text-destructive hover:text-destructive"
						onclick={onClose}
						disabled={false}
					>
						<Lock class="mr-2 h-4 w-4" />
						Close Account
					</Button>
				{:else}
					<div></div>
				{/if}
				{#if onEdit && !account.closedAt}
					<Button variant="default" onclick={onEdit} disabled={false}>Edit Account</Button>
				{/if}
			</div>
		{/if}
	{/snippet}
</SideDrawer>
