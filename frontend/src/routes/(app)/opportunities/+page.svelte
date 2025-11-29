<script>
	import {
		Search,
		Plus,
		Filter,
		SortAsc,
		MoreVertical,
		Eye,
		Edit,
		Trash2,
		DollarSign,
		TrendingUp,
		Users,
		Calendar,
		Building2,
		User,
		CheckCircle,
		XCircle,
		Clock,
		Target,
		X,
		AlertTriangle
	} from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { enhance } from '$app/forms';
	import { page } from '$app/stores';

	/** @type {{ data: import('./$types').PageData, form?: any }} */
	let { data, form } = $props();

	let searchTerm = $state('');
	let selectedStage = $state('all');
	let sortField = $state('createdAt');
	let sortDirection = $state('desc');
	let showFilters = $state(false);
	let showDeleteModal = $state(false);
	/** @type {any} */
	let opportunityToDelete = $state(null);
	let deleteLoading = $state(false);

	// Stage configurations
	const stageConfig = {
		PROSPECTING: {
			label: 'Prospecting',
			color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
			icon: Target
		},
		QUALIFICATION: {
			label: 'Qualification',
			color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
			icon: Search
		},
		PROPOSAL: {
			label: 'Proposal',
			color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
			icon: Edit
		},
		NEGOTIATION: {
			label: 'Negotiation',
			color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
			icon: Users
		},
		CLOSED_WON: {
			label: 'Closed Won',
			color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
			icon: CheckCircle
		},
		CLOSED_LOST: {
			label: 'Closed Lost',
			color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
			icon: XCircle
		}
	};

	// Simple filtering function that we'll call explicitly
	function getFilteredOpportunities() {
		if (!data?.opportunities || !Array.isArray(data.opportunities)) {
			return [];
		}

		let filtered = [...data.opportunities];

		// Search filter
		if (searchTerm && searchTerm.trim()) {
			const searchLower = searchTerm.toLowerCase().trim();
			filtered = filtered.filter((opp) => {
				const nameMatch = opp.name?.toLowerCase().includes(searchLower);
				const accountMatch = opp.account?.name?.toLowerCase().includes(searchLower);
				const ownerMatch =
					opp.owner?.name?.toLowerCase().includes(searchLower) ||
					opp.owner?.email?.toLowerCase().includes(searchLower);
				return nameMatch || accountMatch || ownerMatch;
			});
		}

		// Stage filter
		if (selectedStage && selectedStage !== 'all') {
			filtered = filtered.filter((opp) => opp.stage === selectedStage);
		}

		return filtered;
	}

	// Use $derived with the function
	const filteredOpportunities = $derived(getFilteredOpportunities());

	/**
	 * @param {number | null} amount
	 * @returns {string}
	 */
	function formatCurrency(amount) {
		if (!amount) return '-';
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	/**
	 * @param {string | Date | null} date
	 * @returns {string}
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
	 * @param {string} field
	 */
	function toggleSort(field) {
		if (sortField === field) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortField = field;
			sortDirection = 'asc';
		}
	}

	/**
	 * @param {any} opportunity
	 */
	function openDeleteModal(opportunity) {
		opportunityToDelete = opportunity;
		showDeleteModal = true;
	}

	function closeDeleteModal() {
		showDeleteModal = false;
		opportunityToDelete = null;
		deleteLoading = false;
	}
</script>

