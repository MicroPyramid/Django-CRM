<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { Search, Plus, Eye, Edit, Phone, MapPin, Calendar, Users, TrendingUp, Building2, Globe, DollarSign, ChevronUp, ChevronDown, Filter } from '@lucide/svelte';
  
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
      maximumFractionDigits: 0,
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

<div class="p-6 bg-white dark:bg-gray-900 min-h-screen">
  <!-- Header Section -->
  <div class="mb-8">
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Accounts</h1>
        <p class="text-gray-600 dark:text-gray-400">
          Manage all your customer accounts and business relationships
        </p>
      </div>
      
      <!-- Action Bar -->
      <div class="flex flex-col sm:flex-row gap-3">
        <!-- Search -->
        <div class="relative">
          <label for="accounts-search" class="sr-only">Search accounts</label>
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            id="accounts-search"
            placeholder="Search accounts..."
            class="pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[250px]"
            bind:value={searchQuery}
            oninput={(e) => debounceSearch(/** @type {HTMLInputElement} */ (e.target).value)}
          />
        </div>
        
        <!-- Status Filter -->
        <div class="relative">
          <label for="accounts-status-filter" class="sr-only">Filter accounts by status</label>
          <Filter class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <select
            id="accounts-status-filter"
            class="pl-10 pr-8 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none min-w-[120px]"
            bind:value={statusFilter}
            onchange={updateQueryParams}
          >
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
          </select>
        </div>
        
        <!-- New Account Button -->
        <a href="/accounts/new" class="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors whitespace-nowrap">
          <Plus class="w-4 h-4" />
          New Account
        </a>
      </div>
    </div>
  </div>

  <!-- Stats Cards -->
  <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-8">
    <div class="bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-blue-600 rounded-lg">
          <Building2 class="w-5 h-5 text-white" />
        </div>
        <div>
          <p class="text-sm text-blue-600 dark:text-blue-400 font-medium">Total Accounts</p>
          <p class="text-2xl font-bold text-blue-900 dark:text-blue-100">{pagination.total}</p>
        </div>
      </div>
    </div>
    
    <div class="bg-gradient-to-r from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-green-600 rounded-lg">
          <TrendingUp class="w-5 h-5 text-white" />
        </div>
        <div>
          <p class="text-sm text-green-600 dark:text-green-400 font-medium">Active</p>
          <p class="text-2xl font-bold text-green-900 dark:text-green-100">{accounts.filter(a => a.isActive).length}</p>
        </div>
      </div>
    </div>
    
    <div class="bg-gradient-to-r from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 p-4 rounded-lg border border-orange-200 dark:border-orange-800">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-orange-600 rounded-lg">
          <Users class="w-5 h-5 text-white" />
        </div>
        <div>
          <p class="text-sm text-orange-600 dark:text-orange-400 font-medium">Total Contacts</p>
          <p class="text-2xl font-bold text-orange-900 dark:text-orange-100">{accounts.reduce((sum, a) => sum + (a.contactCount || 0), 0)}</p>
        </div>
      </div>
    </div>
    
    <div class="bg-gradient-to-r from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-purple-600 rounded-lg">
          <DollarSign class="w-5 h-5 text-white" />
        </div>
        <div>
          <p class="text-sm text-purple-600 dark:text-purple-400 font-medium">Opportunities</p>
          <p class="text-2xl font-bold text-purple-900 dark:text-purple-100">{accounts.reduce((sum, a) => sum + (a.opportunityCount || 0), 0)}</p>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Accounts Table -->
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead class="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
          <tr>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600" onclick={() => toggleSort('name')}>
              <div class="flex items-center gap-2">
                <Building2 class="w-4 h-4" />
                Account Name
                {#if sortField === 'name'}
                  {#if sortOrder === 'asc'}
                    <ChevronUp class="w-4 h-4" />
                  {:else}
                    <ChevronDown class="w-4 h-4" />
                  {/if}
                {/if}
              </div>
            </th>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Industry</th>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Type</th>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Contact Info</th>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden xl:table-cell">Revenue</th>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Relations</th>
            <th scope="col" class="px-6 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Created</th>
            <th scope="col" class="px-6 py-4 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {#if isLoading}
            <tr>
              <td colspan="8" class="px-6 py-16 text-center">
                <div class="flex flex-col items-center gap-4">
                  <div class="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
                  <p class="text-gray-500 dark:text-gray-400">Loading accounts...</p>
                </div>
              </td>
            </tr>
          {:else if accounts.length === 0}
            <tr>
              <td colspan="8" class="px-6 py-16 text-center">
                <div class="flex flex-col items-center gap-4">
                  <Building2 class="w-12 h-12 text-gray-400" />
                  <div>
                    <p class="text-gray-500 dark:text-gray-400 text-lg font-medium">No accounts found</p>
                    <p class="text-gray-400 dark:text-gray-500 text-sm mt-1">Get started by creating your first account</p>
                  </div>
                  <a href="/accounts/new" class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                    <Plus class="w-4 h-4" />
                    Create Account
                  </a>
                </div>
              </td>
            </tr>
          {:else}
            {#each accounts as account (account.id)}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors {account.closedAt ? 'opacity-60' : ''}">
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="flex-shrink-0">
                      <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-semibold">
                        {account.name?.[0]?.toUpperCase() || 'A'}
                      </div>
                    </div>
                    <div class="min-w-0 flex-1">
                      <a href="/accounts/{account.id}" class="block group">
                        <p class="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                          {account.name}
                        </p>
                        {#if account.isActive}
                          <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400 mt-1">
                            Active
                          </span>
                        {:else}
                          <div class="mt-1">
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
                              Closed
                            </span>
                            {#if account.closedAt}
                              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {formatDate(account.closedAt)}
                              </p>
                            {/if}
                          </div>
                        {/if}
                      </a>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 hidden sm:table-cell">
                  <span class="text-sm text-gray-600 dark:text-gray-300">{account.industry || '-'}</span>
                </td>
                <td class="px-6 py-4 hidden md:table-cell">
                  <span class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                    {account.type || 'Customer'}
                  </span>
                </td>
                <td class="px-6 py-4 hidden lg:table-cell">
                  <div class="space-y-1">
                    {#if account.website}
                      <div class="flex items-center gap-1 text-sm">
                        <Globe class="w-3 h-3 text-gray-400" />
                        <a href={account.website.startsWith('http') ? account.website : `https://${account.website}`} 
                           target="_blank" 
                           rel="noopener noreferrer" 
                           class="text-blue-600 dark:text-blue-400 hover:underline truncate max-w-[150px]">
                          {account.website.replace(/^https?:\/\//, '')}
                        </a>
                      </div>
                    {/if}
                    {#if account.phone}
                      <div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
                        <Phone class="w-3 h-3 text-gray-400" />
                        <span class="truncate">{account.phone}</span>
                      </div>
                    {/if}
                    {#if account.city || account.state}
                      <div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
                        <MapPin class="w-3 h-3 text-gray-400" />
                        <span class="truncate">{[account.city, account.state].filter(Boolean).join(', ')}</span>
                      </div>
                    {/if}
                  </div>
                </td>
                <td class="px-6 py-4 hidden xl:table-cell">
                  <div class="text-sm">
                    {#if account.annualRevenue}
                      <span class="font-medium text-gray-900 dark:text-white">{formatCurrency(account.annualRevenue)}</span>
                      <p class="text-xs text-gray-500">Annual Revenue</p>
                    {:else}
                      <span class="text-gray-400">-</span>
                    {/if}
                  </div>
                </td>
                <td class="px-6 py-4 hidden md:table-cell">
                  <div class="flex items-center gap-4">
                    <div class="flex items-center gap-1">
                      <Users class="w-4 h-4 text-gray-400" />
                      <span class="text-sm font-medium text-gray-900 dark:text-white">{account.contactCount || 0}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <TrendingUp class="w-4 h-4 text-gray-400" />
                      <span class="text-sm font-medium text-gray-900 dark:text-white">{account.opportunityCount || 0}</span>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 hidden lg:table-cell">
                  <div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-300">
                    <Calendar class="w-3 h-3 text-gray-400" />
                    <span>{formatDate(account.createdAt)}</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <a href="/accounts/{account.id}" 
                       class="p-2 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" 
                       title="View Account">
                      <Eye class="w-4 h-4" />
                    </a>
                    <a href="/opportunities/new?accountId={account.id}" 
                       class="p-2 text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" 
                       title="Add Opportunity">
                      <Plus class="w-4 h-4" />
                    </a>
                    <a href="/accounts/{account.id}/edit" 
                       class="p-2 text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700" 
                       title="Edit Account">
                      <Edit class="w-4 h-4" />
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
    <div class="flex flex-col sm:flex-row items-center justify-between pt-6 gap-4">
      <div class="text-sm text-gray-700 dark:text-gray-300">
        Showing <span class="font-medium">{(pagination.page - 1) * pagination.limit + 1}</span> to 
        <span class="font-medium">{Math.min(pagination.page * pagination.limit, pagination.total)}</span> of 
        <span class="font-medium">{pagination.total}</span> accounts
      </div>
      <div class="flex items-center gap-2">
        <button 
          onclick={() => changePage(1)}
          class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          disabled={pagination.page === 1}
        >
          First
        </button>
        <button 
          onclick={() => changePage(pagination.page - 1)}
          class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          disabled={pagination.page === 1}
        >
          Previous
        </button>
        <span class="px-4 py-2 text-sm font-medium text-gray-900 dark:text-white bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          {pagination.page} of {pagination.totalPages}
        </span>
        <button 
          onclick={() => changePage(pagination.page + 1)}
          class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          disabled={pagination.page === pagination.totalPages}
        >
          Next
        </button>
        <button 
          onclick={() => changePage(pagination.totalPages)}
          class="px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          disabled={pagination.page === pagination.totalPages}
        >
          Last
        </button>
      </div>
    </div>
  {/if}
</div>
