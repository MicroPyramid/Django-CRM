<script>
  /**
   * "Log activity": a call, meeting, email, WhatsApp or text, posted to the
   * page's `?/logActivity` (`interactionActions` in
   * `#lib/server/v2/interactions.js`). The record is the route's; nothing here
   * names it. `kind` is bindable so a Call or WhatsApp button can open the
   * form already set.
   */
  import { enhance } from '$app/forms';
  import {
    CALL_OUTCOMES,
    KIND_LABEL,
    LOGGABLE_KINDS,
    OUTCOME_LABEL
  } from '#lib/v2/interactions.js';

  /** @type {{
   *   kind?: string,
   *   result?: { error?: string } | null,
   *   timeZone?: string,
   *   oncancel?: () => void,
   *   onlogged?: () => void
   * }} */
  let { kind = $bindable('call'), result = null, timeZone = 'UTC', oncancel, onlogged } = $props();

  const uid = $props.id();

  let direction = $state('outbound');
  let outcome = $state('');
  /** @type {number | string | null} */
  let minutes = $state('');
  let subject = $state('');
  let note = $state('');
  let when = $state('');
  let saving = $state(false);

  let hasLength = $derived(kind === 'call' || kind === 'meeting');
  let hasSubject = $derived(kind === 'email' || kind === 'meeting');
  let submitLabel = $derived(
    `Log ${kind === 'whatsapp' ? 'WhatsApp' : (KIND_LABEL[kind] ?? 'activity').toLowerCase()}`
  );

  function clear() {
    direction = 'outbound';
    outcome = '';
    minutes = '';
    subject = '';
    note = '';
    when = '';
  }
</script>

<form
  method="POST"
  action="?/logActivity"
  class="log"
  use:enhance={() => {
    saving = true;
    return async ({ result: answer, update }) => {
      if (answer.type === 'success') clear();
      await update({ reset: false });
      saving = false;
      if (answer.type === 'success') onlogged?.();
    };
  }}
>
  <div class="chips" role="radiogroup" aria-label="What happened">
    {#each LOGGABLE_KINDS as k (k)}
      <label class="chip" class:on={kind === k}>
        <input type="radio" name="kind" value={k} bind:group={kind} />{KIND_LABEL[k]}
      </label>
    {/each}
  </div>

  {#if kind !== 'meeting'}
    <div class="chips" role="radiogroup" aria-label="Direction">
      <label class="chip" class:on={direction === 'outbound'}>
        <input type="radio" name="direction" value="outbound" bind:group={direction} />Outgoing
      </label>
      <label class="chip" class:on={direction === 'inbound'}>
        <input type="radio" name="direction" value="inbound" bind:group={direction} />Incoming
      </label>
    </div>
  {/if}

  {#if kind === 'call'}
    <div class="chips" role="radiogroup" aria-label="How it went">
      {#each CALL_OUTCOMES as o (o)}
        <label class="chip" class:on={outcome === o}>
          <input type="radio" name="outcome" value={o} bind:group={outcome} />{OUTCOME_LABEL[o]}
        </label>
      {/each}
    </div>
  {/if}

  <div class="row">
    {#if hasLength}
      <div class="v2-field">
        <label for="{uid}-min">Minutes</label>
        <input
          id="{uid}-min"
          class="v2-input"
          type="number"
          name="duration_minutes"
          min="0"
          step="1"
          inputmode="numeric"
          bind:value={minutes}
        />
      </div>
    {/if}
    <div class="v2-field">
      <label for="{uid}-when">When</label>
      <input
        id="{uid}-when"
        class="v2-input"
        type="datetime-local"
        name="occurred_at"
        bind:value={when}
      />
      <div class="v2-hint">Leave empty for now. Read as {timeZone} time.</div>
    </div>
  </div>

  {#if hasSubject}
    <div class="v2-field">
      <label for="{uid}-subject">Subject</label>
      <input
        id="{uid}-subject"
        class="v2-input"
        name="subject"
        maxlength="200"
        bind:value={subject}
      />
    </div>
  {/if}

  <div class="v2-field">
    <label for="{uid}-note">Note</label>
    <textarea
      id="{uid}-note"
      class="v2-input"
      name="body"
      rows="2"
      maxlength="10000"
      placeholder="What was said, what happens next"
      bind:value={note}></textarea>
  </div>

  {#if result?.error}
    <p class="v2-error" role="alert" style="margin:0 0 10px">{result.error}</p>
  {/if}

  <div class="actions">
    <button class="v2-btn v2-btn-primary" type="submit" disabled={saving}>
      {saving ? 'Saving…' : submitLabel}
    </button>
    {#if oncancel}
      <button class="v2-btn" type="button" disabled={saving} onclick={oncancel}>Cancel</button>
    {/if}
  </div>
</form>

<style>
  .log {
    padding: 13px 14px 14px;
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 9px;
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 11px;
  }
  .chip {
    position: relative;
    display: inline-flex;
    align-items: center;
    min-height: 32px;
    padding: 5px 11px;
    font-size: 12.5px;
    color: var(--v2-slate);
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 999px;
    cursor: pointer;
  }
  .chip.on {
    color: var(--v2-ink);
    background: var(--v2-hover);
    border-color: var(--v2-slate);
    font-weight: 600;
  }
  .chip:has(input:focus-visible) {
    outline: 2px solid var(--v2-ember);
    outline-offset: 1px;
  }
  /* Visually hidden, still in the tab order and announced as a radio. */
  .chip input {
    position: absolute;
    opacity: 0;
    width: 1px;
    height: 1px;
    pointer-events: none;
  }
  .row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0 12px;
    max-width: 480px;
  }
  .log textarea {
    resize: vertical;
    line-height: 1.5;
  }
  .actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  @media (max-width: 767px) {
    .chip {
      min-height: 44px;
      padding: 8px 14px;
    }
  }
</style>
