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
		Activity,
		AlertCircle,
		Plus,
		PlusCircle,
		Pencil,
		Trash2,
		Eye,
		MessageSquare,
		UserPlus
	} from '@lucide/svelte';

	/** @type {any} */
	export let data;

	$: metrics = data.metrics || {};
	$: recentData = data.recentData || {};

	function formatCurrency(/** @type {any} */ amount) {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(amount);
	}

	function formatDate(/** @type {any} */ date) {
		return new Date(date).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric'
		});
	}

	function getStatusColor(/** @type {any} */ status) {
		const colors = /** @type {{ [key: string]: string }} */ ({
			NEW: 'bg-blue-100 text-blue-800',
			PENDING: 'bg-yellow-100 text-yellow-800',
			CONTACTED: 'bg-green-100 text-green-800',
			QUALIFIED: 'bg-purple-100 text-purple-800',
			High: 'bg-red-100 text-red-800',
			Normal: 'bg-blue-100 text-blue-800',
			Low: 'bg-gray-100 text-gray-800'
		});
		return colors[status] || 'bg-gray-100 text-gray-800';
	}

	/**
	 * Get icon component and colors for activity action
	 * @param {string} action - The action type (CREATE, UPDATE, DELETE, etc.)
	 */
	function getActivityStyle(action) {
		const styles = /** @type {{ [key: string]: { bg: string, text: string, icon: string } }} */ ({
			CREATE: {
				bg: 'bg-green-100 dark:bg-green-900/30',
				text: 'text-green-600 dark:text-green-400',
				icon: 'plus'
			},
			UPDATE: {
				bg: 'bg-blue-100 dark:bg-blue-900/30',
				text: 'text-blue-600 dark:text-blue-400',
				icon: 'pencil'
			},
			DELETE: {
				bg: 'bg-red-100 dark:bg-red-900/30',
				text: 'text-red-600 dark:text-red-400',
				icon: 'trash'
			},
			VIEW: {
				bg: 'bg-gray-100 dark:bg-gray-700',
				text: 'text-gray-600 dark:text-gray-400',
				icon: 'eye'
			},
			COMMENT: {
				bg: 'bg-purple-100 dark:bg-purple-900/30',
				text: 'text-purple-600 dark:text-purple-400',
				icon: 'message'
			},
			ASSIGN: {
				bg: 'bg-orange-100 dark:bg-orange-900/30',
				text: 'text-orange-600 dark:text-orange-400',
				icon: 'user-plus'
			}
		});
		return (
			styles[action] || {
				bg: 'bg-gray-100 dark:bg-gray-700',
				text: 'text-gray-500 dark:text-gray-400',
				icon: 'activity'
			}
		);
	}

	/**
	 * Get the URL path for an entity type
	 * @param {string} entityType - The entity type
	 * @param {string} entityId - The entity ID
	 */
	function getEntityUrl(entityType, entityId) {
		const routes = /** @type {{ [key: string]: string }} */ ({
			Account: '/accounts',
			Lead: '/leads',
			Contact: '/contacts',
			Opportunity: '/opportunities',
			Case: '/cases',
			Task: '/tasks',
			Invoice: '/invoices',
			Event: '/events',
			Document: '/documents',
			Team: '/teams'
		});
		const basePath = routes[entityType] || '/';
		return `${basePath}/${entityId}`;
	}

	/**
	 * Get action verb for display
	 * @param {string} action - The action type
	 */
	function getActionVerb(action) {
		const verbs = /** @type {{ [key: string]: string }} */ ({
			CREATE: 'created',
			UPDATE: 'updated',
			DELETE: 'deleted',
			VIEW: 'viewed',
			COMMENT: 'commented on',
			ASSIGN: 'assigned'
		});
		return verbs[action] || action.toLowerCase();
	}
</script>

<svelte:head>
	<title>Dashboard - BottleCRM</title>
</svelte:head>

