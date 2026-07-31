<script>
  /**
   * The addresses that turn email into tickets.
   *
   * Two things this page is careful about:
   *
   * 1. NO SECRETS. InboundMailbox carries `webhook_secret` and
   *    `imap_password_enc`. The webhook secret is what proves a delivery
   *    really came from the provider — anything holding it can forge tickets
   *    into this org, or read the ones it forges. It is not fetched, not
   *    rendered, and not masked-but-present in the DOM. Rotation belongs
   *    behind an explicit action, not on a page you can arrive at by browsing.
   * 2. An inactive mailbox does not bounce. The address keeps accepting mail
   *    and the webhook stops creating cases, so the sender gets silence rather
   *    than a delivery failure. That is a materially different thing from
   *    "off", and a grey pill saying "Off" does not say it.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import { count, relativeDays } from '$lib/v2/format.js';
  import { MAILBOX_PROVIDER_LABEL, PRIORITY_TONE } from '$lib/v2/enums.js';
  import { Plus, MailWarning, KeyRound } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);
  let mailboxes = $derived(data.mailboxes);
  let silent = $derived(mailboxes.filter((m) => !m.is_active));
</script>

<PageHeader title="Inbound email">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> of
    <span class="v2-num">{count(totals.count)}</span> addresses creating tickets ·
    <span class="v2-num">{count(totals.cases_last_30d)}</span> in the last 30 days
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary"><Plus />Add address</button>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if silent.length}
      <div class="v2-mbx-banner">
        <MailWarning size={17} style="color:var(--v2-clay);flex:none;margin-top:1px" />
        <div>
          <div style="font-weight:600;font-size:13px">
            {silent.map((m) => m.address).join(', ')}
            {silent.length === 1
              ? 'accepts mail and creates nothing'
              : 'accept mail and create nothing'}
          </div>
          <p class="v2-sub" style="font-size:12px;margin:4px 0 0;line-height:1.5">
            Turning an address off stops it opening tickets. It does not stop mail arriving and does
            not bounce, so anyone writing there gets no ticket and no error — just silence.
          </p>
        </div>
      </div>
    {/if}

    <div class="v2-label" style="margin-bottom:10px">Addresses</div>
    <div style="display:flex;flex-direction:column;gap:9px">
      {#each mailboxes as m (m.id)}
        <div class="v2-card v2-mbx" style="opacity:{m.is_active ? 1 : 0.68}">
          <div style="flex:1;min-width:0">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <b style="font-size:13.5px">{m.address}</b>
              <Pill tone={m.is_active ? 'moss' : 'clay'}>
                {m.is_active ? 'Creating tickets' : 'Creating nothing'}
              </Pill>
            </div>
            <div class="v2-sub" style="font-size:11.5px;margin-top:4px">
              {MAILBOX_PROVIDER_LABEL[m.provider]} ·
              {#if m.cases_last_30d}
                <span class="v2-num">{count(m.cases_last_30d)}</span> tickets in 30 days · last mail
                {relativeDays(m.last_received_at)}
              {:else}
                no tickets in 30 days · last mail {relativeDays(m.last_received_at)}
              {/if}
            </div>

            <!-- What a ticket from here starts out as. These are the defaults
                 a routing rule then reads, so they are worth stating next to
                 the address rather than behind an edit dialog. -->
            <div class="v2-mbx-defaults">
              <span class="v2-sub">Opens as</span>
              <Pill tone={PRIORITY_TONE[m.default_priority]}>{m.default_priority}</Pill>
              {#if m.default_case_type}
                <Pill tone="slate">{m.default_case_type}</Pill>
              {/if}
              <span class="v2-sub">
                {m.default_assignee ? `assigned to ${m.default_assignee.name}` : 'then routed'}
              </span>
            </div>
          </div>

          <button class="v2-btn v2-btn-sm" style="flex:none">Edit</button>
        </div>
      {/each}
    </div>

    <!--
      The webhook secret is the credential that authenticates deliveries from
      the provider. It is not on this page in any form — not shown, not
      masked, not sitting in the payload behind a click-to-reveal. See api.js
      for the same rule stated at the boundary.
    -->
    <div class="v2-card" style="padding:15px 16px;margin-top:20px">
      <div style="display:flex;gap:10px;align-items:flex-start">
        <KeyRound size={16} style="color:var(--v2-slate);flex:none;margin-top:2px" />
        <div>
          <div style="font-weight:600;font-size:13px">Webhook secrets are not shown here</div>
          <p class="v2-sub" style="font-size:12.5px;margin:5px 0 0;line-height:1.5">
            Each address has a shared secret that proves a delivery really came from the provider.
            Anything holding it can post mail into this organisation as though a customer sent it,
            so it is never rendered on a page — rotating one is an explicit action that shows the
            new value once.
          </p>
        </div>
      </div>
    </div>

    <p class="v2-sub" style="font-size:11.5px;margin-top:14px">
      Where a new ticket goes after it is created is decided by
      <a href="/settings/routing" style="color:inherit">ticket routing</a>, not by these defaults.
    </p>
  </div>
</div>

<style>
  .v2-mbx {
    display: flex;
    gap: 13px;
    align-items: flex-start;
    padding: 14px 16px;
  }
  .v2-mbx-defaults {
    display: flex;
    gap: 6px;
    align-items: center;
    flex-wrap: wrap;
    margin-top: 9px;
    font-size: 11.5px;
  }
  .v2-mbx-banner {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding: 14px 16px;
    margin-bottom: 18px;
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    background: var(--v2-card);
  }
</style>
