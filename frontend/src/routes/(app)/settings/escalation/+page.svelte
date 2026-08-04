<script>
  /**
   * What happens when a ticket blows its target.
   *
   * One EscalationPolicy per priority, enforced by a unique constraint. The
   * useful question is not "is there a policy", there always is at most one
   * per priority, but "does it do anything", and the model allows three
   * separate ways for the answer to be no:
   *
   *   · the action is `reassign` but the target FK is null (SET_NULL empties
   *     it when a profile is removed, silently)
   *   · the action is `notify` with no individual and no team to notify
   *   · is_active is false
   *
   * All three look identical in v1's form, a row of selects with something
   * chosen. Here the breach count sits next to the outcome, so "11 breaches,
   * nobody told" is one line rather than two screens.
   *
   * Only four priorities exist and each may have at most one policy
   * (`(org, priority)` unique constraint, enforced again by
   * `EscalationPolicySerializer.validate()` on create). So "New policy"
   * offers only the priorities with no policy yet, and disappears once all
   * four are configured: a disabled button with no explanation is the dead
   * end this phase exists to remove, not a control worth keeping around.
   *
   * `priority` never appears on the edit form. `EscalationPolicyDetailView.put`
   * strips the key from the request body before the serializer sees it, so an
   * edit that offered it would report success and change nothing.
   */
  import { enhance } from '$app/forms';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import SettingsFormPanel from '$lib/v2/components/SettingsFormPanel.svelte';
  import ConfirmAction from '$lib/v2/components/ConfirmAction.svelte';
  import { count } from '$lib/v2/format.js';
  import { ESCALATION_ACTION_LABEL, ESCALATION_PRIORITIES, PRIORITY_TONE } from '$lib/v2/enums.js';
  import { missingOption, inactiveOptionLabel } from '$lib/v2/pickers.js';
  import { TriangleAlert, BellOff, Plus } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  /**
   * By severity, not by the model's `ordering = ("priority",)`. That sorts
   * the CharField alphabetically and puts Low between High and Normal, which
   * reads as a mistake every single time.
   */
  let policies = $derived(
    [...data.policies].sort(
      (a, b) => ESCALATION_PRIORITIES.indexOf(a.priority) - ESCALATION_PRIORITIES.indexOf(b.priority)
    )
  );

  /** The priorities with no policy yet: what "New policy" is allowed to offer. */
  let availablePriorities = $derived(
    ESCALATION_PRIORITIES.filter((p) => !data.policies.some((x) => x.priority === p))
  );
  let allConfigured = $derived(availablePriorities.length === 0);

  /**
   * What one half of a policy actually does, and whether that is nothing.
   * @returns {{ text: string, dead: boolean }}
   */
  function outcome(policy, kind) {
    const action = policy[`${kind}_action`];
    const target = policy[`${kind}_target`];
    const team = policy.notify_team;

    if (!policy.is_active) return { text: 'Nothing. The policy is off', dead: true };

    if (action === 'reassign' && !target)
      return { text: 'Reassign to nobody, no target is set', dead: true };

    if (action === 'notify' && !target && !team)
      return { text: 'Notify nobody, no person and no team', dead: true };

    const who = [target?.name, team ? `the ${team.name} team` : null].filter(Boolean).join(' and ');
    return { text: `${ESCALATION_ACTION_LABEL[action]} ${who}`, dead: false };
  }

  let deadCount = $derived(
    policies.filter((p) => outcome(p, 'first_response').dead && outcome(p, 'resolution').dead)
      .length
  );
  let breachesGoingNowhere = $derived(
    policies.reduce(
      (a, p) =>
        a +
        (outcome(p, 'first_response').dead ? p.breaches_last_30d.first_response : 0) +
        (outcome(p, 'resolution').dead ? p.breaches_last_30d.resolution : 0),
      0
    )
  );

  // `null` when the panel is closed, `'new'` when adding, or the policy
  // object when editing that row. One panel, two modes, so two rows can
  // never be open for edit at once.
  let editing = $state(/** @type {any} */ (null));

  // Mirrors of the four action/target fields, so the "reassigns to nobody"
  // hint can react to what is currently picked in the form, before the
  // policy is saved, rather than only ever telling the admin from the card
  // afterward. `notify_team_id` needs no such mirror: there is no live
  // warning tied to it.
  let firstResponseAction = $state('notify');
  let resolutionAction = $state('notify');
  let firstResponseTarget = $state('');
  let resolutionTarget = $state('');

  function openCreate() {
    editing = 'new';
    firstResponseAction = 'notify';
    resolutionAction = 'notify';
    firstResponseTarget = '';
    resolutionTarget = '';
  }

  function openEdit(p) {
    editing = p;
    firstResponseAction = p.first_response_action;
    resolutionAction = p.resolution_action;
    firstResponseTarget = p.first_response_target?.id ?? '';
    resolutionTarget = p.resolution_target?.id ?? '';
  }

  /**
   * A stored target the picker cannot offer.
   *
   * `getOrgPeopleAndTeams` only ever returns active profiles, while
   * `EscalationPolicy.first_response_target` / `resolution_target` carry
   * whoever was chosen, deactivated or not, and `cases/tasks.py` escalates to
   * them with no active filter. A select with no matching option submits
   * nothing, `readValues` reads that absence as `''`, and `buildBody` turns
   * `''` into `null`. So without an option of its own, opening this form to
   * change one unrelated field would stop Urgent breaches escalating to
   * anybody. It would also hide the "reassigns to nobody" warning at the
   * moment it became true, because the binding keeps the stale id when the
   * browser deselects.
   */
  let missingFirstTarget = $derived(
    editing && editing !== 'new' ? missingOption(data.people, editing.first_response_target) : null
  );
  let missingResolutionTarget = $derived(
    editing && editing !== 'new' ? missingOption(data.people, editing.resolution_target) : null
  );
