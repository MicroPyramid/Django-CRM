<script>
  import { AlertCircle, Calendar, Phone, Flame, Zap } from '@lucide/svelte';

  /**
   * @typedef {Object} Props
   * @property {number} [overdueCount] - Number of overdue tasks
   * @property {number} [todayCount] - Number of tasks due today
   * @property {number} [followupsCount] - Number of follow-ups scheduled today
   * @property {number} [hotLeadsCount] - Number of hot leads
   */

  /** @type {Props} */
  let { overdueCount = 0, todayCount = 0, followupsCount = 0, hotLeadsCount = 0 } = $props();

  const items = $derived([
    {
      href: '/tasks?filter=overdue',
      icon: AlertCircle,
      iconClass: 'text-[var(--task-overdue)]',
      bgClass: 'bg-[var(--task-overdue-bg)] dark:bg-[var(--task-overdue)]/15',
      count: overdueCount,
      label: 'Overdue',
      show: overdueCount > 0
    },
    {
      href: '/tasks?filter=today',
      icon: Calendar,
      iconClass: 'text-[var(--task-due-today)]',
      bgClass: 'bg-[var(--task-due-today-bg)] dark:bg-[var(--task-due-today)]/15',
      count: todayCount,
      label: 'Due Today',
      show: true
    },
    {
      href: '/leads?filter=followup_today',
      icon: Phone,
      iconClass: 'text-[var(--activity-call)]',
      bgClass: 'bg-[var(--color-success-light)] dark:bg-[var(--activity-call)]/15',
      count: followupsCount,
      label: 'Follow-ups',
      show: true
    },
    {
      href: '/leads?rating=HOT',
      icon: Flame,
      iconClass: 'text-[var(--lead-hot)]',
      bgClass: 'bg-[var(--lead-hot-bg)] dark:bg-[var(--lead-hot)]/15',
      count: hotLeadsCount,
      label: 'Hot Leads',
      show: hotLeadsCount > 0
    }
  ]);

  const visibleItems = $derived(items.filter((item) => item.show));
  const hasUrgentItems = $derived(overdueCount > 0);
</script>

{#if visibleItems.length > 0}
  <div
    class="relative overflow-hidden rounded-[var(--radius-lg)] border px-4 py-3 backdrop-blur-sm transition-all duration-300 sm:px-6
      {hasUrgentItems
        ? 'border-[var(--task-overdue)]/30 bg-[var(--task-overdue-bg)] dark:border-[var(--task-overdue)]/20 dark:bg-[var(--task-overdue)]/10'
        : 'border-[var(--border-default)] bg-[var(--surface-raised)]/50 dark:bg-[var(--surface-raised)]/30'}"
  >
    <!-- Subtle gradient overlay -->
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent dark:via-white/[0.02]"></div>

    <div class="relative flex items-center gap-3 sm:gap-5">
      <!-- Label with icon - Orange accent -->
      <div class="hidden items-center gap-2 sm:flex">
        <div class="flex size-7 items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-primary-light)] dark:bg-[var(--color-primary-default)]/15">
          <Zap class="size-4 text-[var(--color-primary-default)]" />
        </div>
        <span class="text-[var(--text-secondary)] text-xs font-semibold uppercase tracking-wider">
          Today's Focus
        </span>
      </div>

      <!-- Divider -->
      <div class="hidden h-6 w-px bg-[var(--border-default)]/50 sm:block"></div>

      <!-- Items -->
      <div class="flex flex-1 items-center gap-1 overflow-x-auto sm:gap-2">
        {#each visibleItems as item}
          <a
            href={item.href}
            class="group flex items-center gap-2 rounded-[var(--radius-md)] px-3 py-2 transition-all duration-200 hover:bg-white/50 dark:hover:bg-white/5 sm:gap-2.5 sm:px-4"
          >
            <div class="flex size-8 items-center justify-center rounded-[var(--radius-md)] transition-transform duration-200 group-hover:scale-110 {item.bgClass}">
              <item.icon class="size-4 {item.iconClass}" />
            </div>
            <div class="flex items-center gap-2">
              <span class="text-[var(--text-primary)] text-base font-bold tabular-nums">{item.count}</span>
              <span class="text-[var(--text-secondary)] hidden text-xs font-medium sm:inline">{item.label}</span>
            </div>
          </a>
        {/each}
      </div>
    </div>
  </div>
{/if}
