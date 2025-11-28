<script>
  import { DollarSign, Calendar, Target, TrendingUp, FileText, User, Building, ArrowLeft, Save, X } from '@lucide/svelte';
  
  export let data;
  let opportunity = { ...data.opportunity };
  let error = '';
  let isSubmitting = false;
  
  let closeDateStr = opportunity.closeDate
    ? new Date(opportunity.closeDate).toISOString().slice(0, 10)
    : '';
  
  $: {
    if (closeDateStr) {
      opportunity.closeDate = new Date(closeDateStr);
    } else {
      opportunity.closeDate = null;
    }
  }

  /**
   * @param {SubmitEvent} e
   */
  async function handleSubmit(e) {
    e.preventDefault();
    isSubmitting = true;
    error = '';
    
    const target = /** @type {HTMLFormElement} */ (e.target);
    const formData = new FormData(target);
    const res = await fetch('', { method: 'POST', body: formData });
    
    if (res.ok) {
      window.location.href = `/opportunities/${opportunity.id}`;
    } else {
      const result = await res.json();
      error = result?.message || 'Failed to update opportunity.';
    }
    isSubmitting = false;
  }

  const leadSources = [
    { value: 'WEB', label: 'Web' },
    { value: 'PHONE_INQUIRY', label: 'Phone Inquiry' },
    { value: 'PARTNER_REFERRAL', label: 'Partner Referral' },
    { value: 'COLD_CALL', label: 'Cold Call' },
    { value: 'TRADE_SHOW', label: 'Trade Show' },
    { value: 'EMPLOYEE_REFERRAL', label: 'Employee Referral' },
    { value: 'ADVERTISEMENT', label: 'Advertisement' },
    { value: 'OTHER', label: 'Other' }
  ];

  const forecastCategories = [
    { value: 'Pipeline', label: 'Pipeline' },
    { value: 'Best Case', label: 'Best Case' },
    { value: 'Commit', label: 'Commit' },
    { value: 'Closed', label: 'Closed' }
  ];
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <a 
            href={`/opportunities/${opportunity.id}`}
            class="inline-flex items-center justify-center w-10 h-10 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <ArrowLeft class="w-5 h-5" />
          </a>
          <div>
            <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Opportunity</h1>
            <p class="text-gray-600 dark:text-gray-400 mt-1">Update opportunity details and track progress</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Form Card -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
      <form onsubmit={handleSubmit} class="p-6 sm:p-8">
        <!-- Basic Information Section -->
        <div class="mb-8">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center">
            <Building class="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
            Basic Information
          </h2>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Name -->
            <div class="lg:col-span-2">
              <label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Opportunity Name *
              </label>
              <input 
                id="name" 
                name="name" 
                type="text"
                bind:value={opportunity.name}
                required
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
                placeholder="Enter opportunity name"
              />
            </div>

            <!-- Amount -->
            <div>
              <label for="amount" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <DollarSign class="w-4 h-4 inline mr-1" />
                Amount
              </label>
              <input 
                id="amount" 
                name="amount" 
                type="number"
                step="0.01"
                min="0"
                bind:value={opportunity.amount}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
                placeholder="0.00"
              />
            </div>

            <!-- Expected Revenue -->
            <div>
              <label for="expectedRevenue" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <TrendingUp class="w-4 h-4 inline mr-1" />
                Expected Revenue
              </label>
              <input 
                id="expectedRevenue" 
                name="expectedRevenue" 
                type="number"
                step="0.01"
                min="0"
                bind:value={opportunity.expectedRevenue}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
                placeholder="0.00"
              />
            </div>

            <!-- Stage -->
            <div>
              <label for="stage" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Target class="w-4 h-4 inline mr-1" />
                Stage *
              </label>
              <select 
                id="stage"
                name="stage" 
                bind:value={opportunity.stage}
                required
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
              >
                <option value="PROSPECTING">Prospecting</option>
                <option value="QUALIFICATION">Qualification</option>
                <option value="PROPOSAL">Proposal</option>
                <option value="NEGOTIATION">Negotiation</option>
                <option value="CLOSED_WON">Closed Won</option>
                <option value="CLOSED_LOST">Closed Lost</option>
              </select>
            </div>

            <!-- Probability -->
            <div>
              <label for="probability" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Probability (%)
              </label>
              <input 
                id="probability" 
                name="probability" 
                type="number"
                min="0"
                max="100"
                bind:value={opportunity.probability}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
                placeholder="0"
              />
            </div>

            <!-- Close Date -->
            <div>
              <label for="closeDate" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Calendar class="w-4 h-4 inline mr-1" />
                Close Date
              </label>
              <input 
                id="closeDate" 
                name="closeDate" 
                type="date"
                bind:value={closeDateStr}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
              />
            </div>

            <!-- Lead Source -->
            <div>
              <label for="leadSource" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <User class="w-4 h-4 inline mr-1" />
                Lead Source
              </label>
              <select 
                id="leadSource"
                name="leadSource" 
                bind:value={opportunity.leadSource}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
              >
                <option value="">Select source...</option>
                {#each leadSources as source}
                  <option value={source.value}>{source.label}</option>
                {/each}
              </select>
            </div>

            <!-- Forecast Category -->
            <div>
              <label for="forecastCategory" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Forecast Category
              </label>
              <select 
                id="forecastCategory"
                name="forecastCategory" 
                bind:value={opportunity.forecastCategory}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
              >
                <option value="">Select category...</option>
                {#each forecastCategories as category}
                  <option value={category.value}>{category.label}</option>
                {/each}
              </select>
            </div>

            <!-- Type -->
            <div>
              <label for="type" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Type
              </label>
              <input 
                id="type" 
                name="type" 
                type="text"
                bind:value={opportunity.type}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
                placeholder="e.g., New Business, Existing Business"
              />
            </div>

            <!-- Next Step -->
            <div class="lg:col-span-2">
              <label for="nextStep" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Next Step
              </label>
              <input 
                id="nextStep" 
                name="nextStep" 
                type="text"
                bind:value={opportunity.nextStep}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors"
                placeholder="What's the next action to take?"
              />
            </div>

            <!-- Description -->
            <div class="lg:col-span-2">
              <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <FileText class="w-4 h-4 inline mr-1" />
                Description
              </label>
              <textarea 
                id="description" 
                name="description" 
                rows="4"
                bind:value={opportunity.description}
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white transition-colors resize-none"
                placeholder="Provide additional details about this opportunity..."
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Error Message -->
        {#if error}
          <div class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div class="flex items-center">
              <X class="w-5 h-5 text-red-400 mr-2" />
              <p class="text-red-800 dark:text-red-400 text-sm">{error}</p>
            </div>
          </div>
        {/if}

        <!-- Action Buttons -->
        <div class="flex items-center justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
          <a 
            href={`/opportunities/${opportunity.id}`}
            class="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium"
          >
            Cancel
          </a>
          <button 
            type="submit" 
            disabled={isSubmitting}
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors font-medium flex items-center"
          >
            {#if isSubmitting}
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Saving...
            {:else}
              <Save class="w-4 h-4 mr-2" />
              Save Changes
            {/if}
          </button>
        </div>
      </form>
    </div>
  </div>
</div>

