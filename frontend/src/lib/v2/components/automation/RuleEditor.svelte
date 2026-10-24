<script>
  import { tick, untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import AutomationCrumb from './AutomationCrumb.svelte';
  import NextAction from '#lib/v2/components/NextAction.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import ConfirmAction from '#lib/v2/components/ConfirmAction.svelte';
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import TryPanel from './TryPanel.svelte';
  import {
    objectOf,
    editorState,
    isDirty,
    editorErrors,
    sentRows,
    ruleStatus,
    switchLabel,
    pausedByModule,
    modulePausedNote,
    STATUS
  } from '#lib/v2/automation.js';
  import TriggerSection from './TriggerSection.svelte';
  import ConditionRows from './ConditionRows.svelte';
  import ActionRows from './ActionRows.svelte';

  /**
   * The rule editor both `settings/automation/new` and `[id]` render. The rule
   * is one `$state` draft, posted whole as the `rule` field; it outlives a
   * refused save, so nothing the admin typed is lost.
   *
   * @type {{ catalogue: any, rule?: any, row?: any, modules?: any, form: any }}
   */
  let { catalogue, rule = null, row = null, modules = null, form } = $props();

  let draft = $state(untrack(() => editorState(rule, catalogue?.objects?.[0]?.key ?? '')));
  let busy = $state(false);
  // The rows as they were sent, so a row error stays on its row after an
  // earlier row is removed, and leaves with the row it named.
  let sent = $state.raw(sentRows({}));

  let object = $derived(objectOf(catalogue, draft.object_key));
  let switchTo = $derived(switchLabel(ruleStatus(rule, row)));
  let errors = $derived(editorErrors(form?.save, sent, draft));
  let status = $derived(
    /** @type {Record<string, { label: string, tone: any }>} */ (STATUS)[
      ruleStatus(rule, row) ?? ''
    ] ?? null
  );
  let held = $derived(Boolean(row) && pausedByModule(row, modules));
  let dirty = $derived(rule ? isDirty(draft, rule) : false);
  let ownerName = $derived(rule?.owner ? String(rule.owner.name ?? '').trim() : '');
  let saved = $derived(Boolean(form?.saved) && rule && !isDirty(draft, rule));

  /** @type {import('$app/forms').SubmitFunction} */
  const turnOff =
    () =>
    async ({ update }) => {
      await update({ reset: false });
    };

  /** @type {import('$app/forms').SubmitFunction} */
  const save = () => {
    busy = true;
    const rows = sentRows(draft);
    return async ({ update }) => {
      sent = rows;
      await update({ reset: false });
      busy = false;
      await tick();
      /** @type {HTMLElement | null} */ (
        document.querySelector('.au-editor [aria-invalid="true"]:not([role="group"])')
      )?.focus();
    };
  };
</script>

<PageHeader title={rule?.name || 'New rule'}>
  {#snippet crumb()}<AutomationCrumb />{/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad au-editor">
    {#if rule && status}
      <div class="au-strip">
        <div class="au-strip-main">
          <Pill tone={status.tone} dot>{status.label}</Pill>
          {#if rule.owner}
            <span class="v2-sub">
              {ownerName ? `Switched on by ${ownerName}` : 'Switched on'}
            </span>
          {/if}
          <a
            class="v2-sub au-runs"
            href={resolve(asInternalPath(`/settings/automation/${rule.id}/runs`))}
          >
            Run history
          </a>
          {#if rule.is_active}
            <form method="POST" action="?/switchOff" use:enhance={turnOff} class="au-off">
              <button type="submit" class="v2-btn v2-btn-sm">Switch off</button>
            </form>
          {/if}
        </div>
        {#if held}
          <div class="au-held">
            <NextAction
              label="Paused"
              tone="rust"
              text={modulePausedNote({ name: rule.name, status_text: row.status_text })}
              action="Open Modules"
              href="/settings/apps"
            />
          </div>
        {:else if row?.status_text && row.status_text !== status.label}
          <p class="v2-sub au-strip-text">{row.status_text}</p>
        {/if}
        {#if form?.switchOff?.general}
          <p class="v2-error" role="alert">{form.switchOff.general}</p>
        {/if}
      </div>
    {/if}

    <form method="POST" action="?/save" use:enhance={save}>
      <fieldset class="au-fields" disabled={held}>
        <div class="v2-field">
          <label for="rule-name">Name</label>
          <input
            id="rule-name"
            class="v2-input"
            maxlength="120"
            autocomplete="off"
            bind:value={draft.name}
            aria-invalid={errors.rows.name ? 'true' : undefined}
            aria-describedby={errors.rows.name ? 'rule-name-error' : undefined}
          />
          {#if errors.rows.name}<p class="v2-error" id="rule-name-error">{errors.rows.name}</p>{/if}
        </div>

        <section class="v2-card au-sec" aria-labelledby="au-when">
          <h2 class="v2-label" id="au-when">When</h2>
          <TriggerSection
            {catalogue}
            bind:draft
            fixed={Boolean(rule)}
            error={errors.rows.trigger ?? null}
          />
        </section>

        <section class="v2-card au-sec" aria-labelledby="au-if">
          <h2 class="v2-label" id="au-if">Only if</h2>
          <ConditionRows
            {catalogue}
            {object}
            event={draft.trigger.event}
            bind:match={draft.match}
            bind:conditions={draft.conditions}
            errors={{
              match: errors.rows.match ?? null,
              list: errors.rows.conditions ?? null,
              rows: errors.conditions
            }}
          />
        </section>

        <section class="v2-card au-sec" aria-labelledby="au-then">
          <h2 class="v2-label" id="au-then">Then</h2>
          <ActionRows
            {catalogue}
            {object}
            bind:actions={draft.actions}
            errors={{ list: errors.rows.actions ?? null, rows: errors.actions }}
          />
        </section>
      </fieldset>

      <input type="hidden" name="rule" value={JSON.stringify(draft)} />

      {#if errors.general}
        <div class="au-general">
          <NextAction label="Not saved" text={errors.general} tone="rust" />
        </div>
      {/if}

      {#if !held}
        <div class="au-buttons">
          <button
            type="submit"
            class={switchTo ? 'v2-btn' : 'v2-btn v2-btn-primary'}
            disabled={busy}
          >
            Save
          </button>
          {#if switchTo}
            <button
              type="submit"
              name="switch_on"
              value="true"
              class="v2-btn v2-btn-primary"
              disabled={busy}
            >
              {switchTo}
            </button>
          {/if}
          {#if saved}<span class="v2-sub" role="status">Saved.</span>{/if}
        </div>
      {/if}
    </form>

    {#if rule}
      {#if !held}<TryPanel {rule} {dirty} {form} />{/if}
      <div class="au-delete">
        {#if form?.remove?.general}
          <p class="v2-error" role="alert">{form.remove.general}</p>
        {/if}
        <ConfirmAction
          action="?/remove"
          label="Delete rule"
          confirmLabel="Delete permanently"
          explain="Its run history goes too."
        />
      </div>
    {:else}
      <p class="v2-hint au-try-new">Save the rule to try it on a record.</p>
    {/if}
  </div>
</div>

<style>
  .au-editor {
    max-width: 880px;
    padding-top: 16px;
    padding-bottom: 32px;
  }
  .au-sec {
    padding: 12px 15px 14px;
    margin-bottom: 14px;
  }
  .au-sec h2 {
    margin: 0;
  }
  .au-strip {
    margin-bottom: 14px;
  }
  .au-held {
    margin-top: 10px;
  }
  .au-fields {
    border: 0;
    margin: 0;
    padding: 0;
    min-width: 0;
  }
  .au-strip-main {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px;
  }
  .au-strip-text {
    margin: 4px 0 0;
  }
  .au-off {
    margin-left: auto;
  }
  .au-delete {
    margin-top: 28px;
    padding-top: 14px;
    border-top: 1px solid var(--v2-line-soft);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .au-try-new {
    margin-top: 14px;
  }
  .au-general {
    margin-bottom: 12px;
  }
  .au-buttons {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  @media (max-width: 768px) {
    .au-buttons .v2-btn {
      flex: 1 1 100%;
      justify-content: center;
      min-height: 44px;
    }
    .au-off,
    .au-off .v2-btn {
      min-height: 44px;
    }
    .au-delete :global(.v2-btn) {
      min-height: 44px;
    }
    .au-editor .v2-field :global(.v2-input) {
      min-height: 44px;
    }
  }
</style>
