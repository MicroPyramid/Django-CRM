<script>
  import { goto } from '$app/navigation';
  import { page } from '$app/state';
  import { enhance } from '$app/forms';
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    ChevronLeft,
    Clock,
    MessageSquare,
    History,
    GitMerge,
    Unlink
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Tabs from '$lib/components/ui/tabs/index.js';
  import { invalidateAll } from '$app/navigation';
  import {
    TicketApprovalPanel,
    TicketDetailHeader,
    TicketDetailSidebar,
    TicketSolutionsPanel,
    TicketActivityTimeline,
    TicketDiscussion,
    TicketMergeDialog,
    TicketTimePanel,
    TicketTreePanel,
    WatchToggle
  } from '$lib/components/tickets';
  import CloseWithChildrenDialog from '$lib/components/tickets/CloseWithChildrenDialog.svelte';
  import { CustomFieldsPanel } from '$lib/components/custom-fields';

  /** @type {{ data: any }} */
  let { data } = $props();

  const c = $derived(data.ticketItem);
  const linkedSolutions = $derived(data.linkedSolutions || []);
  const availableSolutions = $derived(data.availableSolutions || []);
  const activities = $derived(data.activities || []);
  const replies = $derived(data.comments || []);
  const internalNotes = $derived(data.internalNotes || []);
  const inboundEmails = $derived(data.inboundEmails || []);
  const customFieldDefinitions = $derived(data.customFieldDefinitions || []);
  const customFieldValues = $derived(data.customFieldValues || {});
  const mergedFromTickets = $derived(c?.mergedFromTickets || []);

  let mergeOpen = $state(false);
  let cascadeOpen = $state(false);
  const shortId = (/** @type {string} */ id) =>
    (id || '').replace(/-/g, '').slice(0, 8);

  // When a server-side merge redirects us here with `?from=<duplicate-id>`,
  // surface a one-time toast so the agent knows where they landed.
  onMount(() => {
    const from = page.url.searchParams.get('from');
    if (from) {
      toast.success(`Merged from #${shortId(from)}`);
      const next = new URL(page.url);
      next.searchParams.delete('from');
      history.replaceState(null, '', next.pathname + next.search);
    }
  });

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function unmergeEnhance({ cancel }) {
    if (
      !window.confirm(
        'Unmerge this ticket? Comments, attachments, and emails moved during the merge will be moved back, and the ticket will be restored to its previous status.'
      )
    ) {
      cancel();
      return;
    }
    return async ({ result, update }) => {
      await update();
      if (result.type === 'success' && /** @type {any} */ (result.data)?.success) {
        toast.success('Ticket unmerged');
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Failed to unmerge');
      }
    };
  }
</script>

<svelte:head>
  <title>{c.subject} - Ticket - BottleCRM</title>
</svelte:head>

