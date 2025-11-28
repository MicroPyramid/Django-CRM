<script>
  import { 
    ArrowLeft, 
    Edit, 
    Lock, 
    Unlock, 
    Users, 
    Target, 
    DollarSign, 
    AlertTriangle,
    Plus,
    ExternalLink,
    Phone,
    Mail,
    Globe,
    MapPin,
    MessageSquare,
    CheckSquare,
    FolderOpen,
    Send
  } from '@lucide/svelte';

  /** @type {any} */
  export let data;
  /** @type {any} */
  export let form;

  const { account, contacts, opportunities = [], tasks, cases } = data;
  let comments = data.comments;

  // Form state
  let showCloseModal = false;
  let closureReason = '';
  let closeError = '';

  // Comment functionality
  let newComment = '';
  let isSubmittingComment = false;
  let commentError = '';

  // Active tab state
  let activeTab = 'contacts';

  async function submitComment() {
    commentError = '';
    if (!newComment.trim()) return;
    isSubmittingComment = true;
    try {
      const formData = new FormData();
      formData.append('body', newComment);
      const res = await fetch(`?/comment`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const commentsRes = await fetch(window.location.pathname + '?commentsOnly=1');
        if (commentsRes.ok) {
          const data = await commentsRes.json();
          if (Array.isArray(data.comments)) {
            comments = data.comments;
          }
        }
        newComment = '';
      } else {
        const data = await res.json().catch(() => ({}));
        commentError = data?.error || data?.message || 'Failed to add comment.';
      }
    } catch {
      commentError = 'Failed to add comment.';
    } finally {
      isSubmittingComment = false;
    }
  }

  /**
   * Format date string
   * @param {string | Date | null | undefined} dateStr
   */
  function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  /**
   * Format currency
   * @param {number | null | undefined} value
   */
  function formatCurrency(value) {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value);
  }

  /**
   * Badge color functions
   * @param {string | null | undefined} stage
   */
  function getStageBadgeColor(stage) {
    switch (stage?.toLowerCase()) {
      case 'prospecting': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'qualification': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400';
      case 'proposal': return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400';
      case 'negotiation': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'closed_won': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'closed_lost': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  }

  /**
   * @param {string | null | undefined} status
   */
  function getCaseStatusBadgeColor(status) {
    switch (status?.toLowerCase()) {
      case 'open': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'in_progress': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'closed': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  }

  // Handle form submission errors
  $: {
    if (form?.success === false) {
      closeError = form.message;
    }
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Header -->
  <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between py-6">
        <div class="flex items-center space-x-4">
          <a 
            href="/accounts"
            class="inline-flex items-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          >
            <ArrowLeft class="w-5 h-5 mr-2" />
            Back to Accounts
          </a>
          <div class="border-l border-gray-300 dark:border-gray-600 pl-4">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{account.name}</h1>
            <div class="flex items-center mt-1 space-x-2">
              <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                account?.isActive ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 
                'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
              }`}>
                {account.isActive ? 'Active' : 'Inactive'}
              </span>
              {#if account.type}
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                  {account.type}
                </span>
              {/if}
            </div>
          </div>
        </div>
        
        <div class="flex items-center space-x-3">
          {#if account.closedAt}
            <form method="POST" action="?/reopenAccount">
              <button 
                type="submit" 
                class="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <Unlock class="w-4 h-4 mr-2" />
                Reopen Account
              </button>
            </form>
          {:else}
            <a 
              href="/accounts/{account.id}/edit"
              class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <Edit class="w-4 h-4 mr-2" />
              Edit
            </a>
            <button 
              onclick={() => showCloseModal = true}
              class="inline-flex items-center px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <Lock class="w-4 h-4 mr-2" />
              Close Account
            </button>
          {/if}
        </div>
      </div>
    </div>
  </div>

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-8">
        <!-- Account Information -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Account Information</h2>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-4">
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Name</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">{account.name || 'N/A'}</p>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Industry</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">{account.industry || 'N/A'}</p>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Website</span>
                  {#if account.website}
                    <a 
                      href={account.website.startsWith('http') ? account.website : `https://${account.website}`} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      class="mt-1 inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      <Globe class="w-4 h-4 mr-1" />
                      {account.website}
                      <ExternalLink class="w-3 h-3 ml-1" />
                    </a>
                  {:else}
                    <p class="mt-1 text-sm text-gray-900 dark:text-white">N/A</p>
                  {/if}
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Phone</span>
                  {#if account.phone}
                    <a href={`tel:${account.phone}`} class="mt-1 inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline">
                      <Phone class="w-4 h-4 mr-1" />
                      {account.phone}
                    </a>
                  {:else}
                    <p class="mt-1 text-sm text-gray-900 dark:text-white">N/A</p>
                  {/if}
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Email</span>
                  {#if account.email}
                    <a href={`mailto:${account.email}`} class="mt-1 inline-flex items-center text-sm text-blue-600 dark:text-blue-400 hover:underline">
                      <Mail class="w-4 h-4 mr-1" />
                      {account.email}
                    </a>
                  {:else}
                    <p class="mt-1 text-sm text-gray-900 dark:text-white">N/A</p>
                  {/if}
                </div>
              </div>
              
              <div class="space-y-4">
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Annual Revenue</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">
                    {account.annualRevenue ? formatCurrency(account.annualRevenue) : 'N/A'}
                  </p>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Employees</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">
                    {account.numberOfEmployees ? account.numberOfEmployees.toLocaleString() : 'N/A'}
                  </p>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Ownership</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">{account.accountOwnership || 'N/A'}</p>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Rating</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">{account.rating || 'N/A'}</p>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-500 dark:text-gray-400">SIC Code</span>
                  <p class="mt-1 text-sm text-gray-900 dark:text-white">{account.sicCode || 'N/A'}</p>
                </div>
              </div>
            </div>
            
            {#if account.street || account.city || account.state || account.country}
              <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Address</span>
                <div class="mt-1 flex items-start text-sm text-gray-900 dark:text-white">
                  <MapPin class="w-4 h-4 mr-2 mt-0.5 text-gray-400" />
                  <address class="not-italic">
                    {account.street || ''}<br>
                    {account.city || ''}{account.city && account.state ? ', ' : ''}{account.state || ''} {account.postalCode || ''}<br>
                    {account.country || ''}
                  </address>
                </div>
              </div>
            {/if}
            
            {#if account.description}
              <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</span>
                <p class="mt-1 text-sm text-gray-900 dark:text-white whitespace-pre-line">{account.description}</p>
              </div>
            {/if}
            
            {#if account.closedAt}
              <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <div class="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
                  <div class="flex">
                    <AlertTriangle class="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
                    <div>
                      <p class="font-medium text-red-800 dark:text-red-200">This account was closed on {formatDate(account.closedAt)}.</p>
                      <p class="text-red-700 dark:text-red-300 mt-1">Reason: {account.closureReason || 'No reason provided'}</p>
                    </div>
                  </div>
                </div>
              </div>
            {/if}
            
            <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-500 dark:text-gray-400">Created</span>
                <p class="text-gray-900 dark:text-white">{formatDate(account.createdAt)}</p>
              </div>
              <div>
                <span class="text-gray-500 dark:text-gray-400">Last Updated</span>
                <p class="text-gray-900 dark:text-white">{formatDate(account.updatedAt)}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Related Records Tabs -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <!-- Tab Navigation -->
          <div class="border-b border-gray-200 dark:border-gray-700">
            <nav class="flex space-x-8 px-6" aria-label="Tabs">
              <button
                onclick={() => activeTab = 'contacts'}
                class={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'contacts' 
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Contacts ({contacts.length})
              </button>
              <button
                onclick={() => activeTab = 'opportunities'}
                class={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'opportunities' 
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Opportunities ({opportunities.length})
              </button>
              <button
                onclick={() => activeTab = 'tasks'}
                class={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'tasks' 
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Tasks ({tasks.length})
              </button>
              <button
                onclick={() => activeTab = 'cases'}
                class={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'cases' 
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Cases ({cases.length})
              </button>
              <button
                onclick={() => activeTab = 'notes'}
                class={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'notes' 
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400' 
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                Notes ({comments.length})
              </button>
            </nav>
          </div>

          <!-- Tab Content -->
          <div class="p-6">
            {#if activeTab === 'contacts'}
              {#if contacts.length === 0}
                <div class="text-center py-12">
                  <Users class="mx-auto h-12 w-12 text-gray-400" />
                  <p class="mt-2 text-gray-500 dark:text-gray-400">No contacts found for this account</p>
                  <a 
                    href="/contacts/new?accountId={account.id}"
                    class="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Plus class="w-4 h-4 mr-2" />
                    Add Contact
                  </a>
                </div>
              {:else}
                <div class="overflow-x-auto">
                  <table class="min-w-full">
                    <thead>
                      <tr class="border-b border-gray-200 dark:border-gray-700">
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Title</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Email</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Phone</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                        <th class="pb-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                      {#each contacts as contact (contact.id)}
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td class="py-4 font-medium text-gray-900 dark:text-white">
                            <a href="/contacts/{contact.id}" class="hover:text-blue-600 dark:hover:text-blue-400 hover:underline">
                              {contact.firstName} {contact.lastName}
                            </a>
                            {#if contact.isPrimary}
                              <span class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400">
                                Primary
                              </span>
                            {/if}
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white">{contact.title || 'N/A'}</td>
                          <td class="py-4 text-gray-900 dark:text-white hidden md:table-cell">
                            {#if contact.email}
                              <a href="mailto:{contact.email}" class="text-blue-600 dark:text-blue-400 hover:underline">
                                {contact.email}
                              </a>
                            {:else}
                              N/A
                            {/if}
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white hidden lg:table-cell">
                            {#if contact.phone}
                              <a href="tel:{contact.phone}" class="text-blue-600 dark:text-blue-400 hover:underline">
                                {contact.phone}
                              </a>
                            {:else}
                              N/A
                            {/if}
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white">{contact.role || 'N/A'}</td>
                          <td class="py-4 text-right">
                            <a href="/contacts/{contact.id}" class="text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium">View</a>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              {/if}
            {/if}

            {#if activeTab === 'opportunities'}
              {#if opportunities.length === 0}
                <div class="text-center py-12">
                  <Target class="mx-auto h-12 w-12 text-gray-400" />
                  <p class="mt-2 text-gray-500 dark:text-gray-400">No opportunities found for this account</p>
                  <a 
                    href="/opportunities/new?accountId={account.id}"
                    class="mt-4 inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Plus class="w-4 h-4 mr-2" />
                    Add Opportunity
                  </a>
                </div>
              {:else}
                <div class="overflow-x-auto">
                  <table class="min-w-full">
                    <thead>
                      <tr class="border-b border-gray-200 dark:border-gray-700">
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Value</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Stage</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Close Date</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Probability</th>
                        <th class="pb-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                      {#each opportunities as opportunity (opportunity.id)}
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td class="py-4 font-medium text-gray-900 dark:text-white">
                            <a href="/opportunities/{opportunity.id}" class="hover:text-blue-600 dark:hover:text-blue-400 hover:underline">
                              {opportunity.name}
                            </a>
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white">{formatCurrency(opportunity.amount)}</td>
                          <td class="py-4">
                            <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStageBadgeColor(opportunity.stage)}`}>
                              {opportunity.stage || 'Unknown'}
                            </span>
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white hidden md:table-cell">{formatDate(opportunity.closeDate)}</td>
                          <td class="py-4 text-gray-900 dark:text-white hidden lg:table-cell">{opportunity.probability ? `${opportunity.probability}%` : 'N/A'}</td>
                          <td class="py-4 text-right">
                            <a href="/opportunities/{opportunity.id}" class="text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium">View</a>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              {/if}
            {/if}

            {#if activeTab === 'tasks'}
              {#if tasks.length === 0}
                <div class="text-center py-12">
                  <CheckSquare class="mx-auto h-12 w-12 text-gray-400" />
                  <p class="mt-2 text-gray-500 dark:text-gray-400">No tasks found for this account</p>
                  <a 
                    href="/tasks/new?accountId={account.id}"
                    class="mt-4 inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Plus class="w-4 h-4 mr-2" />
                    Add Task
                  </a>
                </div>
              {:else}
                <div class="overflow-x-auto">
                  <table class="min-w-full">
                    <thead>
                      <tr class="border-b border-gray-200 dark:border-gray-700">
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Subject</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Priority</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Due Date</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Assigned To</th>
                        <th class="pb-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                      {#each tasks as task (task.id)}
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td class="py-4 font-medium text-gray-900 dark:text-white">
                            <a href="/tasks/{task.id}" class="hover:text-blue-600 dark:hover:text-blue-400 hover:underline">
                              {task.subject}
                            </a>
                          </td>
                          <td class="py-4">
                            <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              task.status === 'Completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 
                              task.status === 'In Progress' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400' : 
                              'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                            }`}>
                              {task.status}
                            </span>
                          </td>
                          <td class="py-4">
                            <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              task.priority === 'High' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' : 
                              task.priority === 'Normal' ? 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300' : 
                              'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                            }`}>
                              {task.priority}
                            </span>
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white hidden md:table-cell">{formatDate(task.dueDate)}</td>
                          <td class="py-4 text-gray-900 dark:text-white hidden lg:table-cell">{task.owner?.name || 'Unassigned'}</td>
                          <td class="py-4 text-right">
                            <a href="/tasks/{task.id}" class="text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium">View</a>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              {/if}
            {/if}

            {#if activeTab === 'cases'}
              {#if cases.length === 0}
                <div class="text-center py-12">
                  <FolderOpen class="mx-auto h-12 w-12 text-gray-400" />
                  <p class="mt-2 text-gray-500 dark:text-gray-400">No cases found for this account</p>
                  <a 
                    href="/cases/new?accountId={account.id}"
                    class="mt-4 inline-flex items-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Plus class="w-4 h-4 mr-2" />
                    Open Case
                  </a>
                </div>
              {:else}
                <div class="overflow-x-auto">
                  <table class="min-w-full">
                    <thead>
                      <tr class="border-b border-gray-200 dark:border-gray-700">
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Case Number</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Subject</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Priority</th>
                        <th class="pb-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Created Date</th>
                        <th class="pb-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                      {#each cases as caseItem (caseItem.id)}
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                          <td class="py-4 font-medium text-gray-900 dark:text-white">
                            <a href="/cases/{caseItem.id}" class="hover:text-blue-600 dark:hover:text-blue-400 hover:underline">
                              {caseItem.caseNumber}
                            </a>
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white">{caseItem.subject}</td>
                          <td class="py-4">
                            <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCaseStatusBadgeColor(caseItem.status)}`}>
                              {caseItem.status}
                            </span>
                          </td>
                          <td class="py-4">
                            <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              caseItem.priority === 'Urgent' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                              caseItem.priority === 'High' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400' :
                              caseItem.priority === 'Normal' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400' :
                              'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'
                            }`}>
                              {caseItem.priority}
                            </span>
                          </td>
                          <td class="py-4 text-gray-900 dark:text-white hidden md:table-cell">{formatDate(caseItem.createdAt)}</td>
                          <td class="py-4 text-right">
                            <a href="/cases/{caseItem.id}" class="text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium">View</a>
                          </td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              {/if}
            {/if}

            {#if activeTab === 'notes'}
              <div class="space-y-6">
                <!-- Add Note Form -->
                <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <label for="comment" class="block text-sm font-medium text-gray-900 dark:text-white mb-2">Add a note</label>
                  <textarea 
                    id="comment" 
                    rows="3" 
                    placeholder="Write your note here..." 
                    bind:value={newComment}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  ></textarea>
                  {#if commentError}
                    <p class="text-red-600 text-sm mt-2">{commentError}</p>
                  {/if}
                  <div class="mt-3 flex justify-end">
                    <button 
                      onclick={submitComment} 
                      disabled={isSubmittingComment}
                      class="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      <Send class="w-4 h-4 mr-2" />
                      {#if isSubmittingComment}Adding...{:else}Add Note{/if}
                    </button>
                  </div>
                </div>

                <!-- Comments List -->
                {#if comments.length === 0}
                  <div class="text-center py-12">
                    <MessageSquare class="mx-auto h-12 w-12 text-gray-400" />
                    <p class="mt-2 text-gray-500 dark:text-gray-400">No notes found for this account</p>
                  </div>
                {:else}
                  <div class="space-y-4">
                    {#each comments as comment (comment.id)}
                      <div class="bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 p-4">
                        <div class="flex justify-between items-start mb-2">
                          <div class="flex items-center space-x-2">
                            <span class="font-medium text-gray-900 dark:text-white">{comment.author?.name || 'Unknown'}</span>
                            <span class="text-xs text-gray-500 dark:text-gray-400">
                              {formatDate(comment.createdAt)}
                            </span>
                            {#if comment.isPrivate}
                              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400">
                                Private
                              </span>
                            {/if}
                          </div>
                        </div>
                        <p class="text-gray-700 dark:text-gray-300 whitespace-pre-line">{comment.body}</p>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Quick Stats -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Overview</h2>
          </div>
          <div class="p-6 space-y-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Contacts</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white">{contacts.length}</p>
              </div>
              <Users class="w-8 h-8 text-blue-500" />
            </div>
            
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Opportunities</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white">{opportunities.length}</p>
              </div>
              <Target class="w-8 h-8 text-green-500" />
            </div>
            
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Pipeline Value</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(opportunities.reduce(/** @param {number} sum @param {any} opp */ (sum, opp) => sum + (opp.amount || 0), 0))}
                </p>
              </div>
              <DollarSign class="w-8 h-8 text-yellow-500" />
            </div>
            
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-500 dark:text-gray-400">Open Cases</p>
                <p class="text-2xl font-bold text-gray-900 dark:text-white">
                  {cases.filter(/** @param {any} c */ (c) => c.status !== 'CLOSED').length}
                </p>
              </div>
              <AlertTriangle class="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Quick Actions</h2>
          </div>
          <div class="p-6 space-y-3">
            <a 
              href="/contacts/new?accountId={account.id}"
              class="w-full inline-flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <Users class="w-4 h-4 mr-2" />
              Add Contact
            </a>
            <a 
              href="/opportunities/new?accountId={account.id}"
              class="w-full inline-flex items-center justify-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <Target class="w-4 h-4 mr-2" />
              Add Opportunity
            </a>
            <a 
              href="/tasks/new?accountId={account.id}"
              class="w-full inline-flex items-center justify-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <CheckSquare class="w-4 h-4 mr-2" />
              Add Task
            </a>
            <a 
              href="/cases/new?accountId={account.id}"
              class="w-full inline-flex items-center justify-center px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <FolderOpen class="w-4 h-4 mr-2" />
              Open Case
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Close Account Modal -->
  {#if showCloseModal}
    <div class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div 
          class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" 
          role="button"
          tabindex="0"
          aria-label="Close modal"
          onclick={() => showCloseModal = false}
          onkeydown={(e) => e.key === 'Escape' && (showCloseModal = false)}
        ></div>
        
        <div class="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
          <form method="POST" action="?/closeAccount">
            <div class="bg-white dark:bg-gray-800 px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
              <div class="sm:flex sm:items-start">
                <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20 sm:mx-0 sm:h-10 sm:w-10">
                  <Lock class="h-6 w-6 text-red-600 dark:text-red-400" />
                </div>
                <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                  <h3 class="text-base font-semibold leading-6 text-gray-900 dark:text-white">Close Account</h3>
                  <div class="mt-2">
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      You are about to close the account "{account.name}". This action will mark the account as closed but will retain all account data for historical purposes.
                    </p>
                    
                    <div class="mt-4">
                      <label for="closureReason" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Reason for Closing <span class="text-red-500">*</span>
                      </label>
                      <textarea 
                        id="closureReason" 
                        name="closureReason" 
                        rows="3" 
                        placeholder="Please provide a reason for closing this account..." 
                        bind:value={closureReason}
                        class="mt-1 w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      ></textarea>
                      {#if closeError}
                        <p class="mt-1 text-sm text-red-600 dark:text-red-400">{closeError}</p>
                      {/if}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
              <button 
                type="submit" 
                class="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto"
              >
                Close Account
              </button>
              <button 
                type="button" 
                onclick={() => showCloseModal = false}
                class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto dark:bg-gray-600 dark:text-white dark:ring-gray-500 dark:hover:bg-gray-500"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  {/if}
</div>
