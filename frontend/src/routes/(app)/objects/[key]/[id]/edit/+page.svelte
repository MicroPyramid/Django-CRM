<script>
  import { enhance } from '$app/forms';
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import RecordFieldInputs from '#lib/v2/components/RecordFieldInputs.svelte';
  import { TriangleAlert } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form: result } = $props();

  let def = $derived(data.definition);
  let record = $derived(data.record);
  let busy = $state(false);
  let recordPath = $derived(`/objects/${def.key}/${record.id}`);

  // What was typed comes back after a refusal.
  let typed = $derived(result?.values ?? {});
  let fields = $derived(
    data.fields.map((/** @type {any} */ f) => {
      const v = typed.custom_fields?.[f.key];
      if (!typed.custom_fields || !(f.key in typed.custom_fields)) return f;
      return { ...f, value: f.field_type === 'checkbox' ? Boolean(v) : v == null ? '' : String(v) };
    })
  );
  let linkFields = $derived(data.linkFields);
</script>

<PageHeader title="Edit {record.name}" center>
  {#snippet crumb()}
    <a href={resolve(asInternalPath(`/objects/${def.key}`))}>{def.label_plural}</a> ›
    <a href={resolve(asInternalPath(recordPath))}>{record.name}</a> ›
  {/snippet}
</PageHeader>

<div class="v2-scroll v2-pad" style="padding-top:18px">
  <form
    class="v2-form"
    method="POST"
    action="?/save"
    use:enhance={() => {
      busy = true;
      return async ({ update }) => {
        await update({ reset: false });
        busy = false;
      };
    }}
  >
    {#if result?.error}
      <div
        class="v2-next"
        style="background:color-mix(in srgb, var(--v2-rust) 9%, transparent);border-color:color-mix(in srgb, var(--v2-rust) 28%, transparent);margin-bottom:18px"
        role="alert"
      >
        <TriangleAlert size={17} style="color:var(--v2-rust);flex:none" />
        <div class="v2-next-body">
          <div style="font-weight:600">The server refused this record</div>
          <div class="v2-sub" style="margin-top:2px;white-space:pre-line">{result.error}</div>
        </div>
      </div>
    {/if}

    <div class="v2-field">
      <label for="f-name">{def.name_label}</label>
      <input
        id="f-name"
        name="name"
        class="v2-input"
        required
        maxlength="255"
        value={typed.name ?? record.name}
      />
    </div>

    <RecordFieldInputs
      {fields}
      {linkFields}
      people={data.people}
      assignees={record.assigned_to}
      edit
    />

    <div class="actions">
      <button class="v2-btn v2-btn-primary" type="submit" disabled={busy}>Save</button>
      <a class="v2-btn" href={resolve(asInternalPath(recordPath))}>Cancel</a>
    </div>
  </form>
</div>

<style>
  .actions {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-top: 22px;
    padding-bottom: 40px;
  }
</style>
