<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2, Lock, Mail, MessageSquare, Send } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Tabs from '$lib/components/ui/tabs/index.js';
  import {
    MentionBody,
    MentionTextarea
  } from '$lib/components/ui/comment-section/index.js';
  import MacroPicker from './MacroPicker.svelte';
  import SolutionSuggester from './SolutionSuggester.svelte';
  import { formatRelativeDate, getInitials } from '$lib/utils/formatting.js';

  /**
   * @type {{
   *   ticketId: string,
   *   replies?: Array<any>,
   *   internalNotes?: Array<any>,
   *   inboundEmails?: Array<any>,
   *   currentUserEmail?: string,
   *   mentionCandidates?: Array<{ username: string, id?: string, email?: string }>
   * }}
   */
  let {
    ticketId,
    replies = [],
    internalNotes = [],
    inboundEmails = [],
    currentUserEmail = '',
    mentionCandidates = []
  } = $props();

  let activeTab = $state('replies');
  let replyText = $state('');
  let internalText = $state('');
  let submittingReplies = $state(false);
  let submittingInternal = $state(false);

  const replyCount = $derived(replies.length);
  const internalCount = $derived(internalNotes.length);
  const inboundCount = $derived(inboundEmails.length);

  function commenterName(c) {
    const email = c.commented_by?.user_details?.email;
    if (!email) return 'Unknown';
    return email.split('@')[0].replace(/[._]/g, ' ');
  }

  function commenterInitials(c) {
    return getInitials(commenterName(c));
  }

  function handleEnhance(internal) {
    return () => {
      return async (/** @type {any} */ { result }) => {
        if (internal) submittingInternal = false;
        else submittingReplies = false;
        if (result.type === 'success') {
          if (internal) internalText = '';
          else replyText = '';
          await invalidateAll();
        } else if (result.type === 'failure') {
          toast.error(result.data?.error || 'Failed to add comment');
        } else if (result.type === 'error') {
          toast.error('An unexpected error occurred');
        }
      };
    };
  }
</script>

<section
  class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
