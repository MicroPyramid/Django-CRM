<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Briefcase, Plus, Filter, X } from '@lucide/svelte';

	export let data;
	let statusFilter = '';
	let assignedFilter = '';
	let accountFilter = '';

	// Use options from server data
	const statusOptions = data.statusOptions;
	const assignedOptions = data.allUsers.map((u: any) => u.name);
	const accountOptions = data.allAccounts.map((a: any) => a.name);

	$: filteredCases = data.cases.filter(
		(c: any) =>
			(!statusFilter || c.status === statusFilter) &&
			(!assignedFilter || c.owner?.name === assignedFilter) &&
			(!accountFilter || c.account?.name === accountFilter)
	);

	function statusColor(status: string) {
		return status === 'OPEN'
			? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-700'
			: status === 'IN_PROGRESS'
				? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:border-amber-700'
				: 'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600';
	}

	function priorityColor(priority: string) {
		return priority === 'Urgent'
			? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-700'
			: priority === 'High'
				? 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-700'
				: priority === 'Normal'
					? 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-700'
					: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-700';
	}

	function onFilterChange() {
		const params = new URLSearchParams();
		if (statusFilter) params.set('status', statusFilter);
		if (assignedFilter) params.set('assigned', assignedFilter);
		if (accountFilter) params.set('account', accountFilter);
		goto(`/cases?${params.toString()}`);
	}

	function clearFilters() {
		statusFilter = '';
		assignedFilter = '';
		accountFilter = '';
		onFilterChange();
	}

	$: hasActiveFilters = statusFilter || assignedFilter || accountFilter;
</script>