</script>

<PageHeader title="Escalation">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    {#if allConfigured}
      One policy per priority · all four are configured
    {:else}
      One policy per priority · <span class="v2-num">{count(policies.length)}</span> configured
    {/if}
  {/snippet}
  {#snippet actions()}
    {#if data.can_edit && !editing && availablePriorities.length > 0}
      <button class="v2-btn v2-btn-primary" onclick={openCreate}><Plus />New policy</button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if editing}
      <SettingsFormPanel
        title={editing === 'new' ? 'New policy' : `Edit ${editing.priority} policy`}
        action={editing === 'new' ? '?/create' : '?/update'}
        error={editing === 'new' ? form?.create?.error : form?.update?.error}
        submitLabel={editing === 'new' ? 'Add policy' : 'Save policy'}
        oncancel={() => (editing = null)}
        ondone={() => (editing = null)}
      >
        {#snippet fields()}
          {#if editing !== 'new'}
            <input type="hidden" name="id" value={editing.id} />
          {/if}

          <div class="v2-field">
            <label for="e-priority">Priority</label>
            {#if editing === 'new'}
              <select id="e-priority" class="v2-input" name="priority" required>
                {#each availablePriorities as p (p)}
                  <option value={p}>{p}</option>
                {/each}
              </select>
            {:else}
              <div style="font-size:13px">{editing.priority}</div>
              <p class="v2-hint">Fixed after creation. One policy per priority.</p>
            {/if}
          </div>

          <div class="v2-field">
            <label for="e-fr-action">First response action</label>
            <select
              id="e-fr-action"
              class="v2-input"
              name="first_response_action"
              bind:value={firstResponseAction}
            >
              {#each Object.entries(ESCALATION_ACTION_LABEL) as [value, label] (value)}
                <option {value}>{label}</option>
              {/each}
            </select>
            {#if firstResponseAction === 'reassign' && !firstResponseTarget}
              <p class="v2-hint">Reassigns to nobody until a target is picked below.</p>
            {/if}
          </div>

          <div class="v2-field">
            <label for="e-fr-target">First response target</label>
            <select
              id="e-fr-target"
              class="v2-input"
              name="first_response_target_id"
              bind:value={firstResponseTarget}
            >
              <option value="">Nobody</option>
              {#if missingFirstTarget}
                <option value={missingFirstTarget.id}>
                  {inactiveOptionLabel(missingFirstTarget.name)}
                </option>
              {/if}
              {#each data.people as p (p.id)}
                <option value={p.id}>{p.name}</option>
              {/each}
            </select>
            {#if missingFirstTarget}
              <p class="v2-hint">
                This target's account is no longer active. It stays set until you change it, and a
                breach reassigned there waits for someone who cannot sign in.
              </p>
            {/if}
          </div>

          <div class="v2-field">
            <label for="e-res-action">Resolution action</label>
            <select
              id="e-res-action"
              class="v2-input"
              name="resolution_action"
              bind:value={resolutionAction}
            >
              {#each Object.entries(ESCALATION_ACTION_LABEL) as [value, label] (value)}
                <option {value}>{label}</option>
              {/each}
            </select>
            {#if resolutionAction === 'reassign' && !resolutionTarget}
              <p class="v2-hint">Reassigns to nobody until a target is picked below.</p>
            {/if}
          </div>

          <div class="v2-field">
            <label for="e-res-target">Resolution target</label>
            <select
              id="e-res-target"
              class="v2-input"
              name="resolution_target_id"
              bind:value={resolutionTarget}
            >
              <option value="">Nobody</option>
              {#if missingResolutionTarget}
                <option value={missingResolutionTarget.id}>
                  {inactiveOptionLabel(missingResolutionTarget.name)}
                </option>
              {/if}
              {#each data.people as p (p.id)}
                <option value={p.id}>{p.name}</option>
              {/each}
            </select>
            {#if missingResolutionTarget}
              <p class="v2-hint">
                This target's account is no longer active. It stays set until you change it, and a
                breach reassigned there waits for someone who cannot sign in.
              </p>
            {/if}
          </div>

          <div class="v2-field">
            <label for="e-team">Notify team</label>
            <select id="e-team" class="v2-input" name="notify_team_id">
              <option value="" selected={editing === 'new' || !editing.notify_team}>No team</option>
              {#each data.teams as t (t.id)}
                <option value={t.id} selected={editing !== 'new' && editing.notify_team?.id === t.id}>
                  {t.name}
                </option>
              {/each}
            </select>
            {#if !data.teams.length}
              <p class="v2-hint">No teams in this org yet.</p>
            {/if}
          </div>

          {#if editing === 'new'}
            <div class="v2-field">
              <label for="e-active">Active</label>
              <label style="display:flex;gap:8px;align-items:center;font-weight:400">
                <input id="e-active" type="checkbox" name="is_active" value="true" checked />
                Starts escalating breaches at this priority as soon as it is saved.
              </label>
            </div>
          {/if}
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

    {#if policies.length === 0}
      <!-- No policy for any priority. Without this the page falls to a header
           over a blank column, the each-block renders nothing and the trailing
           note hangs alone. The empty state says what a policy is and what its
           absence means, and centres itself like every other empty state. -->
      <EmptyState
        title="No escalation policies yet"
        body="An escalation policy decides what happens when a ticket misses its first-response or resolution target. One per priority. None are set for this organisation, so a breach currently escalates to nobody."
      >
        {#snippet icon()}<BellOff size={21} />{/snippet}
      </EmptyState>
    {:else}
      {#if breachesGoingNowhere > 0}
        <!-- The headline fact, above the table, because it is the reason to be
           on this page. Derived from the same rows shown below, not a
           separate figure that could disagree with them. -->
        <div class="v2-escalation-banner">
          <BellOff size={17} style="color:var(--v2-clay);flex:none;margin-top:1px" />
          <div>
            <div style="font-weight:600;font-size:13px">
              <span class="v2-num">{count(breachesGoingNowhere)}</span> breaches in the last 30 days told
              nobody
            </div>
            <p class="v2-sub" style="font-size:12px;margin:4px 0 0">
              {deadCount === 0
                ? 'Some halves of these policies resolve to no recipient.'
                : `${deadCount} of ${policies.length} policies do nothing at all when a ticket breaches.`}
              A policy that exists is not the same as a policy that fires.
            </p>
          </div>
        </div>
      {/if}

      <div style="display:flex;flex-direction:column;gap:10px">
        {#each policies as p (p.id)}
          {@const first = outcome(p, 'first_response')}
          {@const res = outcome(p, 'resolution')}
          <div class="v2-card" style="padding:15px 16px;opacity:{p.is_active ? 1 : 0.62}">
            <div
              style="display:flex;gap:9px;align-items:center;margin-bottom:12px;justify-content:space-between"
            >
              <div style="display:flex;gap:9px;align-items:center">
                <Pill tone={PRIORITY_TONE[p.priority]}>{p.priority}</Pill>
                {#if !p.is_active}<Pill tone="slate">Off</Pill>{/if}
              </div>

              {#if data.can_edit}
                <div style="display:flex;gap:6px;align-items:center;flex:none">
                  <button class="v2-btn v2-btn-sm" type="button" onclick={() => openEdit(p)}>
                    Edit
                  </button>
                  {#if p.is_active}
                    <ConfirmAction
                      action="?/deactivate"
                      label="Turn off"
                      confirmLabel="Turn off"
                      explain="Stops escalating breaches at this priority. It stays in the list, off, until turned back on."
                      hidden={{ id: p.id }}
                    />
                  {:else}
                    <form method="POST" action="?/activate" use:enhance>
                      <input type="hidden" name="id" value={p.id} />
                      <button class="v2-btn v2-btn-sm" type="submit">Turn on</button>
                    </form>
                  {/if}
                  <ConfirmAction
                    action="?/remove"
                    label="Delete"
                    confirmLabel="Delete"
                    explain="Deleted permanently. Breaches at this priority will escalate to nobody."
                    hidden={{ id: p.id }}
                  />
                </div>
              {/if}
            </div>

            <div class="v2-escalation-halves">
              {#each [{ label: 'Missed first response', o: first, n: p.breaches_last_30d.first_response }, { label: 'Missed resolution', o: res, n: p.breaches_last_30d.resolution }] as half (half.label)}
                <div class="v2-escalation-half">
                  <div class="v2-label" style="font-size:10px;margin-bottom:5px">{half.label}</div>
                  <div style="display:flex;gap:7px;align-items:flex-start">
                    {#if half.o.dead}
                      <TriangleAlert
                        size={14}
                        style="color:var(--v2-clay);flex:none;margin-top:2px"
                      />
                    {/if}
                    <span style="font-size:13px;{half.o.dead ? 'color:var(--v2-slate)' : ''}">
                      {half.o.text}
                    </span>
                  </div>
                  <div class="v2-sub" style="font-size:11.5px;margin-top:6px">
                    <span class="v2-num">{count(half.n)}</span>
                    in the last 30 days{half.o.dead && half.n > 0 ? ', none of them acted on' : ''}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>

      <p class="v2-sub" style="font-size:11.5px;margin-top:16px;max-width:64ch">
        Targets are measured on
        <a href="/settings/business-hours" style="color:inherit">business hours</a>, so a breach
        counts working time only. What counts as breached for each priority is set with the target
        itself, not here.
      </p>
    {/if}
  </div>
</div>

<style>
  .v2-escalation-banner {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding: 14px 16px;
    margin-bottom: 18px;
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    background: var(--v2-card);
  }
  .v2-escalation-halves {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
  }
  .v2-escalation-half + .v2-escalation-half {
    border-left: 1px solid var(--v2-line-soft);
    padding-left: 18px;
  }

  /* Class, not an inline grid. An inline grid-template-columns cannot be
     overridden here, which is how four earlier pages stayed two-column on a
     phone. */
  @media (max-width: 768px) {
    .v2-escalation-halves {
      grid-template-columns: 1fr;
    }
    .v2-escalation-half + .v2-escalation-half {
      border-left: 0;
      padding-left: 0;
      border-top: 1px solid var(--v2-line-soft);
      padding-top: 14px;
    }
  }
</style>
