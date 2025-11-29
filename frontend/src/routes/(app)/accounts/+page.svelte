<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		Search,
		Plus,
		Eye,
		Edit,
		Phone,
		MapPin,
		Calendar,
		Users,
		TrendingUp,
		Building2,
		Globe,
		DollarSign,
		ChevronUp,
		ChevronDown,
		Filter
	} from '@lucide/svelte';

	export let data;

	let { accounts, pagination } = data;
	let sortField = $page.url.searchParams.get('sort') || 'name';
	let sortOrder = $page.url.searchParams.get('order') || 'asc';
	let isLoading = false;
	let statusFilter = $page.url.searchParams.get('status') || 'all';
	let searchQuery = $page.url.searchParams.get('q') || '';
	/** @type {NodeJS.Timeout | undefined} */
	let searchTimeout;

	/**
	 * @param {string} value
	 */
	function debounceSearch(value) {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			// eslint-disable-next-line svelte/prefer-svelte-reactivity
			const params = new URLSearchParams($page.url.searchParams);
			if (value.trim()) {
				params.set('q', value.trim());
			} else {
				params.delete('q');
			}
			params.set('page', '1');
			goto(`?${params.toString()}`, { keepFocus: true });
		}, 300);
	}

	function updateQueryParams() {
		isLoading = true;
		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const params = new URLSearchParams($page.url.searchParams);
		params.set('sort', sortField);
		params.set('order', sortOrder);
		params.set('status', statusFilter);
		params.set('page', '1');

		goto(`?${params.toString()}`, { keepFocus: true });
	}

	/**
	 * @param {number} newPage
	 */
	function changePage(newPage) {
		if (newPage < 1 || newPage > pagination.totalPages) return;

		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const params = new URLSearchParams($page.url.searchParams);
		params.set('page', newPage.toString());
		goto(`?${params.toString()}`, { keepFocus: true });
	}

	/**
	 * @param {string} field
	 */
	function toggleSort(field) {
		if (sortField === field) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortField = field;
			sortOrder = 'asc';
		}
		updateQueryParams();
	}

	/**
	 * @param {number | null | undefined} amount
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
	 * @param {string | Date | null | undefined} date
	 */
	function formatDate(date) {
		if (!date) return '-';
		return new Intl.DateTimeFormat('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		}).format(new Date(date));
	}

	// Update data when it changes from the server
	$: {
		accounts = data.accounts;
		pagination = data.pagination;
		isLoading = false;
	}
</script>

<div class="min-h-screen bg-white p-6 dark:bg-gray-900">
	<!-- Header Section -->
	<div class="mb-8">
		<div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
			<div>
				<h1 class="mb-2 text-3xl font-bold text-gray-900 dark:text-white">Accounts</h1>
				<p class="text-gray-600 dark:text-gray-400">
					Manage all your customer accounts and business relationships
				</p>
			</div>

			<!-- Action Bar -->
			<div class="flex flex-col gap-3 sm:flex-row">
				<!-- Search -->
				<div class="relative">
					<label for="accounts-search" class="sr-only">Search accounts</label>
					<Search
						class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform text-gray-400"
					/>
					<input
						type="text"
						id="accounts-search"
						placeholder="Search accounts..."
						class="min-w-[250px] rounded-lg border border-gray-300 bg-white py-2.5 pr-4 pl-10 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
						bind:value={searchQuery}
						oninput={(e) => debounceSearch(/** @type {HTMLInputElement} */ (e.target).value)}
					/>
				</div>

				<!-- Status Filter -->
				<div class="relative">
					<label for="accounts-status-filter" class="sr-only">Filter accounts by status</label>
					<Filter
						class="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform text-gray-400"
					/>
					<select
						id="accounts-status-filter"
						class="min-w-[120px] appearance-none rounded-lg border border-gray-300 bg-white py-2.5 pr-8 pl-10 text-sm text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white"
						bind:value={statusFilter}
						onchange={updateQueryParams}
					>
						<option value="all">All Status</option>
						<option value="open">Open</option>
						<option value="closed">Closed</option>
					</select>
				</div>

				<!-- New Account Button -->
				<a
					href="/accounts/new"
					class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium whitespace-nowrap text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none"
				>
					<Plus class="h-4 w-4" />
					New Account
				</a>
			</div>
		</div>
	</div>

	<!-- Stats Cards -->
	<div class="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-4">
		<div
			class="rounded-lg border border-blue-200 bg-gradient-to-r from-blue-50 to-blue-100 p-4 dark:border-blue-800 dark:from-blue-900/20 dark:to-blue-800/20"
		>
			<div class="flex items-center gap-3">
				<div class="rounded-lg bg-blue-600 p-2">
					<Building2 class="h-5 w-5 text-white" />
				</div>
				<div>
					<p class="text-sm font-medium text-blue-600 dark:text-blue-400">Total Accounts</p>
					<p class="text-2xl font-bold text-blue-900 dark:text-blue-100">{pagination.total}</p>
				</div>
			</div>
		</div>

		<div
			class="rounded-lg border border-green-200 bg-gradient-to-r from-green-50 to-green-100 p-4 dark:border-green-800 dark:from-green-900/20 dark:to-green-800/20"
		>
			<div class="flex items-center gap-3">
				<div class="rounded-lg bg-green-600 p-2">
					<TrendingUp class="h-5 w-5 text-white" />
				</div>
				<div>
					<p class="text-sm font-medium text-green-600 dark:text-green-400">Active</p>
					<p class="text-2xl font-bold text-green-900 dark:text-green-100">
						{accounts.filter((a) => a.isActive).length}
					</p>
				</div>
			</div>
		</div>

		<div
			class="rounded-lg border border-orange-200 bg-gradient-to-r from-orange-50 to-orange-100 p-4 dark:border-orange-800 dark:from-orange-900/20 dark:to-orange-800/20"
		>
			<div class="flex items-center gap-3">
				<div class="rounded-lg bg-orange-600 p-2">
					<Users class="h-5 w-5 text-white" />
				</div>
				<div>
					<p class="text-sm font-medium text-orange-600 dark:text-orange-400">Total Contacts</p>
					<p class="text-2xl font-bold text-orange-900 dark:text-orange-100">
						{accounts.reduce((sum, a) => sum + (a.contactCount || 0), 0)}
					</p>
				</div>
			</div>
		</div>

		<div
			class="rounded-lg border border-purple-200 bg-gradient-to-r from-purple-50 to-purple-100 p-4 dark:border-purple-800 dark:from-purple-900/20 dark:to-purple-800/20"
		>
			<div class="flex items-center gap-3">
				<div class="rounded-lg bg-purple-600 p-2">
					<DollarSign class="h-5 w-5 text-white" />
				</div>
				<div>
					<p class="text-sm font-medium text-purple-600 dark:text-purple-400">Opportunities</p>
					<p class="text-2xl font-bold text-purple-900 dark:text-purple-100">
						{accounts.reduce((sum, a) => sum + (a.opportunityCount || 0), 0)}
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- Accounts Table -->
	<div
		class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
	>
		<div class="overflow-x-auto">
			<table class="w-full">
				<thead class="border-b border-gray-200 bg-gray-50 dark:border-gray-600 dark:bg-gray-700">
					<tr>
						<th
							scope="col"
							class="cursor-pointer px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-600"
							onclick={() => toggleSort('name')}
						>
							<div class="flex items-center gap-2">
								<Building2 class="h-4 w-4" />
								Account Name
								{#if sortField === 'name'}
									{#if sortOrder === 'asc'}
										<ChevronUp class="h-4 w-4" />
									{:else}
										<ChevronDown class="h-4 w-4" />
									{/if}
								{/if}
							</div>
						</th>
						<th
							scope="col"
							class="hidden px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase sm:table-cell dark:text-gray-400"
							>Industry</th
						>
						<th
							scope="col"
							class="hidden px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase md:table-cell dark:text-gray-400"
							>Type</th
						>
						<th
							scope="col"
							class="hidden px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase lg:table-cell dark:text-gray-400"
							>Contact Info</th
						>
						<th
							scope="col"
							class="hidden px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase xl:table-cell dark:text-gray-400"
							>Revenue</th
						>
						<th
							scope="col"
							class="hidden px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase md:table-cell dark:text-gray-400"
							>Relations</th
						>
						<th
							scope="col"
							class="hidden px-6 py-4 text-left text-xs font-medium tracking-wider text-gray-500 uppercase lg:table-cell dark:text-gray-400"
							>Created</th
						>
						<th
							scope="col"
							class="px-6 py-4 text-right text-xs font-medium tracking-wider text-gray-500 uppercase dark:text-gray-400"
							>Actions</th
						>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
					{#if isLoading}
						<tr>
							<td colspan="8" class="px-6 py-16 text-center">
								<div class="flex flex-col items-center gap-4">
									<div
										class="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent"
									></div>
									<p class="text-gray-500 dark:text-gray-400">Loading accounts...</p>
								</div>
							</td>
						</tr>
					{:else if accounts.length === 0}
						<tr>
							<td colspan="8" class="px-6 py-16 text-center">
								<div class="flex flex-col items-center gap-4">
									<Building2 class="h-12 w-12 text-gray-400" />
									<div>
										<p class="text-lg font-medium text-gray-500 dark:text-gray-400">
											No accounts found
										</p>
										<p class="mt-1 text-sm text-gray-400 dark:text-gray-500">
											Get started by creating your first account
										</p>
									</div>
									<a
										href="/accounts/new"
										class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
									>
										<Plus class="h-4 w-4" />
										Create Account
									</a>
								</div>
							</td>
						</tr>
					{:else}
						{#each accounts as account (account.id)}
							<tr
								class="transition-colors hover:bg-gray-50 dark:hover:bg-gray-700 {account.closedAt
									? 'opacity-60'
									: ''}"
							>
								<td class="px-6 py-4">
									<div class="flex items-center gap-3">
										<div class="flex-shrink-0">
											<div
												class="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 font-semibold text-white"
											>
												{account.name?.[0]?.toUpperCase() || 'A'}
											</div>
										</div>
										<div class="min-w-0 flex-1">
											<a href="/accounts/{account.id}" class="group block">
												<p
													class="text-sm font-semibold text-gray-900 transition-colors group-hover:text-blue-600 dark:text-white dark:group-hover:text-blue-400"
												>
													{account.name}
												</p>
												{#if account.isActive}
													<span
														class="mt-1 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900/20 dark:text-green-400"
													>
														Active
													</span>
												{:else}
													<div class="mt-1">
														<span
															class="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900/20 dark:text-red-400"
														>
															Closed
														</span>
														{#if account.closedAt}
															<p class="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
																{formatDate(account.closedAt)}
															</p>
														{/if}
													</div>
												{/if}
											</a>
										</div>
									</div>
								</td>
								<td class="hidden px-6 py-4 sm:table-cell">
									<span class="text-sm text-gray-600 dark:text-gray-300"
										>{account.industry || '-'}</span
									>
								</td>
								<td class="hidden px-6 py-4 md:table-cell">
									<span
										class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-800 dark:bg-gray-700 dark:text-gray-200"
									>
										{account.type || 'Customer'}
									</span>
								</td>
								<td class="hidden px-6 py-4 lg:table-cell">
									<div class="space-y-1">
										{#if account.website}
											<div class="flex items-center gap-1 text-sm">
												<Globe class="h-3 w-3 text-gray-400" />
												<a
													href={account.website.startsWith('http')
														? account.website
														: `https://${account.website}`}
													target="_blank"
													rel="noopener noreferrer"
													class="max-w-[150px] truncate text-blue-600 hover:underline dark:text-blue-400"
												>
													{account.website.replace(/^https?:\/\//, '')}
												</a>
											</div>
										{/if}
										{#if account.phone}
											<div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
												<Phone class="h-3 w-3 text-gray-400" />
												<span class="truncate">{account.phone}</span>
											</div>
										{/if}
										{#if account.city || account.state}
											<div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
												<MapPin class="h-3 w-3 text-gray-400" />
												<span class="truncate"
													>{[account.city, account.state].filter(Boolean).join(', ')}</span
												>
											</div>
										{/if}
									</div>
								</td>
								<td class="hidden px-6 py-4 xl:table-cell">
									<div class="text-sm">
										{#if account.annualRevenue}
											<span class="font-medium text-gray-900 dark:text-white"
												>{formatCurrency(account.annualRevenue)}</span
											>
											<p class="text-xs text-gray-500">Annual Revenue</p>
										{:else}
											<span class="text-gray-400">-</span>
										{/if}
									</div>
								</td>
								<td class="hidden px-6 py-4 md:table-cell">
									<div class="flex items-center gap-4">
										<div class="flex items-center gap-1">
											<Users class="h-4 w-4 text-gray-400" />
											<span class="text-sm font-medium text-gray-900 dark:text-white"
												>{account.contactCount || 0}</span
											>
										</div>
										<div class="flex items-center gap-1">
											<TrendingUp class="h-4 w-4 text-gray-400" />
											<span class="text-sm font-medium text-gray-900 dark:text-white"
												>{account.opportunityCount || 0}</span
											>
										</div>
									</div>
								</td>
								<td class="hidden px-6 py-4 lg:table-cell">
									<div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
										<Calendar class="h-3 w-3 text-gray-400" />
										<span>{formatDate(account.createdAt)}</span>
									</div>
								</td>
								<td class="px-6 py-4 text-right">
									<div class="flex items-center justify-end gap-2">
										<a
											href="/accounts/{account.id}"
											class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-blue-600 dark:hover:bg-gray-700 dark:hover:text-blue-400"
											title="View Account"
										>
											<Eye class="h-4 w-4" />
										</a>
										<a
											href="/opportunities/new?accountId={account.id}"
											class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-green-600 dark:hover:bg-gray-700 dark:hover:text-green-400"
											title="Add Opportunity"
										>
											<Plus class="h-4 w-4" />
										</a>
										<a
											href="/accounts/{account.id}/edit"
											class="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-yellow-600 dark:hover:bg-gray-700 dark:hover:text-yellow-400"
											title="Edit Account"
										>
											<Edit class="h-4 w-4" />
										</a>
									</div>
								</td>
							</tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>
	</div>

	<!-- Pagination -->
	{#if pagination.totalPages > 1}
		<div class="flex flex-col items-center justify-between gap-4 pt-6 sm:flex-row">
			<div class="text-sm text-gray-700 dark:text-gray-300">
				Showing <span class="font-medium">{(pagination.page - 1) * pagination.limit + 1}</span> to
				<span class="font-medium"
					>{Math.min(pagination.page * pagination.limit, pagination.total)}</span
				>
				of
				<span class="font-medium">{pagination.total}</span> accounts
			</div>
			<div class="flex items-center gap-2">
				<button
					onclick={() => changePage(1)}
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
					disabled={pagination.page === 1}
				>
					First
				</button>
				<button
					onclick={() => changePage(pagination.page - 1)}
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
					disabled={pagination.page === 1}
				>
					Previous
				</button>
				<span
					class="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-gray-900 dark:border-blue-800 dark:bg-blue-900/20 dark:text-white"
				>
					{pagination.page} of {pagination.totalPages}
				</span>
				<button
					onclick={() => changePage(pagination.page + 1)}
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
					disabled={pagination.page === pagination.totalPages}
				>
					Next
				</button>
				<button
					onclick={() => changePage(pagination.totalPages)}
					class="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
					disabled={pagination.page === pagination.totalPages}
				>
					Last
				</button>
			</div>
		</div>
	{/if}
</div>
