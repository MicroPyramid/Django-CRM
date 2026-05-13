<script>
  import {
    AlertTriangle,
    AtSign,
    Bell,
    History,
    Loader2,
    Mail,
    MessageSquare,
    RotateCcw,
    Trash2,
    UserPlus
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { formatRelativeDate } from '$lib/utils/formatting.js';
  import { notifications } from '$lib/stores/notifications.svelte.js';

  /**
   * @type {{
   *   onClose?: () => void
   * }}
   */
  let { onClose } = $props();

  // Map machine verbs to icons. Unknown verbs fall back to the bell.
  // NOTE: `case.*` keys are backend wire-format strings — do not rename.
  const VERB_ICONS = {
    'case.commented': MessageSquare,
    'case.mentioned': AtSign,
    'case.assigned': UserPlus,
    'case.sla_breached': AlertTriangle,
    'case.escalated': AlertTriangle,
    'case.reopened': RotateCcw,
    'case.email_received': Mail
  };

  /** @param {any} n */
  function verbIcon(n) {
    return VERB_ICONS[n.verb] || Bell;
  }

  /** @param {any} n */
  function verbLabel(n) {
    if (n.verb === 'case.mentioned') return 'mentioned you';
    if (n.verb === 'case.assigned') return 'assigned you';
    if (n.verb === 'case.commented') return 'commented';
    if (n.verb === 'case.sla_breached') return 'SLA breached';
    if (n.verb === 'case.escalated') return 'escalated';
    if (n.verb === 'case.reopened') return 'reopened';
    if (n.verb === 'case.email_received') return 'received an email';
    return n.verb.replace(/^[^.]+\./, '').replace(/_/g, ' ');
  }

  /** @param {any} n */
  function actorLabel(n) {
    return n.actor?.user_details?.email || 'System';
  }

  /** @param {any} n */
  async function open(n) {
    await notifications.markRead(n.id);
    if (n.link) {
      onClose?.();
      window.location.href = n.link;
    }
  }
</script>

<div
  class="flex w-[360px] max-w-[90vw] flex-col"
  role="dialog"
  aria-label="Notifications"
>
  <header
    class="flex items-center justify-between border-b border-[var(--border-default)] px-3 py-2"
  >
    <div class="flex items-center gap-2">
      <Bell class="h-4 w-4 text-[var(--text-secondary)]" />
      <span class="text-sm font-semibold">Notifications</span>
      {#if notifications.unread_count > 0}
        <span
          class="rounded-full bg-[var(--color-primary-default)]/10 px-1.5 text-[10px] font-medium text-[var(--color-primary-default)]"
        >
          {notifications.unread_count}
        </span>
      {/if}
    </div>
    {#if notifications.unread_count > 0}
      <button
        type="button"
        class="text-xs text-[var(--color-primary-default)] hover:underline"
        onclick={() => notifications.markAllRead()}
      >
        Mark all read
      </button>
    {/if}
  </header>

  <div class="max-h-[60vh] min-h-[120px] overflow-y-auto">
    {#if notifications.loading && notifications.notifications.length === 0}
      <div class="flex items-center justify-center py-8 text-sm text-[var(--text-secondary)]">
        <Loader2 class="mr-2 h-4 w-4 animate-spin" /> Loading…
      </div>
    {:else if notifications.notifications.length === 0}
      <div class="flex flex-col items-center justify-center gap-1 py-8 text-sm text-[var(--text-secondary)]">
        <History class="h-5 w-5 opacity-60" />
        <span>You're all caught up.</span>
      </div>
    {:else}
      <ul class="divide-y divide-[var(--border-default)]">
        {#each notifications.notifications as n (n.id)}
          {@const Icon = verbIcon(n)}
          {@const isUnread = !n.read_at}
          <li
            class="group relative flex items-start gap-2 px-3 py-2 hover:bg-[var(--surface-muted)] {isUnread
              ? 'bg-[var(--color-primary-default)]/[0.03]'
              : ''}"
          >
            <button
              type="button"
              class="flex flex-1 items-start gap-2 text-left"
              onclick={() => open(n)}
            >
              <span
                class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary-default)]"
              >
                <Icon class="h-3.5 w-3.5" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block text-sm leading-snug">
                  <span class="font-medium">{actorLabel(n)}</span>
                  {' '}{verbLabel(n)}{n.entity_name ? ` — ${n.entity_name}` : ''}
                </span>
                {#if n.data?.comment_excerpt}
                  <span class="mt-0.5 line-clamp-2 block text-xs text-[var(--text-secondary)]">
                    {n.data.comment_excerpt}
                  </span>
                {/if}
                <span class="mt-0.5 block text-[11px] text-[var(--text-secondary)]">
                  {formatRelativeDate(n.created_at)}
                </span>
              </span>
              {#if isUnread}
                <span
                  class="mt-2 h-2 w-2 shrink-0 rounded-full bg-[var(--color-primary-default)]"
                  aria-label="unread"
                ></span>
              {/if}
            </button>
            <button
              type="button"
              class="invisible absolute top-2 right-2 rounded-md p-1 text-[var(--text-secondary)] hover:bg-[var(--surface-default)] group-hover:visible"
              aria-label="Delete notification"
              onclick={() => notifications.remove(n.id)}
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>

  {#if notifications.error}
    <div class="border-t border-[var(--border-default)] px-3 py-1.5 text-xs text-[var(--color-danger-default)]">
      {notifications.error}
    </div>
  {/if}
</div>