<svelte:head>
	<title>Opportunities - BottleCRM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Success/Error Messages -->
	{#if form?.success}
		<div class="fixed top-4 right-4 z-50 max-w-md">
			<div
				class="relative rounded border border-green-400 bg-green-100 px-4 py-3 text-green-700"
				role="alert"
			>
				<strong class="font-bold">Success!</strong>
				<span class="block sm:inline">{form.message || 'Opportunity deleted successfully.'}</span>
			</div>
		</div>
	{/if}

	{#if form?.message && !form?.success}
		<div class="fixed top-4 right-4 z-50 max-w-md">
			<div
				class="relative rounded border border-red-400 bg-red-100 px-4 py-3 text-red-700"
				role="alert"
			>
				<strong class="font-bold">Error!</strong>
				<span class="block sm:inline">{form.message}</span>
			</div>
		</div>
	{/if}

	<!-- Header -->
	<div class="bg-white shadow dark:bg-gray-800">
		<div class="px-4 sm:px-6 lg:px-8">
			<div class="flex h-16 items-center justify-between">
				<div class="flex items-center">
					<h1 class="text-2xl font-semibold text-gray-900 dark:text-white">Opportunities</h1>
				</div>
				<div class="flex items-center space-x-4">
					<a
						href="/opportunities/new"
						class="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:bg-blue-500 dark:hover:bg-blue-600"
					>
						<Plus class="mr-2 h-4 w-4" />
						New Opportunity
					</a>
				</div>
			</div>
		</div>
	</div>

	<!-- Stats Cards -->
	<div class="px-4 py-6 sm:px-6 lg:px-8">
		<div class="mb-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
			<div class="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<Target class="h-6 w-6 text-gray-400" />
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
									Total Opportunities
								</dt>
								<dd class="text-lg font-medium text-gray-900 dark:text-white">
									{data.stats.total}
								</dd>
							</dl>
						</div>
					</div>
				</div>
			</div>

			<div class="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<DollarSign class="h-6 w-6 text-gray-400" />
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
									Total Value
								</dt>
								<dd class="text-lg font-medium text-gray-900 dark:text-white">
									{formatCurrency(data.stats.totalValue)}
								</dd>
							</dl>
						</div>
					</div>
				</div>
			</div>

			<div class="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<TrendingUp class="h-6 w-6 text-green-400" />
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
									Pipeline Value
								</dt>
								<dd class="text-lg font-medium text-gray-900 dark:text-white">
									{formatCurrency(data.stats.pipeline)}
								</dd>
							</dl>
						</div>
					</div>
				</div>
			</div>

			<div class="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
				<div class="p-5">
					<div class="flex items-center">
						<div class="flex-shrink-0">
							<CheckCircle class="h-6 w-6 text-green-400" />
						</div>
						<div class="ml-5 w-0 flex-1">
							<dl>
								<dt class="truncate text-sm font-medium text-gray-500 dark:text-gray-400">
									Won Value
								</dt>
								<dd class="text-lg font-medium text-gray-900 dark:text-white">
									{formatCurrency(data.stats.wonValue)}
								</dd>
							</dl>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Filters and Search -->
		<div class="mb-6 rounded-lg bg-white shadow dark:bg-gray-800">
			<div class="p-6">
				<div class="flex flex-col gap-4 sm:flex-row">
					<!-- Search -->
					<div class="flex-1">
						<div class="relative">
							<label for="opportunities-search" class="sr-only">Search opportunities</label>
							<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
								<Search class="h-5 w-5 text-gray-400" />
							</div>
							<input
								type="text"
								id="opportunities-search"
								bind:value={searchTerm}
								placeholder="Search opportunities, accounts, or owners..."
								class="block w-full rounded-md border border-gray-300 bg-white py-2 pr-3 pl-10 leading-5 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
							/>
						</div>
					</div>

					<!-- Stage Filter -->
					<div class="sm:w-48">
						<label for="opportunities-stage-filter" class="sr-only"
							>Filter opportunities by stage</label
						>
						<select
							id="opportunities-stage-filter"
							bind:value={selectedStage}
							class="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
						>
							<option value="all">All Stages</option>
							{#each Object.entries(stageConfig) as [stage, config]}
								<option value={stage}>{config.label}</option>
							{/each}
						</select>
					</div>

					<!-- Filter Toggle -->
					<button
						type="button"
						onclick={() => (showFilters = !showFilters)}
						class="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
					>
						<Filter class="mr-2 h-4 w-4" />
						Filters
					</button>
				</div>
			</div>
		</div>

		<!-- Opportunities Table -->
		<div class="overflow-hidden rounded-lg bg-white shadow dark:bg-gray-800">
			<div class="min-w-full overflow-x-auto">
				<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
					<thead class="bg-gray-50 dark:bg-gray-700">
						<tr>
							<th
								class="cursor-pointer px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600"
								onclick={() => toggleSort('name')}
							>
								<div class="flex items-center space-x-1">
									<span>Opportunity</span>
									<SortAsc class="h-4 w-4" />
								</div>
							</th>
							<th
								class="cursor-pointer px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600"
								onclick={() => toggleSort('account.name')}
							>
								<div class="flex items-center space-x-1">
									<span>Account</span>
									<SortAsc class="h-4 w-4" />
								</div>
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
							>
								Stage
							</th>
							<th
								class="cursor-pointer px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600"
								onclick={() => toggleSort('amount')}
							>
								<div class="flex items-center space-x-1">
									<span>Amount</span>
									<SortAsc class="h-4 w-4" />
								</div>
							</th>
							<th
								class="cursor-pointer px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600"
								onclick={() => toggleSort('closeDate')}
							>
								<div class="flex items-center space-x-1">
									<span>Close Date</span>
									<SortAsc class="h-4 w-4" />
								</div>
							</th>
							<th
								class="cursor-pointer px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-600"
								onclick={() => toggleSort('owner.name')}
							>
								<div class="flex items-center space-x-1">
									<span>Owner</span>
									<SortAsc class="h-4 w-4" />
								</div>
							</th>
							<th
								class="px-6 py-3 text-left text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-300"
							>
								Activities
							</th>
							<th class="relative px-6 py-3">
								<span class="sr-only">Actions</span>
							</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
						{#each filteredOpportunities as opportunity (opportunity.id)}
							{@const config = stageConfig[opportunity.stage] || stageConfig.PROSPECTING}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div>
											<div class="text-sm font-medium text-gray-900 dark:text-white">
												{opportunity.name || 'Unnamed Opportunity'}
											</div>
											{#if opportunity.type}
												<div class="text-sm text-gray-500 dark:text-gray-400">
													{opportunity.type}
												</div>
											{/if}
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<Building2 class="mr-2 h-4 w-4 text-gray-400" />
										<div>
											<div class="text-sm font-medium text-gray-900 dark:text-white">
												{opportunity.account?.name || 'No Account'}
											</div>
											{#if opportunity.account?.type}
												<div class="text-sm text-gray-500 dark:text-gray-400">
													{opportunity.account.type}
												</div>
											{/if}
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span
										class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {config.color}"
									>
										{#if config.icon}
											{@const IconComponent = config.icon}
											<IconComponent class="mr-1 h-3 w-3" />
										{/if}
										{config.label}
									</span>
								</td>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-900 dark:text-white">
									{formatCurrency(opportunity.amount)}
									{#if opportunity.probability}
										<div class="text-xs text-gray-500 dark:text-gray-400">
											{opportunity.probability}% probability
										</div>
									{/if}
								</td>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-900 dark:text-white">
									<div class="flex items-center">
										<Calendar class="mr-2 h-4 w-4 text-gray-400" />
										{formatDate(opportunity.closeDate)}
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<User class="mr-2 h-4 w-4 text-gray-400" />
										<div class="text-sm font-medium text-gray-900 dark:text-white">
											{opportunity.owner?.name || opportunity.owner?.email || 'No Owner'}
										</div>
									</div>
								</td>
								<td class="px-6 py-4 text-sm whitespace-nowrap text-gray-500 dark:text-gray-400">
									<div class="flex items-center space-x-4">
										{#if opportunity._count?.tasks > 0}
											<span class="flex items-center">
												<Clock class="mr-1 h-4 w-4" />
												{opportunity._count.tasks}
											</span>
										{/if}
										{#if opportunity._count?.events > 0}
											<span class="flex items-center">
												<Calendar class="mr-1 h-4 w-4" />
												{opportunity._count.events}
											</span>
										{/if}
									</div>
								</td>
								<td class="px-6 py-4 text-right text-sm font-medium whitespace-nowrap">
									<div class="flex items-center justify-end space-x-2">
										<a
											href="/opportunities/{opportunity.id}"
											class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
											title="View"
										>
											<Eye class="h-4 w-4" />
										</a>
										<a
											href="/opportunities/{opportunity.id}/edit"
											class="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300"
											title="Edit"
										>
											<Edit class="h-4 w-4" />
										</a>
										<button
											type="button"
											onclick={() => openDeleteModal(opportunity)}
											class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
											title="Delete"
										>
											<Trash2 class="h-4 w-4" />
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			{#if filteredOpportunities.length === 0}
				<div class="py-12 text-center">
					<Target class="mx-auto h-12 w-12 text-gray-400" />
					<h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No opportunities</h3>
					<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
						{searchTerm || selectedStage !== 'all'
							? 'No opportunities match your current filters.'
							: 'Get started by creating a new opportunity.'}
					</p>
					{#if !searchTerm && selectedStage === 'all'}
						<div class="mt-6">
							<a
								href="/opportunities/new"
								class="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none"
							>
								<Plus class="mr-2 h-4 w-4" />
								New Opportunity
							</a>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && opportunityToDelete}
	<div
		class="bg-opacity-50 fixed inset-0 z-50 h-full w-full overflow-y-auto bg-gray-600"
		role="dialog"
		aria-modal="true"
		aria-labelledby="modal-title"
		tabindex="-1"
		onclick={closeDeleteModal}
		onkeydown={(e) => e.key === 'Escape' && closeDeleteModal()}
	>
		<div
			class="relative top-20 mx-auto w-96 rounded-md border bg-white p-5 shadow-lg dark:bg-gray-800"
			role="button"
			tabindex="0"
			onkeydown={(e) => e.key === 'Escape' && closeDeleteModal()}
			onclick={(e) => e.stopPropagation()}
		>
			<div class="mt-3">
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center">
						<div
							class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-900"
						>
							<AlertTriangle class="h-6 w-6 text-red-600 dark:text-red-400" />
						</div>
						<div class="ml-4">
							<h3
								id="modal-title"
								class="text-lg leading-6 font-medium text-gray-900 dark:text-white"
							>
								Delete Opportunity
							</h3>
						</div>
					</div>
					<button
						type="button"
						onclick={closeDeleteModal}
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
					>
						<X class="h-5 w-5" />
					</button>
				</div>

				<div class="mt-2">
					<p class="text-sm text-gray-500 dark:text-gray-400">
						Are you sure you want to delete the opportunity <strong
							>"{opportunityToDelete?.name || 'Unknown'}"</strong
						>? This action cannot be undone and will also delete all associated tasks, events, and
						comments.
					</p>
				</div>

				<div class="mt-6 flex justify-end space-x-3">
					<button
						type="button"
						onclick={closeDeleteModal}
						disabled={deleteLoading}
						class="rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
					>
						Cancel
					</button>

					<form
						method="POST"
						action="?/delete"
						use:enhance={({ formElement, formData }) => {
							deleteLoading = true;

							return async ({ result }) => {
								deleteLoading = false;

								if (result.type === 'success') {
									closeDeleteModal();
									// Use goto with replaceState and invalidateAll for a clean refresh
									await goto($page.url.pathname, {
										replaceState: true,
										invalidateAll: true
									});
								} else if (result.type === 'failure') {
									console.error('Delete failed:', result.data?.message);
									alert(
										'Failed to delete opportunity: ' + (result.data?.message || 'Unknown error')
									);
								} else if (result.type === 'error') {
									console.error('Delete error:', result.error);
									alert('An error occurred while deleting the opportunity.');
								}
							};
						}}
					>
						<input type="hidden" name="opportunityId" value={opportunityToDelete?.id || ''} />
						<button
							type="submit"
							disabled={deleteLoading}
							class="rounded-md border border-transparent bg-red-600 px-4 py-2 text-white hover:bg-red-700 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
						>
							{deleteLoading ? 'Deleting...' : 'Delete'}
						</button>
					</form>
				</div>
			</div>
		</div>
	</div>
{/if}
