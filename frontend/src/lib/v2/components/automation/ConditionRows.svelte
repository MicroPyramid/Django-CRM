<script>
  import { tick } from 'svelte';
  import { Plus, X } from '@lucide/svelte';
  import {
    fieldOf,
    operatorsFor,
    operatorLabel,
    valueKind,
    withStored,
    blankCondition,
    keptValue
  } from '#lib/v2/automation.js';
  import RuleValueInput from './RuleValueInput.svelte';

  /**
   * ONLY IF: whether all or any of the conditions must hold, and the rows.
   * `errors.rows[i]` is the server's message for the row now shown at `i`.
   *
   * @type {{
   *   catalogue: any,
   *   object: any,
   *   event: string,
   *   match: string,
   *   conditions: any[],
   *   errors?: { match?: string | null, list?: string | null, rows?: (string | null)[] }
   * }}
   */
  let {
    catalogue,
    object,
    event,
    match = $bindable(),
    conditions = $bindable(),
    errors = {}
  } = $props();

  /** @type {HTMLButtonElement | undefined} */
  let addButton = $state();

  let limit = $derived(catalogue?.limits?.conditions ?? Infinity);
  let fields = $derived(
    (object?.fields ?? []).map((/** @type {any} */ f) => ({ value: f.key, label: f.label }))
  );

  /** The operators offered, plus a stored one they no longer include. @param {any} cond @param {any} field */
  function operators(cond, field) {
    const offered = operatorsFor(catalogue, field, event).map((op) => ({
      value: op,
      label: operatorLabel(op, field?.type)
    }));
    if (!cond.op || offered.some((o) => o.value === cond.op)) return offered;
    // With the field gone, the field is what is marked; the test reads as it was.
    const label = field
      ? `${operatorLabel(cond.op, field.type)} (no longer available)`
      : operatorLabel(cond.op);
    return [...offered, { value: cond.op, label }];
  }

  /** @param {any} cond @param {string} key */
  function chooseField(cond, key) {
    cond.field = key;
    cond.op = operatorsFor(catalogue, fieldOf(object, key), event)[0] ?? '';
    cond.value = null;
  }

  /** @param {any} cond @param {string} op */
  function chooseOp(cond, op) {
    cond.value = keptValue(fieldOf(object, cond.field), cond.op, op, cond.value);
    cond.op = op;
  }

  async function add() {
    conditions = [...conditions, blankCondition()];
    await tick();
    document.getElementById(`cond-${conditions.length - 1}-field`)?.focus();
  }

  /** @param {number} at */
  async function remove(at) {
    conditions = conditions.filter((_, i) => i !== at);
    await tick();
    addButton?.focus();
  }

  /** A stored value whose field is gone, as text. @param {any} value */
  const asText = (value) => (Array.isArray(value) ? value.join(', ') : String(value));
</script>

{#if conditions.length}
  <select
    class="v2-input cr-match"
    aria-label="How the conditions combine"
    bind:value={match}
    aria-invalid={errors.match ? 'true' : undefined}
  >
    <option value="all">all of these hold</option>
    <option value="any">any of these hold</option>
  </select>
  {#if errors.match}<p class="v2-error">{errors.match}</p>{/if}
{:else}
  <p class="v2-hint cr-none">With no conditions it runs every time it is set off.</p>
{/if}

{#each conditions as cond, i (cond)}
  {@const field = fieldOf(object, cond.field)}
  {@const error = errors.rows?.[i] ?? null}
  <div class="cr-item">
    <div class="cr-row">
      <select
        id="cond-{i}-field"
        class="v2-input cr-field"
        aria-label="Condition {i + 1} field"
        value={cond.field}
        onchange={(e) => chooseField(cond, e.currentTarget.value)}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error ? `cond-${i}-error` : undefined}
      >
        {#if !cond.field}<option value="">Choose a field</option>{/if}
        {#each withStored(fields, cond.field) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
      {#if cond.field}
        <select
          class="v2-input cr-op"
          aria-label="Condition {i + 1} test"
          value={cond.op}
          onchange={(e) => chooseOp(cond, e.currentTarget.value)}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? `cond-${i}-error` : undefined}
        >
          {#if !cond.op}<option value="">Choose a test</option>{/if}
          {#each operators(cond, field) as o (o.value)}
            <option value={o.value}>{o.label}</option>
          {/each}
        </select>
      {/if}
      <div class="cr-value">
        {#if field && cond.op}
          <RuleValueInput
            {field}
            kind={valueKind(field, cond.op)}
            bind:value={cond.value}
            people={catalogue?.people ?? []}
            id="cond-{i}-value"
            label="Condition {i + 1} value"
            invalid={Boolean(error)}
            describedby={error ? `cond-${i}-error` : undefined}
          />
        {:else if cond.value !== null && cond.value !== undefined}
          <span class="v2-muted cr-stored">{asText(cond.value)}</span>
        {/if}
      </div>
      <button
        type="button"
        class="v2-btn cr-remove"
        aria-label="Remove condition {i + 1}"
        onclick={() => remove(i)}
      >
        <X />
      </button>
    </div>
    {#if cond.field && !field}
      <p class="v2-muted cr-lost">This field is no longer available. Choose another.</p>
    {/if}
    {#if error}<p class="v2-error" id="cond-{i}-error">{error}</p>{/if}
  </div>
{/each}

<div class="cr-foot">
  <button
    bind:this={addButton}
    type="button"
    class="v2-btn cr-add"
    onclick={add}
    disabled={conditions.length >= limit}
  >
    <Plus />Add condition
  </button>
  {#if conditions.length >= limit}
    <p class="v2-hint">A rule can have at most {limit} conditions.</p>
  {/if}
  {#if errors.list}<p class="v2-error">{errors.list}</p>{/if}
</div>

<style>
  .cr-match {
    width: auto;
    margin-top: 8px;
  }
  .cr-none {
    margin-top: 8px;
  }
  .cr-item {
    padding: 10px 0;
  }
  .cr-item + .cr-item {
    border-top: 1px dashed var(--v2-line);
  }
  .cr-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 0.9fr) minmax(0, 1.3fr) 44px;
    grid-template-areas: 'field op value remove';
    gap: 8px;
    align-items: start;
  }
  .cr-field {
    grid-area: field;
  }
  .cr-op {
    grid-area: op;
  }
  .cr-value {
    grid-area: value;
    min-width: 0;
  }
  .cr-remove {
    grid-area: remove;
    min-width: 44px;
    min-height: 44px;
    padding: 0;
    justify-content: center;
  }
  .cr-stored {
    display: block;
    padding-top: 10px;
    overflow-wrap: anywhere;
  }
  .cr-lost {
    margin: 6px 0 0;
  }
  .cr-foot {
    margin-top: 6px;
  }
  .cr-add {
    min-height: 44px;
  }
  @media (max-width: 768px) {
    .cr-row {
      grid-template-columns: minmax(0, 1fr) 44px;
      grid-template-areas:
        'field remove'
        'op op'
        'value value';
    }
    .cr-row :global(.v2-input),
    .cr-match {
      min-height: 44px;
    }
  }
</style>
