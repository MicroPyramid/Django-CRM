<script>
  import { withStored } from '#lib/v2/automation.js';

  /**
   * One value in a rule, drawn by its kind (`valueKind`, or the field's type
   * when an action sets it). A stored value the options no longer carry stays
   * selected and marked, so saving never drops it.
   *
   * @type {{
   *   field: { key: string, label: string, type: string, choices: any[] } | null,
   *   kind: string,
   *   value: any,
   *   people: { id: string, name: string }[],
   *   settableOnly?: boolean,
   *   lostLabel?: (value: any) => string | undefined,
   *   id: string,
   *   label?: string,
   *   invalid?: boolean,
   *   describedby?: string
   * }}
   */
  let {
    field,
    kind,
    value = $bindable(),
    people = [],
    settableOnly = false,
    lostLabel = undefined,
    id,
    label = 'Value',
    invalid = false,
    describedby = undefined
  } = $props();

  let choices = $derived(
    withStored(
      (field?.choices ?? []).filter((/** @type {any} */ c) => !settableOnly || c.settable),
      value,
      { label: lostLabel }
    )
  );
  let groups = $derived.by(() => {
    /** @type {{ group: string, options: any[] }[]} */
    const out = [];
    for (const option of choices) {
      const group = option.group ?? '';
      const bucket = out.find((g) => g.group === group);
      if (bucket) bucket.options.push(option);
      else out.push({ group, options: [option] });
    }
    return out;
  });
  let members = $derived(
    withStored(
      people.map((p) => ({ value: p.id, label: p.name })),
      value,
      { person: true }
    )
  );
  let picked = $derived(Array.isArray(value) ? value : []);

  /**
   * Ticked values in the order the list shows them.
   * @param {{ value: string }[]} options @param {string} option @param {boolean} on
   */
  function toggle(options, option, on) {
    value = options.map((o) => o.value).filter((v) => (v === option ? on : picked.includes(v)));
  }
</script>

{#if kind === 'text'}
  <input
    {id}
    class="v2-input"
    type="text"
    autocomplete="off"
    bind:value
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  />
{:else if kind === 'number'}
  <input
    {id}
    class="v2-input"
    type="number"
    step="any"
    inputmode="decimal"
    bind:value
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  />
{:else if kind === 'date'}
  <input
    {id}
    class="v2-input"
    type="date"
    bind:value
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  />
{:else if kind === 'choice'}
  <select
    {id}
    class="v2-input"
    bind:value
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  >
    <option value={null}>Choose an option</option>
    {#each groups as g (g.group)}
      {#if g.group}
        <optgroup label={g.group}>
          {#each g.options as o (o.value)}<option value={o.value}>{o.label}</option>{/each}
        </optgroup>
      {:else}
        {#each g.options as o (o.value)}<option value={o.value}>{o.label}</option>{/each}
      {/if}
    {/each}
  </select>
{:else if kind === 'boolean'}
  <select
    {id}
    class="v2-input"
    bind:value
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  >
    <option value={null}>Choose Yes or No</option>
    <option value={true}>Yes</option>
    <option value={false}>No</option>
  </select>
{:else if kind === 'person'}
  <select
    {id}
    class="v2-input"
    bind:value
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  >
    <option value={null}>Choose a person</option>
    {#each members as m (m.value)}<option value={m.value}>{m.label}</option>{/each}
  </select>
{:else if kind === 'choices' || kind === 'people'}
  {@const options = kind === 'people' ? members : choices}
  <!-- ARIA lists no aria-invalid on a group, so each box carries it too. -->
  <!-- svelte-ignore a11y_role_supports_aria_props -->
  <div
    {id}
    class="rv-list"
    role="group"
    aria-label={label}
    aria-invalid={invalid ? 'true' : undefined}
    aria-describedby={describedby}
  >
    {#each options as o, i (o.value)}
      <label class="rv-box">
        <input
          type="checkbox"
          id="{id}-{i}"
          aria-invalid={invalid ? 'true' : undefined}
          checked={picked.includes(o.value)}
          onchange={(e) => toggle(options, o.value, e.currentTarget.checked)}
        />
        <span>{o.group ? `${o.group}: ${o.label}` : o.label}</span>
      </label>
    {/each}
  </div>
{/if}

<style>
  .rv-list {
    display: flex;
    flex-direction: column;
    max-height: 220px;
    overflow-y: auto;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    padding: 2px 10px;
    background: var(--v2-card);
  }
  .rv-list[aria-invalid='true'] {
    border-color: var(--v2-rust);
  }
  /* 44px so each box is a thumb-sized target on a phone. */
  .rv-box {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 44px;
    font-size: 13px;
  }
  .rv-box input {
    width: 18px;
    height: 18px;
    flex: none;
  }
</style>
