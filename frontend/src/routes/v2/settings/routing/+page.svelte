<script>
  /**
   * Who a new ticket lands on.
   *
   * `cases.routing.evaluate` walks active rules by priority_order, runs the
   * first match, and stops there when stop_processing is set. So the list is
   * ordered because the order IS the behaviour — which means two things this
   * page does that v1's table of names does not:
   *
   * 1. Each rule reads as the sentence it performs, not as four columns
   *    (conditions JSON, strategy slug, assignee ids, a checkbox) that the
   *    reader has to reassemble.
   * 2. A rule that can never run is marked as such. Once an active,
   *    unconditional, stop-processing rule appears, everything below it is
   *    dead — and "matched 0 times" on its own looks like a quiet month.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import { count } from '$lib/v2/format.js';
  import {
    ROUTING_STRATEGY_LABEL,
    CONDITION_FIELD_LABEL,
    CONDITION_OP_LABEL
  } from '$lib/v2/enums.js';
  import { Plus, GripVertical, TriangleAlert, UserX } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);

  /**
   * Reachability, walked in evaluation order.
   *
   * This is derived on the client rather than sent by the API, and that is
   * deliberate — unlike a list total, it is not a fact about rows we cannot
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

  /**
   * Who the next matching ticket goes to. Only knowable for round_robin, where
   * RoutingRuleState holds the cursor — for the other strategies it depends on
   * the ticket or on live workload, and guessing would be worse than silence.
   */
  function nextUp(r) {
    if (r.strategy !== 'round_robin' || !r.state || !r.target_assignees.length) return null;
    return r.target_assignees[(r.state.last_assigned_index + 1) % r.target_assignees.length];
  }
</script>

<PageHeader title="Ticket routing">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> active rules, run in this order until one matches
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary"><Plus />New rule</button>
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
    <div class="v2-label" style="margin-bottom:10px">In evaluation order</div>

    <div style="display:flex;flex-direction:column;gap:9px">
      {#each rules as r, i (r.id)}
        {@const next = nextUp(r)}
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
                  {inactiveTargets.length === 1 ? 'is' : 'are'} deactivated and still in the rotation
                  — tickets routed there wait for someone who cannot sign in.
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
  .v2-rule-flag {
    display: flex;
    gap: 7px;
    align-items: flex-start;
    margin-top: 9px;
    font-size: 12px;
    color: var(--v2-slate);
    line-height: 1.45;
  }

  /* The match count is a footnote at 414px, not a column — stacking keeps the
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
  }
</style>
