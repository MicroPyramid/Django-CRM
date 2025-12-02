<script>
	import {
		Users,
		Target,
		Building,
		Phone,
		CheckSquare,
		DollarSign,
		TrendingUp,
		Calendar,
		AlertCircle,
		ChevronRight
	} from '@lucide/svelte';
	import { KPICard, StatsGrid, RecentItemsCard, ActivityFeed } from '$lib/components/dashboard';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	/** @type {{ data: any }} */
	let { data } = $props();

	const metrics = $derived(data.metrics || {});
	const recentData = $derived(data.recentData || {});

	/**
	 * Format currency values
	 * @param {number} amount
	 */
	function formatCurrency(amount) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	/**
	 * Format date for display
	 * @param {string} date
	 */
	function formatDate(date) {
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
		});
	}

	/**
	 * Get status badge variant
	 * @param {string} status
	 */
	function getStatusVariant(status) {
		const variants =
			/** @type {{ [key: string]: 'default' | 'secondary' | 'destructive' | 'outline' }} */ ({
				NEW: 'default',
				PENDING: 'secondary',
				CONTACTED: 'outline',
				QUALIFIED: 'default',
				High: 'destructive',
				Normal: 'secondary',
				Low: 'outline'
			});
		return variants[status] || 'secondary';
	}

	/**
	 * Get status badge color class
	 * @param {string} status
	 */
	function getStatusClass(status) {
		const classes = /** @type {{ [key: string]: string }} */ ({
			NEW: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			PENDING: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
			CONTACTED: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
			QUALIFIED: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
			High: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
			Normal: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
			Low: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
		});
		return classes[status] || 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
	}
</script>

<svelte:head>
	<title>Dashboard - BottleCRM</title>
</svelte:head>

