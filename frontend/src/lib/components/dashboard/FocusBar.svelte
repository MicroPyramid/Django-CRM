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
      iconClass: 'text-rose-500 dark:text-rose-400',
      bgClass: 'bg-rose-500/10 dark:bg-rose-500/15',
      count: overdueCount,
      label: 'Overdue',
      show: overdueCount > 0
    },
    {
      href: '/tasks?filter=today',
      icon: Calendar,
      iconClass: 'text-amber-500 dark:text-amber-400',
      bgClass: 'bg-amber-500/10 dark:bg-amber-500/15',
      count: todayCount,
      label: 'Due Today',
      show: true
    },
    {
      href: '/leads?filter=followup_today',
      icon: Phone,
      iconClass: 'text-cyan-500 dark:text-cyan-400',
      bgClass: 'bg-cyan-500/10 dark:bg-cyan-500/15',
      count: followupsCount,
      label: 'Follow-ups',
      show: true
    },
    {
      href: '/leads?rating=HOT',
      icon: Flame,
      iconClass: 'text-orange-500 dark:text-orange-400',
      bgClass: 'bg-orange-500/10 dark:bg-orange-500/15',
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
    class="relative overflow-hidden rounded-xl border px-4 py-3 backdrop-blur-sm transition-all duration-300 sm:px-6
      {hasUrgentItems
        ? 'border-rose-300/50 bg-rose-50/50 dark:border-rose-500/20 dark:bg-rose-950/20'
        : 'border-border/50 bg-card/50 dark:bg-card/30'}"
  >
    <!-- Subtle gradient overlay -->
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent dark:via-white/[0.02]"></div>

    <div class="relative flex items-center gap-3 sm:gap-5">
      <!-- Label with icon -->
      <div class="hidden items-center gap-2 sm:flex">
        <div class="flex size-7 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/10 to-teal-500/10 dark:from-cyan-500/20 dark:to-teal-500/20">
          <Zap class="size-4 text-cyan-600 dark:text-cyan-400" />
        </div>
        <span class="text-muted-foreground text-xs font-semibold uppercase tracking-wider">
          Today's Focus
        </span>
      </div>

      <!-- Divider -->
      <div class="hidden h-6 w-px bg-border/50 sm:block"></div>

      <!-- Items -->
      <div class="flex flex-1 items-center gap-1 overflow-x-auto sm:gap-2">
        {#each visibleItems as item}
          <a
            href={item.href}
            class="group flex items-center gap-2 rounded-lg px-3 py-2 transition-all duration-200 hover:bg-white/50 dark:hover:bg-white/5 sm:gap-2.5 sm:px-4"
          >
            <div class="flex size-8 items-center justify-center rounded-lg transition-transform duration-200 group-hover:scale-110 {item.bgClass}">
              <item.icon class="size-4 {item.iconClass}" />
            </div>
            <div class="flex items-center gap-2">
              <span class="text-foreground text-base font-bold tabular-nums">{item.count}</span>
              <span class="text-muted-foreground hidden text-xs font-medium sm:inline">{item.label}</span>
            </div>
          </a>
        {/each}
      </div>
    </div>
  </div>
{/if}
