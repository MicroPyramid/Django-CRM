<script>
  import { Plus, Calendar, User, Building2, Edit3, Trash2, Clock, AlertCircle, CheckCircle2, PlayCircle, Pause, XCircle } from '@lucide/svelte';
  
  export let data;

  /**
   * Format date for display
   * @param {string|Date|null|undefined} dateInput - Date to format
   * @returns {string} Formatted date string
   */
  function formatDate(dateInput) {
    if (!dateInput) return 'N/A';
    /** @type {Intl.DateTimeFormatOptions} */
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
    return date.toLocaleDateString(undefined, options);
  }

  /**
   * Get status icon component
   * @param {string} status - Task status
   * @returns {any} Icon component
   */
  function getStatusIcon(status) {
    switch (status) {
      case 'Completed': return CheckCircle2;
      case 'In Progress': return PlayCircle;
      case 'New': return AlertCircle;
      default: return AlertCircle;
    }
  }

  /**
   * Get priority icon component
   * @param {string} priority - Task priority
   * @returns {any} Icon component
   */
  function getPriorityIcon(priority) {
    switch (priority) {
      case 'High': return AlertCircle;
      case 'Medium': return Clock;
      case 'Low': return Clock;
      default: return Clock;
    }
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header Section -->
    <div class="mb-8">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Tasks</h1>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">Manage and track your team's tasks</p>
        </div>
        <a
          href="/app/tasks/new"
          class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white font-medium px-4 py-2 rounded-lg shadow-sm transition-colors duration-200"
        >
          <Plus size={20} />
          New Task
        </a>
      </div>
    </div>

    <!-- Tasks Table -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      {#if data.tasks.length === 0}
        <div class="text-center py-16">
          <div class="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
            <CheckCircle2 size={32} class="text-gray-400 dark:text-gray-500" />
          </div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No tasks yet</h3>
          <p class="text-gray-500 dark:text-gray-400 mb-6">Get started by creating your first task</p>
          <a
            href="/app/tasks/new"
            class="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white font-medium px-4 py-2 rounded-lg shadow-sm transition-colors duration-200"
          >
            <Plus size={20} />
            Create Task
          </a>
        </div>
      {:else}
        <!-- Desktop Table -->
        <div class="hidden md:block overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Task
                </th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Priority
                </th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Due Date
                </th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Owner
                </th>
                <th class="px-6 py-4 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Account
                </th>
                <th class="px-6 py-4 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {#each data.tasks as task (task.id)}
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-150">
                  <td class="px-6 py-4">
                    <div class="flex items-start">
                      <div class="min-w-0 flex-1">
                        <a 
                          href="/app/tasks/{task.id}" 
                          class="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {task.subject}
                        </a>
                        {#if task.description}
                          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 truncate max-w-xs">
                            {task.description}
                          </p>
                        {/if}
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      {#snippet statusIcon(/** @type {string} */ status)}
                        {@const StatusIcon = getStatusIcon(status)}
                        <StatusIcon
                          size={16}
                          class={
                            status === 'Completed' ? 'text-green-500 dark:text-green-400' :
                            status === 'In Progress' ? 'text-yellow-500 dark:text-yellow-400' :
                            status === 'New' ? 'text-blue-500 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'
                          }
                        />
                      {/snippet}
                      {@render statusIcon(task.status)}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                        {task.status === 'Completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' : ''}
                        {task.status === 'In Progress' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' : ''}
                        {task.status === 'New' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300' : ''}
                      ">
                        {task.status || 'N/A'}
                      </span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      {#snippet priorityIcon(/** @type {string} */ priority)}
                        {@const PriorityIcon = getPriorityIcon(priority)}
                        <PriorityIcon
                          size={16}
                          class={
                            priority === 'High' ? 'text-red-500 dark:text-red-400' :
                            priority === 'Medium' ? 'text-blue-500 dark:text-blue-400' :
                            priority === 'Low' ? 'text-gray-400 dark:text-gray-500' : 'text-gray-400 dark:text-gray-500'
                          }
                        />
                      {/snippet}
                      {@render priorityIcon(task.priority)}
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                        {task.priority === 'High' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' : ''}
                        {task.priority === 'Medium' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300' : ''}
                        {task.priority === 'Low' ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300' : ''}
                      ">
                        {task.priority || 'Medium'}
                      </span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2 text-sm text-gray-900 dark:text-gray-100">
                      <Calendar size={16} class="text-gray-400 dark:text-gray-500" />
                      {formatDate(task.dueDate)}
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <User size={16} class="text-gray-400 dark:text-gray-500" />
                      <span class="text-sm text-gray-900 dark:text-gray-100">{task.owner?.name || 'Unassigned'}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center gap-2">
                      <Building2 size={16} class="text-gray-400 dark:text-gray-500" />
                      <span class="text-sm text-gray-900 dark:text-gray-100">{task.account?.name || 'N/A'}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                      <a
                        href="/app/tasks/{task.id}/edit"
                        class="inline-flex items-center gap-1 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors p-1"
                        aria-label="Edit Task"
                      >
                        <Edit3 size={16} />
                      </a>
                      <button
                        class="inline-flex items-center gap-1 text-gray-400 dark:text-gray-500 p-1 cursor-not-allowed"
                        disabled
                        title="Delete (functionality to be implemented)"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Mobile Cards -->
        <div class="md:hidden">
          {#each data.tasks as task (task.id)}
            <div class="border-b border-gray-200 dark:border-gray-700 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div class="flex items-start justify-between mb-3">
                <div class="min-w-0 flex-1">
                  <a 
                    href="/app/tasks/{task.id}" 
                    class="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors block"
                  >
                    {task.subject}
                  </a>
                  {#if task.description}
                    <p class="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                      {task.description}
                    </p>
                  {/if}
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <a
                    href="/app/tasks/{task.id}/edit"
                    class="text-gray-400 dark:text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors p-1"
                  >
                    <Edit3 size={16} />
                  </a>
                  <button class="text-gray-300 dark:text-gray-600 p-1 cursor-not-allowed" disabled>
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              
              <div class="flex flex-wrap gap-2 mb-3">
                <div class="flex items-center gap-1">
                  {#snippet statusIconCard(/** @type {string} */ status)}
                    {@const StatusIcon = getStatusIcon(status)}
                    <StatusIcon
                      size={14}
                      class={
                        status === 'Completed' ? 'text-green-500 dark:text-green-400' :
                        status === 'In Progress' ? 'text-yellow-500 dark:text-yellow-400' :
                        status === 'New' ? 'text-blue-500 dark:text-blue-400' : 'text-gray-400 dark:text-gray-500'
                      }
                    />
                  {/snippet}
                  {@render statusIconCard(task.status)}
                  <span class="text-xs px-2 py-1 rounded-full font-medium
                    {task.status === 'Completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : ''}
                    {task.status === 'In Progress' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' : ''}
                    {task.status === 'New' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : ''}
                  ">
                    {task.status || 'N/A'}
                  </span>
                </div>
                
                <div class="flex items-center gap-1">
                  {#snippet priorityIconCard(/** @type {string} */ priority)}
                    {@const PriorityIcon = getPriorityIcon(priority)}
                    <PriorityIcon
                      size={14}
                      class={
                        priority === 'High' ? 'text-red-500 dark:text-red-400' :
                        priority === 'Medium' ? 'text-blue-500 dark:text-blue-400' :
                        priority === 'Low' ? 'text-gray-400 dark:text-gray-500' : 'text-gray-400 dark:text-gray-500'
                      }
                    />
                  {/snippet}
                  {@render priorityIconCard(task.priority)}
                  <span class="text-xs px-2 py-1 rounded-full font-medium
                    {task.priority === 'High' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' : ''}
                    {task.priority === 'Medium' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' : ''}
                    {task.priority === 'Low' ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' : ''}
                  ">
                    {task.priority || 'Medium'}
                  </span>
                </div>
              </div>
              
              <div class="grid grid-cols-1 gap-2 text-sm">
                <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <Calendar size={14} class="text-gray-400 dark:text-gray-500" />
                  <span>Due: {formatDate(task.dueDate)}</span>
                </div>
                <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                  <User size={14} class="text-gray-400 dark:text-gray-500" />
                  <span>{task.owner?.name || 'Unassigned'}</span>
                </div>
                {#if task.account?.name}
                  <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                    <Building2 size={14} class="text-gray-400 dark:text-gray-500" />
                    <span>{task.account.name}</span>
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  /* Optional: fade-in animation for modal (can be removed if no other modals use it) */
  /* Or keep if edit modal will use it */
  @keyframes fade-in {
    from { opacity: 0; transform: translateY(20px);}
    to { opacity: 1; transform: translateY(0);}
  }
  
</style>