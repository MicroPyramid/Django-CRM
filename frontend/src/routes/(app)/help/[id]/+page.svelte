<script>
  import { enhance } from '$app/forms';
  import { resolve } from '$app/paths';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import { shortDate } from '$lib/v2/format.js';
  import { Paperclip, Send } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();
  let submitting = $state(false);
  let ticket = $derived(data.ticket);

  const STATUS_TONE = {
    open: 'rust',
    in_progress: 'clay',
    waiting_on_customer: 'sky',
    resolved: 'moss',
    closed: 'slate'
  };
</script>

<PageHeader title={ticket.subject} center width="840px">
  {#snippet sub()}
    {ticket.reference} · {ticket.categoryLabel} · opened {shortDate(ticket.createdAt)}
  {/snippet}
  {#snippet actions()}
    <Pill tone={STATUS_TONE[ticket.status]}>{ticket.statusLabel}</Pill>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div
    class="v2-pad"
    style="padding-top:18px;padding-bottom:32px;max-width:840px;margin-inline:auto"
  >
    <a class="back" href={resolve('/help')}>Back to help</a>

    <div class="summary v2-card">
      <span><b>Status</b>{ticket.statusLabel}</span>
      <span><b>Priority</b>{ticket.priorityLabel}</span>
      <span
        ><b>Assigned</b>{ticket.assigned
          ? 'Support agent assigned'
          : 'Waiting for assignment'}</span
      >
    </div>

    <div class="v2-label" style="margin:22px 0 10px">Conversation</div>
    <div class="conversation">
      {#each ticket.messages as message (message.id)}
        <article class:staff={message.authorType === 'staff'} class="message v2-card">
          <div class="meta">
            <b>{message.author}</b>
            <span>{shortDate(message.createdAt)}</span>
          </div>
          {#if message.body}<div class="body">{message.body}</div>{/if}
          {#if message.attachmentUrl}
            <a class="attachment" href={resolve(message.attachmentUrl)}>
              <Paperclip size={14} />{message.attachmentName}
            </a>
          {/if}
        </article>
      {/each}
    </div>

    {#if form?.error}<p class="v2-card error">{form.error}</p>{/if}
    {#if form?.sent}<p class="v2-card sent">Your reply was sent.</p>{/if}

    {#if ticket.status === 'closed'}
      <div class="v2-card closed">
        This ticket is closed. Open a new ticket if you still need help.
        <a class="v2-btn" href={resolve('/help/new')}>New ticket</a>
      </div>
    {:else}
      <form
        method="POST"
        action="?/reply"
        enctype="multipart/form-data"
        class="v2-card composer"
        use:enhance={() => {
          submitting = true;
          return async ({ update }) => {
            await update({ reset: true });
            submitting = false;
          };
        }}
      >
        <div class="v2-field">
          <label for="reply">Reply</label>
          <textarea
            id="reply"
            class="v2-input"
            name="body"
            rows="5"
            maxlength="10000"
            placeholder="Add any details that will help us investigate."
            >{form?.body ?? ''}</textarea
          >
        </div>
        <div class="compose-actions">
          <input class="v2-input" type="file" name="attachment" aria-label="Attach a file" />
          <button class="v2-btn v2-btn-primary" type="submit" disabled={submitting}
            ><Send />{submitting ? 'Sending…' : 'Send reply'}</button
          >
        </div>
      </form>
    {/if}
  </div>
</div>

<style>
  .back {
    color: var(--v2-slate);
    font-size: 12px;
  }
  .summary {
    margin-top: 14px;
    padding: 13px 15px;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    font-size: 12px;
  }
  .summary span,
  .summary b {
    display: block;
  }
  .summary b {
    margin-bottom: 3px;
    color: var(--v2-slate);
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .conversation {
    display: grid;
    gap: 10px;
  }
  .message {
    padding: 13px 15px;
    margin-right: 42px;
  }
  .message.staff {
    margin-right: 0;
    margin-left: 42px;
    border-color: color-mix(in srgb, var(--v2-moss) 38%, var(--v2-line));
  }
  .meta {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 7px;
    font-size: 11.5px;
    color: var(--v2-slate);
  }
  .body {
    white-space: pre-wrap;
    font-size: 13.5px;
    line-height: 1.55;
  }
  .attachment {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 10px;
    font-size: 12px;
    color: inherit;
  }
  .composer,
  .closed,
  .error,
  .sent {
    margin-top: 18px;
    padding: 15px;
  }
  .compose-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 12px;
  }
  .compose-actions input {
    max-width: 430px;
  }
  .closed {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 13px;
  }
  .error {
    color: var(--v2-rust);
  }
  .sent {
    color: var(--v2-moss);
  }
  @media (max-width: 768px) {
    .summary {
      grid-template-columns: 1fr;
    }
    .message,
    .message.staff {
      margin-inline: 0;
    }
    .compose-actions,
    .closed {
      align-items: stretch;
      flex-direction: column;
    }
    .compose-actions input {
      max-width: none;
    }
  }
</style>
