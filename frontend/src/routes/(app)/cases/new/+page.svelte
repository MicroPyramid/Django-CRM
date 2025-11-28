<script lang="ts">
  import { enhance } from '$app/forms';
  import { FolderOpen } from '@lucide/svelte';
  export let data;
  let title = '';
  let description = '';
  let accountId = data.preSelectedAccountId || '';
  let dueDate = '';
  let assignedId = '';
  let priority = 'Normal';
  let errorMsg = '';
</script>

<div class="h-screen bg-gray-50/50 dark:bg-gray-900/50 overflow-hidden">
  <div class="container mx-auto px-4 py-4 max-w-2xl h-full">
    <!-- Header -->
    <div class="mb-4">
      <div class="flex items-center gap-3 mb-1">
        <div class="p-1.5 bg-blue-100 dark:bg-blue-900/50 rounded-lg">
          <FolderOpen class="w-5 h-5 text-blue-600 dark:text-blue-400" />
        </div>
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">Create New Case</h1>
      </div>
      <p class="text-sm text-gray-600 dark:text-gray-400">Create and assign a new support case to track customer issues and requests.</p>
    </div>

    <!-- Form Card -->
    <div class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-y-auto">
      <form method="POST" action="?/create" use:enhance class="p-4 space-y-4">
        
        <!-- Case Details Section -->
        <div class="space-y-4">
          <div class="border-b border-gray-100 dark:border-gray-700 pb-2">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-0.5">Case Details</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400">Basic information about the case</p>
          </div>

          <!-- Title -->
          <div class="space-y-1">
            <label for="title" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Case Title <span class="text-red-500 dark:text-red-400">*</span>
            </label>
            <input 
              id="title" 
              type="text" 
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors text-sm placeholder-gray-400 dark:placeholder-gray-500" 
              placeholder="Brief description of the issue..."
              required 
              bind:value={title} 
              name="title" 
            />
          </div>

          <!-- Description -->
          <div class="space-y-1">
            <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Description</label>
            <textarea 
              id="description" 
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors resize-none text-sm placeholder-gray-400 dark:placeholder-gray-500" 
              rows="5" 
              placeholder="Detailed description of the case..."
              bind:value={description} 
              name="description"
            ></textarea>
          </div>

          <!-- Account Selection -->
          <div class="space-y-1">
            <label for="accountId" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Account <span class="text-red-500 dark:text-red-400">*</span>
            </label>
            <select 
              id="accountId" 
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors text-sm" 
              bind:value={accountId} 
              name="accountId" 
              required
            >
              <option value="" disabled>Select an account...</option>
              {#each data.accounts as acc}
                <option value={acc.id}>{acc.name}</option>
              {/each}
            </select>
          </div>
        </div>

        <!-- Assignment Section -->
        <div class="space-y-4">
          <div class="border-b border-gray-100 dark:border-gray-700 pb-2">
            <h2 class="text-base font-semibold text-gray-900 dark:text-white mb-0.5">Assignment & Priority</h2>
            <p class="text-xs text-gray-500 dark:text-gray-400">Set ownership and urgency level</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Due Date -->
            <div class="space-y-1">
              <label for="dueDate" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Due Date</label>
              <input 
                id="dueDate" 
                type="date" 
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors text-sm" 
                bind:value={dueDate} 
                name="dueDate" 
              />
            </div>

            <!-- Priority -->
            <div class="space-y-1">
              <label for="priority" class="block text-sm font-medium text-gray-700 dark:text-gray-300">Priority</label>
              <select
                id="priority"
                class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors text-sm"
                bind:value={priority}
                name="priority"
              >
                <option value="Urgent">🔴 Urgent</option>
                <option value="High">🟠 High</option>
                <option value="Normal">🟡 Normal</option>
                <option value="Low">🟢 Low</option>
              </select>
            </div>
          </div>

          <!-- Assigned To -->
          <div class="space-y-1">
            <label for="assignedId" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Assign To <span class="text-red-500 dark:text-red-400">*</span>
            </label>
            <select 
              id="assignedId" 
              class="w-full px-3 py-2 border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors text-sm" 
              bind:value={assignedId} 
              name="assignedId" 
              required
            >
              <option value="" disabled>Select a team member...</option>
              {#each data.users as u}
                <option value={u.user.id}>{u.user.name}</option>
              {/each}
            </select>
          </div>
        </div>

        <!-- Error Message -->
        {#if errorMsg}
          <div class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p class="text-sm text-red-600 dark:text-red-400">{errorMsg}</p>
          </div>
        {/if}

        <!-- Form Actions -->
        <div class="flex flex-col sm:flex-row gap-2 pt-4 border-t border-gray-100 dark:border-gray-700 sticky bottom-0 bg-white dark:bg-gray-800">
          <button 
            type="submit" 
            class="flex-1 sm:flex-none px-4 py-2 bg-blue-600 dark:bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 dark:hover:bg-blue-500 focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors text-sm"
          >
            Create Case
          </button>
          <a 
            href="/cases" 
            class="flex-1 sm:flex-none px-4 py-2 border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors text-center text-sm"
          >
            Cancel
          </a>
        </div>
      </form>
    </div>
  </div>
</div>
