<script>
  import { Calendar, ChevronLeft, ChevronRight, Clock, AlertCircle, CheckCircle2, Circle } from '@lucide/svelte';
  
  export let data;
  let today = new Date();
  let currentDate = new Date(today);
  let selectedDate = today.toISOString().slice(0, 10);

  // Group tasks by due date (YYYY-MM-DD)
  /** @type {Record<string, Array<{id: string, title: string, description: string, type: string, status: string, priority: string}>>} */
  let tasksByDate = {};
  if (data) {
    for (const t of data.tasks) {
      if (!t.dueDate) continue;
      const date = (typeof t.dueDate === 'string' ? t.dueDate : t.dueDate?.toISOString?.())?.slice(0, 10);
      if (!date) continue;
      if (!tasksByDate[date]) tasksByDate[date] = [];
      tasksByDate[date].push({
        id: t.id,
        title: t.subject || 'Untitled Task',
        description: t.description || '',
        type: 'CRM',
        status: t.status,
        priority: t.priority
      });
    }
  }

  // Calendar logic
  $: year = currentDate.getFullYear();
  $: month = currentDate.getMonth();
  $: monthStart = new Date(year, month, 1);
  $: monthEnd = new Date(year, month + 1, 0);
  $: startDay = monthStart.getDay();
  $: daysInMonth = monthEnd.getDate();
  $: calendar = (() => {
    let cal = [];
    for (let i = 0; i < startDay; i++) cal.push(null);
    for (let d = 1; d <= daysInMonth; d++) cal.push(new Date(Date.UTC(year, month, d)));
    while (cal.length % 7 !== 0) cal.push(null);
    return cal;
  })();

  $: monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'];
  
  /**
   * Format date to YYYY-MM-DD string
   * @param {Date} date - Date to format
   * @returns {string} Formatted date string
   */
  function formatDate(date) {
    return date.toISOString().slice(0, 10);
  }
  
  /**
   * Check if date is today
   * @param {Date|null} date - Date to check
   * @returns {boolean} True if date is today
   */
  function isToday(date) {
    return !!(date && formatDate(date) === today.toISOString().slice(0, 10));
  }
  
  /**
   * Check if date has tasks
   * @param {Date|null} date - Date to check
   * @returns {boolean} True if date has tasks
   */
  function hasTasks(date) {
    return !!(date && tasksByDate[formatDate(date)]?.length > 0);
  }
  
  /**
   * Select a day on the calendar
   * @param {Date|null} date - Date to select
   */
  function selectDay(date) {
    if (date) {
      selectedDate = formatDate(date);
    }
  }

  function previousMonth() {
    currentDate = new Date(year, month - 1, 1);
  }

  function nextMonth() {
    currentDate = new Date(year, month + 1, 1);
  }

  function goToToday() {
    currentDate = new Date(today);
    selectedDate = today.toISOString().slice(0, 10);
  }

  /**
   * Get priority icon component
   * @param {string} priority - Task priority
   * @returns {any} Icon component
   */
  function getPriorityIcon(priority) {
    switch (priority?.toLowerCase()) {
      case 'high': return AlertCircle;
      case 'medium': return Clock;
      default: return Circle;
    }
  }

  /**
   * Get status icon component
   * @param {string} status - Task status
   * @returns {any} Icon component
   */
  function getStatusIcon(status) {
    if (status?.toLowerCase() === 'completed') return CheckCircle2;
    return Circle;
  }

  // Calculate monthly stats
  $: monthlyTasks = Object.keys(tasksByDate).filter(dateStr => {
    const taskDate = new Date(dateStr);
    return taskDate.getFullYear() === year && taskDate.getMonth() === month;
  });

  $: totalMonthlyTasks = monthlyTasks.reduce((total, dateStr) => {
    return total + tasksByDate[dateStr].length;
  }, 0);

  $: selectedTasks = tasksByDate[selectedDate] || [];
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 p-4 sm:p-6 lg:p-8">
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="mb-8 text-center">
      <div class="flex items-center justify-center gap-3 mb-4">
        <Calendar class="w-8 h-8 text-blue-600 dark:text-blue-400" />
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Task Calendar</h1>
      </div>
      <p class="text-gray-600 dark:text-gray-300">Manage and track your tasks with ease</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Calendar Section -->
      <div class="lg:col-span-2">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 overflow-hidden">
          <!-- Calendar Header -->
          <div class="bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-700 dark:to-blue-800 px-6 py-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <button
                  onclick={previousMonth}
                  class="p-2 rounded-lg bg-white/10 hover:bg-white/20 dark:bg-white/10 dark:hover:bg-white/20 transition-colors"
                >
                  <ChevronLeft class="w-5 h-5 text-white" />
                </button>
                <h2 class="text-xl font-semibold text-white">
                  {monthNames[month]} {year}
                </h2>
                <button
                  onclick={nextMonth}
                  class="p-2 rounded-lg bg-white/10 hover:bg-white/20 dark:bg-white/10 dark:hover:bg-white/20 transition-colors"
                >
                  <ChevronRight class="w-5 h-5 text-white" />
                </button>
              </div>
              <button
                onclick={goToToday}
                class="px-4 py-2 bg-white/10 hover:bg-white/20 dark:bg-white/10 dark:hover:bg-white/20 text-white rounded-lg font-medium transition-colors"
              >
                Today
              </button>
            </div>
          </div>

          <!-- Days of Week -->
          <div class="grid grid-cols-7 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
            {#each ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as day}
              <div class="p-4 text-center text-sm font-medium text-gray-600 dark:text-gray-300 border-r border-gray-200 dark:border-gray-600 last:border-r-0">
                {day}
              </div>
            {/each}
          </div>

          <!-- Calendar Grid -->
          <div class="grid grid-cols-7">
            {#each calendar as date, i}
              {#if date}
                <button
                  onclick={() => selectDay(date)}
                  class="relative h-16 sm:h-20 p-2 border-r border-b border-gray-200 dark:border-gray-600 last:border-r-0 
                         hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors group
                         {formatDate(date) === selectedDate ? 'bg-blue-600 dark:bg-blue-700 text-white' : ''}
                         {isToday(date) && formatDate(date) !== selectedDate ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300' : ''}
                         {!isToday(date) && formatDate(date) !== selectedDate ? 'text-gray-900 dark:text-gray-100' : ''}"
                >
                  <div class="text-sm font-medium">
                    {date.getDate()}
                  </div>
                  {#if hasTasks(date)}
                    <div class="absolute bottom-1 right-1 w-2 h-2 rounded-full 
                               {formatDate(date) === selectedDate ? 'bg-white' : 'bg-blue-500 dark:bg-blue-400'}">
                    </div>
                    <div class="absolute bottom-1 left-1 text-xs font-medium
                               {formatDate(date) === selectedDate ? 'text-white' : 'text-blue-600 dark:text-blue-400'}">
                      {tasksByDate[formatDate(date)].length}
                    </div>
                  {/if}
                </button>
              {:else}
                <div class="h-16 sm:h-20 border-r border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800"></div>
              {/if}
            {/each}
          </div>
        </div>
      </div>

      <!-- Tasks Section -->
      <div class="lg:col-span-1">
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 h-fit">
          <div class="p-6 border-b border-gray-200 dark:border-gray-600">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Tasks for {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </h3>
            <div class="text-sm text-gray-600 dark:text-gray-300">
              {selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''}
            </div>
          </div>

          <div class="p-6">
            {#if selectedTasks.length > 0}
              <div class="space-y-4">
                {#each selectedTasks as task}
                  <a 
                    href="/tasks/{task.id}"
                    class="block p-4 bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-xl transition-colors border border-gray-200 dark:border-gray-600"
                  >
                    <div class="flex items-start justify-between mb-2">
                      <h4 class="font-medium text-gray-900 dark:text-white overflow-hidden text-ellipsis" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{task.title}</h4>
                      {#snippet statusIcon(/** @type {string} */ status)}
                        {@const StatusIcon = getStatusIcon(status)}
                        <StatusIcon 
                          class="w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0 ml-2"
                        />
                      {/snippet}
                      {@render statusIcon(task.status)}
                    </div>
                    
                    {#if task.description}
                      <p class="text-sm text-gray-600 dark:text-gray-300 mb-3 overflow-hidden text-ellipsis" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{task.description}</p>
                    {/if}

                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span class="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-xs font-medium rounded-lg">
                          {task.type}
                        </span>
                        <span class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-lg
                               {task.priority === 'Urgent' ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300' :
                                 task.priority === 'High' ? 'bg-orange-100 dark:bg-orange-900 text-orange-700 dark:text-orange-300' :
                                 task.priority === 'Normal' ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300' :
                                 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300'}">
                          {#snippet priorityIcon(/** @type {string} */ priority)}
                            {@const PriorityIcon = getPriorityIcon(priority)}
                            <PriorityIcon class="w-3 h-3" />
                          {/snippet}
                          {@render priorityIcon(task.priority)}
                          {task.priority}
                        </span>
                      </div>
                      <span class="text-xs text-gray-500 dark:text-gray-400 font-medium">{task.status}</span>
                    </div>
                  </a>
                {/each}
              </div>
            {:else}
              <div class="text-center py-12">
                <Calendar class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p class="text-gray-500 dark:text-gray-400 text-sm">No tasks scheduled for this date</p>
                <p class="text-gray-400 dark:text-gray-500 text-xs mt-1">Select a different date to view tasks</p>
              </div>
            {/if}
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="mt-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 p-6">
          <h4 class="font-semibold text-gray-900 dark:text-white mb-4">This Month</h4>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600 dark:text-gray-300">Total Tasks</span>
              <span class="font-medium text-gray-900 dark:text-white">
                {totalMonthlyTasks}
              </span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600 dark:text-gray-300">Days with Tasks</span>
              <span class="font-medium text-gray-900 dark:text-white">{monthlyTasks.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
