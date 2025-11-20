<script lang="ts">
  import { Briefcase, Edit3, Trash2, Clock, User, Building, Calendar, AlertCircle, MessageCircle, Send, CheckCircle, RotateCcw, XCircle } from '@lucide/svelte';
  
  export let data;
  let comment = '';
  let errorMsg = '';
  
  function getPriorityColor(priority: string) {
    switch (priority) {
      case 'Urgent': return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800';
      case 'High': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800';
      case 'Normal': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800';
      case 'Low': return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800';
      default: return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700';
    }
  }
  
  function getStatusColor(status: string) {
    switch (status) {
      case 'OPEN': return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
      case 'IN_PROGRESS': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 border-orange-200 dark:border-orange-800';
      case 'CLOSED': return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700';
      default: return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700';
    }
  }
  
  function getStatusIcon(status: string) {
    switch (status) {
      case 'OPEN': return AlertCircle;
      case 'IN_PROGRESS': return RotateCcw;
      case 'CLOSED': return CheckCircle;
      default: return AlertCircle;
    }
  }
  
  // Reactive declarations for components
  $: StatusIcon = getStatusIcon(data.caseItem.status);
</script>

<section class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <div class="container mx-auto p-4 max-w-5xl">
    <!-- Header -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <div class="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
        <div class="flex items-start gap-4">
          <div class="p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
            <Briefcase class="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">{data.caseItem.subject}</h1>
            <p class="text-gray-600 dark:text-gray-400 text-sm">Case #{data.caseItem.caseNumber}</p>
          </div>
        </div>
        <div class="flex gap-3">
          <a href="/app/cases/{data.caseItem.id}/edit" 
             class="inline-flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors">
            <Edit3 class="w-4 h-4" />
            Edit
          </a>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Case Details -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Case Information</h2>
          
          {#if data.caseItem.description}
            <div class="mb-6">
              <h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</h3>
              <p class="text-gray-600 dark:text-gray-400 leading-relaxed">{data.caseItem.description}</p>
            </div>
          {/if}

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-4">
              <div class="flex items-center gap-3">
                <Building class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                <div>
                  <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Account</p>
                  <p class="text-gray-900 dark:text-white">{data.caseItem.account?.name || 'Not assigned'}</p>
                </div>
              </div>
              
              <div class="flex items-center gap-3">
                <User class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                <div>
                  <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Assigned to</p>
                  <p class="text-gray-900 dark:text-white">{data.caseItem.owner?.name || 'Unassigned'}</p>
                </div>
              </div>
            </div>
            
            <div class="space-y-4">
              {#if data.caseItem.dueDate}
                <div class="flex items-center gap-3">
                  <Calendar class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <div>
                    <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Due Date</p>
                    <p class="text-gray-900 dark:text-white">{(new Date(data.caseItem.dueDate)).toLocaleDateString()}</p>
                  </div>
                </div>
              {/if}
              
              <div class="flex items-center gap-3">
                <Clock class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                <div>
                  <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Created</p>
                  <p class="text-gray-900 dark:text-white">{(new Date(data.caseItem.createdAt)).toLocaleDateString()}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Comments Section -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center gap-2 mb-6">
            <MessageCircle class="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Comments</h2>
            <span class="text-sm text-gray-500 dark:text-gray-400">({data.caseItem.comments?.length || 0})</span>
          </div>
          
          <!-- Comments List -->
          <div class="space-y-4 mb-6">
            {#if data.caseItem.comments && data.caseItem.comments.length}
              {#each data.caseItem.comments as c}
                <div class="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 border border-gray-100 dark:border-gray-600">
                  <div class="flex items-start gap-3">
                    <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                      <span class="text-blue-700 dark:text-blue-300 font-semibold text-sm">
                        {c.author?.name?.[0]?.toUpperCase() || 'U'}
                      </span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <p class="font-medium text-gray-900 dark:text-white">{c.author?.name || 'Unknown User'}</p>
                        <span class="text-gray-400 dark:text-gray-500">•</span>
                        <p class="text-sm text-gray-500 dark:text-gray-400">{(new Date(c.createdAt)).toLocaleDateString()}</p>
                      </div>
                      <p class="text-gray-700 dark:text-gray-300 leading-relaxed">{c.body}</p>
                    </div>
                  </div>
                </div>
              {/each}
            {:else}
              <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                <MessageCircle class="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                <p>No comments yet. Be the first to add one!</p>
              </div>
            {/if}
          </div>
          
          <!-- Add Comment Form -->
          <form method="POST" action="?/comment" class="border-t border-gray-200 dark:border-gray-600 pt-4">
            <div class="flex gap-3">
              <input 
                type="text" 
                name="body"
                bind:value={comment}
                placeholder="Write a comment..." 
                required
                class="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 transition-colors"
              />
              <button 
                type="submit"
                class="px-6 py-3 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors flex items-center gap-2">
                <Send class="w-4 h-4" />
                Post
              </button>
            </div>
            {#if errorMsg}
              <p class="text-red-600 dark:text-red-400 text-sm mt-2">{errorMsg}</p>
            {/if}
          </form>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Status & Priority -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Status & Priority</h3>
          
          <div class="space-y-4">
            <div>
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</p>
              <div class="flex items-center gap-2">
                <StatusIcon class="w-4 h-4" />
                <span class="px-3 py-1 rounded-full text-sm font-medium border {getStatusColor(data.caseItem.status)}">
                  {data.caseItem.status.replace('_', ' ')}
                </span>
              </div>
            </div>
            
            <div>
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Priority</p>
              <span class="px-3 py-1 rounded-full text-sm font-medium border {getPriorityColor(data.caseItem.priority)}">
                {data.caseItem.priority}
              </span>
            </div>
          </div>
        </div>

        <!-- Activity Timeline -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Activity Timeline</h3>
          
          <div class="space-y-4">
            <div class="flex items-start gap-3">
              <div class="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full mt-2 flex-shrink-0"></div>
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-900 dark:text-white">Case Created</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{(new Date(data.caseItem.createdAt)).toLocaleDateString()}</p>
              </div>
            </div>
            
            {#if data.caseItem.updatedAt && data.caseItem.updatedAt !== data.caseItem.createdAt}
              <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-yellow-500 dark:bg-yellow-400 rounded-full mt-2 flex-shrink-0"></div>
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900 dark:text-white">Last Updated</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{(new Date(data.caseItem.updatedAt)).toLocaleDateString()}</p>
                </div>
              </div>
            {/if}
            
            {#if data.caseItem.closedAt}
              <div class="flex items-start gap-3">
                <div class="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full mt-2 flex-shrink-0"></div>
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900 dark:text-white">Case Closed</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{(new Date(data.caseItem.closedAt)).toLocaleDateString()}</p>
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
