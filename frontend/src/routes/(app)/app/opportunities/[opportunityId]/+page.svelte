<script>
  import { 
    ArrowLeft, 
    Edit, 
    Trash2, 
    DollarSign, 
    Calendar, 
    TrendingUp, 
    Building, 
    User, 
    Target, 
    Percent,
    MapPin,
    Clock,
    FileText,
    Activity,
    Award
  } from '@lucide/svelte';
  
  export let data;
  let opportunity = data.opportunity;
  let account = data.account;
  let owner = data.owner;

  // Stage color mapping
  const stageColors = {
    'PROSPECTING': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    'QUALIFICATION': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
    'PROPOSAL': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
    'NEGOTIATION': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
    'CLOSED_WON': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
    'CLOSED_LOST': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
  };

  /**
   * @param {string} stage
   * @returns {string}
   */
  const getStageColor = (stage) => stageColors[/** @type {keyof typeof stageColors} */ (stage)] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  
  /**
   * @param {number | null} amount
   * @returns {string}
   */
  const formatCurrency = (amount) => {
    return amount ? `$${amount.toLocaleString()}` : 'N/A';
  };

  /**
   * @param {string | Date | null} date
   * @returns {string}
   */
  const formatDate = (date) => {
    return date ? new Date(date).toLocaleDateString() : 'N/A';
  };

  /**
   * @param {string | Date | null} date
   * @returns {string}
   */
  const formatDateTime = (date) => {
    return date ? new Date(date).toLocaleString() : 'N/A';
  };

  /**
   * @param {string} stage
   * @returns {number}
   */
  const getStageProgress = (stage) => {
    const stages = ['PROSPECTING', 'QUALIFICATION', 'PROPOSAL', 'NEGOTIATION', 'CLOSED_WON'];
    const index = stages.indexOf(stage);
    return index >= 0 ? ((index + 1) / stages.length) * 100 : 0;
  };
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div class="flex items-center gap-3">
          <a 
            href={account ? `/app/accounts/${account.id}` : '/app/accounts'} 
            class="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
          >
            <ArrowLeft size={16} />
            Back to Account
          </a>
        </div>
        <div class="flex gap-3">
          <a 
            href={`/app/opportunities/${opportunity.id}/edit`} 
            class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Edit size={16} />
            Edit
          </a>
          <a 
            href={`/app/opportunities/${opportunity.id}/delete`} 
            class="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <Trash2 size={16} />
            Delete
          </a>
        </div>
      </div>
      
      <div class="mt-4">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">{opportunity.name}</h1>
        <div class="mt-2 flex items-center gap-3">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {getStageColor(opportunity.stage)}">
            {opportunity.stage.replace('_', ' ')}
          </span>
          {#if opportunity.probability}
            <div class="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
              <Percent size={14} />
              {opportunity.probability}% probability
            </div>
          {/if}
        </div>
      </div>

      <!-- Stage Progress Bar -->
      {#if opportunity.stage !== 'CLOSED_LOST'}
        <div class="mt-4">
          <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
            <span>Progress</span>
            <span>{Math.round(getStageProgress(opportunity.stage))}%</span>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              class="bg-blue-600 h-2 rounded-full transition-all duration-300" 
              style="width: {getStageProgress(opportunity.stage)}%"
            ></div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      
      <!-- Left Column - Main Details -->
      <div class="lg:col-span-2 space-y-6">
        
        <!-- Financial Information -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center gap-2 mb-4">
            <DollarSign size={20} class="text-green-600" />
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Financial Details</h2>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div class="text-sm text-gray-500 dark:text-gray-400">Amount</div>
              <div class="text-xl font-bold text-gray-900 dark:text-white">{formatCurrency(opportunity.amount)}</div>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div class="text-sm text-gray-500 dark:text-gray-400">Expected Revenue</div>
              <div class="text-xl font-bold text-gray-900 dark:text-white">{formatCurrency(opportunity.expectedRevenue)}</div>
            </div>
          </div>
        </div>

        <!-- Opportunity Details -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center gap-2 mb-4">
            <Target size={20} class="text-blue-600" />
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Opportunity Information</h2>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">Type</div>
              <div class="text-gray-900 dark:text-white">{opportunity.type || 'Not specified'}</div>
            </div>
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">Lead Source</div>
              <div class="text-gray-900 dark:text-white">{opportunity.leadSource || 'Not specified'}</div>
            </div>
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">Forecast Category</div>
              <div class="text-gray-900 dark:text-white">{opportunity.forecastCategory || 'Not specified'}</div>
            </div>
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">Close Date</div>
              <div class="flex items-center gap-1 text-gray-900 dark:text-white">
                <Calendar size={14} />
                {formatDate(opportunity.closeDate)}
              </div>
            </div>
          </div>
        </div>

        <!-- Next Steps -->
        {#if opportunity.nextStep}
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div class="flex items-center gap-2 mb-4">
              <Activity size={20} class="text-orange-600" />
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Next Steps</h2>
            </div>
            <div class="text-gray-700 dark:text-gray-300">{opportunity.nextStep}</div>
          </div>
        {/if}

        <!-- Description -->
        {#if opportunity.description}
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div class="flex items-center gap-2 mb-4">
              <FileText size={20} class="text-gray-600" />
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Description</h2>
            </div>
            <div class="text-gray-700 dark:text-gray-300 whitespace-pre-line">{opportunity.description}</div>
          </div>
        {/if}
      </div>

      <!-- Right Column - Sidebar -->
      <div class="space-y-6">
        
        <!-- Key Metrics -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center gap-2 mb-4">
            <TrendingUp size={20} class="text-purple-600" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Key Metrics</h3>
          </div>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Probability</span>
              <span class="font-semibold text-gray-900 dark:text-white">
                {opportunity.probability ? `${opportunity.probability}%` : 'N/A'}
              </span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-500 dark:text-gray-400">Days to Close</span>
              <span class="font-semibold text-gray-900 dark:text-white">
                {opportunity.closeDate ? Math.ceil((new Date(opportunity.closeDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)) : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <!-- Related Records -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center gap-2 mb-4">
            <Building size={20} class="text-blue-600" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Related Records</h3>
          </div>
          <div class="space-y-4">
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">Account</div>
              {#if account}
                <a 
                  href={`/app/accounts/${account.id}`} 
                  class="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                >
                  {account.name}
                </a>
              {:else}
                <span class="text-gray-500 dark:text-gray-400">No account</span>
              {/if}
            </div>
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">Owner</div>
              <div class="flex items-center gap-2">
                <User size={16} class="text-gray-400" />
                <span class="text-gray-900 dark:text-white">{owner?.name ?? 'Unassigned'}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- System Information -->
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center gap-2 mb-4">
            <Clock size={20} class="text-gray-600" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">System Information</h3>
          </div>
          <div class="space-y-3">
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Created</div>
              <div class="text-sm text-gray-900 dark:text-white">{formatDateTime(opportunity.createdAt)}</div>
            </div>
            <div>
              <div class="text-sm text-gray-500 dark:text-gray-400">Last Updated</div>
              <div class="text-sm text-gray-900 dark:text-white">{formatDateTime(opportunity.updatedAt)}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  @media (max-width: 640px) {
    .max-w-2xl { max-width: 100%; padding: 0.5rem; }
  }
</style>
