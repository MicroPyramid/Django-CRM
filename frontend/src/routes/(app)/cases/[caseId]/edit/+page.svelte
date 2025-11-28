<script lang="ts">
  export let data;
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { Save, X, AlertTriangle, User, Building, Calendar, Flag, FileText, Lock, Unlock } from '@lucide/svelte';

  let title = data.caseItem.subject;
  let description = data.caseItem.description || '';
  let accountId = data.caseItem.accountId;
  let dueDate = '';
  if (data.caseItem.dueDate) {
    const dueDateValue: any = data.caseItem.dueDate;
    if (typeof dueDateValue === 'string') {
      dueDate = dueDateValue.split('T')[0];
    } else if (dueDateValue instanceof Date) {
      dueDate = dueDateValue.toISOString().split('T')[0];
    }
  }
  let assignedId = data.caseItem.ownerId;
  let priority = data.caseItem.priority || 'Normal';
  let errorMsg = '';
  let successMsg = '';
  let loading = false;
  let showCloseConfirmation = false;
  let showReopenConfirmation = false;

  function handleCloseCase() {
    showCloseConfirmation = true;
  }

  function confirmCloseCase() {
    const form = document.getElementById('close-case-form');
    if (form && 'submit' in form && typeof form.submit === 'function') {
      form.submit();
    }
    showCloseConfirmation = false;
  }

  function cancelCloseCase() {
    showCloseConfirmation = false;
  }

  function handleReopenCase() {
    showReopenConfirmation = true;
  }

  function confirmReopenCase() {
    const form = document.getElementById('reopen-case-form');
    if (form && 'submit' in form && typeof form.submit === 'function') {
      form.submit();
    }
    showReopenConfirmation = false;
  }

  function cancelReopenCase() {
    showReopenConfirmation = false;
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
  <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Edit Case</h1>
          <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">Update case details and assignment</p>
        </div>
        <div class="flex items-center gap-3">
          <button 
            onclick={() => goto(`/cases/${data.caseItem.id}`)}
            class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900 transition-colors"
          >
            <X size="16" />
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Main Form -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <form method="POST" action="?/update" use:enhance={({ formData, cancel }) => {
        loading = true;
        errorMsg = '';
        successMsg = '';
        return async ({ result, update }) => {
          loading = false;
          if (result.type === 'failure') {
            errorMsg = (result.data as any)?.error || 'An error occurred';
          } else if (result.type === 'success') {
            successMsg = 'Case updated successfully!';
            // Update the data and reset form values from fresh data
            await update();
            // Re-initialize form values from updated data
            title = data.caseItem.subject;
            description = data.caseItem.description || '';
            accountId = data.caseItem.accountId;
            if (data.caseItem.dueDate) {
              const dueDateValue: any = data.caseItem.dueDate;
              if (typeof dueDateValue === 'string') {
                dueDate = dueDateValue.split('T')[0];
              } else if (dueDateValue instanceof Date) {
                dueDate = dueDateValue.toISOString().split('T')[0];
              }
            } else {
              dueDate = '';
            }
            assignedId = data.caseItem.ownerId;
            priority = data.caseItem.priority || 'Normal';
          } else {
            await update();
          }
        };
      }}>
        <!-- Hidden field for status -->
        <input type="hidden" name="status" value={data.caseItem.status} />
        <div class="p-6 space-y-6">
          <!-- Case Title -->
          <div class="space-y-2">
            <label for="title" class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
              <FileText size="16" class="text-gray-500 dark:text-gray-400" />
              Case Title
              <span class="text-red-500 dark:text-red-400">*</span>
            </label>
            <input 
              id="title" 
              type="text" 
              name="title"
              bind:value={title}
              required
              class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:border-blue-500 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              placeholder="Enter case title"
            />
          </div>

          <!-- Description -->
          <div class="space-y-2">
            <label for="description" class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
              <FileText size="16" class="text-gray-500 dark:text-gray-400" />
              Description
            </label>
            <textarea 
              id="description" 
              name="description"
              bind:value={description}
              rows="4"
              class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:border-blue-500 transition-colors resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              placeholder="Describe the case details..."
            ></textarea>
          </div>

          <!-- Account Selection -->
          <div class="space-y-2">
            <label for="accountId" class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
              <Building size="16" class="text-gray-500 dark:text-gray-400" />
              Account
              <span class="text-red-500 dark:text-red-400">*</span>
            </label>
            <select 
              id="accountId" 
              name="accountId"
              bind:value={accountId}
              required
              class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:border-blue-500 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Select an account...</option>
              {#each data.accounts as acc}
                <option value={acc.id}>{acc.name}</option>
              {/each}
            </select>
          </div>

          <!-- Due Date and Assignment Row -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label for="dueDate" class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
                <Calendar size="16" class="text-gray-500 dark:text-gray-400" />
                Due Date
              </label>
              <input 
                id="dueDate" 
                type="date" 
                name="dueDate"
                bind:value={dueDate}
                class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:border-blue-500 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div class="space-y-2">
              <label for="assignedId" class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
                <User size="16" class="text-gray-500 dark:text-gray-400" />
                Assign To
                <span class="text-red-500 dark:text-red-400">*</span>
              </label>
              <select 
                id="assignedId" 
                name="assignedId"
                bind:value={assignedId}
                required
                class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:border-blue-500 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Select a user...</option>
                {#each data.users as u}
                  <option value={u.id}>{u.name}</option>
                {/each}
              </select>
            </div>
          </div>

          <!-- Priority -->
          <div class="space-y-2">
            <label for="priority" class="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white">
              <Flag size="16" class="text-gray-500 dark:text-gray-400" />
              Priority
            </label>
            <select
              id="priority"
              name="priority"
              bind:value={priority}
              class="w-full px-3 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:border-blue-500 transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="Urgent">Urgent</option>
              <option value="High">High</option>
              <option value="Normal">Normal</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <!-- Messages -->
          {#if errorMsg}
            <div class="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <AlertTriangle size="20" class="text-red-500 dark:text-red-400 mt-0.5 flex-shrink-0" />
              <div class="text-sm text-red-700 dark:text-red-300">{errorMsg}</div>
            </div>
          {/if}

          {#if successMsg}
            <div class="flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div class="w-5 h-5 rounded-full bg-green-500 dark:bg-green-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                <div class="w-2 h-2 bg-white rounded-full"></div>
              </div>
              <div class="text-sm text-green-700 dark:text-green-300">{successMsg}</div>
            </div>
          {/if}
        </div>

        <!-- Form Actions -->
        <div class="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row gap-3">
          <button 
            type="submit" 
            disabled={loading || data.caseItem.status === 'CLOSED'}
            class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-blue-600 dark:bg-blue-600 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save size="16" />
            {loading ? 'Saving...' : data.caseItem.status === 'CLOSED' ? 'Case is Closed' : 'Save Changes'}
          </button>
          
          {#if data.caseItem.status === 'CLOSED'}
            <button 
              type="button"
              onclick={handleReopenCase}
              class="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/30 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
            >
              <Unlock size="16" />
              Reopen Case
            </button>
          {:else}
            <button 
              type="button"
              onclick={handleCloseCase}
              class="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg hover:bg-amber-100 dark:hover:bg-amber-900/30 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
            >
              <Lock size="16" />
              Close Case
            </button>
          {/if}
        </div>
      </form>
    </div>

    <!-- Hidden Close Case Form -->
    <form id="close-case-form" method="POST" action="?/close" style="display: none;"></form>

    <!-- Hidden Reopen Case Form -->
    <form id="reopen-case-form" method="POST" action="?/reopen" style="display: none;"></form>

    <!-- Close Case Confirmation Modal -->
    {#if showCloseConfirmation}
      <div class="fixed inset-0 bg-black bg-opacity-50 dark:bg-black dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
          <div class="p-6">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/20 flex items-center justify-center">
                <Lock size="20" class="text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">Close Case</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Are you sure you want to close this case?</p>
              </div>
            </div>
            <p class="text-sm text-gray-700 dark:text-gray-300 mb-6">
              This action will mark the case as closed. You can still view the case details, but it will no longer be active.
            </p>
            <div class="flex gap-3">
              <button
                onclick={confirmCloseCase}
                class="flex-1 px-4 py-2 text-sm font-medium text-white bg-amber-600 dark:bg-amber-600 rounded-lg hover:bg-amber-700 dark:hover:bg-amber-700 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
              >
                Close Case
              </button>
              <button
                onclick={cancelCloseCase}
                class="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Reopen Case Confirmation Modal -->
    {#if showReopenConfirmation}
      <div class="fixed inset-0 bg-black bg-opacity-50 dark:bg-black dark:bg-opacity-70 flex items-center justify-center z-50 p-4">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full">
          <div class="p-6">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center">
                <Unlock size="20" class="text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">Reopen Case</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Are you sure you want to reopen this case?</p>
              </div>
            </div>
            <p class="text-sm text-gray-700 dark:text-gray-300 mb-6">
              This action will mark the case as active again and allow you to continue working on it.
            </p>
            <div class="flex gap-3">
              <button
                onclick={confirmReopenCase}
                class="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 dark:bg-green-600 rounded-lg hover:bg-green-700 dark:hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
              >
                Reopen Case
              </button>
              <button
                onclick={cancelReopenCase}
                class="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>
