<script>
  import { untrack } from 'svelte';
  import {
    History,
    Plus,
    Pencil,
    Trash2,
    UserPlus,
    MessageSquare,
    BookOpen,
    BookOpenCheck,
    AlertTriangle,
    RotateCcw,
    GitMerge,
    Route,
    Mail,
    Eye,
    EyeOff,
    Loader2
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { formatRelativeDate, getInitials } from '$lib/utils/formatting.js';

  /** @type {{
   *   ticketId: string,
   *   initial?: Array<any>,
   * }} */
  let { ticketId, initial = [] } = $props();

  // `initial` is a one-time seed; the user mutates `activities` via Load older.
  // Reading inside untrack() silences Svelte's "initial value only" warning
  // because we explicitly do *not* want this to refresh on prop changes.
  let activities = $state(untrack(() => [...initial]));
  let nextOffset = $state(untrack(() => initial.length));
  let totalCount = $state(untrack(() => initial.length));
  let loading = $state(false);
  let error = $state('');

  const PAGE_SIZE = 20;

  async function loadMore() {
    if (loading) return;
    loading = true;
    error = '';
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(nextOffset)
      });
      const res = await fetch(`/api/cases/${ticketId}/activities?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const fetched = data.activities || [];
      const seen = new Set(activities.map((a) => a.id));
      for (const row of fetched) {
        if (!seen.has(row.id)) activities.push(row);
      }
      activities = [...activities];
      totalCount = data.count ?? totalCount;
      nextOffset = activities.length;
    } catch (err) {
      console.error('Activity load-more failed', err);
      error = 'Could not load older activity. Try again.';
    } finally {
      loading = false;
    }
  }

  const ACTION_ICONS = {
    CREATE: Plus,
    UPDATE: Pencil,
    DELETE: Trash2,
    ASSIGN: UserPlus,
    COMMENT: MessageSquare,
    STATUS_CHANGED: Pencil,
    PRIORITY_CHANGED: AlertTriangle,
    LINKED_SOLUTION: BookOpenCheck,
    UNLINKED_SOLUTION: BookOpen,
    REOPENED: RotateCcw,
    MERGED: GitMerge,
    MERGE_TARGET: GitMerge,
    ROUTED: Route,
    ESCALATED: AlertTriangle,
    EMAIL_RECEIVED: Mail
  };

  function actionIcon(a) {
    // Visibility flips reuse the COMMENT verb but should look distinct.
    if (a.action === 'COMMENT' && a.metadata?.visibility_changed) {
      return a.metadata.after ? EyeOff : Eye;
    }
    return ACTION_ICONS[a.action] || History;
  }

  function actorName(activity) {
    return (
      activity?.user?.user_details?.email || activity?.user?.email || 'System'
    );
  }

  function actionSummary(a) {
    const who = actorName(a);
    const m = a.metadata || {};
    switch (a.action) {
      case 'CREATE':
        return `${who} created the ticket`;
      case 'STATUS_CHANGED':
        return `${who} changed status from ${m.before || '—'} → ${m.after || '—'}`;
      case 'PRIORITY_CHANGED':
        return `${who} changed priority from ${m.before || '—'} → ${m.after || '—'}`;
      case 'ASSIGN': {
        const added = (m.added || []).length;
        const removed = (m.removed || []).length;
        if (added && !removed) return `${who} added ${added} assignee${added > 1 ? 's' : ''}`;
        if (removed && !added) return `${who} removed ${removed} assignee${removed > 1 ? 's' : ''}`;
        return `${who} updated assignment`;
      }
      case 'COMMENT':
        if (m.visibility_changed) {
          return `${who} changed comment visibility ${m.before ? 'internal' : 'public'} → ${m.after ? 'internal' : 'public'}`;
        }
        if (m.out_of_reopen_window) {
          return `${who} commented (outside reopen window — ticket stays closed)`;
        }
        return `${who} commented`;
      case 'REOPENED':
        return m.to_status
          ? `${who} reopened the ticket (→ ${m.to_status})`
          : `${who} reopened the ticket`;
      case 'LINKED_SOLUTION':
        return `${who} linked a knowledge-base solution`;
      case 'UNLINKED_SOLUTION':
        return `${who} unlinked a knowledge-base solution`;
      case 'DELETE':
        return `${who} deleted the ticket`;
      case 'UPDATE': {
        const fields = Object.keys(m.changes || {});
        if (!fields.length) return `${who} updated the ticket`;
        return `${who} updated ${fields.join(', ')}`;
      }
      case 'MERGED':
        return `${who} merged this ticket into another`;
      case 'MERGE_TARGET':
        return `${who} merged a duplicate into this ticket`;
      case 'ROUTED':
        return `${who} routed the ticket`;
      case 'ESCALATED':
        return `${who} escalated the ticket`;
      case 'EMAIL_RECEIVED':
        return m.from_address
          ? `Received email from ${m.from_address}`
          : 'Received inbound email';
      default:
        return `${who} ${a.action.toLowerCase().replace(/_/g, ' ')}`;
    }
  }

  function actionDetail(a) {
    const m = a.metadata || {};
    if (a.action === 'UPDATE' && m.changes) {
      return Object.entries(m.changes)
        .map(
          ([k, v]) =>
            `${k}: ${v.before == null ? '∅' : String(v.before)} → ${
              v.after == null ? '∅' : String(v.after)
            }`
        )
        .join('\n');
    }
    if (m._truncated) return '(metadata truncated — payload too large)';
    return null;
  }
</script>

<section
  class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
>
  <div class="mb-3 flex items-center gap-2">
    <History class="h-4 w-4 text-[var(--text-secondary)]" />
    <h3 class="text-sm font-medium text-[var(--text-secondary)]">
      Activity timeline
    </h3>
    {#if totalCount}
      <span class="text-xs text-[var(--text-secondary)]">({totalCount})</span>
    {/if}
  </div>

  {#if activities.length === 0}
    <p class="text-sm text-[var(--text-secondary)]">No activity yet.</p>
  {:else}
    <ol class="space-y-3">
      {#each activities as a (a.id)}
        {@const Icon = actionIcon(a)}
        {@const detail = actionDetail(a)}
        <li class="flex gap-3 text-sm">
          <div
            class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary-default)]"
            aria-hidden="true"
          >
            <Icon class="h-3.5 w-3.5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-baseline gap-x-2">
              <span class="text-[var(--text-primary)]">{actionSummary(a)}</span>
              <span class="text-xs text-[var(--text-secondary)]">
                {formatRelativeDate(a.created_at)}
              </span>
            </div>
            {#if detail}
              <pre
                class="mt-1 whitespace-pre-wrap text-xs text-[var(--text-secondary)]">{detail}</pre>
            {/if}
          </div>
          {#if a.user}
            <span
              class="ml-2 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--surface-muted)] text-[10px] font-medium text-[var(--text-secondary)]"
              title={actorName(a)}
            >
              {getInitials(actorName(a))}
            </span>
          {/if}
        </li>
      {/each}
    </ol>

    {#if totalCount > activities.length}
      <div class="mt-3 flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onclick={loadMore}
          disabled={loading}
        >
          {#if loading}
            <Loader2 class="mr-2 h-3.5 w-3.5 animate-spin" />
          {/if}
          Load older
        </Button>
        {#if error}
          <span class="text-xs text-[var(--color-danger-default)]">{error}</span>
        {/if}
      </div>
    {/if}
  {/if}
</section>

