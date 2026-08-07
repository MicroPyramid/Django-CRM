<script>
  import { resolve } from '$app/paths';
  /**
   * Whether a customer's reply can bring a closed ticket back.
   *
   * One row per org, four fields. Small enough that v1's form is not wrong,
   * just uninformative. The whole question here is what number to put in the
   * window, and the only thing that answers it is how customers actually
   * behave: the median reply comes back in two days, and four replies last
   * month arrived after the window and reopened nothing.
   *
   * Those four are the cost of the current setting. A settings form that shows
   * the field but not the consequence makes the number a guess forever.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import SettingsFormPanel from '$lib/v2/components/SettingsFormPanel.svelte';
  import { count } from '$lib/v2/format.js';
  import { REOPEN_TO_STATUSES } from '$lib/v2/enums.js';
  import { RotateCcw, MailX } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let editing = $state(false);

  let p = $derived(data.policy);
</script>

<PageHeader title="Reopen policy">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    {p.is_enabled
      ? `Replies within ${p.reopen_window_days} days bring a closed ticket back`
      : 'Closed tickets stay closed'}
  {/snippet}
  {#snippet actions()}
    {#if data.can_edit && !editing}
      <button class="v2-btn v2-btn-primary" onclick={() => (editing = true)}>Edit policy</button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:16px;flex:none">
  <div class="v2-stats">
    <StatCard
      label="Reopened, 30 days"
      value={count(p.reopened_last_30d)}
      tone="ink"
      detail="Closed, then a reply landed in time"
    />
    <!-- "n/a" rather than 0 while the policy is off. `_evaluate_reopen` returns
         `None` on `if not policy["is_enabled"]` BEFORE it compares the window,
         and the `out_of_reopen_window` flag this metric counts is written only
         for the "out_of_window" return. So with reopening off nothing is ever
         flagged and the count is always zero, in exactly the state where every
         reply to a closed ticket reopens nothing. A plain 0 there is
         reassurance about the one thing certainly happening. -->
    <StatCard
      label="Missed the window"
      value={p.is_enabled ? count(p.replies_after_window_30d) : 'n/a'}
      tone={p.is_enabled && p.replies_after_window_30d > 0 ? 'clay' : 'slate'}
      detail={p.is_enabled ? 'Replies that reopened nothing' : 'Not counted while reopening is off'}
    />
    <StatCard
      label="Median reply"
      value={`${p.median_days_to_reply}d`}
      tone="slate"
      detail="After the ticket was closed"
    />
  </div>
</div>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#if editing}
      <SettingsFormPanel
        title="Reopen policy"
        action="?/update"
        error={form?.update?.error}
        submitLabel="Save policy"
        oncancel={() => (editing = false)}
        ondone={() => (editing = false)}
      >
        {#snippet fields()}
          <div class="v2-field v2-sfp-wide">
            <label for="f-enabled">Reopen on customer reply</label>
            <label style="display:flex;gap:8px;align-items:center;font-weight:400">
              <input
                id="f-enabled"
                type="checkbox"
                name="is_enabled"
                value="true"
                checked={p.is_enabled}
              />
              Off means a reply is filed on the closed ticket and nothing else happens.
            </label>
          </div>

          <div class="v2-field">
            <label for="f-window">Window, in days</label>
            <input
              id="f-window"
              class="v2-input"
              type="number"
              name="reopen_window_days"
              min="1"
              max="365"
              required
              value={p.reopen_window_days}
            />
            <p class="v2-hint">Counted from when the ticket was closed, in calendar days.</p>
          </div>

          <div class="v2-field">
            <label for="f-status">Comes back as</label>
            <select id="f-status" class="v2-input" name="reopen_to_status">
              {#each REOPEN_TO_STATUSES as status (status)}
                <option value={status} selected={status === p.reopen_to_status}>{status}</option>
              {/each}
            </select>
            <p class="v2-hint">
              Only these three. A ticket reopened into a closed status would close again on arrival.
            </p>
          </div>

          <div class="v2-field v2-sfp-wide">
            <label for="f-notify">Tell the assignee</label>
            <label style="display:flex;gap:8px;align-items:center;font-weight:400">
              <input
                id="f-notify"
                type="checkbox"
                name="notify_assigned"
                value="true"
                checked={p.notify_assigned}
              />
              The person the ticket was assigned to when it closed.
            </label>
          </div>
        {/snippet}
      </SettingsFormPanel>
    {/if}
    <div class="v2-split">
      <div>
        <div class="v2-label" style="margin-bottom:10px">The rule</div>
        <div class="v2-card" style="overflow:hidden">
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Reopen on customer reply</b>
              <span class="v2-sub" style="font-size:11.5px">
                Off means a reply is filed on the closed ticket and nothing else happens.
              </span>
            </div>
            <Pill tone={p.is_enabled ? 'moss' : 'slate'}>{p.is_enabled ? 'On' : 'Off'}</Pill>
          </div>
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Window</b>
              <span class="v2-sub" style="font-size:11.5px">
                Counted from when the ticket was closed, in calendar days.
              </span>
            </div>
            <span class="v2-num" style="font-size:13px">{p.reopen_window_days} days</span>
          </div>
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Comes back as</b>
              <!-- Must be a non-terminal status: reopening a ticket into a
                   closed status would close it again on arrival. -->
              <span class="v2-sub" style="font-size:11.5px">
                Has to be a status that counts as open.
              </span>
            </div>
            <Pill tone="ink">{p.reopen_to_status}</Pill>
          </div>
          <div class="v2-setting">
            <div class="v2-setting-body">
              <b>Tell the assignee</b>
              <span class="v2-sub" style="font-size:11.5px">
                The person the ticket was assigned to when it closed.
              </span>
            </div>
            <Pill tone={p.notify_assigned ? 'moss' : 'slate'}>
              {p.notify_assigned ? 'Yes' : 'No'}
            </Pill>
          </div>
        </div>
      </div>

      <div>
        <div class="v2-label" style="margin-bottom:10px">What this changes</div>
        <div class="v2-card" style="padding:15px 16px">
          <div style="display:flex;gap:10px;align-items:flex-start">
            <RotateCcw size={16} style="color:var(--v2-slate);flex:none;margin-top:2px" />
            <p class="v2-sub" style="font-size:12.5px;margin:0;line-height:1.5">
              {#if p.is_enabled}
                A reply inside the window puts the ticket back in the queue as
                <b style="font-weight:600;color:var(--v2-ink)">{p.reopen_to_status}</b>, keeping its
                history and its original number. It is the same ticket, not a new one, so first
                response and resolution are still measured against the original open.
              {:else}
                <!-- Present tense, and the policy is off, so this cannot be
                     written as though a reply still reopened anything. -->
                Nothing. A reply is filed on the closed ticket, the ticket stays closed and nobody is
                told. Turned on, a reply inside the window would put it back in the queue as
                <b style="font-weight:600;color:var(--v2-ink)">{p.reopen_to_status}</b>, keeping its
                history and its number.
              {/if}
            </p>
          </div>
        </div>

        {#if !p.is_enabled}
          <div class="v2-card" style="padding:15px 16px;margin-top:12px">
            <div style="display:flex;gap:10px;align-items:flex-start">
              <MailX size={16} style="color:var(--v2-clay);flex:none;margin-top:2px" />
              <div>
                <div style="font-weight:600;font-size:13px">Nothing is counting the misses</div>
                <p class="v2-sub" style="font-size:12.5px;margin:5px 0 0;line-height:1.5">
                  With reopening off, a reply to a closed ticket is filed and nothing else happens,
                  and nothing records it as having missed anything. The figure above is a zero
                  because nothing is measured, not because nothing is being lost.
                </p>
              </div>
            </div>
          </div>
        {:else if p.replies_after_window_30d > 0}
          <div class="v2-card" style="padding:15px 16px;margin-top:12px">
            <div style="display:flex;gap:10px;align-items:flex-start">
              <MailX size={16} style="color:var(--v2-clay);flex:none;margin-top:2px" />
              <div>
                <div style="font-weight:600;font-size:13px">
                  <span class="v2-num">{count(p.replies_after_window_30d)}</span> replies arrived too
                  late
                </div>
                <p class="v2-sub" style="font-size:12.5px;margin:5px 0 0;line-height:1.5">
                  They landed on tickets closed more than
                  <span class="v2-num">{p.reopen_window_days}</span> days earlier, so no ticket came back
                  and nobody was told. Those customers are still waiting.
                </p>
              </div>
            </div>
          </div>
        {/if}

        <p class="v2-sub" style="font-size:11.5px;margin-top:14px">
          Which addresses accept replies at all is set in
          <a href={resolve('/settings/inbound-email')} style="color:inherit">inbound email</a>.
        </p>
      </div>
    </div>
  </div>
</div>
