<script>
  import { enhance } from '$app/forms';
  import { tryBlocked } from '#lib/v2/automation.js';
  import RecordPicker from '#lib/v2/components/RecordPicker.svelte';

  /**
   * Plans the saved rule on one record; nothing is written. The result comes
   * back as `form.tried`, and every step is shown as text.
   *
   * @type {{ rule: any, dirty: boolean, form: any }}
   */
  let { rule, dirty, form } = $props();

  let chosen = $state(/** @type {{ id: string, name: string }[]} */ ([]));
  let busy = $state(false);
  let blocked = $derived(tryBlocked({ dirty, busy, chosen }));
  let tried = $derived(dirty ? null : (form?.tried ?? null));
  let header = $derived(
    `${tried?.recordName ? `Tried on "${tried.recordName}".` : 'Tried.'} Nothing was changed.`
  );
  let tryError = $derived(dirty ? null : (form?.tryError ?? null));

  /** @type {import('$app/forms').SubmitFunction} */
  const submit = () => {
    busy = true;
    return async ({ update }) => {
      await update({ reset: false });
      busy = false;
    };
  };
</script>

<section class="v2-card au-try" aria-labelledby="au-try-h">
  <h2 class="v2-label" id="au-try-h">Try it on a record</h2>
  <form method="POST" action="?/try" use:enhance={submit}>
    <RecordPicker
      name="record_id"
      target={rule.object_key}
      label="Try it on a record"
      placeholder="Search for a record"
      bind:chosen
    />
    <input type="hidden" name="record_name" value={chosen[0]?.name ?? ''} />
    <div class="au-try-go">
      <button
        type="submit"
        class="v2-btn"
        disabled={blocked !== null}
        aria-describedby={blocked ? 'au-try-dirty' : undefined}
      >
        Try it
      </button>
      {#if blocked}
        <span class="v2-hint" id="au-try-dirty">{blocked}</span>
      {/if}
    </div>
  </form>

  {#if tryError}
    <p class="v2-error" role="alert">{tryError}</p>
  {:else if tried}
    <div class="au-result" role="status">
      <b>{header}</b>
      <p class="v2-hint">
        The trigger and conditions are not checked: this is what the actions would do.
      </p>
      <ol class="au-steps">
        {#each tried.steps as step, i (i)}
          <li class="au-step au-{step.status}">
            {#if step.status === 'skipped'}<span class="au-tag">Skipped</span>
            {:else if step.status === 'failed'}<span class="au-tag">Would fail</span>{/if}
            {step.text}
          </li>
        {:else}
          <li class="au-step v2-hint">The rule has no steps to run.</li>
        {/each}
      </ol>
    </div>
  {/if}
</section>

<style>
  .au-try {
    padding: 12px 15px 14px;
    margin-top: 14px;
  }
  .au-try h2 {
    margin: 0 0 8px;
  }
  .au-try-go {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
  }
  .au-result {
    margin-top: 12px;
    padding: 10px 12px;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    background: var(--v2-line-soft);
    font-size: 13px;
  }
  .au-result p {
    margin: 4px 0 0;
  }
  .au-steps {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
  }
  .au-step {
    padding: 4px 0;
    overflow-wrap: anywhere;
  }
  .au-skipped {
    color: var(--v2-slate);
  }
  .au-failed {
    color: var(--v2-rust);
  }
  .au-tag {
    font-weight: 600;
    margin-right: 4px;
  }
  @media (max-width: 768px) {
    .au-try-go .v2-btn {
      flex: 1 1 100%;
      justify-content: center;
      min-height: 44px;
    }
  }
</style>
