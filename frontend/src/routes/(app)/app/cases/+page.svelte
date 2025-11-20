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

  $: filteredCases = data.cases.filter((c: any) =>
    (!statusFilter || c.status === statusFilter) &&
    (!assignedFilter || c.owner?.name === assignedFilter) &&
    (!accountFilter || c.account?.name === accountFilter)
  );

  function statusColor(status: string) {
    return status === 'OPEN' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-700' :
           status === 'IN_PROGRESS' ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:border-amber-700' :
           'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600';
  }

  function priorityColor(priority: string) {
    return priority === 'Urgent' ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-300 dark:border-red-700' :
           priority === 'High' ? 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:border-orange-700' :
           priority === 'Normal' ? 'bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-900/20 dark:text-yellow-300 dark:border-yellow-700' :
           'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-700';
  }

  function onFilterChange() {
    const params = new URLSearchParams();
    if (statusFilter) params.set('status', statusFilter);
    if (assignedFilter) params.set('assigned', assignedFilter);
    if (accountFilter) params.set('account', accountFilter);
    goto(`/app/cases?${params.toString()}`);
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
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
          <Briefcase class="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Cases</h1>
          <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">Manage customer support cases and issues</p>
        </div>
      </div>
      <a 
        href="/app/cases/new" 
        class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors duration-200 shadow-sm"
      >
        <Plus class="w-4 h-4" />
        New Case
      </a>
    </div>

    <!-- Filters -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 mb-6">
      <div class="flex items-center gap-2 mb-4">
        <Filter class="w-4 h-4 text-slate-600 dark:text-slate-400" />
        <h3 class="text-sm font-semibold text-slate-900 dark:text-white">Filters</h3>
        {#if hasActiveFilters}
          <span class="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-medium rounded-full">
            {[statusFilter, assignedFilter, accountFilter].filter(Boolean).length} active
          </span>
        {/if}
      </div>
      
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label for="status" class="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Status</label>
          <select 
            id="status" 
            class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
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
          <label for="assigned" class="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Assigned To</label>
          <select 
            id="assigned" 
            class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
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
          <label for="account" class="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-2">Account</label>
          <select 
            id="account" 
            class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-slate-700 text-slate-900 dark:text-white"
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
              class="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg transition-colors duration-200"
              onclick={clearFilters}
            >
              <X class="w-4 h-4" />
              Clear
            </button>
          </div>
        {/if}
      </div>
    </div>

    <!-- Cases List -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
      {#if filteredCases.length}
        <!-- Desktop Table -->
        <div class="hidden lg:block overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Case</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Account</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Assigned</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Due Date</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Priority</th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Status</th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 dark:divide-slate-700">
              {#each filteredCases as c}
                <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors duration-150">
                  <td class="px-6 py-4">
                    <div>
                      <a href={`/app/cases/${c.id}`} class="font-semibold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200">
                        {c.subject}
                      </a>
                      {#if c.description}
                        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{c.description}</p>
                      {/if}
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-sm text-slate-900 dark:text-white">{c.account?.name || '-'}</span>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                        <span class="text-sm font-medium text-blue-700 dark:text-blue-300">
                          {c.owner?.name?.[0] || '?'}
                        </span>
                      </div>
                      <span class="text-sm text-slate-900 dark:text-white">{c.owner?.name || 'Unassigned'}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-sm text-slate-900 dark:text-white">
                      {c.dueDate ? new Date(c.dueDate).toLocaleDateString() : '-'}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${priorityColor(c.priority)}`}>
                      {c.priority}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusColor(c.status)}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <a 
                      href={`/app/cases/${c.id}`} 
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors duration-200"
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
        <div class="lg:hidden divide-y divide-slate-200 dark:divide-slate-700">
          {#each filteredCases as c}
            <div class="p-4 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors duration-150">
              <div class="flex justify-between items-start mb-3">
                <a href={`/app/cases/${c.id}`} class="font-semibold text-slate-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors duration-200">
                  {c.subject}
                </a>
                <span class={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${statusColor(c.status)}`}>
                  {c.status.replace('_', ' ')}
                </span>
              </div>
              
              {#if c.description}
                <p class="text-sm text-slate-600 dark:text-slate-400 mb-3 line-clamp-2">{c.description}</p>
              {/if}
              
              <div class="grid grid-cols-2 gap-3 text-sm mb-4">
                <div>
                  <span class="text-slate-500 dark:text-slate-400">Account:</span>
                  <span class="text-slate-900 dark:text-white ml-1">{c.account?.name || '-'}</span>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400">Priority:</span>
                  <span class={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ml-1 ${priorityColor(c.priority)}`}>
                    {c.priority}
                  </span>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400">Assigned:</span>
                  <span class="text-slate-900 dark:text-white ml-1">{c.owner?.name || 'Unassigned'}</span>
                </div>
                <div>
                  <span class="text-slate-500 dark:text-slate-400">Due:</span>
                  <span class="text-slate-900 dark:text-white ml-1">
                    {c.dueDate ? new Date(c.dueDate).toLocaleDateString() : '-'}
                  </span>
                </div>
              </div>
              
              <div class="flex justify-end">
                <a 
                  href={`/app/cases/${c.id}`} 
                  class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-colors duration-200"
                >
                  View Details
                </a>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="p-12 text-center">
          <div class="w-16 h-16 mx-auto mb-4 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center">
            <Briefcase class="w-8 h-8 text-slate-400 dark:text-slate-500" />
          </div>
          <h3 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">No cases found</h3>
          <p class="text-slate-500 dark:text-slate-400 mb-6">
            {hasActiveFilters ? 'No cases match your current filters.' : 'Get started by creating your first case.'}
          </p>
          {#if hasActiveFilters}
            <button 
              class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg transition-colors duration-200"
              onclick={clearFilters}
            >
              <X class="w-4 h-4" />
              Clear Filters
            </button>
          {:else}
            <a 
              href="/app/cases/new"
              class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white font-medium rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors duration-200"
            >
              <Plus class="w-4 h-4" />
              Create Case
            </a>
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>
