<script>
  /**
   * Custom objects: org-defined record types. Admins add and manage them
   * here; members reach the records from the sidebar.
   */
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '#lib/v2/components/SettingsCrumb.svelte';
  import SettingsFormPanel from '#lib/v2/components/SettingsFormPanel.svelte';
  import StatCard from '#lib/v2/components/StatCard.svelte';
  import EmptyState from '#lib/v2/components/EmptyState.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import { suggestKey } from '#lib/v2/custom-objects.js';
  import { count } from '#lib/v2/format.js';
  import { Plus } from '@lucide/svelte';

  const OBJECT_LIMIT = 20;

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let creating = $state(false);
  let label = $state('');
  let key = $state('');
  let keyEdited = $state(false);

  let objects = $derived(data.answer.objects);
  let archived = $derived(objects.filter((/** @type {any} */ o) => !o.is_active).length);
  let canAdd = $derived(data.can_edit && data.answer.has_custom_objects);

  function openCreate() {
    label = '';
    key = '';
    keyEdited = false;
    creating = true;
  }

  /** @param {Event} event */
  function onLabel(event) {
    label = /** @type {HTMLInputElement} */ (event.currentTarget).value;
    if (!keyEdited) key = suggestKey(label, 28);
  }
</script>

<PageHeader title="Custom objects">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(objects.length - archived)}</span> in use
  {/snippet}
  {#snippet actions()}
    {#if canAdd && !creating}
      <button class="v2-btn v2-btn-primary" onclick={openCreate}><Plus />New object</button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:16px;flex:none">
  <div class="v2-stats">
    <StatCard label="Active objects" value={count(objects.length - archived)} tone="ink" />
    <StatCard label="Archived" value={count(archived)} tone="slate" />
    <StatCard
      label="Objects used"
      value={count(objects.length)}
      tone="slate"
      detail={`of ${OBJECT_LIMIT} objects`}
    />
  </div>
</div>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#if data.can_edit && !data.answer.has_custom_objects}
      <p class="v2-sub" style="font-size:12.5px;margin:0 0 16px;max-width:66ch">
        Custom objects are not included in this organization's plan. Existing objects stay readable,
        and can be archived, restored or deleted.
      </p>
    {/if}

    {#if creating && canAdd}
      <SettingsFormPanel
        title="New custom object"
        action="?/create"
        error={form?.create?.error}
        submitLabel="Add object"
        oncancel={() => (creating = false)}
        ondone={() => (creating = false)}
      >
        {#snippet fields()}
          <div class="v2-field">
            <label for="o-label">Name (singular)</label>
            <input
              id="o-label"
              class="v2-input"
              name="label"
              maxlength="64"
              required
              placeholder="Property"
              value={label}
              oninput={onLabel}
            />
          </div>
          <div class="v2-field">
            <label for="o-plural">Name (plural)</label>
            <input
              id="o-plural"
              class="v2-input"
              name="label_plural"
              maxlength="64"
              required
              placeholder="Properties"
            />
          </div>
          <div class="v2-field">
            <label for="o-key">Key</label>
            <input
              id="o-key"
              class="v2-input"
              name="key"
              maxlength="28"
              pattern={'[a-z][a-z0-9_]{1,27}'}
              required
              placeholder="property"
              bind:value={key}
              oninput={() => (keyEdited = true)}
            />
            <p class="v2-hint">
              Lowercase letters, numbers and underscores, starting with a letter. Cannot be changed
              later.
            </p>
          </div>
          <div class="v2-field">
            <label for="o-name-label">What each record's name is called</label>
            <input
              id="o-name-label"
              class="v2-input"
              name="name_label"
              maxlength="64"
              placeholder="Name"
            />
          </div>
          <div class="v2-field v2-sfp-wide">
            <label for="o-desc">Description</label>
            <textarea id="o-desc" class="v2-input" name="description" rows="2"></textarea>
          </div>
          <fieldset class="v2-field v2-sfp-wide" style="border:0;padding:0;margin:0">
            <legend class="v2-label" style="padding:0">Who can see its records</legend>
            <label class="o-choice">
              <input type="radio" name="record_access" value="own" checked />
              Only the people involved
            </label>
            <label class="o-choice">
              <input type="radio" name="record_access" value="everyone" />
              Everyone in this organization
            </label>
          </fieldset>
        {/snippet}
      </SettingsFormPanel>
    {/if}

    {#if !objects.length}
      <EmptyState
        title="No custom objects yet"
        body="A custom object is a record type of your own, such as properties, vehicles or projects, with the fields you choose."
      />
    {:else}
      <div class="v2-table-wrap" style="margin-left:0;margin-right:0">
        <table class="v2-table">
          <thead>
            <tr>
              <th>Object</th>
              <th>Status</th>
              <th>Records visible to</th>
              <th>Key</th>
            </tr>
          </thead>
          <tbody>
            {#each objects as o (o.key)}
              <tr style="opacity:{o.is_active ? 1 : 0.7}">
                <td data-m="title">
                  <a
                    class="v2-row-link o-tap"
                    href={resolve(asInternalPath(`/settings/objects/${o.key}`))}
                  >
                    <div class="v2-table-primary">{o.label_plural}</div>
                    {#if o.description}
                      <div class="v2-table-secondary">{o.description}</div>
                    {/if}
                  </a>
                </td>
                <td data-m="tag">
                  {#if !o.is_active}<Pill tone="slate">Archived</Pill>{/if}
                </td>
                <td data-m="meta"
                  >{o.record_access === 'everyone' ? 'Everyone' : 'People involved'}</td
                >
                <td data-m="meta"><code class="o-key">{o.key}</code></td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

<style>
  .o-choice {
    display: flex;
    gap: 8px;
    align-items: center;
    font-weight: 400;
    min-height: 32px;
  }
  .o-key {
    font-family: var(--v2-mono);
    font-size: 11px;
    color: var(--v2-slate);
  }
  .o-tap {
    display: block;
    min-height: 32px;
  }

  @media (max-width: 768px) {
    .o-choice,
    .o-tap {
      min-height: 44px;
    }
  }
</style>
