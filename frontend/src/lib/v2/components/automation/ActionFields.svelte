<script>
  import {
    fieldOf,
    targetsFor,
    recipientsFor,
    taskAudience,
    withStored,
    applyTarget,
    applyField,
    applyAssignTo,
    applyClear,
    applyMode,
    isClearing,
    setActionValue,
    shownValue,
    recipientLabel,
    replacePerson
  } from '#lib/v2/automation.js';
  import RuleValueInput from './RuleValueInput.svelte';

  /**
   * The fields of one action, by its type. A stored target, field, person,
   * recipient or endpoint the catalogue lost stays selected and marked.
   *
   * @type {{ catalogue: any, object: any, action: any, errorId?: string }}
   */
  let { catalogue, object, action = $bindable(), errorId = undefined } = $props();

  const uid = $props.id();
  const people = $derived(catalogue?.people ?? []);

  // What the action held before "Clear it instead" was ticked.
  let previous = $state();
  let clear = $derived(isClearing(action));

  let targets = $derived(targetsFor(catalogue, object));
  let target = $derived(targets.find((t) => t.value === action.target) ?? null);
  let fieldOptions = $derived(
    (target?.object?.fields ?? [])
      .filter((/** @type {any} */ f) => f.settable)
      .map((/** @type {any} */ f) => ({ value: f.key, label: f.label }))
  );
  let field = $derived(fieldOf(target?.object, action.field));

  let recipients = $derived(recipientsFor(object));
  let recipientField = $derived({
    key: 'to',
    label: 'Who',
    type: 'choice',
    settable: true,
    choices: recipients.map((r) => ({ ...r, group: '', settable: true }))
  });
  let audience = $derived(taskAudience(object));
  let one = $derived(replacePerson(action));
  let endpoints = $derived(
    (catalogue?.endpoints ?? []).map((/** @type {any} */ e) => ({
      value: e.id,
      label: e.description
    }))
  );

  /** The single person of a replace, as the list the API stores. @param {string} id */
  function setOne(id) {
    action.people = id ? [id] : [];
  }

  /** @param {boolean} on */
  function setClear(on) {
    if (on) previous = action.value;
    applyClear(action, on, previous);
  }
</script>