<div class="space-y-6 p-6">
	<!-- Header -->
	<div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
		<div>
			<h1 class="text-foreground text-2xl font-semibold">Dashboard</h1>
			<p class="text-muted-foreground text-sm">
				Welcome back! Here's what's happening with your CRM.
			</p>
		</div>
	</div>

	{#if data.error}
		<div
			class="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
		>
			<AlertCircle class="h-5 w-5 text-red-500 dark:text-red-400" />
			<span class="text-sm text-red-700 dark:text-red-300">{data.error}</span>
		</div>
	{:else}
		<!-- KPI Cards Grid -->
		<StatsGrid>
			<KPICard
				label="Active Leads"
				value={metrics.totalLeads}
				iconBgClass="bg-blue-100 dark:bg-blue-900/30"
				iconClass="text-blue-600 dark:text-blue-400"
			>
				{#snippet icon()}
					<Users class="h-5 w-5" />
				{/snippet}
			</KPICard>

			<KPICard
				label="Opportunities"
				value={metrics.totalOpportunities}
				iconBgClass="bg-green-100 dark:bg-green-900/30"
				iconClass="text-green-600 dark:text-green-400"
			>
				{#snippet icon()}
					<Target class="h-5 w-5" />
				{/snippet}
			</KPICard>

			<KPICard
				label="Accounts"
				value={metrics.totalAccounts}
				iconBgClass="bg-purple-100 dark:bg-purple-900/30"
				iconClass="text-purple-600 dark:text-purple-400"
			>
				{#snippet icon()}
					<Building class="h-5 w-5" />
				{/snippet}
			</KPICard>

			<KPICard
				label="Contacts"
				value={metrics.totalContacts}
				iconBgClass="bg-orange-100 dark:bg-orange-900/30"
				iconClass="text-orange-600 dark:text-orange-400"
			>
				{#snippet icon()}
					<Phone class="h-5 w-5" />
				{/snippet}
			</KPICard>

			<KPICard
				label="Pending Tasks"
				value={metrics.pendingTasks}
				iconBgClass="bg-yellow-100 dark:bg-yellow-900/30"
				iconClass="text-yellow-600 dark:text-yellow-400"
			>
				{#snippet icon()}
					<CheckSquare class="h-5 w-5" />
				{/snippet}
			</KPICard>

			<KPICard
				label="Pipeline Value"
				value={formatCurrency(metrics.opportunityRevenue)}
				iconBgClass="bg-emerald-100 dark:bg-emerald-900/30"
				iconClass="text-emerald-600 dark:text-emerald-400"
			>
				{#snippet icon()}
					<DollarSign class="h-5 w-5" />
				{/snippet}
			</KPICard>
		</StatsGrid>

		<!-- Content Grid -->
		<div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
			<!-- Recent Leads -->
			<RecentItemsCard title="Recent Leads" isEmpty={!recentData.leads?.length}>
				{#snippet icon()}
					<TrendingUp class="h-5 w-5" />
				{/snippet}
				{#snippet headerAction()}
					<Button variant="ghost" size="sm" href="/leads" class="text-xs" disabled={false}>
						View all
						<ChevronRight class="ml-1 h-3 w-3" />
					</Button>
				{/snippet}
				{#snippet empty()}
					<Users class="text-muted-foreground/50 mb-2 h-10 w-10" />
					<p class="text-muted-foreground text-sm">No recent leads</p>
				{/snippet}
				<div class="space-y-3">
					{#each recentData.leads || [] as lead (lead.id)}
						<a
							href="/leads/{lead.id}"
							class="hover:bg-muted -mx-2 flex items-center justify-between rounded-lg p-2 transition-colors"
						>
							<div class="min-w-0 flex-1">
								<p class="text-foreground truncate text-sm font-medium">
									{lead.firstName}
									{lead.lastName}
								</p>
								<p class="text-muted-foreground truncate text-xs">
									{lead.company || 'No company'}
								</p>
							</div>
							<div class="ml-4 flex-shrink-0 text-right">
								<span
									class="inline-block rounded-full px-2 py-0.5 text-xs font-medium {getStatusClass(
										lead.status
									)}"
								>
									{lead.status}
								</span>
								<p class="text-muted-foreground mt-1 text-xs">
									{formatDate(lead.createdAt)}
								</p>
							</div>
						</a>
					{/each}
				</div>
			</RecentItemsCard>

			<!-- Recent Opportunities -->
			<RecentItemsCard title="Recent Opportunities" isEmpty={!recentData.opportunities?.length}>
				{#snippet icon()}
					<Target class="h-5 w-5" />
				{/snippet}
				{#snippet headerAction()}
					<Button variant="ghost" size="sm" href="/opportunities" class="text-xs" disabled={false}>
						View all
						<ChevronRight class="ml-1 h-3 w-3" />
					</Button>
				{/snippet}
				{#snippet empty()}
					<Target class="text-muted-foreground/50 mb-2 h-10 w-10" />
					<p class="text-muted-foreground text-sm">No recent opportunities</p>
				{/snippet}
				<div class="space-y-3">
					{#each recentData.opportunities || [] as opportunity (opportunity.id)}
						<a
							href="/opportunities/{opportunity.id}"
							class="hover:bg-muted -mx-2 flex items-center justify-between rounded-lg p-2 transition-colors"
						>
							<div class="min-w-0 flex-1">
								<p class="text-foreground truncate text-sm font-medium">
									{opportunity.name}
								</p>
								<p class="text-muted-foreground truncate text-xs">
									{opportunity.account?.name || 'No account'}
								</p>
							</div>
							<div class="ml-4 flex-shrink-0 text-right">
								{#if opportunity.amount}
									<p class="text-sm font-medium text-[var(--status-success)]">
										{formatCurrency(opportunity.amount)}
									</p>
								{/if}
								<p class="text-muted-foreground text-xs">
									{formatDate(opportunity.createdAt)}
								</p>
							</div>
						</a>
					{/each}
				</div>
			</RecentItemsCard>

			<!-- Upcoming Tasks -->
			<RecentItemsCard title="Upcoming Tasks" isEmpty={!recentData.tasks?.length}>
				{#snippet icon()}
					<Calendar class="h-5 w-5" />
				{/snippet}
				{#snippet headerAction()}
					<Button variant="ghost" size="sm" href="/tasks" class="text-xs" disabled={false}>
						View all
						<ChevronRight class="ml-1 h-3 w-3" />
					</Button>
				{/snippet}
				{#snippet empty()}
					<CheckSquare class="text-muted-foreground/50 mb-2 h-10 w-10" />
					<p class="text-muted-foreground text-sm">No upcoming tasks</p>
				{/snippet}
				<div class="space-y-3">
					{#each recentData.tasks || [] as task (task.id)}
						<a
							href="/tasks/{task.id}"
							class="hover:bg-muted -mx-2 flex items-center justify-between rounded-lg p-2 transition-colors"
						>
							<div class="min-w-0 flex-1">
								<p class="text-foreground truncate text-sm font-medium">
									{task.subject}
								</p>
								<p class="text-muted-foreground truncate text-xs">
									{task.status}
								</p>
							</div>
							<div class="ml-4 flex-shrink-0 text-right">
								<span
									class="inline-block rounded-full px-2 py-0.5 text-xs font-medium {getStatusClass(
										task.priority
									)}"
								>
									{task.priority}
								</span>
								{#if task.dueDate}
									<p class="text-muted-foreground mt-1 text-xs">
										{formatDate(task.dueDate)}
									</p>
								{/if}
							</div>
						</a>
					{/each}
				</div>
			</RecentItemsCard>
		</div>

		<!-- Activity Feed -->
		<ActivityFeed activities={recentData.activities || []} />
	{/if}
</div>
