<script>
  import { Button } from '$lib/components/ui/button/index.js';
  import {
    Activity,
    Plus,
    Pencil,
    Trash2,
    Eye,
    MessageSquare,
    UserPlus,
    ChevronRight,
    Clock
  } from '@lucide/svelte';

  /**
   * @typedef {Object} ActivityItem
   * @property {string} id
   * @property {string} [description]
   * @property {string} [message]
   * @property {string} [timestamp]
   * @property {string} [createdAt]
   * @property {string} [action]
   * @property {string} [entityType]
   * @property {string} [entityName]
   * @property {{ name?: string }} [user]
   */

  /**
   * @typedef {Object} Props
   * @property {ActivityItem[]} [activities=[]] - List of activity items
   */

  /** @type {Props} */
  let { activities = [] } = $props();

  let showAll = $state(false);

  const actionConfig = /** @type {Record<string, { icon: typeof Activity, bg: string, text: string }>} */ ({
    CREATE: {
      icon: Plus,
      bg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
      text: 'text-emerald-600 dark:text-emerald-400'
    },
    UPDATE: {
      icon: Pencil,
      bg: 'bg-cyan-500/10 dark:bg-cyan-500/20',
      text: 'text-cyan-600 dark:text-cyan-400'
    },
    DELETE: {
      icon: Trash2,
      bg: 'bg-rose-500/10 dark:bg-rose-500/20',
      text: 'text-rose-600 dark:text-rose-400'
    },
    VIEW: {
      icon: Eye,
      bg: 'bg-slate-500/10 dark:bg-slate-500/20',
      text: 'text-slate-600 dark:text-slate-400'
    },
    COMMENT: {
      icon: MessageSquare,
      bg: 'bg-violet-500/10 dark:bg-violet-500/20',
      text: 'text-violet-600 dark:text-violet-400'
    },
    ASSIGN: {
      icon: UserPlus,
      bg: 'bg-amber-500/10 dark:bg-amber-500/20',
      text: 'text-amber-600 dark:text-amber-400'
    }
  });

  const defaultConfig = {
    icon: Activity,
    bg: 'bg-muted',
    text: 'text-muted-foreground'
  };

  /**
   * Get date category for grouping
   * @param {string | undefined} dateStr
   */
  function getDateCategory(dateStr) {
    if (!dateStr) return 'Earlier';
    const date = new Date(dateStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    if (date >= today) return 'Today';
    if (date >= yesterday) return 'Yesterday';
    if (date >= weekAgo) return 'This Week';
    return 'Earlier';
  }

  /**
   * Format time only
   * @param {string | undefined} dateStr
   */
  function formatTime(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }

  /**
   * Group activities by date category
   * @param {ActivityItem[]} activities
   */
  function groupByDate(activities) {
    const groups = /** @type {Record<string, ActivityItem[]>} */ ({});
    const order = ['Today', 'Yesterday', 'This Week', 'Earlier'];

    for (const activity of activities) {
      const category = getDateCategory(activity.timestamp || activity.createdAt);
      if (!groups[category]) groups[category] = [];
      groups[category].push(activity);
    }

    return order
      .filter((cat) => groups[cat]?.length > 0)
      .map((cat) => ({
        category: cat,
        items: groups[cat]
      }));
  }

  const displayedActivities = $derived(showAll ? activities : activities.slice(0, 5));
  const groupedActivities = $derived(groupByDate(displayedActivities));
</script>

<div class="overflow-hidden rounded-xl border border-border/50 bg-card/80 backdrop-blur-sm dark:bg-card/50">
  <!-- Header -->
  <div class="flex items-center justify-between border-b border-border/50 px-5 py-4">
    <div class="flex items-center gap-3">
      <div class="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500/10 to-purple-500/10 dark:from-violet-500/20 dark:to-purple-500/20">
        <Activity class="size-4 text-violet-600 dark:text-violet-400" />
      </div>
      <h3 class="text-foreground text-sm font-semibold tracking-tight">Recent Activity</h3>
    </div>
    <Button variant="ghost" size="sm" href="/activities" class="gap-1 text-xs font-medium">
      View all
      <ChevronRight class="size-3.5" />
    </Button>
  </div>

  <!-- Activity list -->
  <div class="p-5">
    {#if activities.length === 0}
      <div class="flex flex-col items-center justify-center py-10 text-center">
        <div class="mb-3 flex size-12 items-center justify-center rounded-xl bg-muted/50">
          <Clock class="text-muted-foreground/50 size-6" />
        </div>
        <p class="text-muted-foreground text-sm font-medium">No recent activity</p>
        <p class="text-muted-foreground/70 text-xs">Actions will appear here</p>
      </div>
    {:else}
      <div class="space-y-5">
        {#each groupedActivities as group}
          <div>
            <p class="text-muted-foreground mb-3 text-[10px] font-semibold uppercase tracking-widest">
              {group.category}
            </p>
            <div class="space-y-2">
              {#each group.items as activity (activity.id)}
                {@const config = actionConfig[activity.action || ''] || defaultConfig}
                {@const Icon = config.icon}
                <div
                  class="group -mx-2 flex items-start gap-3 rounded-lg px-2 py-2 transition-all duration-200 hover:bg-muted/30"
                >
                  <!-- Icon -->
                  <div
                    class="flex size-7 shrink-0 items-center justify-center rounded-lg transition-transform duration-200 group-hover:scale-105 {config.bg}"
                  >
                    <Icon class="size-3.5 {config.text}" />
                  </div>

                  <!-- Content -->
                  <div class="min-w-0 flex-1">
                    <p class="text-foreground text-sm leading-snug">
                      {activity.description ||
                        activity.message ||
                        `${activity.action} ${activity.entityType}: ${activity.entityName}`}
                    </p>
                    <div class="text-muted-foreground mt-1 flex items-center gap-1.5 text-xs">
                      <span class="font-medium">{activity.user?.name || 'System'}</span>
                      <span class="text-muted-foreground/50">&middot;</span>
                      <span>{formatTime(activity.timestamp || activity.createdAt)}</span>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>

      {#if activities.length > 5 && !showAll}
        <Button
          variant="ghost"
          size="sm"
          class="mt-4 w-full text-xs font-medium"
          onclick={() => (showAll = true)}
        >
          Show more ({activities.length - 5} more)
        </Button>
      {/if}
    {/if}
  </div>
</div>