{#if action.type === 'set_field'}
  <div class="af-grid">
    <div class="v2-field">
      <label for="{uid}-target">On</label>
      <select
        id="{uid}-target"
        class="v2-input"
        value={action.target}
        aria-describedby={errorId}
        onchange={(e) => applyTarget(action, e.currentTarget.value)}
      >
        {#each withStored( targets.map( (t) => ({ value: t.value, label: t.label }) ), action.target, { label: () => 'A removed link' } ) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
    </div>
    <div class="v2-field">
      <label for="{uid}-field">Set</label>
      <select
        id="{uid}-field"
        class="v2-input"
        value={action.field}
        aria-describedby={errorId}
        onchange={(e) => applyField(action, e.currentTarget.value)}
      >
        {#if !action.field}<option value="">Choose a field</option>{/if}
        {#each withStored(fieldOptions, action.field) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
    </div>
    {#if action.field}
      <div class="v2-field af-wide">
        {#if !field}
          <p class="v2-muted">This field is no longer available. Choose another.</p>
        {:else}
          {#if !clear}
            {#if field.type === 'people'}
              <span class="af-label">To</span>
            {:else}
              <label for="{uid}-value">To</label>
            {/if}
            <RuleValueInput
              {field}
              kind={field.type}
              bind:value={() => shownValue(action), (v) => setActionValue(action, v)}
              {people}
              settableOnly
              id="{uid}-value"
              label="Value to set"
              describedby={errorId}
            />
          {/if}
          <label class="af-check">
            <input
              type="checkbox"
              checked={clear}
              onchange={(e) => setClear(e.currentTarget.checked)}
            />
            <span>Clear it instead</span>
          </label>
        {/if}
      </div>
    {/if}
  </div>
{:else if action.type === 'assign'}
  <div class="af-grid">
    <div class="v2-field">
      <label for="{uid}-mode">Who</label>
      <select
        id="{uid}-mode"
        class="v2-input"
        value={action.mode}
        aria-describedby={errorId}
        onchange={(e) => applyMode(action, e.currentTarget.value)}
      >
        <option value="replace">One person</option>
        <option value="rotate">In turn</option>
      </select>
    </div>
    <div class="v2-field">
      {#if action.mode === 'rotate'}
        <RuleValueInput
          field={null}
          kind="people"
          bind:value={action.people}
          {people}
          id="{uid}-people"
          label="People in turn"
          describedby={errorId}
        />
        <p class="v2-hint">Choose 2 to 20 people; each new record goes to the next one.</p>
      {:else}
        <label for="{uid}-one">Person</label>
        <select
          id="{uid}-one"
          class="v2-input"
          value={one.id}
          aria-describedby={errorId}
          onchange={(e) => setOne(e.currentTarget.value)}
        >
          <option value="">Choose a person</option>
          {#each withStored( people.map( (/** @type {any} */ p) => ({ value: p.id, label: p.name }) ), action.people, { person: true } ) as o (o.value)}
            <option value={o.value}>{o.label}</option>
          {/each}
        </select>
        {#if one.several}
          <p class="v2-hint">One person takes exactly one. Choose who stays.</p>
        {/if}
      {/if}
    </div>
    <p class="v2-hint af-wide">Replaces current assignees.</p>
  </div>
{:else if action.type === 'create_task'}
  <div class="af-grid">
    <div class="v2-field af-wide">
      <label for="{uid}-title">Title</label>
      <input
        id="{uid}-title"
        class="v2-input"
        maxlength="200"
        autocomplete="off"
        bind:value={action.title}
        aria-describedby={errorId}
      />
      <p class="v2-hint">{'{name}'} becomes the record's name.</p>
    </div>
    <div class="v2-field">
      <label for="{uid}-due">Due in (days)</label>
      <input
        id="{uid}-due"
        class="v2-input"
        type="number"
        min="0"
        max="365"
        step="1"
        inputmode="numeric"
        bind:value={action.due_in_days}
        aria-describedby={errorId}
      />
      <p class="v2-hint">Leave empty for no due date.</p>
    </div>
    <div class="v2-field">
      <label for="{uid}-priority">Priority</label>
      <select
        id="{uid}-priority"
        class="v2-input"
        bind:value={action.priority}
        aria-describedby={errorId}
      >
        {#each withStored([{ value: 'Low', label: 'Low' }, { value: 'Medium', label: 'Medium' }, { value: 'High', label: 'High' }], action.priority) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
    </div>
    <div class="v2-field">
      <label for="{uid}-for">For</label>
      <select
        id="{uid}-for"
        class="v2-input"
        value={action.assign_to}
        aria-describedby={errorId}
        onchange={(e) => applyAssignTo(action, e.currentTarget.value)}
      >
        {#each withStored(audience, action.assign_to, { label: recipientLabel }) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
    </div>
    {#if action.assign_to === 'person'}
      <div class="v2-field">
        <label for="{uid}-person">Person</label>
        <RuleValueInput
          field={null}
          kind="person"
          bind:value={action.person}
          {people}
          id="{uid}-person"
          label="Person the task is for"
          describedby={errorId}
        />
      </div>
    {/if}
  </div>
{:else if action.type === 'notify'}
  <div class="af-grid">
    <div class="v2-field">
      <span class="af-label">Who</span>
      <RuleValueInput
        field={recipientField}
        kind="choices"
        lostLabel={recipientLabel}
        bind:value={action.to}
        {people}
        id="{uid}-to"
        label="Who to notify"
        describedby={errorId}
      />
    </div>
    <div class="v2-field">
      <span class="af-label">And these people</span>
      <RuleValueInput
        field={null}
        kind="people"
        bind:value={action.people}
        {people}
        id="{uid}-people"
        label="And these people"
        describedby={errorId}
      />
    </div>
    <div class="v2-field af-wide">
      <label for="{uid}-message">Message</label>
      <textarea
        id="{uid}-message"
        class="v2-input"
        rows="3"
        maxlength="500"
        bind:value={action.message}
        aria-describedby={errorId}></textarea>
      <p class="v2-hint">{'{name}'} becomes the record's name.</p>
    </div>
    <p class="v2-hint af-wide">In the app and by email, to active members only.</p>
  </div>
{:else if action.type === 'webhook'}
  <div class="af-grid">
    <div class="v2-field">
      <label for="{uid}-endpoint">Endpoint</label>
      <select
        id="{uid}-endpoint"
        class="v2-input"
        bind:value={action.endpoint}
        aria-describedby={errorId}
      >
        {#if !action.endpoint}<option value="">Choose an endpoint</option>{/if}
        {#each withStored( endpoints, action.endpoint, { label: () => 'An endpoint no longer available' } ) as o (o.value)}
          <option value={o.value}>{o.label}</option>
        {/each}
      </select>
    </div>
  </div>
{:else}
  <p class="v2-muted">This action is no longer available.</p>
{/if}

<style>
  .af-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px 12px;
    align-items: start;
  }
  .af-grid :global(.v2-field) {
    margin: 0;
    min-width: 0;
  }
  .af-wide {
    grid-column: 1 / -1;
  }
  .af-label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  .af-check {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 44px;
    font-size: 13px;
  }
  .af-check input {
    width: 18px;
    height: 18px;
    flex: none;
  }
  @media (max-width: 768px) {
    .af-grid {
      grid-template-columns: minmax(0, 1fr);
    }
    .af-grid :global(.v2-input) {
      min-height: 44px;
    }
  }
</style>
