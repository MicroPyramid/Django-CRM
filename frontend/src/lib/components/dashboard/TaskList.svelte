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

  /**
   * Get priority config
   * @param {string} priority
   */
  function getPriorityConfig(priority) {
    const configs = /** @type {Record<string, { bg: string, text: string, border: string }>} */ ({
      High: {
        bg: 'bg-rose-500/10 dark:bg-rose-500/15',
        text: 'text-rose-600 dark:text-rose-400',
        border: 'border-rose-500/30 dark:border-rose-400/20'
      },
      Medium: {
        bg: 'bg-amber-500/10 dark:bg-amber-500/15',
        text: 'text-amber-600 dark:text-amber-400',
        border: 'border-amber-500/30 dark:border-amber-400/20'
      },
      Low: {
        bg: 'bg-slate-500/10 dark:bg-slate-500/15',
        text: 'text-slate-600 dark:text-slate-400',
        border: 'border-slate-500/30 dark:border-slate-400/20'
      }
    });
    return configs[priority] || configs['Medium'];
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

<div class="flex h-full flex-col overflow-hidden rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm dark:bg-card/50">
  <!-- Header -->
  <div class="flex items-center justify-between border-b border-border/50 px-5 py-4">
    <div class="flex items-center gap-3">
      <div class="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/10 to-teal-500/10 dark:from-cyan-500/20 dark:to-teal-500/20">
        <ListTodo class="size-4 text-cyan-600 dark:text-cyan-400" />
      </div>
      <h3 class="text-foreground text-sm font-semibold tracking-tight">My Tasks</h3>
    </div>
    <Button variant="ghost" size="sm" href="/tasks" class="gap-1 text-xs font-medium">
      View all
      <ChevronRight class="size-3.5" />
    </Button>
  </div>

  <!-- Filter tabs -->
  <div class="flex gap-1 border-b border-border/50 px-4 py-2">
    {#each filterButtons as btn}
      <Button
        variant={filter === btn.id ? 'secondary' : 'ghost'}
        size="sm"
        class="h-7 px-3 text-xs font-medium transition-all duration-200
          {filter === btn.id ? 'bg-secondary shadow-sm' : 'hover:bg-secondary/50'}"
        onclick={() => (filter = btn.id)}
      >
        {btn.label}
        {#if btn.id === 'overdue' && overdueTasks.length > 0}
          <Badge class="ml-1.5 h-4 min-w-4 bg-rose-500 px-1 text-[10px] font-bold text-white">
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
        <div class="mb-3 flex size-12 items-center justify-center rounded-xl bg-muted/50">
          <ListTodo class="text-muted-foreground/50 size-6" />
        </div>
        <p class="text-muted-foreground text-sm font-medium">No tasks found</p>
        <p class="text-muted-foreground/70 text-xs">All caught up!</p>
      </div>
    {:else}
      <div class="divide-y divide-border/30">
        {#each filteredTasks() as task (task.id)}
          {@const config = getPriorityConfig(task.priority)}
          <a
            href="/tasks?view={task.id}"
            class="group flex items-center gap-3 px-5 py-3 transition-all duration-200 hover:bg-muted/30"
          >
            <!-- Status icon -->
            <button class="text-muted-foreground flex-shrink-0 transition-colors hover:text-foreground">
              {#if task.status === 'Completed'}
                <CheckCircle2 class="size-5 text-emerald-500 dark:text-emerald-400" />
              {:else}
                <Circle class="size-5" />
              {/if}
            </button>

            <!-- Task details -->
            <div class="min-w-0 flex-1">
              <p
                class="text-foreground truncate text-sm font-medium transition-colors group-hover:text-primary
                  {task.status === 'Completed' ? 'text-muted-foreground line-through' : ''}"
              >
                {task.subject}
              </p>
              <p class="text-muted-foreground mt-0.5 truncate text-xs">{task.status}</p>
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
                  {isOverdue(task.dueDate) ? 'text-rose-500 dark:text-rose-400' : 'text-muted-foreground'}"
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
