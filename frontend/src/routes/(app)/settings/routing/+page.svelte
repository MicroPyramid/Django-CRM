<script>
  /**
   * Who a new ticket lands on.
   *
   * `cases.routing.evaluate` walks active rules by priority_order, runs the
   * first match, and stops there when stop_processing is set. So the list is
   * ordered because the order IS the behaviour, which means two things this
   * page does that v1's table of names does not:
   *
   * 1. Each rule reads as the sentence it performs, not as four columns
   *    (conditions JSON, strategy slug, assignee ids, a checkbox) that the
   *    reader has to reassemble.
   * 2. A rule that can never run is marked as such. Once an active,
   *    unconditional, stop-processing rule appears, everything below it is
   *    dead, and "matched 0 times" on its own looks like a quiet month.
   */
  import { enhance } from '$app/forms';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import SettingsFormPanel from '$lib/v2/components/SettingsFormPanel.svelte';
  import ConfirmAction from '$lib/v2/components/ConfirmAction.svelte';
  import { count } from '$lib/v2/format.js';
  import {
    ROUTING_STRATEGY_LABEL,
    ROUTING_STRATEGY_NAME,
    CONDITION_FIELD_LABEL,
    CONDITION_OP_LABEL
  } from '$lib/v2/enums.js';
  import { missingOptions, inactiveOptionLabel } from '$lib/v2/pickers.js';
  import { nextInRotation } from './rotation.js';
  import { Plus, GripVertical, TriangleAlert, UserX } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  // `null` when the panel is closed, `'new'` when adding, or the rule object
  // when editing that row. One panel, two modes, so two rows can never be
  // open for edit at once.
  let editing = $state(/** @type {any} */ (null));

  // The strategy currently selected in the form, so the target picker below
  // it (team vs. people) can switch without a round trip. Seeded from the
  // rule being edited.
  let strategy = $state('direct');

  // The repeating condition rows being edited, as `{ field, op, value }`.
  // Held here, rather than read off `editing`, so a row can be added or
  // removed before submitting.
  let conditionRows = $state(/** @type {{ field: string, op: string, value: string }[]} */ ([]));

  function openCreate() {
    editing = 'new';
    strategy = 'direct';
    conditionRows = [];
  }

  function openEdit(r) {
    editing = r;
    strategy = r.strategy;
    // Joining an array value into a comma-separated string is the right
    // editing representation for a single text input, and it round-trips: on
    // save, `routing.js`'s `cleanConditions` splits an `in` row's value back
    // on commas. That round trip is lossless for any value made up of
    // entries with no comma in them, which is the whole reason this editor
    // can stay one text input instead of its own repeating sub-list. Known
    // limitation: a value that itself contains a literal comma cannot be
    // expressed here, since splitting can't tell that comma apart from a
    // separator.
    conditionRows = r.conditions.map((c) => ({
      field: c.field,
      op: c.op,
      value: Array.isArray(c.value) ? c.value.join(', ') : String(c.value ?? '')
    }));
  }

  let totals = $derived(data.totals);

  // Targets the picker cannot offer, because the profile was deactivated
  // after it was chosen. `getOrgPeopleAndTeams` only ever returns active
  // profiles, while the rule's M2M keeps them, which is exactly what the
  // deactivated-target flag on the card below is about. Without an option of
  // their own the multi-select submits nothing for them, so an edit made for
  // another reason would quietly rewrite the rotation.
  let missingAssignees = $derived(
    editing && editing !== 'new' ? missingOptions(data.people, editing.target_assignees) : []
  );

  /**
   * A stored condition field the select cannot show.
   *
   * `custom_fields.<key>` is a first-class field everywhere else: the backend
   * accepts it, `cleanConditions` accepts it, and `when()` below renders it.
   * `CONDITION_FIELD_LABEL` only carries the six fixed ones, so without this
   * the select would have no matching option, would submit nothing, and the
   * row would be dropped or, worse, shift its neighbours.
   */
  function unlistedField(field) {
    if (!field || field in CONDITION_FIELD_LABEL) return null;
    return field.startsWith('custom_fields.')
      ? `Custom field: ${field.slice('custom_fields.'.length)}`
      : field;
  }

  /**
   * Reachability, walked in evaluation order.
   *
   * This is derived on the client rather than sent by the API, and that is
   * deliberate. Unlike a list total, it is not a fact about rows we cannot
   * see. It is a property of this complete ordered list, and it has to stay
   * correct the instant someone drags a rule, before any request goes out.
   */
  let rules = $derived.by(() => {
    let sealed = false;
    return data.rules.map((r) => {
      const unreachable = sealed;
      if (r.is_active && r.stop_processing && r.conditions.length === 0) sealed = true;
      return { ...r, unreachable };
    });
  });

  /** The conditions as one clause. No conditions means every ticket. */
  function when(r) {
    if (!r.conditions.length) return 'Any ticket';
    return r.conditions
      .map((c) => {
        const field = CONDITION_FIELD_LABEL[c.field] ?? c.field.replace('custom_fields.', '');
        const value = Array.isArray(c.value) ? c.value.join(', ') : c.value;
        return `${field} ${CONDITION_OP_LABEL[c.op]} ${value}`;
      })
      .join(' and ');
  }

  /** The action as one clause: verb phrase from the strategy, then its object. */
  function then(r) {
    const verb = ROUTING_STRATEGY_LABEL[r.strategy];
    if (r.strategy === 'by_team') return `${verb} ${r.target_team?.name ?? '—'}`;
    return `${verb} ${r.target_assignees.map((a) => a.name).join(', ') || '—'}`;
  }
