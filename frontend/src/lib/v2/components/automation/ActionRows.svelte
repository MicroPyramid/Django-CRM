<script>
  import { tick } from 'svelte';
  import { ArrowDown, ArrowUp, Plus, X } from '@lucide/svelte';
  import { actionOptions, actionTypes, blankAction, moveItem } from '#lib/v2/automation.js';
  import ActionFields from './ActionFields.svelte';

  /**
   * THEN: the actions in the order they run. `errors.rows[i]` is the server's
   * message for the row now shown at `i`; `errors.list` is about the list.
   *
   * @type {{
   *   catalogue: any,
   *   object: any,
   *   actions: any[],
   *   errors?: { list?: string | null, rows?: (string | null)[] }
   * }}
   */
  let { catalogue, object, actions = $bindable(), errors = {} } = $props();

  /** @type {HTMLButtonElement | undefined} */
  let addButton = $state();

  let limit = $derived(catalogue?.limits?.actions ?? Infinity);
  const EMPTY = 'Add at least one action.';

  /** @param {number} at @param {string} type */
  async function retype(at, type) {
    actions[at] = blankAction(type);
    await tick();
    document.getElementById(`act-${at}-type`)?.focus();
  }

  async function add() {
    const types = actionTypes(catalogue, object);
    if (!types.length) return;
    actions = [...actions, blankAction(types.includes('create_task') ? 'create_task' : types[0])];
    await tick();
    document.getElementById(`act-${actions.length - 1}-type`)?.focus();
  }

  /** @param {number} at */
  async function remove(at) {
    actions = actions.filter((_, i) => i !== at);
    await tick();
    addButton?.focus();
  }

  /** @param {number} at @param {number} direction */
  async function move(at, direction) {
    actions = moveItem(actions, at, direction);
    const to = at + direction;
    await tick();
    const same = document.getElementById(`act-${to}-${direction < 0 ? 'up' : 'down'}`);
    const other = document.getElementById(`act-${to}-${direction < 0 ? 'down' : 'up'}`);
    (same && !(/** @type {HTMLButtonElement} */ (same).disabled) ? same : other)?.focus();
  }
</script>

{#if !actions.length && !errors.list}
  <p class="v2-hint ar-none">{EMPTY}</p>
{/if}
{#if errors.list}
  <p class="v2-error" role="alert">{errors.list}</p>
{/if}

{#each actions as action, i (action)}
  {@const error = errors.rows?.[i] ?? null}
  <div class="ar-item">
    <div class="ar-head">
      <span class="ar-num" aria-hidden="true">{i + 1}.</span>
      <select
        id="act-{i}-type"
        class="v2-input ar-type"
        aria-label="Action {i + 1} type"
        value={action.type}
        onchange={(e) => retype(i, e.currentTarget.value)}
        aria-invalid={error ? 'true' : undefined}
        aria-describedby={error ? `act-${i}-error` : undefined}
      >
        {#each actionOptions(catalogue, object, action.type) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
      <div class="ar-btns">
        <button
          type="button"
          id="act-{i}-up"
          class="v2-btn ar-btn"
          aria-label="Move action {i + 1} up"
          disabled={i === 0}
          onclick={() => move(i, -1)}
        >
          <ArrowUp />
        </button>
        <button
          type="button"
          id="act-{i}-down"
          class="v2-btn ar-btn"
          aria-label="Move action {i + 1} down"
          disabled={i === actions.length - 1}
          onclick={() => move(i, 1)}
        >
          <ArrowDown />
        </button>
        <button
          type="button"
          class="v2-btn ar-btn"
          aria-label="Remove action {i + 1}"
          onclick={() => remove(i)}
        >
          <X />
        </button>
      </div>
    </div>
    <div class="ar-body">
      <ActionFields
        {catalogue}
        {object}
        bind:action={actions[i]}
        errorId={error ? `act-${i}-error` : undefined}
      />
    </div>
    {#if error}<p class="v2-error" id="act-{i}-error">{error}</p>{/if}
  </div>
{/each}

<div class="ar-foot">
  <button
    bind:this={addButton}
    type="button"
    class="v2-btn ar-add"
    onclick={add}
    disabled={actions.length >= limit}
  >
    <Plus />Add action
  </button>
  {#if actions.length >= limit}
    <p class="v2-hint">A rule can have at most {limit} actions.</p>
  {/if}
</div>

<style>
  .ar-none {
    margin-top: 8px;
  }
  .ar-item {
    padding: 10px 0;
  }
  .ar-item + .ar-item {
    border-top: 1px dashed var(--v2-line);
  }
  .ar-head {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 8px;
    align-items: center;
  }
  .ar-num {
    font-weight: 600;
    min-width: 1.4em;
  }
  .ar-type {
    width: auto;
    max-width: 320px;
  }
  .ar-btns {
    display: flex;
    gap: 4px;
    justify-self: end;
  }
  .ar-btn {
    min-width: 44px;
    min-height: 44px;
    padding: 0;
    justify-content: center;
  }
  .ar-body {
    margin-top: 8px;
    padding-left: calc(1.4em + 8px);
  }
  .ar-foot {
    margin-top: 6px;
  }
  .ar-add {
    min-height: 44px;
  }
  @media (max-width: 768px) {
    .ar-head {
      grid-template-columns: auto minmax(0, 1fr);
      grid-template-areas:
        'num type'
        'btns btns';
    }
    .ar-num {
      grid-area: num;
    }
    .ar-type {
      grid-area: type;
      width: 100%;
      max-width: none;
      min-height: 44px;
    }
    .ar-btns {
      grid-area: btns;
      justify-self: stretch;
    }
    .ar-btn {
      flex: 1;
    }
    .ar-body {
      padding-left: 0;
    }
  }
</style>
