<script>
  import { ArrowLeft, Mail, Phone, Building2, Calendar, User, MapPin, Edit, Plus, ExternalLink, Clock, DollarSign, Target, CheckCircle, Circle, AlertCircle, Users, Star } from '@lucide/svelte';
  
  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();
  
  const contact = data.contact;
  
  if (!contact) {
    throw new Error('Contact not found');
  }

  // Get primary account relationship
  const primaryAccountRel = contact.accountRelationships?.find(rel => rel.isPrimary);
  const hasMultipleAccounts = contact.accountRelationships?.length > 1;

  /** @param {string | Date} dateStr */
  function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric'
    });
  }

  /** @param {string | Date} dateStr */
  function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
    });
  }

  /** @param {number} amount */
  function formatCurrency(amount) {
    if (!amount) return '$0';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  }

  /** @param {string} status */
  function getStatusColor(status) {
    const colors = {
      'Completed': 'text-green-600 bg-green-50 dark:bg-green-900/20',
      'In Progress': 'text-blue-600 bg-blue-50 dark:bg-blue-900/20',
      'Not Started': 'text-gray-600 bg-gray-50 dark:bg-gray-900/20',
      'CLOSED_WON': 'text-green-600 bg-green-50 dark:bg-green-900/20',
      'CLOSED_LOST': 'text-red-600 bg-red-50 dark:bg-red-900/20',
      'NEGOTIATION': 'text-orange-600 bg-orange-50 dark:bg-orange-900/20',
      'PROPOSAL': 'text-purple-600 bg-purple-50 dark:bg-purple-900/20'
    };
    return colors[/** @type {keyof typeof colors} */ (status)] || 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
  }

  /** @param {string} priority */
  function getPriorityColor(priority) {
    const colors = {
      'High': 'text-red-600 bg-red-50 dark:bg-red-900/20',
      'Normal': 'text-blue-600 bg-blue-50 dark:bg-blue-900/20',
      'Low': 'text-gray-600 bg-gray-50 dark:bg-gray-900/20'
    };
    return colors[/** @type {keyof typeof colors} */ (priority)] || 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Header -->
  <div class="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between py-6">
        <div class="flex items-center gap-4">
          {#if primaryAccountRel}
            <a href="/accounts/{primaryAccountRel.account.id}" class="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 flex items-center transition-colors">
              <ArrowLeft class="w-5 h-5 mr-2" />
              Back to {primaryAccountRel.account.name}
            </a>
          {:else}
            <a href="/contacts" class="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 flex items-center transition-colors">
              <ArrowLeft class="w-5 h-5 mr-2" />
              Back to Contacts
            </a>
          {/if}
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
              {contact.firstName?.[0]}{contact.lastName?.[0]}
            </div>
            <div>
              <h1 class="text-2xl font-bold text-gray-900 dark:text-white">{contact.firstName} {contact.lastName}</h1>
              <p class="text-gray-500 dark:text-gray-400">{contact.title || 'Contact'}</p>
            </div>
            {#if primaryAccountRel?.isPrimary}
              <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 rounded-full flex items-center gap-1">
                <Star class="w-3 h-3" />
                Primary
              </span>
            {/if}
            {#if hasMultipleAccounts}
              <span class="px-2 py-1 text-xs bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 rounded-full flex items-center gap-1">
                <Users class="w-3 h-3" />
                {contact.accountRelationships.length} Accounts
              </span>
            {/if}
          </div>
        </div>
        <div class="flex gap-3 mt-4 sm:mt-0">
          <a href="/contacts/{contact.id}/edit" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
            <Edit class="w-4 h-4" />
            Edit
          </a>
        </div>
      </div>
    </div>
  </div>

  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-8">
      <!-- Main Content -->
      <div class="lg:col-span-3 space-y-8">
        <!-- Contact Information -->
        <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <User class="w-5 h-5" />
            Contact Information
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
              <div>
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Email</span>
                {#if contact.email}
                  <a href="mailto:{contact.email}" class="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mt-1">
                    <Mail class="w-4 h-4" />
                    {contact.email}
                  </a>
                {:else}
                  <p class="text-gray-900 dark:text-white mt-1">N/A</p>
                {/if}
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Phone</span>
                {#if contact.phone}
                  <a href="tel:{contact.phone}" class="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mt-1">
                    <Phone class="w-4 h-4" />
                    {contact.phone}
                  </a>
                {:else}
                  <p class="text-gray-900 dark:text-white mt-1">N/A</p>
                {/if}
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Department</span>
                <p class="text-gray-900 dark:text-white mt-1">{contact.department || 'N/A'}</p>
              </div>
            </div>
            <div class="space-y-4">
              <div>
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Title</span>
                <p class="text-gray-900 dark:text-white mt-1">{contact.title || 'N/A'}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Owner</span>
                <p class="text-gray-900 dark:text-white mt-1">{contact.owner?.name || 'N/A'}</p>
              </div>
              <div>
                <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</span>
                <p class="text-gray-900 dark:text-white mt-1 flex items-center gap-2">
                  <Calendar class="w-4 h-4" />
                  {formatDate(contact.createdAt)}
                </p>
              </div>
            </div>
          </div>
          {#if contact.description}
            <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <span class="text-sm font-medium text-gray-500 dark:text-gray-400">Description</span>
              <p class="text-gray-900 dark:text-white mt-2">{contact.description}</p>
            </div>
          {/if}
        </div>

        <!-- Account Relationships -->
        {#if contact.accountRelationships && contact.accountRelationships.length > 0}
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
              <Building2 class="w-5 h-5" />
              Account Relationships
              <span class="text-sm font-normal text-gray-500 dark:text-gray-400">({contact.accountRelationships.length})</span>
            </h2>
            <div class="space-y-4">
              {#each contact.accountRelationships as relationship}
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div class="flex-1">
                    <div class="flex items-center gap-3">
                      <a href="/accounts/{relationship.account.id}" class="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 flex items-center gap-2">
                        <Building2 class="w-4 h-4" />
                        {relationship.account.name}
                      </a>
                      {#if relationship.isPrimary}
                        <span class="flex px-2 py-0.5 text-xs bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 rounded-full items-center gap-1">
                          <Star class="w-3 h-3" />
                          Primary
                        </span>
                      {/if}
                    </div>
                    <div class="mt-1 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                      {#if relationship.role}
                        <span class="flex items-center gap-1">
                          <User class="w-3 h-3" />
                          {relationship.role}
                        </span>
                      {/if}
                      <span class="flex items-center gap-1">
                        <Calendar class="w-3 h-3" />
                        Since {formatDate(relationship.startDate)}
                      </span>
                    </div>
                    {#if relationship.description}
                      <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">{relationship.description}</p>
                    {/if}
                  </div>
                  <div class="text-right">
                    <span class="text-xs text-gray-500 dark:text-gray-400">
                      {relationship.account.type || 'Account'}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Address Information -->
        {#if contact.street || contact.city || contact.state || contact.country}
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
              <MapPin class="w-5 h-5" />
              Address
            </h2>
            <div class="space-y-2 text-gray-900 dark:text-white">
              {#if contact.street}<p>{contact.street}</p>{/if}
              <p>
                {contact.city || ''}{contact.city && contact.state ? ', ' : ''}{contact.state || ''} {contact.postalCode || ''}
              </p>
              {#if contact.country}<p>{contact.country}</p>{/if}
            </div>
          </div>
        {/if}

        <!-- Recent Opportunities -->
        {#if contact.opportunities && contact.opportunities.length > 0}
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Target class="w-5 h-5" />
                Opportunities
              </h2>
              <a href="/opportunities?contact={contact.id}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                View all
                <ExternalLink class="w-3 h-3" />
              </a>
            </div>
            <div class="space-y-4">
              {#each contact.opportunities as opp}
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <div class="flex-1">
                    <a href="/opportunities/{opp.id}" class="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400">
                      {opp.name}
                    </a>
                    <p class="text-sm text-gray-500 dark:text-gray-400">{opp.account?.name}</p>
                  </div>
                  <div class="text-right">
                    <p class="font-medium text-gray-900 dark:text-white flex items-center gap-1">
                      <DollarSign class="w-4 h-4" />
                      {formatCurrency(opp.amount || 0)}
                    </p>
                    <span class="inline-flex px-2 py-1 text-xs rounded-full {getStatusColor(opp.stage)}">
                      {opp.stage.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <!-- Sidebar -->
      <div class="lg:col-span-1 space-y-8">
        <!-- Recent Tasks -->
        {#if contact.tasks && contact.tasks.length > 0}
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <CheckCircle class="w-5 h-5" />
                Recent Tasks
              </h3>
              <a href="/tasks?contact={contact.id}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">View all</a>
            </div>
            <div class="space-y-3">
              {#each contact.tasks as task}
                <div class="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  {#if task.status === 'Completed'}
                    <CheckCircle class="w-4 h-4 text-green-500 mt-0.5" />
                  {:else}
                    <Circle class="w-4 h-4 text-gray-400 mt-0.5" />
                  {/if}
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">{task.subject}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="inline-flex px-2 py-0.5 text-xs rounded {getPriorityColor(task.priority)}">
                        {task.priority}
                      </span>
                      {#if task.dueDate}
                        <span class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                          <Clock class="w-3 h-3" />
                          {formatDate(task.dueDate)}
                        </span>
                      {/if}
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Upcoming Events -->
        {#if contact.events && contact.events.length > 0}
          <div class="bg-white dark:bg-gray-800 shadow-sm rounded-xl p-6 border border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Calendar class="w-5 h-5" />
                Recent Events
              </h3>
              <a href="/events?contact={contact.id}" class="text-sm text-blue-600 dark:text-blue-400 hover:underline">View all</a>
            </div>
            <div class="space-y-3">
              {#each contact.events as event}
                <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <p class="text-sm font-medium text-gray-900 dark:text-white">{event.subject}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1">
                    <Calendar class="w-3 h-3" />
                    {formatDateTime(event.startDate)}
                  </p>
                  {#if event.location}
                    <p class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <MapPin class="w-3 h-3" />
                      {event.location}
                    </p>
                  {/if}
                </div>
              {/each}
            </div>
          </div>
        {/if}

      </div>
    </div>
  </div>
</div>