>
  <Tabs.Root bind:value={activeTab} class="w-full">
    <Tabs.List class="mb-4 grid w-full grid-cols-3 sm:w-[480px]">
      <Tabs.Trigger value="replies" class="gap-2">
        <MessageSquare class="h-4 w-4" />
        Replies
        {#if replyCount > 0}
          <span
            class="rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-xs text-[var(--text-secondary)]"
          >
            {replyCount}
          </span>
        {/if}
      </Tabs.Trigger>
      <Tabs.Trigger value="internal" class="gap-2">
        <Lock class="h-4 w-4" />
        Internal Notes
        {#if internalCount > 0}
          <span
            class="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800 dark:bg-amber-900/40 dark:text-amber-200"
          >
            {internalCount}
          </span>
        {/if}
      </Tabs.Trigger>
      <Tabs.Trigger value="emails" class="gap-2">
        <Mail class="h-4 w-4" />
        Emails
        {#if inboundCount > 0}
          <span
            class="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700 dark:bg-blue-900/40 dark:text-blue-200"
          >
            {inboundCount}
          </span>
        {/if}
      </Tabs.Trigger>
    </Tabs.List>

    <Tabs.Content value="replies" class="">
      <form
        method="POST"
        action="?/comment"
        use:enhance={handleEnhance(false)}
        onsubmit={() => (submittingReplies = true)}
        class="space-y-2"
      >
        <input type="hidden" name="is_internal" value="false" />
        <MentionTextarea
          name="body"
          bind:value={replyText}
          candidates={mentionCandidates}
          placeholder="Write a public reply… type @ to mention"
          class="min-h-[80px] resize-none"
          disabled={submittingReplies}
        />
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1">
            <MacroPicker
              {ticketId}
              disabled={submittingReplies}
              onApply={(rendered) => {
                replyText = replyText
                  ? `${replyText}${replyText.endsWith('\n') ? '' : '\n'}${rendered}`
                  : rendered;
              }}
            />
            <SolutionSuggester
              {ticketId}
              disabled={submittingReplies}
              onInsert={(body) => {
                replyText = replyText
                  ? `${replyText}${replyText.endsWith('\n') ? '' : '\n'}${body}`
                  : body;
              }}
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={!replyText.trim() || submittingReplies}
            class="gap-1.5"
          >
            {#if submittingReplies}
              <Loader2 class="h-3 w-3 animate-spin" />
            {:else}
              <Send class="h-3 w-3" />
            {/if}
            Send reply
          </Button>
        </div>
      </form>

      <ul class="mt-4 space-y-3">
        {#if replies.length === 0}
          <li class="text-sm text-[var(--text-secondary)]">No replies yet.</li>
        {:else}
          {#each replies as c (c.id)}
            <li class="flex gap-3 rounded-md px-2 py-2">
              <span
                class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-semibold text-blue-700 uppercase dark:bg-blue-900/40 dark:text-blue-200"
              >
                {commenterInitials(c)}
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex items-baseline gap-2">
                  <span class="text-sm font-medium text-[var(--text-primary)]">
                    {commenterName(c)}
                  </span>
                  <span class="text-xs text-[var(--text-secondary)]">
                    {formatRelativeDate(c.commented_on)}
                  </span>
                </div>
                <p class="mt-1 text-sm text-[var(--text-secondary)]">
                  <MentionBody body={c.comment} candidates={mentionCandidates} />
                </p>
              </div>
            </li>
          {/each}
        {/if}
      </ul>
    </Tabs.Content>

    <Tabs.Content value="internal" class="">
      <form
        method="POST"
        action="?/comment"
        use:enhance={handleEnhance(true)}
        onsubmit={() => (submittingInternal = true)}
        class="space-y-2 rounded-md border border-amber-200 bg-amber-50/60 p-3 dark:border-amber-900/40 dark:bg-amber-900/10"
      >
        <input type="hidden" name="is_internal" value="true" />
        <div
          class="flex items-center gap-2 text-xs font-medium text-amber-900 dark:text-amber-200"
        >
          <Lock class="h-3 w-3" />
          Visible to agents only — never shown to customers.
        </div>
        <MentionTextarea
          name="body"
          bind:value={internalText}
          candidates={mentionCandidates}
          placeholder="Coordinate with your team privately… type @ to mention"
          class="min-h-[80px] resize-none border-amber-200 bg-white dark:border-amber-900/40 dark:bg-[var(--surface-default)]"
          disabled={submittingInternal}
        />
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1">
            <MacroPicker
              {ticketId}
              disabled={submittingInternal}
              onApply={(rendered) => {
                internalText = internalText
                  ? `${internalText}${internalText.endsWith('\n') ? '' : '\n'}${rendered}`
                  : rendered;
              }}
            />
            <SolutionSuggester
              {ticketId}
              disabled={submittingInternal}
              onInsert={(body) => {
                internalText = internalText
                  ? `${internalText}${internalText.endsWith('\n') ? '' : '\n'}${body}`
                  : body;
              }}
            />
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={!internalText.trim() || submittingInternal}
            class="gap-1.5 bg-amber-600 hover:bg-amber-700"
          >
            {#if submittingInternal}
              <Loader2 class="h-3 w-3 animate-spin" />
            {:else}
              <Send class="h-3 w-3" />
            {/if}
            Post internal note
          </Button>
        </div>
      </form>

      <ul class="mt-4 space-y-3">
        {#if internalNotes.length === 0}
          <li class="text-sm text-[var(--text-secondary)]">
            No internal notes yet.
          </li>
        {:else}
          {#each internalNotes as c (c.id)}
            <li
              class="flex gap-3 rounded-md border-l-4 border-amber-400 bg-amber-50/70 px-3 py-2 dark:border-amber-500 dark:bg-amber-900/15"
            >
              <span
                class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-200 text-xs font-semibold text-amber-900 uppercase dark:bg-amber-800/60 dark:text-amber-100"
              >
                {commenterInitials(c)}
              </span>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-baseline gap-2">
                  <span class="text-sm font-medium text-[var(--text-primary)]">
                    {commenterName(c)}
                  </span>
                  <span
                    class="rounded bg-amber-200 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-amber-900 uppercase dark:bg-amber-800/60 dark:text-amber-100"
                    aria-label="Internal note"
                  >
                    Internal
                  </span>
                  <span class="text-xs text-[var(--text-secondary)]">
                    {formatRelativeDate(c.commented_on)}
                  </span>
                </div>
                <p class="mt-1 text-sm text-[var(--text-primary)]">
                  <MentionBody body={c.comment} candidates={mentionCandidates} />
                </p>
              </div>
            </li>
          {/each}
        {/if}
      </ul>
    </Tabs.Content>

    <Tabs.Content value="emails" class="">
      <p class="mb-3 text-xs text-[var(--text-secondary)]">
        Inbound emails routed to this ticket via configured mailboxes. Outbound
        replies live on the Replies tab.
      </p>
      <ul class="space-y-3">
        {#if inboundEmails.length === 0}
          <li class="text-sm text-[var(--text-secondary)]">
            No inbound emails on this ticket yet.
          </li>
        {:else}
          {#each inboundEmails as msg (msg.id)}
            <li
              class="rounded-md border border-blue-100 bg-blue-50/60 p-3 dark:border-blue-900/40 dark:bg-blue-900/10"
            >
              <div class="flex flex-wrap items-baseline gap-2">
                <span
                  class="rounded bg-blue-200 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-blue-900 uppercase dark:bg-blue-800/60 dark:text-blue-100"
                  aria-label="Inbound email"
                >
                  <Mail class="mr-0.5 inline h-3 w-3" />
                  Email
                </span>
                <span class="text-sm font-medium text-[var(--text-primary)]">
                  {msg.from_address}
                </span>
                <span class="text-xs text-[var(--text-secondary)]">
                  {formatRelativeDate(msg.received_at)}
                </span>
              </div>
              {#if msg.subject}
                <p class="mt-1 text-sm font-medium text-[var(--text-primary)]">
                  {msg.subject}
                </p>
              {/if}
              <p class="mt-1 text-sm whitespace-pre-wrap text-[var(--text-secondary)]">
                {msg.body_text || ''}
              </p>
            </li>
          {/each}
        {/if}
      </ul>
    </Tabs.Content>
  </Tabs.Root>
</section>
