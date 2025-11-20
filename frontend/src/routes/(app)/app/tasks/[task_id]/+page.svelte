<script>
  import { goto } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { ArrowLeft, Edit3, Calendar, User, Building2, MessageSquare, Send } from '@lucide/svelte';
  
  export let data;
  /** @type {import('./$types').ActionData} */
  export let form;

  // Reactive assignment for task to allow modifications in edit mode
  /** @type {any} */
  $: task = data.task;
  // Comments are now part of the task object from the server

  let newComment = '';

  // The addComment function is no longer needed here,
  // form submission with `enhance` will handle it.

  // Helper to format date for display, if not already a string
  /**
   * @param {string | Date | null} dateString - The date to format
   * @returns {string} Formatted date string
   */
  function formatDate(dateString) {
    if (!dateString) return 'N/A';
    // If it's already YYYY-MM-DD, it's fine. Otherwise, format it.
    try {
      return new Date(dateString).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) {
      return typeof dateString === 'string' ? dateString : 'N/A'; // Fallback to original string if not a valid date
    }
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <div class="max-w-4xl mx-auto p-3 sm:p-4 lg:p-6">
    <!-- Header -->
    <div class="mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button 
            onclick={() => goto('/app/tasks/list')} 
            class="flex items-center justify-center w-8 h-8 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            aria-label="Back to tasks"
          >
            <ArrowLeft class="w-4 h-4" />
          </button>
          <div>
            <h1 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">Task Details</h1>
            <p class="text-sm text-gray-600 dark:text-gray-400">View and manage task information</p>
          </div>
        </div>
        <button 
          class="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 dark:bg-blue-500 text-white font-medium shadow-sm hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors text-sm" 
          onclick={() => task && goto(`/app/tasks/${task.id}/edit`)}
        >
          <Edit3 class="w-4 h-4" />
          <span class="hidden sm:inline">Edit</span>
        </button>
      </div>
    </div>

    <!-- Task Detail Card -->
    {#if task}
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden mb-6">
        <!-- Task Header -->
        <div class="p-4 border-b border-gray-100 dark:border-gray-700">
          <div class="flex flex-wrap items-center gap-2 mb-3">
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium
              {task.status === 'Completed' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800' : ''}
              {task.status === 'In Progress' ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800' : ''}
              {task.status === 'New' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : ''}">
              {task.status}
            </span>
            <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium
              {task.priority === 'High' ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800' : ''}
              {task.priority === 'Medium' ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : ''}
              {task.priority === 'Low' ? 'bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600' : ''}">
              {task.priority}
            </span>
            <div class="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400 ml-auto">
              <Calendar class="w-3.5 h-3.5" />
              <span>Due {formatDate(task.dueDate)}</span>
            </div>
          </div>
          
          <h2 class="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white mb-2">{task.title}</h2>
          
          {#if task.description}
            <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{task.description}</p>
          {:else}
            <p class="text-sm text-gray-500 dark:text-gray-400 italic">No description provided</p>
          {/if}
        </div>

        <!-- Task Meta Information -->
        <div class="p-4 bg-gray-50 dark:bg-gray-700/50">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Owner -->
            <div class="space-y-1.5">
              <div class="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400">
                <User class="w-3.5 h-3.5" />
                <span>Task Owner</span>
              </div>
              <div class="flex items-center gap-2.5">
                {#if task.owner?.profilePhoto}
                  <img 
                    src={task.owner.profilePhoto} 
                    alt={task.owner.name} 
                    class="w-8 h-8 rounded-full border border-white dark:border-gray-600 shadow-sm" 
                    referrerpolicy="no-referrer" 
                  />
                {:else}
                  <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 border border-white dark:border-gray-600 shadow-sm flex items-center justify-center">
                    <span class="text-xs font-medium text-blue-700 dark:text-blue-400">
                      {task.owner?.name?.charAt(0) || 'U'}
                    </span>
                  </div>
                {/if}
                <div>
                  <div class="text-sm font-medium text-gray-900 dark:text-white">{task.owner?.name || 'Unassigned'}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Owner</div>
                </div>
              </div>
            </div>

            <!-- Account -->
            <div class="space-y-1.5">
              <div class="flex items-center gap-1.5 text-xs font-medium text-gray-600 dark:text-gray-400">
                <Building2 class="w-3.5 h-3.5" />
                <span>Related Account</span>
              </div>
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-600 flex items-center justify-center">
                  <Building2 class="w-4 h-4 text-gray-500 dark:text-gray-400" />
                </div>
                <div>
                  <div class="text-sm font-medium text-gray-900 dark:text-white">{task.account?.name || 'No account assigned'}</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">Account</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Comments Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="p-4 border-b border-gray-100 dark:border-gray-700">
          <div class="flex items-center gap-2">
            <MessageSquare class="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <h2 class="text-base font-semibold text-gray-900 dark:text-white">Comments</h2>
            {#if task.comments && task.comments.length > 0}
              <span class="text-xs text-gray-500 dark:text-gray-400">({task.comments.length})</span>
            {/if}
          </div>
        </div>

        <div class="p-4">
          {#if form?.message}
            <div class="mb-4 p-3 rounded-lg {form.success === false ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800' : 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800'}">
              <p class="text-xs font-medium">{form.message}</p>
            </div>
          {/if}
          
          {#if form?.fieldError && Array.isArray(form.fieldError) && form.fieldError.includes('commentBody')}
            {@const formData = /** @type {any} */ (form)}
            {#if 'commentBody' in formData}
              {@const _ = newComment = /** @type {string} */ (formData.commentBody || '')}
            {/if}
          {/if}

          <!-- Comments List -->
          <div class="space-y-3 mb-6">
            {#if task.comments && task.comments.length > 0}
              {#each task.comments as c (c.id || c.createdAt)}
                <div class="flex gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border border-gray-100 dark:border-gray-600">
                  {#if c.author.profilePhoto}
                    <img 
                      src={c.author.profilePhoto} 
                      alt={c.author.name} 
                      class="w-8 h-8 rounded-full border border-gray-200 dark:border-gray-600 flex-shrink-0" 
                      referrerpolicy="no-referrer" 
                    />
                  {:else}
                    <div class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 border border-gray-200 dark:border-gray-600 flex items-center justify-center flex-shrink-0">
                      <span class="text-xs font-medium text-blue-700 dark:text-blue-400">
                        {c.author?.name?.charAt(0) || 'U'}
                      </span>
                    </div>
                  {/if}
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-sm font-medium text-gray-900 dark:text-white">{c.author.name}</span>
                      <span class="text-xs text-gray-500 dark:text-gray-400">{new Date(c.createdAt).toLocaleString()}</span>
                    </div>
                    <div class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{c.body}</div>
                  </div>
                </div>
              {/each}
            {:else}
              <div class="text-center py-6">
                <MessageSquare class="w-8 h-8 text-gray-300 dark:text-gray-600 mx-auto mb-2" />
                <p class="text-sm text-gray-500 dark:text-gray-400 font-medium">No comments yet</p>
                <p class="text-xs text-gray-400 dark:text-gray-500">Be the first to add a comment</p>
              </div>
            {/if}
          </div>

          <!-- Add Comment Form -->
          <form method="POST" action="?/addComment" use:enhance class="space-y-3">
            <div>
              <label for="commentBody" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Add a comment
              </label>
              <textarea
                id="commentBody"
                name="commentBody"
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent resize-none transition-colors"
                rows="2"
                placeholder="Share your thoughts or updates..."
                bind:value={newComment}
                required
              ></textarea>
            </div>
            <div class="flex justify-end">
              <button 
                type="submit" 
                class="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 text-white font-medium shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm" 
                disabled={!newComment.trim()}
              >
                <Send class="w-3.5 h-3.5" />
                Add Comment
              </button>
            </div>
          </form>
        </div>
      </div>
    {/if}
  </div>
</div>