</script>

<PageHeader title="Ticket routing">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> active rules, run in this order until one matches
  {/snippet}
  {#snippet actions()}
    {#if data.can_edit && !editing}
      <button class="v2-btn v2-btn-primary" onclick={openCreate}><Plus />New rule</button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:16px;flex:none">
  <div class="v2-stats">
    <StatCard label="Active rules" value={count(totals.active)} tone="ink" />
    <StatCard label="Rules off" value={count(totals.count - totals.active)} tone="slate" />
    <StatCard
      label="Unrouted, 30 days"
      value={count(totals.unrouted_last_30d)}
      tone={totals.unrouted_last_30d > 0 ? 'clay' : 'slate'}
      detail="No rule matched, so nobody was assigned"
    />
  </div>
</div>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#if editing}
      <SettingsFormPanel
        title={editing === 'new' ? 'New rule' : `Edit ${editing.name}`}
        action={editing === 'new' ? '?/create' : '?/update'}
        error={editing === 'new' ? form?.create?.error : form?.update?.error}
        submitLabel={editing === 'new' ? 'Add rule' : 'Save rule'}
        oncancel={() => (editing = null)}
        ondone={() => (editing = null)}
      >
        {#snippet fields()}
          {#if editing !== 'new'}
            <input type="hidden" name="id" value={editing.id} />
          {/if}

          <div class="v2-field">
            <label for="r-name">Name</label>
            <input
              id="r-name"
              class="v2-input"
              name="name"
              maxlength="128"
              required
              value={editing === 'new' ? '' : editing.name}
            />
          </div>

          <div class="v2-field">
            <label for="r-priority">Priority</label>
            <input
              id="r-priority"
              class="v2-input"
              type="number"
              name="priority_order"
              min="0"
              value={editing === 'new' ? 0 : editing.priority_order}
            />
            <p class="v2-hint">The engine runs rules low number first and takes the first match.</p>
          </div>

          <div class="v2-field">
            <label for="r-strategy">Then</label>
            <select id="r-strategy" class="v2-input" name="strategy" bind:value={strategy}>
              {#each Object.entries(ROUTING_STRATEGY_NAME) as [value, label] (value)}
                <option {value}>{label}</option>
              {/each}
            </select>
          </div>

          {#if strategy === 'by_team'}
            <div class="v2-field">
              <label for="r-team">Team</label>
              <select id="r-team" class="v2-input" name="target_team_id" required>
                <option value="" disabled selected={editing === 'new' || !editing.target_team}>
                  Choose a team
                </option>
                {#each data.teams as t (t.id)}
                  <option
                    value={t.id}
                    selected={editing !== 'new' && editing.target_team?.id === t.id}
                  >
                    {t.name}
                  </option>
                {/each}
              </select>
              {#if !data.teams.length}
                <p class="v2-hint">No teams in this org yet.</p>
              {/if}
            </div>
          {:else}
            <div class="v2-field">
              <label for="r-people">Who</label>
              <select
                id="r-people"
                class="v2-input"
                name="target_assignee_ids"
                multiple
                style="height:118px"
              >
                <!-- A target whose profile has been deactivated is not in
                     `data.people`, so it gets an option of its own. Dropping
                     it would be a change to who tickets go to, made by an
                     edit that was about something else. -->
                {#each missingAssignees as a (a.id)}
                  <option value={a.id} selected>{inactiveOptionLabel(a.name)}</option>
                {/each}
                {#each data.people as p (p.id)}
                  <option
                    value={p.id}
                    selected={editing !== 'new' &&
                      editing.target_assignees.some((a) => a.id === p.id)}
                  >
                    {p.name}
                  </option>
                {/each}
              </select>
              <p class="v2-hint">
                {#if strategy === 'direct'}
                  Direct uses only the first person selected here; the rest are ignored unless the
                  strategy changes.
                {:else}
                  Round robin and least busy cycle through everyone listed here.
                {/if}
              </p>
              {#if missingAssignees.length}
                <p class="v2-hint">
                  {missingAssignees.map((a) => a.name).join(', ')}
                  {missingAssignees.length === 1 ? 'is' : 'are'} deactivated and still in the rotation.
                  Deselect to take them out.
                </p>
              {/if}
            </div>
          {/if}

          <div class="v2-field">
            <label for="r-stop">Stop processing</label>
            <label style="display:flex;gap:8px;align-items:center;font-weight:400">
              <input
                id="r-stop"
                type="checkbox"
                name="stop_processing"
                value="true"
                checked={editing !== 'new' && editing.stop_processing}
              />
              A matching rule with this on stops the engine, so later rules never see the ticket.
            </label>
          </div>

          {#if editing === 'new'}
            <div class="v2-field">
              <label for="r-active">Active</label>
              <label style="display:flex;gap:8px;align-items:center;font-weight:400">
                <input id="r-active" type="checkbox" name="is_active" value="true" checked />
                Starts matching tickets as soon as it is saved.
              </label>
            </div>
          {/if}

          <div class="v2-field v2-sfp-wide">
            <label for="r-cond-0">Conditions</label>
            <!-- One indexed name per row, not three parallel `condition_field`
                 / `condition_op` / `condition_value` lists. A select with no
                 matching option submits no entry at all, so parallel lists
                 paired by position silently shifted every row after the gap.
                 Indexed names make a row's three inputs travel together, and
                 `readConditionRows` in `routing.js` pairs them by index. -->
            {#each conditionRows as row, i (i)}
              {@const unlisted = unlistedField(row.field)}
              <div style="margin-bottom:6px">
                <div style="display:flex;gap:7px;align-items:center">
                  <select
                    id={i === 0 ? 'r-cond-0' : undefined}
                    class="v2-input"
                    name="condition_field_{i}"
                    bind:value={row.field}
                  >
                    <option value="">Choose a field</option>
                    {#if unlisted}
                      <!-- A stored `custom_fields.<key>` condition. The label
                           map carries only the six fixed fields, so without
                           this option the select would match nothing and the
                           condition would not survive an unrelated edit. -->
                      <option value={row.field}>{unlisted}</option>
                    {/if}
                    {#each Object.entries(CONDITION_FIELD_LABEL) as [value, label] (value)}
                      <option {value}>{label}</option>
                    {/each}
                  </select>
                  <select class="v2-input" name="condition_op_{i}" bind:value={row.op}>
                    {#each Object.entries(CONDITION_OP_LABEL) as [value, label] (value)}
                      <option {value}>{label}</option>
                    {/each}
                  </select>
                  <input
                    class="v2-input"
                    name="condition_value_{i}"
                    bind:value={row.value}
                    placeholder="Value"
                  />
                  <button
                    class="v2-btn v2-btn-sm"
                    type="button"
                    onclick={() => (conditionRows = conditionRows.filter((_, j) => j !== i))}
                  >
                    Remove
                  </button>
                </div>
                {#if row.op === 'in'}
                  <!-- Only for `in`: `eq`, `contains` and `regex` all take the
                       value as one plain string, so this hint would be wrong
                       for them. -->
                  <p class="v2-hint">
                    Comma separated. Matches if any one of these values matches.
                  </p>
                {/if}
              </div>
            {/each}
            <button
              class="v2-btn v2-btn-sm"
              type="button"
              style="align-self:flex-start"
              onclick={() =>
                (conditionRows = [...conditionRows, { field: '', op: 'eq', value: '' }])}
            >
              Add a condition
            </button>
            {#if !conditionRows.some((row) => row.field)}
              <p class="v2-error" style="margin-top:8px">
                <TriangleAlert size={13} style="flex:none;margin-top:1px" />
                <span>With no conditions this rule matches every ticket.</span>
              </p>
            {/if}
          </div>
        {/snippet}
      </SettingsFormPanel>
    {/if}

    {#if form?.deactivate?.error}
      <p class="v2-error" style="margin-bottom:12px">{form.deactivate.error}</p>
    {/if}
    {#if form?.activate?.error}
      <p class="v2-error" style="margin-bottom:12px">{form.activate.error}</p>
    {/if}
    {#if form?.remove?.error}
      <p class="v2-error" style="margin-bottom:12px">{form.remove.error}</p>
    {/if}

    <div class="v2-label" style="margin-bottom:10px">In evaluation order</div>

    <div style="display:flex;flex-direction:column;gap:9px">
      {#each rules as r, i (r.id)}
        {@const next = nextInRotation(r)}
        {@const inactiveTargets = r.target_assignees.filter((a) => !a.is_active)}
        <div class="v2-card v2-rule" style="opacity:{r.is_active && !r.unreachable ? 1 : 0.62}">
          <!-- The handle and the number say the same thing: this position is
               the logic. Dragging is the edit; the number is the reading. -->
          <div class="v2-rule-order">
            <GripVertical size={14} style="color:var(--v2-slate)" />
            <span class="v2-num">{i + 1}</span>
          </div>

          <div style="flex:1;min-width:0">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <b style="font-size:13.5px">{r.name}</b>
              {#if !r.is_active}<Pill tone="slate">Off</Pill>{/if}
              {#if r.unreachable && r.is_active}<Pill tone="rust">Never runs</Pill>{/if}
            </div>

            <div class="v2-sub" style="font-size:12.5px;margin-top:5px;white-space:normal">
              <b style="font-weight:600;color:var(--v2-ink)">When</b>
              {when(r)}
              <b style="font-weight:600;color:var(--v2-ink)">→</b>
              {then(r)}
            </div>

            {#if next}
              <div class="v2-sub" style="font-size:11.5px;margin-top:5px">
                Next in the rotation: {next.name}
              </div>
            {/if}

            {#if inactiveTargets.length}
              <!-- A deactivated profile stays in target_assignees; the M2M has
                   no active filter and the engine does not skip them. -->
              <div class="v2-rule-flag">
                <UserX size={14} style="color:var(--v2-clay);flex:none" />
                <span>
                  {inactiveTargets.map((a) => a.name).join(', ')}
                  {inactiveTargets.length === 1 ? 'is' : 'are'} deactivated and still in the rotation,
                  tickets routed there wait for someone who cannot sign in.
                </span>
              </div>
            {/if}

            {#if r.unreachable && r.is_active}
              <div class="v2-rule-flag">
                <TriangleAlert size={14} style="color:var(--v2-rust);flex:none" />
                <span>
                  Rule {rules.findIndex(
                    (x) => x.is_active && x.stop_processing && !x.conditions.length
                  ) + 1} above matches every ticket and stops, so this one is never reached. Move it higher,
                  or let that rule fall through.
                </span>
              </div>
            {/if}
          </div>

          <div class="v2-rule-stat">
            <span class="v2-num" style="font-size:15px;font-weight:600">
              {count(r.matched_last_30d)}
            </span>
            <span class="v2-sub" style="font-size:10.5px">matched, 30d</span>
            {#if !r.stop_processing && r.is_active}
              <span class="v2-sub" style="font-size:10.5px;margin-top:4px">falls through</span>
            {/if}
          </div>

          {#if data.can_edit}
            <div class="v2-rule-actions">
              <button class="v2-btn v2-btn-sm" type="button" onclick={() => openEdit(r)}>
                Edit
              </button>
              {#if r.is_active}
                <ConfirmAction
                  action="?/deactivate"
                  label="Turn off"
                  confirmLabel="Turn off"
                  explain="Stops matching new tickets. It stays in the list, off, until turned back on."
                  hidden={{ id: r.id }}
                />
              {:else}
                <form method="POST" action="?/activate" use:enhance>
                  <input type="hidden" name="id" value={r.id} />
                  <button class="v2-btn v2-btn-sm" type="submit">Turn on</button>
                </form>
              {/if}
              <ConfirmAction
                action="?/remove"
                label="Delete"
                confirmLabel="Delete"
                explain="Deleted permanently. Tickets already routed by it stay where they are."
                hidden={{ id: r.id }}
              />
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <p class="v2-sub" style="font-size:11.5px;margin-top:16px;max-width:62ch">
      A ticket takes the first rule that matches. Rules marked “falls through” keep going down the
      list after they run, so a ticket can be touched by more than one.
    </p>
  </div>
</div>

<style>
  .v2-rule {
    display: flex;
    gap: 13px;
    align-items: flex-start;
    padding: 14px 16px;
  }
  .v2-rule-order {
    display: flex;
    align-items: center;
    gap: 2px;
    flex: none;
    font-size: 12px;
    color: var(--v2-slate);
    padding-top: 1px;
  }
  .v2-rule-stat {
    flex: none;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    text-align: right;
  }
  .v2-rule-actions {
    flex: none;
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .v2-rule-flag {
    display: flex;
    gap: 7px;
    align-items: flex-start;
    margin-top: 9px;
    font-size: 12px;
    color: var(--v2-slate);
    line-height: 1.45;
  }

  /* The match count is a footnote at 414px, not a column. Stacking keeps the
     sentence full-width, which is the part you came to read. */
  @media (max-width: 768px) {
    .v2-rule {
      flex-wrap: wrap;
    }
    .v2-rule-stat {
      flex-direction: row;
      align-items: baseline;
      gap: 5px;
      width: 100%;
      margin-top: 10px;
      padding-left: 30px;
    }
    /* Same reflow as `.v2-rule-stat` above: a flex:none column becomes its
       own full-width row, indented to align under the card's main content
       rather than the grip handle. `flex-wrap` is added here (unlike the
       stat block) because an armed `ConfirmAction` grows into a button pair
       plus a sentence of explain text, which does not fit one line at
       390px. */
    .v2-rule-actions {
      flex-wrap: wrap;
      width: 100%;
      margin-top: 10px;
      padding-left: 30px;
    }
  }
</style>
