<script>
  import { fade, fly } from 'svelte/transition';
  import { formatDistanceToNow } from 'date-fns';
  import { 
    Search, 
    Filter, 
    Plus, 
    ChevronDown, 
    ChevronUp, 
    Phone, 
    Mail, 
    Building2, 
    User, 
    Calendar,
    Star,
    TrendingUp,
    AlertCircle,
    CheckCircle2,
    Clock,
    XCircle,
    Eye
  } from '@lucide/svelte';
  
  // Get leads from the data prop passed from the server
  export let data;
  const { leads } = data;
  
  // State management
  let searchQuery = '';
  let statusFilter = 'ALL';
  let sourceFilter = 'ALL';
  let ratingFilter = 'ALL';
  let sortBy = 'createdAt';
  let sortOrder = 'desc';
  let isLoading = false;
  let showFilters = false;
  
  // Available statuses for filtering
  const statuses = [
    { value: 'ALL', label: 'All Statuses' },
    { value: 'NEW', label: 'New' },
    { value: 'PENDING', label: 'Pending' },
    { value: 'CONTACTED', label: 'Contacted' },
    { value: 'QUALIFIED', label: 'Qualified' },
    { value: 'UNQUALIFIED', label: 'Unqualified' },
    { value: 'CONVERTED', label: 'Converted' }
  ];

  // Lead sources for filtering
  const sources = [
    { value: 'ALL', label: 'All Sources' },
    { value: 'WEB', label: 'Website' },
    { value: 'PHONE_INQUIRY', label: 'Phone Inquiry' },
    { value: 'PARTNER_REFERRAL', label: 'Partner Referral' },
    { value: 'COLD_CALL', label: 'Cold Call' },
    { value: 'TRADE_SHOW', label: 'Trade Show' },
    { value: 'EMPLOYEE_REFERRAL', label: 'Employee Referral' },
    { value: 'ADVERTISEMENT', label: 'Advertisement' },
    { value: 'OTHER', label: 'Other' }
  ];

  // Rating options
  const ratings = [
    { value: 'ALL', label: 'All Ratings' },
    { value: 'Hot', label: 'Hot' },
    { value: 'Warm', label: 'Warm' },
    { value: 'Cold', label: 'Cold' }
  ];
  
  // Sort options
  const sortOptions = [
    { value: 'createdAt', label: 'Created Date' },
    { value: 'firstName', label: 'First Name' },
    { value: 'lastName', label: 'Last Name' },
    { value: 'company', label: 'Company' },
    { value: 'rating', label: 'Rating' }
  ];
  
  // Function to get the full name of a lead
  /**
   * @param {any} lead
   */
  function getFullName(lead) {
    return `${lead.firstName} ${lead.lastName}`.trim();
  }
  
  // Function to map lead status to colors and icons
  /**
   * @param {string} status
   */
  function getStatusConfig(status) {
    switch (status) {
      case 'NEW':
        return { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: Star };
      case 'PENDING':
        return { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: Clock };
      case 'CONTACTED':
        return { color: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle2 };
      case 'QUALIFIED':
        return { color: 'bg-indigo-100 text-indigo-800 border-indigo-200', icon: TrendingUp };
      case 'UNQUALIFIED':
        return { color: 'bg-red-100 text-red-800 border-red-200', icon: XCircle };
      case 'CONVERTED':
        return { color: 'bg-gray-100 text-gray-800 border-gray-200', icon: CheckCircle2 };
      default:
        return { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: AlertCircle };
    }
  }

  // Function to get rating config
  /**
   * @param {string} rating
   */
  function getRatingConfig(rating) {
    switch (rating) {
      case 'Hot':
        return { color: 'text-red-600', dots: 3 };
      case 'Warm':
        return { color: 'text-orange-500', dots: 2 };
      case 'Cold':
        return { color: 'text-blue-500', dots: 1 };
      default:
        return { color: 'text-gray-400', dots: 0 };
    }
  }
  
  // Replace fixed date formatting with relative time
  /**
   * @param {string | Date | null | undefined} dateString
   */
  function formatDate(dateString) {
    if (!dateString) return '-';
    return formatDistanceToNow(new Date(dateString), { addSuffix: true });
  }
  
  // Computed filtered and sorted leads
  $: filteredLeads = leads.filter(lead => {
    const matchesSearch = searchQuery === '' || 
      getFullName(lead).toLowerCase().includes(searchQuery.toLowerCase()) ||
      (lead.company && lead.company.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (lead.email && lead.email.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesStatus = statusFilter === 'ALL' || lead.status === statusFilter;
    const matchesSource = sourceFilter === 'ALL' || lead.leadSource === sourceFilter;
    const matchesRating = ratingFilter === 'ALL' || lead.rating === ratingFilter;
    
    return matchesSearch && matchesStatus && matchesSource && matchesRating;
  }).sort((a, b) => {
    const getFieldValue = (/** @type {any} */ obj, /** @type {string} */ field) => {
      return obj[field];
    };
    
    const aValue = getFieldValue(a, sortBy);
    const bValue = getFieldValue(b, sortBy);
    
    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });
  
  // Function to toggle sort order
  /**
   * @param {string} field
   */
  function toggleSort(field) {
    if (sortBy === field) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = field;
      sortOrder = 'desc';
    }
  }

  // Clear all filters
  function clearFilters() {
    searchQuery = '';
    statusFilter = 'ALL';
    sourceFilter = 'ALL';
    ratingFilter = 'ALL';
    sortBy = 'createdAt';
    sortOrder = 'desc';
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Header -->
  <header class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
            <User class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100">Open Leads</h1>
            <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">{filteredLeads.length} of {leads.length} leads</p>
          </div>
        </div>
        <a 
          href="/app/leads/new" 
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-700 transition-colors duration-200 font-medium"
        >
          <Plus class="w-4 h-4" />
          New Lead
        </a>
      </div>
    </div>
  </header>

  <!-- Filters and Search -->
  <div class="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <!-- Search and Filter Toggle -->
      <div class="flex flex-col sm:flex-row gap-4 mb-4">
        <div class="flex-1 relative">
          <label for="lead-search" class="sr-only">Search leads</label>
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
          <input
            id="lead-search"
            type="text"
            placeholder="Search by name, company, or email..."
            bind:value={searchQuery}
            class="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
          />
        </div>
        <button
          onclick={() => showFilters = !showFilters}
          class="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        >
          <Filter class="w-4 h-4" />
          Filters
          {#if showFilters}
            <ChevronUp class="w-4 h-4" />
          {:else}
            <ChevronDown class="w-4 h-4" />
          {/if}
        </button>
      </div>

      <!-- Advanced Filters -->
      {#if showFilters}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg" transition:fade>
          <div>
            <label for="status-filter" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
            <select id="status-filter" bind:value={statusFilter} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
              {#each statuses as status}
                <option value={status.value}>{status.label}</option>
              {/each}
            </select>
          </div>
          <div>
            <label for="source-filter" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Source</label>
            <select id="source-filter" bind:value={sourceFilter} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
              {#each sources as source}
                <option value={source.value}>{source.label}</option>
              {/each}
            </select>
          </div>
          <div>
            <label for="rating-filter" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Rating</label>
            <select id="rating-filter" bind:value={ratingFilter} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
              {#each ratings as rating}
                <option value={rating.value}>{rating.label}</option>
              {/each}
            </select>
          </div>
          <div class="flex items-end">
            <button
              onclick={clearFilters}
              class="w-full px-4 py-2 text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors bg-white dark:bg-gray-700"
            >
              Clear Filters
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Main Content -->
  <main class="max-w-full mx-auto px-4 sm:px-6 lg:px-8 pb-8">
    {#if isLoading}
      <div class="flex justify-center items-center py-20" transition:fade>
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
      </div>
    {:else if filteredLeads.length === 0}
      <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700" transition:fade>
        <div class="text-gray-400 dark:text-gray-500 text-6xl mb-4">📭</div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No leads found</h3>
        <p class="text-gray-500 dark:text-gray-400 mb-6">Try adjusting your search criteria or create a new lead.</p>
        <a href="/app/leads/new" class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 dark:bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-700 transition-colors font-medium">
          <Plus class="w-4 h-4" />
          Create New Lead
        </a>
      </div>
    {:else}
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden" in:fade={{duration: 300}}>
        <!-- Desktop Table View -->
        <div class="hidden xl:block">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-48">Lead</th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 w-40" onclick={() => toggleSort('company')}>
                    <div class="flex items-center gap-1">
                      Company
                      {#if sortBy === 'company'}
                        {#if sortOrder === 'asc'}
                          <ChevronUp class="w-4 h-4" />
                        {:else}
                          <ChevronDown class="w-4 h-4" />
                        {/if}
                      {/if}
                    </div>
                  </th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-48">Contact</th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">Source</th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">Rating</th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">Status</th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 w-32" onclick={() => toggleSort('createdAt')}>
                    <div class="flex items-center gap-1">
                      Created
                      {#if sortBy === 'createdAt'}
                        {#if sortOrder === 'asc'}
                          <ChevronUp class="w-4 h-4" />
                        {:else}
                          <ChevronDown class="w-4 h-4" />
                        {/if}
                      {/if}
                    </div>
                  </th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-32">Owner</th>
                  <th class="px-4 py-4 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider w-24">Actions</th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {#each filteredLeads as lead, i}
                  {@const statusConfig = getStatusConfig(lead.status)}
                  {@const ratingConfig = getRatingConfig(lead.rating || '')}
                  <tr 
                    class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150"
                    in:fly={{y: 20, duration: 300, delay: i * 50}}
                  >
                    <td class="px-4 py-4">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-full flex items-center justify-center text-white font-medium text-sm flex-shrink-0">
                          {lead.firstName.charAt(0)}{lead.lastName.charAt(0)}
                        </div>
                        <div class="min-w-0">
                          <a href="/app/leads/{lead.id}" class="text-gray-900 dark:text-gray-100 font-medium hover:text-blue-600 dark:hover:text-blue-400 transition-colors block truncate">
                            {getFullName(lead)}
                          </a>
                          {#if lead.title}
                            <p class="text-sm text-gray-500 dark:text-gray-400 truncate">{lead.title}</p>
                          {/if}
                        </div>
                      </div>
                    </td>
                    <td class="px-4 py-4">
                      {#if lead.company}
                        <div class="flex items-center gap-2 min-w-0">
                          <Building2 class="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                          <span class="text-gray-900 dark:text-gray-100 truncate">{lead.company}</span>
                        </div>
                      {:else}
                        <span class="text-gray-400 dark:text-gray-500">-</span>
                      {/if}
                    </td>
                    <td class="px-4 py-4">
                      <div class="space-y-1">
                        {#if lead.email}
                          <a href="mailto:{lead.email}" class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors min-w-0">
                            <Mail class="w-4 h-4 flex-shrink-0" />
                            <span class="truncate">{lead.email}</span>
                          </a>
                        {/if}
                        {#if lead.phone}
                          <a href="tel:{lead.phone}" class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                            <Phone class="w-4 h-4 flex-shrink-0" />
                            <span class="whitespace-nowrap">{lead.phone}</span>
                          </a>
                        {/if}
                        {#if !lead.email && !lead.phone}
                          <span class="text-gray-400 dark:text-gray-500">-</span>
                        {/if}
                      </div>
                    </td>
                    <td class="px-4 py-4">
                      {#if lead.leadSource}
                        <span class="text-sm text-gray-600 dark:text-gray-300 capitalize truncate block">
                          {lead.leadSource.replace('_', ' ').toLowerCase()}
                        </span>
                      {:else}
                        <span class="text-gray-400 dark:text-gray-500">-</span>
                      {/if}
                    </td>
                    <td class="px-4 py-4">
                      {#if lead.rating}
                        <div class="flex items-center gap-1">
                          {#each Array(ratingConfig.dots) as _, i}
                            <div class="w-2 h-2 rounded-full {ratingConfig.color.replace('text-', 'bg-')} flex-shrink-0"></div>
                          {/each}
                          <span class="text-sm {ratingConfig.color} font-medium ml-1 whitespace-nowrap">{lead.rating}</span>
                        </div>
                      {:else}
                        <span class="text-gray-400 dark:text-gray-500">-</span>
                      {/if}
                    </td>
                    <td class="px-4 py-4">
                      <div class="flex items-center gap-2">
                        {#snippet statusIcon(/** @type {any} */ config)}
                          {@const StatusIcon = config.icon}
                          <StatusIcon class="w-4 h-4 {config.color.split(' ')[1]} flex-shrink-0" />
                        {/snippet}
                        {@render statusIcon(statusConfig)}
                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border {statusConfig.color} whitespace-nowrap">
                          {lead.status}
                        </span>
                      </div>
                    </td>
                    <td class="px-4 py-4">
                      <div class="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
                        <Calendar class="w-4 h-4 flex-shrink-0" />
                        <span class="whitespace-nowrap">{formatDate(lead.createdAt)}</span>
                      </div>
                    </td>
                    <td class="px-4 py-4">
                      {#if lead.owner?.name}
                        <div class="flex items-center gap-2 min-w-0">
                          <div class="w-6 h-6 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 text-gray-700 dark:text-gray-200">
                            {lead.owner.name.charAt(0)}
                          </div>
                          <span class="text-sm text-gray-600 dark:text-gray-300 truncate">{lead.owner.name}</span>
                        </div>
                      {:else}
                        <span class="text-gray-400 dark:text-gray-500">-</span>
                      {/if}
                    </td>
                    <td class="px-4 py-4">
                      <a 
                        href="/app/leads/{lead.id}" 
                        class="inline-flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors whitespace-nowrap"
                      >
                        <Eye class="w-4 h-4" />
                        View
                      </a>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Mobile Card View -->
        <div class="xl:hidden divide-y divide-gray-200 dark:divide-gray-700">
          {#each filteredLeads as lead, i}
            {@const statusConfig = getStatusConfig(lead.status)}
            {@const ratingConfig = getRatingConfig(lead.rating || '')}
            <div 
              class="p-6 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150" 
              in:fly={{y: 20, duration: 300, delay: i * 50}}
            >
              <!-- Header -->
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-full flex items-center justify-center text-white font-medium">
                    {lead.firstName.charAt(0)}{lead.lastName.charAt(0)}
                  </div>
                  <div>
                    <a href="/app/leads/{lead.id}" class="text-lg font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      {getFullName(lead)}
                    </a>
                    {#if lead.title}
                      <p class="text-sm text-gray-500 dark:text-gray-400">{lead.title}</p>
                    {/if}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  {#snippet statusIcon(/** @type {any} */ config)}
                    {@const StatusIcon = config.icon}
                    <StatusIcon class="w-4 h-4 {config.color.split(' ')[1]}" />
                  {/snippet}
                  {@render statusIcon(statusConfig)}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {statusConfig.color}">
                    {lead.status}
                  </span>
                </div>
              </div>
              
              <!-- Details Grid -->
              <div class="grid grid-cols-1 gap-3">
                {#if lead.company}
                  <div class="flex items-center gap-2">
                    <Building2 class="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                    <span class="text-gray-700 dark:text-gray-200">{lead.company}</span>
                  </div>
                {/if}
                
                {#if lead.email}
                  <a href="mailto:{lead.email}" class="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    <Mail class="w-4 h-4 flex-shrink-0" />
                    <span class="truncate">{lead.email}</span>
                  </a>
                {/if}
                
                {#if lead.phone}
                  <a href="tel:{lead.phone}" class="flex items-center gap-2 text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    <Phone class="w-4 h-4 flex-shrink-0" />
                    <span>{lead.phone}</span>
                  </a>
                {/if}

                <div class="flex items-center justify-between text-sm">
                  <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                    <Calendar class="w-4 h-4" />
                    {formatDate(lead.createdAt)}
                  </div>
                  
                  {#if lead.rating}
                    <div class="flex items-center gap-1">
                      {#each Array(ratingConfig.dots) as _, i}
                        <div class="w-2 h-2 rounded-full {ratingConfig.color.replace('text-', 'bg-')}"></div>
                      {/each}
                      <span class="text-sm {ratingConfig.color} font-medium ml-1">{lead.rating}</span>
                    </div>
                  {/if}
                </div>

                {#if lead.owner?.name}
                  <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                    <User class="w-4 h-4" />
                    <span>Owned by {lead.owner.name}</span>
                  </div>
                {/if}
              </div>

              <!-- Action Button -->
              <div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                <a 
                  href="/app/leads/{lead.id}" 
                  class="inline-flex items-center gap-2 px-4 py-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors font-medium"
                >
                  <Eye class="w-4 h-4" />
                  View Details
                </a>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </main>
</div>
