<script>
  import { untrack } from 'svelte';
  import {
    objectOf,
    fieldOf,
    triggerFields,
    withStored,
    switchObject,
    changeHint
  } from '#lib/v2/automation.js';
  import RuleValueInput from './RuleValueInput.svelte';

  /**
   * WHEN: the object (chosen on a new rule, fixed after), created or updated,
   * and on an update the field and, if asked, the value it moves into.
   *
   * @type {{ catalogue: any, draft: any, fixed?: boolean, error?: string | null }}
   */
  let { catalogue, draft = $bindable(), fixed = false, error = null } = $props();

  let object = $derived(objectOf(catalogue, draft.object_key));
  let field = $derived(draft.trigger.field ? fieldOf(object, draft.trigger.field) : null);
  let objects = $derived([
    ...(catalogue?.objects ?? []).filter((/** @type {any} */ o) => !o.key.startsWith('obj:')),
    ...(catalogue?.objects ?? []).filter((/** @type {any} */ o) => o.key.startsWith('obj:'))
  ]);
  let fields = $derived(
    withStored(
      triggerFields(object).map((f) => ({ value: f.key, label: f.label })),
      draft.trigger.field
    )
  );
  let noun = $derived(object?.label ?? `${draft.object_key} (no longer available)`);
  let hint = $derived(changeHint(field, draft.trigger.to));
  // The box can be ticked before a value is chosen; the draft holds `to` only once there is one.
  let limited = $state(untrack(() => draft.trigger.to !== undefined && draft.trigger.to !== null));

  /** @param {string} key */
  function chooseObject(key) {
    limited = false;
    draft = switchObject(draft, catalogue, key);
  }

  /** @param {string} event */
  function chooseEvent(event) {
    limited = false;
    draft.trigger = { event };
  }

  /** @param {string} key */
  function chooseField(key) {
    limited = false;
    draft.trigger = key ? { event: 'updated', field: key } : { event: 'updated' };
  }

  /** @param {boolean} on */
  function limit(on) {
    limited = on;
    if (!on) delete draft.trigger.to;
  }

  /** An empty "changes to" is no "changes to". @param {any} value */
  function setTo(value) {
    const empty = value === null || value === undefined || value === '' || Number.isNaN(value);
    if (empty) delete draft.trigger.to;
    else draft.trigger.to = value;
  }
</script>

<div class="tr-line">
  {#if fixed}
    <strong>{noun}</strong>
  {:else}
    <select
      class="v2-input tr-ctl"
      aria-label="Record type"
      value={draft.object_key}
      onchange={(e) => chooseObject(e.currentTarget.value)}
    >
      {#each objects as o (o.key)}<option value={o.key}>{o.label}</option>{/each}
    </select>
  {/if}
  <select
    class="v2-input tr-ctl"
    aria-label="When it runs"
    value={draft.trigger.event}
    onchange={(e) => chooseEvent(e.currentTarget.value)}
    aria-invalid={error ? 'true' : undefined}
    aria-describedby={error ? 'trigger-error' : undefined}
  >
    <option value="created">is created</option>
    <option value="updated">is updated</option>
  </select>
</div>

{#if draft.trigger.event === 'updated'}
  <div class="tr-line">
    <span>and</span>
    <select
      class="v2-input tr-ctl"
      aria-label="Which field changes"
      value={draft.trigger.field ?? ''}
      onchange={(e) => chooseField(e.currentTarget.value)}
      aria-invalid={error ? 'true' : undefined}
      aria-describedby={error ? 'trigger-error' : undefined}
    >
      <option value="">any field</option>
      {#each fields as o (o.value)}<option value={o.value}>{o.label}</option>{/each}
    </select>
    <span>changes</span>
  </div>

  {#if draft.trigger.field}
    <label class="tr-check">
      <input type="checkbox" checked={limited} onchange={(e) => limit(e.currentTarget.checked)} />
      only when it changes to
    </label>
    {#if limited}
      <div class="tr-to">
        {#if field}
          <RuleValueInput
            {field}
            kind={field.type}
            bind:value={() => draft.trigger.to ?? null, setTo}
            people={catalogue?.people ?? []}
            id="trigger-to"
            label="Changes to"
            invalid={Boolean(error)}
            describedby={error ? 'trigger-error' : undefined}
          />
        {:else if draft.trigger.to !== undefined}
          <span class="v2-muted">{String(draft.trigger.to)}</span>
        {/if}
        {#if hint}<p class="v2-hint">{hint}</p>{/if}
      </div>
    {/if}
  {/if}
{/if}

{#if error}
  <p class="v2-error" id="trigger-error">{error}</p>
{/if}

<style>
  .tr-line {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    font-size: 13.5px;
  }
  .tr-ctl {
    width: auto;
    max-width: 100%;
  }
  .tr-check {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    min-height: 44px;
    margin-top: 4px;
    font-size: 13.5px;
  }
  .tr-check input {
    width: 18px;
    height: 18px;
  }
  .tr-to {
    max-width: 380px;
  }
  @media (max-width: 768px) {
    .tr-ctl {
      flex: 1 1 auto;
      min-width: 0;
      min-height: 44px;
    }
    .tr-to {
      max-width: none;
    }
    .tr-to :global(.v2-input) {
      min-height: 44px;
    }
  }
</style>