<div class="min-h-screen bg-slate-50 dark:bg-slate-900">
	<div class="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
			<div class="flex items-center gap-3">
				<div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900/30">
					<Briefcase class="h-6 w-6 text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<h1 class="text-2xl font-bold text-slate-900 dark:text-white">Cases</h1>
					<p class="mt-1 text-sm text-slate-600 dark:text-slate-400">
						Manage customer support cases and issues
					</p>
				</div>
			</div>
			<a
				href="/cases/new"
				class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white shadow-sm transition-colors duration-200 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
			>
				<Plus class="h-4 w-4" />
				New Case
			</a>
		</div>

		<!-- Filters -->
		<div
			class="mb-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800"
		>
			<div class="mb-4 flex items-center gap-2">
				<Filter class="h-4 w-4 text-slate-600 dark:text-slate-400" />
				<h3 class="text-sm font-semibold text-slate-900 dark:text-white">Filters</h3>
				{#if hasActiveFilters}
					<span
						class="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
					>
						{[statusFilter, assignedFilter, accountFilter].filter(Boolean).length} active
					</span>
				{/if}
			</div>

			<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
				<div>
					<label
						for="status"
						class="mb-2 block text-xs font-medium text-slate-700 dark:text-slate-300">Status</label
					>
					<select
						id="status"
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
						bind:value={statusFilter}
						onchange={onFilterChange}
					>
						<option value="">All Statuses</option>
						{#each statusOptions as s}
							<option value={s}>{s.replace('_', ' ')}</option>
						{/each}
					</select>
				</div>

				<div>
					<label
						for="assigned"
						class="mb-2 block text-xs font-medium text-slate-700 dark:text-slate-300"
						>Assigned To</label
					>
					<select
						id="assigned"
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
						bind:value={assignedFilter}
						onchange={onFilterChange}
					>
						<option value="">All Users</option>
						{#each assignedOptions as a}
							<option value={a}>{a}</option>
						{/each}
					</select>
				</div>

				<div>
					<label
						for="account"
						class="mb-2 block text-xs font-medium text-slate-700 dark:text-slate-300">Account</label
					>
					<select
						id="account"
						class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-700 dark:text-white"
						bind:value={accountFilter}
						onchange={onFilterChange}
					>
						<option value="">All Accounts</option>
						{#each accountOptions as acc}
							<option value={acc}>{acc}</option>
						{/each}
					</select>
				</div>

				{#if hasActiveFilters}
					<div class="flex items-end">
						<button
							class="inline-flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white"
							onclick={clearFilters}
						>
							<X class="h-4 w-4" />
							Clear
						</button>
					</div>
				{/if}
			</div>
		</div>

		<!-- Cases List -->
		<div
			class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800"
		>
			{#if filteredCases.length}
				<!-- Desktop Table -->
				<div class="hidden overflow-x-auto lg:block">
					<table class="w-full">
						<thead
							class="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900/50"
						>
							<tr>
								<th
									class="px-6 py-4 text-left text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Case</th
								>
								<th
									class="px-6 py-4 text-left text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Account</th
								>
								<th
									class="px-6 py-4 text-left text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Assigned</th
								>
								<th
									class="px-6 py-4 text-left text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Due Date</th
								>
								<th
									class="px-6 py-4 text-left text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Priority</th
								>
								<th
									class="px-6 py-4 text-left text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Status</th
								>
								<th
									class="px-6 py-4 text-right text-xs font-semibold tracking-wider text-slate-600 uppercase dark:text-slate-400"
									>Actions</th
								>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-200 dark:divide-slate-700">
							{#each filteredCases as c}
								<tr
									class="transition-colors duration-150 hover:bg-slate-50 dark:hover:bg-slate-700/50"
								>
									<td class="px-6 py-4">
										<div>
											<a
												href={`/cases/${c.id}`}
												class="font-semibold text-slate-900 transition-colors duration-200 hover:text-blue-600 dark:text-white dark:hover:text-blue-400"
											>
												{c.subject}
											</a>
											{#if c.description}
												<p class="mt-1 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">
													{c.description}
												</p>
											{/if}
										</div>
									</td>
									<td class="px-6 py-4">
										<span class="text-sm text-slate-900 dark:text-white"
											>{c.account?.name || '-'}</span
										>
									</td>
									<td class="px-6 py-4">
										<div class="flex items-center gap-2">
											<div
												class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30"
											>
												<span class="text-sm font-medium text-blue-700 dark:text-blue-300">
													{c.owner?.name?.[0] || '?'}
												</span>
											</div>
											<span class="text-sm text-slate-900 dark:text-white"
												>{c.owner?.name || 'Unassigned'}</span
											>
										</div>
									</td>
									<td class="px-6 py-4">
										<span class="text-sm text-slate-900 dark:text-white">
											{c.dueDate ? new Date(c.dueDate).toLocaleDateString() : '-'}
										</span>
									</td>
									<td class="px-6 py-4">
										<span
											class={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${priorityColor(c.priority)}`}
										>
											{c.priority}
										</span>
									</td>
									<td class="px-6 py-4">
										<span
											class={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusColor(c.status)}`}
										>
											{c.status.replace('_', ' ')}
										</span>
									</td>
									<td class="px-6 py-4 text-right">
										<a
											href={`/cases/${c.id}`}
											class="inline-flex items-center rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
										>
											View
										</a>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Mobile Cards -->
				<div class="divide-y divide-slate-200 lg:hidden dark:divide-slate-700">
					{#each filteredCases as c}
						<div
							class="p-4 transition-colors duration-150 hover:bg-slate-50 dark:hover:bg-slate-700/50"
						>
							<div class="mb-3 flex items-start justify-between">
								<a
									href={`/cases/${c.id}`}
									class="font-semibold text-slate-900 transition-colors duration-200 hover:text-blue-600 dark:text-white dark:hover:text-blue-400"
								>
									{c.subject}
								</a>
								<span
									class={`inline-flex items-center rounded-full border px-2 py-1 text-xs font-medium ${statusColor(c.status)}`}
								>
									{c.status.replace('_', ' ')}
								</span>
							</div>

							{#if c.description}
								<p class="mb-3 line-clamp-2 text-sm text-slate-600 dark:text-slate-400">
									{c.description}
								</p>
							{/if}

							<div class="mb-4 grid grid-cols-2 gap-3 text-sm">
								<div>
									<span class="text-slate-500 dark:text-slate-400">Account:</span>
									<span class="ml-1 text-slate-900 dark:text-white">{c.account?.name || '-'}</span>
								</div>
								<div>
									<span class="text-slate-500 dark:text-slate-400">Priority:</span>
									<span
										class={`ml-1 inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${priorityColor(c.priority)}`}
									>
										{c.priority}
									</span>
								</div>
								<div>
									<span class="text-slate-500 dark:text-slate-400">Assigned:</span>
									<span class="ml-1 text-slate-900 dark:text-white"
										>{c.owner?.name || 'Unassigned'}</span
									>
								</div>
								<div>
									<span class="text-slate-500 dark:text-slate-400">Due:</span>
									<span class="ml-1 text-slate-900 dark:text-white">
										{c.dueDate ? new Date(c.dueDate).toLocaleDateString() : '-'}
									</span>
								</div>
							</div>

							<div class="flex justify-end">
								<a
									href={`/cases/${c.id}`}
									class="inline-flex items-center rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors duration-200 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
								>
									View Details
								</a>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<div class="p-12 text-center">
					<div
						class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-700"
					>
						<Briefcase class="h-8 w-8 text-slate-400 dark:text-slate-500" />
					</div>
					<h3 class="mb-2 text-lg font-semibold text-slate-900 dark:text-white">No cases found</h3>
					<p class="mb-6 text-slate-500 dark:text-slate-400">
						{hasActiveFilters
							? 'No cases match your current filters.'
							: 'Get started by creating your first case.'}
					</p>
					{#if hasActiveFilters}
						<button
							class="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors duration-200 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-700 dark:hover:text-white"
							onclick={clearFilters}
						>
							<X class="h-4 w-4" />
							Clear Filters
						</button>
					{:else}
						<a
							href="/cases/new"
							class="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors duration-200 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-600"
						>
							<Plus class="h-4 w-4" />
							Create Case
						</a>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>
