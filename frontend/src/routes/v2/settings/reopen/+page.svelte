<script>
  /**
   * Whether a customer's reply can bring a closed ticket back.
   *
   * One row per org, four fields — small enough that v1's form is not wrong,
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
  import { count } from '$lib/v2/format.js';
  import { RotateCcw, MailX } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

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
    <button class="v2-btn v2-btn-primary">Edit policy</button>
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
    <StatCard
      label="Missed the window"
      value={count(p.replies_after_window_30d)}
      tone={p.replies_after_window_30d > 0 ? 'clay' : 'slate'}
      detail="Replies that reopened nothing"
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
              A reply inside the window puts the ticket back in the queue as
              <b style="font-weight:600;color:var(--v2-ink)">{p.reopen_to_status}</b>, keeping its
              history and its original number. It is the same ticket, not a new one, so first
              response and resolution are still measured against the original open.
            </p>
          </div>
        </div>

        {#if p.replies_after_window_30d > 0}
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
          <a href="/v2/settings/inbound-email" style="color:inherit">inbound email</a>.
        </p>
      </div>
    </div>
  </div>
</div>
