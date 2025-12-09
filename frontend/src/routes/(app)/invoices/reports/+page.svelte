<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	import { PageHeader } from '$lib/components/layout';
	import { Button } from '$lib/components/ui/button';
	import { formatCurrency, formatDate } from '$lib/utils/formatting.js';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	const dashboard = $derived(data.dashboard);
	const revenue = $derived(data.revenue);
	const aging = $derived(data.aging);
	const filters = $derived(data.filters);

	// Group by options
	const GROUP_BY_OPTIONS = [
		{ value: 'day', label: 'Daily' },
		{ value: 'week', label: 'Weekly' },
		{ value: 'month', label: 'Monthly' },
		{ value: 'year', label: 'Yearly' }
	];

	// Filter handlers
	async function updateFilters(newFilters) {
		const url = new URL($page.url);

		if (newFilters.startDate) url.searchParams.set('start_date', newFilters.startDate);
		if (newFilters.endDate) url.searchParams.set('end_date', newFilters.endDate);
		if (newFilters.groupBy) url.searchParams.set('group_by', newFilters.groupBy);

		await goto(url.toString(), { replaceState: true, invalidateAll: true });
	}

	function getStatusColor(status) {
		const colors = {
			Draft: 'bg-gray-500',
			Sent: 'bg-blue-500',
			Viewed: 'bg-indigo-500',
			Partially_Paid: 'bg-yellow-500',
			Paid: 'bg-green-500',
			Overdue: 'bg-red-500',
			Cancelled: 'bg-gray-400'
		};
		return colors[status] || 'bg-gray-500';
	}
</script>