<div class="space-y-6 p-6">
	<!-- Header -->
	<div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
		<div>
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
			<p class="text-gray-600 dark:text-gray-400">
				Welcome back! Here's what's happening with your CRM.
			</p>
		</div>
	</div>

	{#if data.error}
		<div
			class="flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
		>
			<AlertCircle class="text-red-500 dark:text-red-400" size={20} />
			<span class="text-red-700 dark:text-red-300">{data.error}</span>
		</div>
	{:else}
		<!-- Metrics Cards -->
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Active Leads</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{metrics.totalLeads}</p>
					</div>
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30"
					>
						<Users class="text-blue-600 dark:text-blue-400" size={24} />
					</div>
				</div>
			</div>

			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Opportunities</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">
							{metrics.totalOpportunities}
						</p>
					</div>
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
					>
						<Target class="text-green-600 dark:text-green-400" size={24} />
					</div>
				</div>
			</div>

			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Accounts</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{metrics.totalAccounts}</p>
					</div>
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30"
					>
						<Building class="text-purple-600 dark:text-purple-400" size={24} />
					</div>
				</div>
			</div>

			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Contacts</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{metrics.totalContacts}</p>
					</div>
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-orange-100 dark:bg-orange-900/30"
					>
						<Phone class="text-orange-600 dark:text-orange-400" size={24} />
					</div>
				</div>
			</div>

			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Pending Tasks</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{metrics.pendingTasks}</p>
					</div>
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-yellow-100 dark:bg-yellow-900/30"
					>
						<CheckSquare class="text-yellow-600 dark:text-yellow-400" size={24} />
					</div>
				</div>
			</div>

			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-gray-600 dark:text-gray-400">Pipeline Value</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">
							{formatCurrency(metrics.opportunityRevenue)}
						</p>
					</div>
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900/30"
					>
						<DollarSign class="text-emerald-600 dark:text-emerald-400" size={24} />
					</div>
				</div>
			</div>
		</div>

		<!-- Content Grid -->
		<div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
			<!-- Recent Leads -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 p-6 dark:border-gray-700">
					<div class="flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Leads</h2>
						<TrendingUp class="text-gray-400 dark:text-gray-500" size={20} />
					</div>
				</div>
				<div class="p-6">
					{#if recentData.leads?.length > 0}
						<div class="space-y-4">
							{#each recentData.leads as lead}
								<div class="flex items-center justify-between">
									<div>
										<p class="font-medium text-gray-900 dark:text-white">
											{lead.firstName}
											{lead.lastName}
										</p>
										<p class="text-sm text-gray-500 dark:text-gray-400">
											{lead.company || 'No company'}
										</p>
									</div>
									<div class="text-right">
										<span
											class="inline-block rounded-full px-2 py-1 text-xs font-medium {getStatusColor(
												lead.status
											)}"
										>
											{lead.status}
										</span>
										<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
											{formatDate(lead.createdAt)}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<p class="py-8 text-center text-gray-500 dark:text-gray-400">No recent leads</p>
					{/if}
				</div>
			</div>

			<!-- Recent Opportunities -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 p-6 dark:border-gray-700">
					<div class="flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
							Recent Opportunities
						</h2>
						<Target class="text-gray-400 dark:text-gray-500" size={20} />
					</div>
				</div>
				<div class="p-6">
					{#if recentData.opportunities?.length > 0}
						<div class="space-y-4">
							{#each recentData.opportunities as opportunity}
								<div class="flex items-center justify-between">
									<div>
										<p class="font-medium text-gray-900 dark:text-white">{opportunity.name}</p>
										<p class="text-sm text-gray-500 dark:text-gray-400">
											{opportunity.account?.name || 'No account'}
										</p>
									</div>
									<div class="text-right">
										{#if opportunity.amount}
											<p class="font-medium text-green-600 dark:text-green-400">
												{formatCurrency(opportunity.amount)}
											</p>
										{/if}
										<p class="text-xs text-gray-500 dark:text-gray-400">
											{formatDate(opportunity.createdAt)}
										</p>
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<p class="py-8 text-center text-gray-500 dark:text-gray-400">No recent opportunities</p>
					{/if}
				</div>
			</div>

			<!-- Upcoming Tasks -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 p-6 dark:border-gray-700">
					<div class="flex items-center justify-between">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Upcoming Tasks</h2>
						<Calendar class="text-gray-400 dark:text-gray-500" size={20} />
					</div>
				</div>
				<div class="p-6">
					{#if recentData.tasks?.length > 0}
						<div class="space-y-4">
							{#each recentData.tasks as task}
								<div class="flex items-center justify-between">
									<div>
										<p class="font-medium text-gray-900 dark:text-white">{task.subject}</p>
										<p class="text-sm text-gray-500 dark:text-gray-400">{task.status}</p>
									</div>
									<div class="text-right">
										<span
											class="inline-block rounded-full px-2 py-1 text-xs font-medium {getStatusColor(
												task.priority
											)}"
										>
											{task.priority}
										</span>
										{#if task.dueDate}
											<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
												{formatDate(task.dueDate)}
											</p>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{:else}
						<p class="py-8 text-center text-gray-500 dark:text-gray-400">No upcoming tasks</p>
					{/if}
				</div>
			</div>
		</div>

		<!-- Recent Activities -->
		<div
			class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="border-b border-gray-200 p-6 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Activities</h2>
					<Activity class="text-gray-400 dark:text-gray-500" size={20} />
				</div>
			</div>
			<div class="p-6">
				{#if recentData.activities?.length > 0}
					<div class="space-y-4">
						{#each recentData.activities as activity}
							{@const style = getActivityStyle(activity.action)}
							<div class="flex items-start gap-3">
								<div
									class="h-8 w-8 {style.bg} flex flex-shrink-0 items-center justify-center rounded-full"
								>
									{#if style.icon === 'plus'}
										<PlusCircle class={style.text} size={16} />
									{:else if style.icon === 'pencil'}
										<Pencil class={style.text} size={16} />
									{:else if style.icon === 'trash'}
										<Trash2 class={style.text} size={16} />
									{:else if style.icon === 'eye'}
										<Eye class={style.text} size={16} />
									{:else if style.icon === 'message'}
										<MessageSquare class={style.text} size={16} />
									{:else if style.icon === 'user-plus'}
										<UserPlus class={style.text} size={16} />
									{:else}
										<Activity class={style.text} size={16} />
									{/if}
								</div>
								<div class="min-w-0 flex-1">
									<p class="text-sm text-gray-900 dark:text-white">
										<span class="font-medium">{activity.user?.name || 'Someone'}</span>
										{' '}{getActionVerb(activity.action)}{' '}
										<span class="text-gray-500 dark:text-gray-400"
											>{activity.entityType.toLowerCase()}</span
										>
										{#if activity.entityName && activity.action !== 'DELETE'}
											<a
												href={getEntityUrl(activity.entityType, activity.entityId)}
												class="font-medium text-blue-600 hover:underline dark:text-blue-400"
											>
												{activity.entityName}
											</a>
										{:else if activity.entityName}
											<span class="font-medium">{activity.entityName}</span>
										{/if}
									</p>
									<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
										{activity.humanizedTime || formatDate(activity.timestamp)}
									</p>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="py-8 text-center text-gray-500 dark:text-gray-400">No recent activities</p>
				{/if}
			</div>
		</div>
	{/if}
</div>
