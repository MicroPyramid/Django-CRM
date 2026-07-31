<script>
  /**
   * What gates a ticket close, and who can clear it.
   *
   * The queue at /v2/tickets/approvals answers "what is waiting on me". This
   * answers "what will be gated next time, and by whom" — the same rows, a
   * different question, which is why it is a settings page and not a tab.
   *
   * One configuration state the model permits and the form does not warn
   * about, shown here: approver_role MANAGER with no named approvers.
   * Profile.role is only ADMIN or USER, so the rule matches nobody and the
   * cases it gates can never be closed by anyone.
   *
   * Separation of duties — an admin clearing their own requested close — is
   * NOT a gap to warn about: `ApprovalApproveView` rejects an approval whose
   * requester is the approver, unconditionally (no admin exception), so the API
   * enforces it however a rule is configured. An earlier version of this page
   * flagged "any admin, including the requester" as a hole; the view has since
   * closed it, so the warning is gone.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import { count } from '$lib/v2/format.js';
  import { Plus, TriangleAlert, ChevronRight } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);
  let rules = $derived(data.rules);

  /** MANAGER matches no Profile.role, so an empty approvers list means nobody. */
  const clearableByNobody = (r) =>
    r.is_active && r.approver_role === 'MANAGER' && !r.approvers.length;

  /** What the rule matches, as the sentence a person would say. */
  function matches(r) {
    const parts = [
      r.match_priority ? `${r.match_priority} priority` : null,
      r.match_case_type ? r.match_case_type.toLowerCase() : null,
      r.match_team ? `${r.match_team.name} team` : null
    ].filter(Boolean);
    return parts.length ? parts.join(' · ') : 'Every ticket';
  }
</script>

<PageHeader title="Approval rules">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> active ·
    <span class="v2-num">{count(totals.pending)}</span> approvals waiting on them right now
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary"><Plus />New rule</button>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    <div class="v2-label" style="margin-bottom:10px">Rules</div>
    <div style="display:flex;flex-direction:column;gap:9px">
      {#each rules as r (r.id)}
        <div class="v2-card" style="padding:14px 16px;opacity:{r.is_active ? 1 : 0.62}">
          <div style="display:flex;gap:11px;align-items:flex-start">
            <div style="flex:1;min-width:0">
              <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
                <b style="font-size:13.5px">{r.name}</b>
                {#if !r.is_active}<Pill tone="slate">Off</Pill>{/if}
                {#if clearableByNobody(r)}<Pill tone="rust">Nobody can clear</Pill>{/if}
              </div>

              <div class="v2-sub" style="font-size:12.5px;margin-top:5px;white-space:normal">
                <b style="font-weight:600;color:var(--v2-ink)">Gates</b>
                {matches(r)}
                <b style="font-weight:600;color:var(--v2-ink)">→</b>
                cleared by
                {#if r.approvers.length}
                  {r.approvers.join(' or ')}
                {:else}
                  any {r.approver_role.toLowerCase()}
                {/if}
              </div>

              {#if clearableByNobody(r)}
                <div class="v2-rule-flag">
                  <TriangleAlert size={14} style="color:var(--v2-rust);flex:none" />
                  <span>
                    This organisation has admins and members — there is no manager role. With no
                    named approvers, the first ticket this gates cannot be closed by anyone. Name
                    approvers, or set it to admin.
                  </span>
                </div>
              {/if}
            </div>

            <div style="flex:none;text-align:right">
              {#if r.pending_count}
                <a
                  href="/v2/tickets/approvals"
                  class="v2-sub"
                  style="font-size:12px;display:inline-flex;align-items:center;gap:2px"
                >
                  <span class="v2-num">{count(r.pending_count)}</span> waiting
                  <ChevronRight size={13} />
                </a>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>

<style>
  .v2-rule-flag {
    display: flex;
    gap: 7px;
    align-items: flex-start;
    margin-top: 9px;
    font-size: 12px;
    color: var(--v2-slate);
    line-height: 1.45;
  }
</style>