<div class="flex flex-col gap-4 p-4">
  <div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
    <button
      type="button"
      onclick={() => goto('/tickets')}
      class="inline-flex items-center gap-1 hover:text-[var(--text-primary)]"
    >
      <ChevronLeft class="h-4 w-4" />
      Tickets
    </button>
    <span>/</span>
    <span class="font-medium text-[var(--text-primary)]">{c.subject}</span>
  </div>

  {#if c.mergedInto}
    <section
      class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <span class="flex items-center gap-2">
          <GitMerge class="h-4 w-4" />
          This ticket was merged into another. New replies should land on the primary.
        </span>
        <div class="flex flex-wrap items-center gap-2">
          <form method="POST" action="?/unmerge" use:enhance={unmergeEnhance}>
            <Button type="submit" variant="outline" size="sm" class="gap-1">
              <Unlink class="h-4 w-4" />
              Unmerge
            </Button>
          </form>
          <Button
            size="sm"
            onclick={() => goto(`/tickets/${c.mergedInto}`)}
            class="gap-1"
          >
            Open primary
          </Button>
        </div>
      </div>
    </section>
  {/if}

  <div class="flex flex-wrap items-start justify-between gap-3">
    <div class="min-w-0 flex-1">
      <TicketDetailHeader ticketItem={c} />
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <WatchToggle
        ticketId={c.id}
        currentUserId={data.currentUserId}
        initialWatchers={data.watchers}
      />
      <Button
        variant="outline"
        size="sm"
        class="gap-1"
        onclick={() => (mergeOpen = true)}
        disabled={c.status === 'Duplicate' || !!c.mergedInto}
        title={c.mergedInto ? 'This ticket has already been merged' : 'Merge into another ticket'}
      >
        <GitMerge class="h-4 w-4" />
        Merge
      </Button>
      {#if c.childCount > 0 && c.status !== 'Closed'}
        <Button
          variant="outline"
          size="sm"
          class="gap-1"
          onclick={() => (cascadeOpen = true)}
          title="Close this ticket and (optionally) cascade-close children"
        >
          Close with children
        </Button>
      {/if}
    </div>
  </div>

  {#if mergedFromTickets.length > 0}
    <section
      class="rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm dark:border-blue-900/40 dark:bg-blue-900/20"
    >
      <h3 class="mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-blue-800 dark:text-blue-200">
        <GitMerge class="h-3 w-3" />
        Merged from
      </h3>
      <ul class="space-y-1">
        {#each mergedFromTickets as m (m.id)}
          <li class="flex items-center gap-2">
            <a
              href={`/tickets/${m.id}?show_merged=true`}
              class="min-w-0 flex-1 truncate text-blue-700 underline hover:text-blue-900 dark:text-blue-200"
            >
              {m.name}
            </a>
            <span class="font-mono text-[10px] text-[var(--text-secondary)]">
              #{shortId(m.id)}
            </span>
            <form method="POST" action="?/unmerge" use:enhance={unmergeEnhance}>
              <input type="hidden" name="source_id" value={m.id} />
              <Button
                type="submit"
                variant="ghost"
                size="sm"
                class="h-7 gap-1 px-2 text-xs"
                title="Move this duplicate's content back to its own ticket"
              >
                <Unlink class="h-3 w-3" />
                Unmerge
              </Button>
            </form>
          </li>
        {/each}
      </ul>
    </section>
  {/if}

  <div class="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
    <div class="space-y-6">
      {#if c.description}
        <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
          <h3 class="mb-2 text-sm font-medium text-[var(--text-secondary)]">Description</h3>
          <p class="whitespace-pre-wrap text-sm text-[var(--text-primary)]">{c.description}</p>
        </section>
      {/if}

      {#if customFieldDefinitions.length > 0}
        <CustomFieldsPanel
          target="Case"
          definitions={customFieldDefinitions}
          values={customFieldValues}
        />
      {/if}

      <TicketTreePanel
        ticketId={c.id}
        parentSummary={c.parentSummary}
        isProblem={c.isProblem}
        childCount={c.childCount}
        onLinkChange={() => invalidateAll()}
      />

      <TicketApprovalPanel
        ticketId={c.id}
        currentProfileId={data.currentProfileId}
        isAdmin={!!data.isAdmin}
        initialApprovals={data.approvals || []}
      />

      <TicketSolutionsPanel
        ticketId={c.id}
        linked={linkedSolutions}
        available={availableSolutions}
      />

      <Tabs.Root value="discussion" class="w-full">
        <Tabs.List class="mb-3 grid w-full grid-cols-3 sm:w-[420px]">
          <Tabs.Trigger value="discussion" class="gap-2">
            <MessageSquare class="h-4 w-4" />
            Discussion
          </Tabs.Trigger>
          <Tabs.Trigger value="time" class="gap-2">
            <Clock class="h-4 w-4" />
            Time
          </Tabs.Trigger>
          <Tabs.Trigger value="activity" class="gap-2">
            <History class="h-4 w-4" />
            Activity
          </Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="discussion" class="">
          <TicketDiscussion
            ticketId={c.id}
            replies={replies}
            internalNotes={internalNotes}
            inboundEmails={inboundEmails}
            mentionCandidates={data.mentionCandidates || []}
          />
        </Tabs.Content>
        <Tabs.Content value="time" class="">
          <TicketTimePanel
            ticketId={c.id}
            currentUserId={data.currentUserId}
            isAdmin={!!data.isAdmin}
            timeSummary={c.timeSummary}
          />
        </Tabs.Content>
        <Tabs.Content value="activity" class="">
          <TicketActivityTimeline ticketId={c.id} initial={activities} />
        </Tabs.Content>
      </Tabs.Root>
    </div>

    <TicketDetailSidebar ticketItem={c} formOptions={data.formOptions} />
  </div>
</div>

<TicketMergeDialog
  ticketId={c.id}
  ticketSubject={c.subject}
  bind:open={mergeOpen}
  onOpenChange={(v) => (mergeOpen = v)}
/>

<CloseWithChildrenDialog
  ticketId={c.id}
  ticketSubject={c.subject}
  childCount={c.childCount}
  bind:open={cascadeOpen}
  onOpenChange={(v) => (cascadeOpen = v)}
/>
