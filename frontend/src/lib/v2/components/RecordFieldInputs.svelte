<script>
  /**
   * The inputs below a record's name, shared by the new and edit pages: one
   * per custom field, one picker per link field, and the assignees (only when
   * `people` is given). The `__was` inputs tell the server what the page
   * showed, so it sends only a change. `typed` restores what a refused save
   * carried; `errors` holds the server's message per field key. `form` ties
   * the custom field inputs to a form they sit outside of, by its id.
   */
  import { inactiveOptionLabel, missingOptions } from '#lib/v2/pickers.js';
  import RecordPicker from '#lib/v2/components/RecordPicker.svelte';

  /**
   * @type {{
   *   fields: any[],
   *   linkFields?: any[],
   *   people?: { id: string, name: string }[],
   *   assignees?: { id: string, name: string }[],
   *   edit?: boolean,
   *   typed?: Record<string, any> | null,
   *   errors?: Record<string, string> | null,
   *   heading?: string,
   *   form?: string
   * }}
   */
  let {
    fields,
    linkFields = [],
    people,
    assignees = [],
    edit = false,
    typed = null,
    errors = null,
    heading = '',
    form: formId = undefined
  } = $props();

  let shown = $derived(
    fields.map((f) => {
      if (!typed || !(f.key in typed)) return f;
      const v = typed[f.key];
      return { ...f, value: f.field_type === 'checkbox' ? Boolean(v) : v == null ? '' : String(v) };
    })
  );
  let stale = $derived(missingOptions(people ?? [], assignees));
  let assigned = $derived(new Set(assignees.map((a) => a.id)));
  let was = $derived(assignees.map((a) => a.id).join(','));
</script>

<input type="hidden" name="cf__rendered" form={formId} value={fields.map((f) => f.key).join(',')} />

{#if heading && fields.length > 0}
  <div class="v2-label ri-heading">{heading}</div>
{/if}

{#each shown as f (f.key)}
  {@const problem = errors?.[f.key] ?? ''}
  <div class="v2-field">
    {#if f.field_type === 'checkbox'}
      <label class="ri-check">
        <input
          type="checkbox"
          name="cf_{f.key}"
          form={formId}
          checked={f.value}
          aria-invalid={problem ? 'true' : undefined}
        />
        <span>{f.label}</span>
      </label>
    {:else}
      <label for="cf-{f.key}"
        >{f.label}{#if f.is_required}<span class="ri-req">required</span>{/if}</label
      >
      {#if f.field_type === 'textarea'}
        <textarea
          id="cf-{f.key}"
          name="cf_{f.key}"
          form={formId}
          class="v2-input"
          rows="4"
          required={f.is_required}
          aria-invalid={problem ? 'true' : undefined}>{f.value}</textarea
        >
      {:else if f.field_type === 'dropdown'}
        <select
          id="cf-{f.key}"
          name="cf_{f.key}"
          form={formId}
          class="v2-input"
          value={f.value}
          required={f.is_required}
          aria-invalid={problem ? 'true' : undefined}
        >
          <option value="">None</option>
          {#each f.options as o (o.value)}
            <option value={o.value}>{o.label}</option>
          {/each}
        </select>
      {:else}
        <input
          id="cf-{f.key}"
          name="cf_{f.key}"
          form={formId}
          class="v2-input"
          class:v2-num={f.field_type === 'number'}
          type={f.field_type === 'number' ? 'number' : f.field_type === 'date' ? 'date' : 'text'}
          step={f.field_type === 'number' ? 'any' : undefined}
          value={f.value}
          required={f.is_required}
          aria-invalid={problem ? 'true' : undefined}
        />
      {/if}
    {/if}
    {#if problem}<p class="v2-error">{problem}</p>{/if}
  </div>
{/each}

{#each linkFields as l (l.key)}
  <div class="v2-field">
    <span class="ri-label" id="lf-{l.key}">{l.label}</span>
    {#if l.readOnly}
      <p>
        {l.records.map((r) => r.name).join(', ')}{#if l.hidden > 0}
          {l.records.length > 0 ? ' and ' : ''}{l.hidden} you can't open{/if}
      </p>
    {:else}
      <input
        type="hidden"
        name="link_{l.key}__was"
        value={edit ? l.records.map((r) => r.id).join(',') : ''}
      />
      <RecordPicker
        name="link_{l.key}"
        target={l.target}
        multiple={l.many}
        selected={l.records}
        label={l.label}
      />
      {#if l.many && l.hidden > 0}
        <p class="v2-hint">and {l.hidden} you can't open</p>
      {/if}
    {/if}
  </div>
{/each}

{#if people}
  <fieldset class="v2-field ri-people">
    <legend class="ri-label">Assigned to</legend>
    {#if edit}<input type="hidden" name="assigned_to__was" value={was} />{/if}
    {#each stale as s (s.id)}
      <label class="ri-person">
        <input type="checkbox" name="assigned_to" value={s.id} checked />
        <span>{inactiveOptionLabel(s.name)}</span>
      </label>
    {/each}
    {#each people as p (p.id)}
      <label class="ri-person">
        <input type="checkbox" name="assigned_to" value={p.id} checked={assigned.has(p.id)} />
        <span>{p.name}</span>
      </label>
    {/each}
    {#if people.length === 0 && stale.length === 0}
      <p class="v2-hint">No one to assign.</p>
    {/if}
  </fieldset>
{/if}

<style>
  .ri-heading {
    margin: 22px 0 10px;
  }
  .ri-req {
    margin-left: 6px;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--v2-clay);
  }
  .ri-label {
    display: block;
    font-size: 12.5px;
    font-weight: 600;
    margin-bottom: 5px;
    padding: 0;
  }
  .ri-people {
    border: 0;
    padding: 0;
    min-width: 0;
  }
  .ri-check,
  .ri-person {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 44px;
    font-size: 13.5px;
    cursor: pointer;
  }
  .ri-check input,
  .ri-person input {
    width: 18px;
    height: 18px;
    flex: none;
  }
  .ri-person {
    font-weight: 400;
  }
  .ri-person span {
    overflow-wrap: anywhere;
  }
</style>