<div class="flex flex-col gap-6 p-6">
	<!-- Header -->
	<PageHeader title="Invoice Reports">
		{#snippet actions()}
			<Button variant="ghost" size="sm" onclick={() => goto('/invoices')}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="mr-2"
				>
					<path d="M19 12H5M12 19l-7-7 7-7" />
				</svg>
				Invoices
			</Button>
		{/snippet}
	</PageHeader>

	<!-- Summary Cards -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
		<!-- Total Invoiced -->
		<div class="bg-white rounded-xl border p-6 shadow-sm">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm text-gray-500">Total Invoiced</p>
					<p class="text-2xl font-bold text-gray-900 mt-1">
						{formatCurrency(Number(dashboard.summary?.total_invoiced || 0), 'USD')}
					</p>
				</div>
				<div class="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="24"
						height="24"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="text-blue-600"
					>
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
						<polyline points="14 2 14 8 20 8" />
						<line x1="16" y1="13" x2="8" y2="13" />
						<line x1="16" y1="17" x2="8" y2="17" />
					</svg>
				</div>
			</div>
		</div>

		<!-- Total Paid -->
		<div class="bg-white rounded-xl border p-6 shadow-sm">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm text-gray-500">Total Collected</p>
					<p class="text-2xl font-bold text-green-600 mt-1">
						{formatCurrency(Number(dashboard.summary?.total_paid || 0), 'USD')}
					</p>
				</div>
				<div class="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="24"
						height="24"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="text-green-600"
					>
						<line x1="12" y1="1" x2="12" y2="23" />
						<path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
					</svg>
				</div>
			</div>
		</div>

		<!-- Outstanding -->
		<div class="bg-white rounded-xl border p-6 shadow-sm">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm text-gray-500">Outstanding</p>
					<p class="text-2xl font-bold text-orange-600 mt-1">
						{formatCurrency(Number(dashboard.summary?.total_due || 0), 'USD')}
					</p>
				</div>
				<div class="h-12 w-12 rounded-full bg-orange-100 flex items-center justify-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="24"
						height="24"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="text-orange-600"
					>
						<circle cx="12" cy="12" r="10" />
						<polyline points="12 6 12 12 16 14" />
					</svg>
				</div>
			</div>
		</div>

		<!-- Overdue -->
		<div class="bg-white rounded-xl border p-6 shadow-sm">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm text-gray-500">Overdue ({dashboard.overdue?.count || 0})</p>
					<p class="text-2xl font-bold text-red-600 mt-1">
						{formatCurrency(Number(dashboard.overdue?.amount || 0), 'USD')}
					</p>
				</div>
				<div class="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="24"
						height="24"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="text-red-600"
					>
						<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
						<line x1="12" y1="9" x2="12" y2="13" />
						<line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
				</div>
			</div>
		</div>
	</div>

	<!-- Recent Activity & Status -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<!-- Recent Activity -->
		<div class="bg-white rounded-xl border p-6 shadow-sm">
			<h3 class="text-lg font-semibold text-gray-900 mb-4">Last 30 Days</h3>
			<div class="space-y-4">
				<div class="flex justify-between items-center">
					<span class="text-gray-600">Revenue Collected</span>
					<span class="font-medium text-green-600">
						{formatCurrency(Number(dashboard.recent_activity?.revenue_30d || 0), 'USD')}
					</span>
				</div>
				<div class="flex justify-between items-center">
					<span class="text-gray-600">Invoices Created</span>
					<span class="font-medium">{dashboard.recent_activity?.invoices_created_30d || 0}</span>
				</div>
				<div class="flex justify-between items-center">
					<span class="text-gray-600">Invoices Paid</span>
					<span class="font-medium">{dashboard.recent_activity?.invoices_paid_30d || 0}</span>
				</div>
				<div class="flex justify-between items-center">
					<span class="text-gray-600">Total Invoiced</span>
					<span class="font-medium">
						{formatCurrency(Number(dashboard.recent_activity?.invoiced_30d || 0), 'USD')}
					</span>
				</div>
			</div>
		</div>

		<!-- Status Breakdown -->
		<div class="bg-white rounded-xl border p-6 shadow-sm">
			<h3 class="text-lg font-semibold text-gray-900 mb-4">Invoice Status</h3>
			<div class="space-y-3">
				{#each Object.entries(dashboard.status_counts || {}) as [status, count]}
					<div class="flex items-center gap-3">
						<div class="w-3 h-3 rounded-full {getStatusColor(status)}"></div>
						<span class="text-gray-600 flex-1">{status.replace('_', ' ')}</span>
						<span class="font-medium">{count}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>

	<!-- Revenue Chart Section -->
	<div class="bg-white rounded-xl border p-6 shadow-sm">
		<div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
			<h3 class="text-lg font-semibold text-gray-900">Revenue Over Time</h3>
			<div class="flex flex-wrap gap-3">
				<input
					type="date"
					value={filters.startDate}
					onchange={(e) => updateFilters({ ...filters, startDate: /** @type {HTMLInputElement} */ (e.target).value })}
					class="px-3 py-1.5 text-sm border rounded-lg"
				/>
				<input
					type="date"
					value={filters.endDate}
					onchange={(e) => updateFilters({ ...filters, endDate: /** @type {HTMLInputElement} */ (e.target).value })}
					class="px-3 py-1.5 text-sm border rounded-lg"
				/>
				<select
					value={filters.groupBy}
					onchange={(e) => updateFilters({ ...filters, groupBy: /** @type {HTMLSelectElement} */ (e.target).value })}
					class="px-3 py-1.5 text-sm border rounded-lg"
				>
					{#each GROUP_BY_OPTIONS as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
			</div>
		</div>

		{#if revenue.data && revenue.data.length > 0}
			<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b">
							<th class="text-left py-2 font-medium text-gray-500">Period</th>
							<th class="text-right py-2 font-medium text-gray-500">Invoices</th>
							<th class="text-right py-2 font-medium text-gray-500">Revenue</th>
						</tr>
					</thead>
					<tbody>
						{#each revenue.data as item}
							<tr class="border-b last:border-b-0">
								<td class="py-3 text-gray-700">{formatDate(item.period)}</td>
								<td class="py-3 text-right text-gray-600">{item.count}</td>
								<td class="py-3 text-right font-medium text-green-600">
									{formatCurrency(Number(item.revenue), 'USD')}
								</td>
							</tr>
						{/each}
					</tbody>
					<tfoot>
						<tr class="border-t bg-gray-50">
							<td class="py-3 font-medium">Total</td>
							<td class="py-3 text-right font-medium">{revenue.total?.count || 0}</td>
							<td class="py-3 text-right font-bold text-green-600">
								{formatCurrency(Number(revenue.total?.revenue || 0), 'USD')}
							</td>
						</tr>
					</tfoot>
				</table>
			</div>
		{:else}
			<div class="text-center py-8 text-gray-500">
				No revenue data for the selected period
			</div>
		{/if}
	</div>

	<!-- Aging Report -->
	<div class="bg-white rounded-xl border p-6 shadow-sm">
		<h3 class="text-lg font-semibold text-gray-900 mb-6">Accounts Receivable Aging</h3>

		<div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
			<!-- Current -->
			<div class="bg-green-50 rounded-lg p-4">
				<p class="text-sm text-green-700 font-medium">Current</p>
				<p class="text-xl font-bold text-green-800 mt-1">
					{formatCurrency(Number(aging.current?.amount || 0), 'USD')}
				</p>
				<p class="text-sm text-green-600">{aging.current?.count || 0} invoices</p>
			</div>

			<!-- 1-30 Days -->
			<div class="bg-yellow-50 rounded-lg p-4">
				<p class="text-sm text-yellow-700 font-medium">1-30 Days</p>
				<p class="text-xl font-bold text-yellow-800 mt-1">
					{formatCurrency(Number(aging['1_30_days']?.amount || 0), 'USD')}
				</p>
				<p class="text-sm text-yellow-600">{aging['1_30_days']?.count || 0} invoices</p>
			</div>

			<!-- 31-60 Days -->
			<div class="bg-orange-50 rounded-lg p-4">
				<p class="text-sm text-orange-700 font-medium">31-60 Days</p>
				<p class="text-xl font-bold text-orange-800 mt-1">
					{formatCurrency(Number(aging['31_60_days']?.amount || 0), 'USD')}
				</p>
				<p class="text-sm text-orange-600">{aging['31_60_days']?.count || 0} invoices</p>
			</div>

			<!-- 61-90 Days -->
			<div class="bg-red-50 rounded-lg p-4">
				<p class="text-sm text-red-700 font-medium">61-90 Days</p>
				<p class="text-xl font-bold text-red-800 mt-1">
					{formatCurrency(Number(aging['61_90_days']?.amount || 0), 'USD')}
				</p>
				<p class="text-sm text-red-600">{aging['61_90_days']?.count || 0} invoices</p>
			</div>

			<!-- Over 90 Days -->
			<div class="bg-red-100 rounded-lg p-4">
				<p class="text-sm text-red-800 font-medium">Over 90 Days</p>
				<p class="text-xl font-bold text-red-900 mt-1">
					{formatCurrency(Number(aging['over_90_days']?.amount || 0), 'USD')}
				</p>
				<p class="text-sm text-red-700">{aging['over_90_days']?.count || 0} invoices</p>
			</div>
		</div>

		<!-- Total Outstanding -->
		<div class="border-t pt-4 flex justify-between items-center">
			<span class="text-gray-600 font-medium">Total Outstanding</span>
			<div class="text-right">
				<p class="text-2xl font-bold text-gray-900">
					{formatCurrency(Number(aging.total?.amount || 0), 'USD')}
				</p>
				<p class="text-sm text-gray-500">{aging.total?.count || 0} invoices</p>
			</div>
		</div>
	</div>

	<!-- Estimates Summary -->
	<div class="bg-white rounded-xl border p-6 shadow-sm">
		<h3 class="text-lg font-semibold text-gray-900 mb-4">Estimates Overview</h3>
		<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
			<div class="text-center p-4 bg-blue-50 rounded-lg">
				<p class="text-3xl font-bold text-blue-600">{dashboard.estimates?.pending || 0}</p>
				<p class="text-sm text-blue-700 mt-1">Pending</p>
			</div>
			<div class="text-center p-4 bg-green-50 rounded-lg">
				<p class="text-3xl font-bold text-green-600">{dashboard.estimates?.accepted || 0}</p>
				<p class="text-sm text-green-700 mt-1">Accepted</p>
			</div>
			<div class="text-center p-4 bg-red-50 rounded-lg">
				<p class="text-3xl font-bold text-red-600">{dashboard.estimates?.declined || 0}</p>
				<p class="text-sm text-red-700 mt-1">Declined</p>
			</div>
		</div>
	</div>
</div>
