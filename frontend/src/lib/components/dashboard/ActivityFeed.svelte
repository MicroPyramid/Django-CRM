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

  // Using design system activity tokens
  const actionConfig = /** @type {Record<string, { icon: typeof Activity, bg: string, text: string }>} */ ({
    CREATE: {
      icon: Plus,
      bg: 'bg-[var(--color-success-light)] dark:bg-[var(--color-success-default)]/15',
      text: 'text-[var(--color-success-default)]'
    },
    UPDATE: {
      icon: Pencil,
      bg: 'bg-[var(--color-primary-light)] dark:bg-[var(--color-primary-default)]/15',
      text: 'text-[var(--color-primary-default)]'
    },
    DELETE: {
      icon: Trash2,
      bg: 'bg-[var(--color-negative-light)] dark:bg-[var(--color-negative-default)]/15',
      text: 'text-[var(--color-negative-default)]'
    },
    VIEW: {
      icon: Eye,
      bg: 'bg-[var(--surface-sunken)]',
      text: 'text-[var(--text-secondary)]'
    },
    COMMENT: {
      icon: MessageSquare,
      bg: 'bg-[var(--activity-note)]/10 dark:bg-[var(--activity-note)]/15',
      text: 'text-[var(--activity-note)]'
    },
    ASSIGN: {
      icon: UserPlus,
      bg: 'bg-[var(--activity-meeting)]/10 dark:bg-[var(--activity-meeting)]/15',
      text: 'text-[var(--activity-meeting)]'
    }
  });

  const defaultConfig = {
    icon: Activity,
    bg: 'bg-[var(--surface-sunken)]',
    text: 'text-[var(--text-tertiary)]'
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

<div class="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-raised)] dark:bg-[var(--surface-raised)]/80 dark:backdrop-blur-sm">
  <!-- Header - Orange accent -->
  <div class="flex items-center justify-between border-b border-[var(--border-default)]/50 px-5 py-4">
    <div class="flex items-center gap-3">
      <div class="flex size-8 items-center justify-center rounded-[var(--radius-md)] bg-[var(--color-primary-light)] dark:bg-[var(--color-primary-default)]/15">
        <Activity class="size-4 text-[var(--color-primary-default)]" />
      </div>
      <h3 class="text-[var(--text-primary)] text-sm font-semibold tracking-tight">Recent Activity</h3>
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
        <div class="mb-3 flex size-12 items-center justify-center rounded-[var(--radius-lg)] bg-[var(--surface-sunken)]">
          <Clock class="size-6 text-[var(--text-tertiary)]" />
        </div>
        <p class="text-[var(--text-secondary)] text-sm font-medium">No recent activity</p>
        <p class="text-[var(--text-tertiary)] text-xs">Actions will appear here</p>
      </div>
    {:else}
      <div class="space-y-5">
        {#each groupedActivities as group}
          <div>
            <p class="text-[var(--text-tertiary)] mb-3 text-[10px] font-semibold uppercase tracking-widest">
              {group.category}
            </p>
            <div class="space-y-2">
              {#each group.items as activity (activity.id)}
                {@const config = actionConfig[activity.action || ''] || defaultConfig}
                {@const Icon = config.icon}
                <div
                  class="group -mx-2 flex items-start gap-3 rounded-[var(--radius-md)] px-2 py-2 transition-all duration-200 hover:bg-[var(--color-primary-light)] dark:hover:bg-[var(--color-primary-default)]/5"
                >
                  <!-- Icon -->
                  <div
                    class="flex size-7 shrink-0 items-center justify-center rounded-[var(--radius-md)] transition-transform duration-200 group-hover:scale-105 {config.bg}"
                  >
                    <Icon class="size-3.5 {config.text}" />
                  </div>

                  <!-- Content -->
                  <div class="min-w-0 flex-1">
                    <p class="text-[var(--text-primary)] text-sm leading-snug">
                      {activity.description ||
                        activity.message ||
                        `${activity.action} ${activity.entityType}: ${activity.entityName}`}
                    </p>
                    <div class="mt-1 flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
                      <span class="font-medium">{activity.user?.name || 'System'}</span>
                      <span class="text-[var(--text-tertiary)]">&middot;</span>
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
