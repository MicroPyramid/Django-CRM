<script>
  /**
   * What happens when a ticket blows its target.
   *
   * One EscalationPolicy per priority, enforced by a unique constraint. The
   * useful question is not "is there a policy" — there always is — but "does
   * it do anything", and the model allows three separate ways for the answer
   * to be no:
   *
   *   · the action is `reassign` but the target FK is null (SET_NULL empties
   *     it when a profile is removed, silently)
   *   · the action is `notify` with no individual and no team to notify
   *   · is_active is false
   *
   * All three look identical in v1's form — a row of selects with something
   * chosen. Here the breach count sits next to the outcome, so "11 breaches,
   * nobody told" is one line rather than two screens.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import { count } from '$lib/v2/format.js';
  import { ESCALATION_ACTION_LABEL, PRIORITY_TONE } from '$lib/v2/enums.js';
  import { TriangleAlert, BellOff } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  /**
   * By severity, not by the model's `ordering = ("priority",)` — that sorts
   * the CharField alphabetically and puts Low between High and Normal, which
   * reads as a mistake every single time.
   */
  const SEVERITY = ['Urgent', 'High', 'Normal', 'Low'];
  let policies = $derived(
    [...data.policies].sort((a, b) => SEVERITY.indexOf(a.priority) - SEVERITY.indexOf(b.priority))
  );

  /**
   * What one half of a policy actually does, and whether that is nothing.
   * @returns {{ text: string, dead: boolean }}
   */
  function outcome(policy, kind) {
    const action = policy[`${kind}_action`];
    const target = policy[`${kind}_target`];
    const team = policy.notify_team;

    if (!policy.is_active) return { text: 'Nothing — the policy is off', dead: true };

    if (action === 'reassign' && !target)
      return { text: 'Reassign to nobody — no target is set', dead: true };

    if (action === 'notify' && !target && !team)
      return { text: 'Notify nobody — no person and no team', dead: true };

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
</script>

<PageHeader title="Escalation">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    One policy per priority · <span class="v2-num">{count(policies.length)}</span> configured
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if policies.length === 0}
      <!-- No policy for any priority. Without this the page falls to a header
           over a blank column — the each-block renders nothing and the trailing
           note hangs alone. The empty state says what a policy is and what its
           absence means, and centres itself like every other empty state. -->
      <EmptyState
        title="No escalation policies yet"
        body="An escalation policy decides what happens when a ticket misses its first-response or resolution target — one per priority. None are set for this organisation, so a breach currently escalates to nobody."
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
            <div style="display:flex;gap:9px;align-items:center;margin-bottom:12px">
              <Pill tone={PRIORITY_TONE[p.priority]}>{p.priority}</Pill>
              {#if !p.is_active}<Pill tone="slate">Off</Pill>{/if}
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
                    in the last 30 days{half.o.dead && half.n > 0 ? ' — none of them acted on' : ''}
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

  /* Class, not an inline grid — an inline grid-template-columns cannot be
     overridden here, which is how four earlier pages stayed two-column on a
     phone. */
  @media (max-width: 768px) {
    .v2-escalation-halves {
      grid-template-columns: 1fr;
      gap: 14px;
    }
    .v2-escalation-half + .v2-escalation-half {
      border-left: 0;
      padding-left: 0;
      border-top: 1px solid var(--v2-line-soft);
      padding-top: 14px;
    }
  }
</style>
