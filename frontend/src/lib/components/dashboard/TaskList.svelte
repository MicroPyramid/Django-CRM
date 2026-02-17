<script>
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Circle, CheckCircle2, ChevronRight, ListTodo } from '@lucide/svelte';

  /**
   * @typedef {Object} Task
   * @property {string} id
   * @property {string} subject
   * @property {string} status
   * @property {string} priority
   * @property {string} [dueDate]
   * @property {boolean} [isOverdue]
   * @property {boolean} [isDueToday]
   */

  /**
   * @typedef {Object} Props
   * @property {Task[]} [tasks] - All tasks
   */

  /** @type {Props} */
  let { tasks = [] } = $props();

  /** @type {'all' | 'overdue' | 'today' | 'week'} */
  let filter = $state('all');

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const weekEnd = new Date(today);
  weekEnd.setDate(weekEnd.getDate() + 7);

  /**
   * Check if a date is today
   * @param {string} dateStr
   */
  function isToday(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    date.setHours(0, 0, 0, 0);
    return date.getTime() === today.getTime();
  }

  /**
   * Check if a date is overdue
   * @param {string} dateStr
   */
  function isOverdue(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    date.setHours(0, 0, 0, 0);
    return date.getTime() < today.getTime();
  }

  /**
   * Check if a date is within this week
   * @param {string} dateStr
   */
  function isThisWeek(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    date.setHours(0, 0, 0, 0);
    return date.getTime() >= today.getTime() && date.getTime() <= weekEnd.getTime();
  }

  const filteredTasks = $derived(() => {
    return tasks.filter((task) => {
      if (task.status === 'Completed') return false;
      if (filter === 'overdue') return isOverdue(task.dueDate);
      if (filter === 'today') return isToday(task.dueDate);
      if (filter === 'week') return isThisWeek(task.dueDate);
      return true;
    });
  });

  const overdueTasks = $derived(
    tasks.filter((t) => t.status !== 'Completed' && isOverdue(t.dueDate))
  );

  // Using design system priority tokens
  const priorityConfig =
    /** @type {Record<string, { bg: string, text: string, border: string }>} */ ({
      Urgent: {
        bg: 'bg-[var(--priority-urgent-bg)] dark:bg-[var(--priority-urgent)]/15',
        text: 'text-[var(--priority-urgent)]',
        border: 'border-[var(--priority-urgent)]/30'
      },
      High: {
        bg: 'bg-[var(--priority-high-bg)] dark:bg-[var(--priority-high)]/15',
        text: 'text-[var(--priority-high)]',
        border: 'border-[var(--priority-high)]/30'
      },
      Medium: {
        bg: 'bg-[var(--priority-medium-bg)] dark:bg-[var(--priority-medium)]/15',
        text: 'text-[var(--priority-medium)]',
        border: 'border-[var(--priority-medium)]/30'
      },
      Low: {
        bg: 'bg-[var(--priority-low-bg)] dark:bg-[var(--priority-low)]/15',
        text: 'text-[var(--priority-low)]',
        border: 'border-[var(--priority-low)]/30'
      }
    });

  /**
   * Get priority config
   * @param {string} priority
   */
  function getPriorityConfig(priority) {
    return priorityConfig[priority] || priorityConfig['Medium'];
  }

  /**
   * Format date for display
   * @param {string} dateStr
   */
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isToday(dateStr)) return 'Today';
    if (isOverdue(dateStr)) {
      const days = Math.floor((today.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
      return days === 1 ? 'Yesterday' : `${days}d ago`;
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  /** @type {{ id: 'all' | 'overdue' | 'today' | 'week', label: string }[]} */
  const filterButtons = [
    { id: 'all', label: 'All' },
    { id: 'overdue', label: 'Overdue' },
    { id: 'today', label: 'Today' },
    { id: 'week', label: 'Week' }
  ];
</script>

<div
  class="flex h-full flex-col overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-raised)] dark:bg-[var(--surface-raised)]/80 dark:backdrop-blur-sm"
>
  <!-- Header - Orange accent -->
  <div
    class="flex items-center justify-between border-b border-[var(--border-default)]/50 px-5 py-4"
  >
    <div class="flex items-center gap-3">
      <div
        class="flex size-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-primary-light)] dark:bg-[var(--color-primary-default)]/15"
      >
        <ListTodo class="size-4 text-[var(--color-primary-default)]" />
      </div>
      <h3 class="text-sm font-semibold tracking-tight text-[var(--text-primary)]">My Tasks</h3>
    </div>
    <Button variant="ghost" size="sm" href="/tasks" class="gap-1 text-xs font-medium">
      View all
      <ChevronRight class="size-3.5" />
    </Button>
  </div>

  <!-- Filter tabs -->
  <div class="flex gap-1 border-b border-[var(--border-default)]/50 px-4 py-2">
    {#each filterButtons as btn}
      <Button
        variant={filter === btn.id ? 'secondary' : 'ghost'}
        size="sm"
        class="h-7 px-3 text-xs font-medium transition-all duration-200
          {filter === btn.id
          ? 'bg-[var(--surface-sunken)] shadow-sm'
          : 'hover:bg-[var(--surface-sunken)]/50'}"
        onclick={() => (filter = btn.id)}
      >
        {btn.label}
        {#if btn.id === 'overdue' && overdueTasks.length > 0}
          <Badge
            class="ml-1.5 h-4 min-w-4 bg-[var(--task-overdue)] px-1 text-[10px] font-bold text-white"
          >
            {overdueTasks.length}
          </Badge>
        {/if}
      </Button>
    {/each}
  </div>

  <!-- Task list -->
  <div class="flex-1 overflow-auto">
    {#if filteredTasks().length === 0}
      <div class="flex h-full flex-col items-center justify-center py-10 text-center">
        <div
          class="mb-3 flex size-12 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--surface-sunken)]"
        >
          <ListTodo class="size-6 text-[var(--text-tertiary)]" />
        </div>
        <p class="text-sm font-medium text-[var(--text-secondary)]">No tasks found</p>
        <p class="text-xs text-[var(--text-tertiary)]">All caught up!</p>
      </div>
    {:else}
      <div class="divide-y divide-[var(--border-default)]/30">
        {#each filteredTasks() as task (task.id)}
          {@const config = getPriorityConfig(task.priority)}
          <a
            href="/tasks?view={task.id}"
            class="group flex items-center gap-3 px-5 py-3 transition-all duration-200 hover:bg-[var(--color-primary-light)] dark:hover:bg-[var(--color-primary-default)]/5"
          >
            <!-- Status icon -->
            <button
              class="flex-shrink-0 text-[var(--text-tertiary)] transition-colors hover:text-[var(--text-primary)]"
            >
              {#if task.status === 'Completed'}
                <CheckCircle2 class="size-5 text-[var(--task-completed)]" />
              {:else}
                <Circle class="size-5" />
              {/if}
            </button>

            <!-- Task details -->
            <div class="min-w-0 flex-1">
              <p
                class="truncate text-sm font-medium text-[var(--text-primary)] transition-colors group-hover:text-[var(--color-primary-default)]
                  {task.status === 'Completed' ? 'text-[var(--text-tertiary)] line-through' : ''}"
              >
                {task.subject}
              </p>
              <p class="mt-0.5 truncate text-xs text-[var(--text-secondary)]">{task.status}</p>
            </div>

            <!-- Priority badge -->
            <Badge
              variant="outline"
              class="flex-shrink-0 border text-[10px] font-semibold {config.bg} {config.text} {config.border}"
            >
              {task.priority}
            </Badge>

            <!-- Due date -->
            {#if task.dueDate}
              <span
                class="flex-shrink-0 text-xs font-medium tabular-nums
                  {isOverdue(task.dueDate)
                  ? 'text-[var(--task-overdue)]'
                  : 'text-[var(--text-secondary)]'}"
              >
                {formatDate(task.dueDate)}
              </span>
            {/if}
          </a>
        {/each}
      </div>
    {/if}
  </div>
</div>
