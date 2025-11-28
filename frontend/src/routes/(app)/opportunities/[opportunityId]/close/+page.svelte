<script>
  import { Check, X, Calendar, FileText } from '@lucide/svelte';
  import { enhance } from '$app/forms';
  
  export let data;
  export let form;
  
  let opportunity = data.opportunity;
  let isSubmitting = false;
  let selectedStatus = 'CLOSED_WON';
  let closeDate = new Date().toISOString().split('T')[0];
  let closeReason = '';

  const statusOptions = [
    { value: 'CLOSED_WON', label: 'Closed Won', color: 'text-green-600' },
    { value: 'CLOSED_LOST', label: 'Closed Lost', color: 'text-red-600' }
  ];

</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
  <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white flex items-center gap-3">
          <div class="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
            <Check class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          Close Opportunity
        </h1>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Update the status and close details for this opportunity
        </p>
      </div>
    </div>

    <!-- Opportunity Info -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 mb-6">
      <div class="px-6 py-4">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white mb-4">Opportunity Details</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Name</p>
            <p class="text-base text-gray-900 dark:text-white">{opportunity.name}</p>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Amount</p>
            <p class="text-base text-gray-900 dark:text-white">
              {opportunity.amount ? `$${opportunity.amount.toLocaleString()}` : 'Not specified'}
            </p>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Current Stage</p>
            <p class="text-base text-gray-900 dark:text-white">{opportunity.stage.replace('_', ' ')}</p>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Probability</p>
            <p class="text-base text-gray-900 dark:text-white">
              {opportunity.probability ? `${opportunity.probability}%` : 'Not specified'}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Close Form -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 class="text-lg font-medium text-gray-900 dark:text-white">Close Opportunity</h2>
      </div>
      
      <form method="POST" use:enhance={() => {
        return async ({ update }) => {
          isSubmitting = true;
          await update();
          isSubmitting = false;
        };
      }} class="p-6 space-y-6">
        {#if form?.error}
          <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div class="flex items-center gap-2">
              <X class="w-5 h-5 text-red-600 dark:text-red-400" />
              <span class="text-sm font-medium text-red-800 dark:text-red-400">Error</span>
            </div>
            <p class="text-sm text-red-700 dark:text-red-300 mt-1">{form.error}</p>
          </div>
        {/if}

        <!-- Status Selection -->
        <div>
          <label for="status" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Closing Status *
          </label>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {#each statusOptions as option}
              <label class="relative cursor-pointer">
                <input
                  type="radio"
                  name="status"
                  value={option.value}
                  bind:group={selectedStatus}
                  class="sr-only"
                  required
                />
                <div class="border-2 rounded-lg p-4 transition-all duration-200 {selectedStatus === option.value 
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'}">
                  <div class="flex items-center justify-between">
                    <span class="font-medium {option.color} dark:opacity-90">{option.label}</span>
                    {#if selectedStatus === option.value}
                      <Check class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    {/if}
                  </div>
                </div>
              </label>
            {/each}
          </div>
        </div>

        <!-- Close Date -->
        <div>
          <label for="closeDate" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            <Calendar class="w-4 h-4 inline mr-1" />
            Close Date *
          </label>
          <input
            type="date"
            id="closeDate"
            name="closeDate"
            bind:value={closeDate}
            required
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   disabled:bg-gray-50 disabled:text-gray-500"
          />
        </div>

        <!-- Close Reason -->
        <div>
          <label for="closeReason" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            <FileText class="w-4 h-4 inline mr-1" />
            Reason for Closing
          </label>
          <textarea
            id="closeReason"
            name="closeReason"
            bind:value={closeReason}
            rows="4"
            placeholder="Provide details about why this opportunity is being closed..."
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white
                   focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                   placeholder-gray-400 dark:placeholder-gray-500 resize-none"
          ></textarea>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-col sm:flex-row gap-3 pt-4">
          <button
            type="submit"
            disabled={isSubmitting}
            class="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 
                   text-white font-medium py-2 px-4 rounded-lg
                   transition-colors duration-200 flex items-center justify-center gap-2
                   disabled:cursor-not-allowed"
          >
            {#if isSubmitting}
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Closing Opportunity...
            {:else}
              <Check class="w-4 h-4" />
              Close Opportunity
            {/if}
          </button>
          
          <a
            href={`/opportunities/${opportunity.id}`}
            class="flex-1 sm:flex-none px-6 py-2 text-gray-700 dark:text-gray-300 
                   bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 
                   rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 
                   transition-colors duration-200 text-center font-medium"
          >
            Cancel
          </a>
        </div>
      </form>
    </div>
  </div>
</div>

<style>
  @media (max-width: 640px) {
    .max-w-md { max-width: 100%; padding: 0.5rem; }
  }
</style>
