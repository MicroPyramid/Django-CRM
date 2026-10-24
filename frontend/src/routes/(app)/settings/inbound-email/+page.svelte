<script>
  import { resolve } from '$app/paths';
  /**
   * The addresses that turn email into tickets, or into leads (`creates`).
   *
   * Two things this page is careful about:
   *
   * 1. NO SECRET COMES BACK. InboundMailbox carries a `webhook_secret` column
   *    (Postmark's basic-auth password, Mailgun's signing key). It is
   *    write-only: the form field is never prefilled, the form says only
   *    whether one is stored (`has_webhook_secret`), and a blank field sends
   *    nothing, so an edit cannot blank it. SES is proved by the SNS signature
   *    plus the topic pin (`topic_arn`, submitted only when changed,
   *    `topicArnEdit`); both are checked in `InboundMailboxWebhookView.post`.
   * 2. An address that creates nothing does not bounce. It keeps accepting
   *    mail and the webhook stops opening cases, so the sender gets silence
   *    rather than a delivery failure. That is a materially different thing
   *    from "off", and a grey pill saying "Off" does not say it.
   *
   * The ways an address creates nothing live in `./delivery.js`: turned
   * off, a provider the webhook does not implement, and an address not yet
   * connected (no SNS pin, or no stored webhook secret).
   */
  import { enhance } from '$app/forms';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '#lib/v2/components/SettingsCrumb.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import SettingsFormPanel from '#lib/v2/components/SettingsFormPanel.svelte';
  import ConfirmAction from '#lib/v2/components/ConfirmAction.svelte';
  import { count, relativeDays } from '#lib/v2/format.js';
  import { MAILBOX_PROVIDER_LABEL, PRIORITY_TONE } from '#lib/v2/enums.js';
  import { missingOption, inactiveOptionLabel } from '#lib/v2/pickers.js';
  import { sourceLabel, sourceOptions } from '#lib/v2/lead-sources.js';
  import { isOn } from '#lib/v2/modules.js';
  import {
    deliveryState,
    deliveryLabel,
    deliveryTone,
    deliveryExplanation,
    deliveringCount,
    silentMailboxes,
    providerChoiceLabel,
    SECRET_PROVIDERS,
    webhookSetupUrl
  } from './delivery.js';
  import { Plus, MailWarning, KeyRound } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  // cases.InboundMailbox.PROVIDER_CHOICES is MAILBOX_PROVIDER_LABEL's key
  // order. PRIORITY_CHOICE and CASE_TYPE mirror ticket-approvals' own local
  // copies: value and label are the same string for both, and no shared map
  // exists to derive them from.
  const PROVIDERS = ['ses', 'mailgun', 'postmark', 'imap'];
  const PRIORITIES = ['Low', 'Normal', 'High', 'Urgent'];
  const CASE_TYPES = ['Question', 'Incident', 'Problem'];

  let totals = $derived(data.totals);
  let mailboxes = $derived(data.mailboxes);
  let delivering = $derived(deliveringCount(mailboxes));
  let silent = $derived(silentMailboxes(mailboxes));

  // `null` when the panel is closed, `'new'` when adding, or the mailbox
  // object when editing that row. One panel, two modes, so two rows can
  // never be open for edit at once.
  let editing = $state(/** @type {any} */ (null));
  // What the open form makes, and whether the server picks the address.
  let creates = $state('tickets');
  // The provider picked in the open form, which decides the credential shown.
  let provider = $state('ses');
  let addressMode = $state('own');

  // Lead addresses need an API that has them and Leads switched on. The page
  // is also open while only Leads is on, and then offers nothing else.
  let offerLeads = $derived(data.can_create_leads && isOn(data.modules, 'leads'));
  let ticketsOn = $derived(isOn(data.modules, 'tickets'));
  let generating = $derived(editing === 'new' && addressMode === 'generate');
  // A generated address is the server's, routed by its own catch-all.
  let serverOwned = $derived(generating || (editing && editing !== 'new' && editing.is_generated));

  function openCreate() {
    editing = 'new';
    creates = ticketsOn ? 'tickets' : 'leads';
    provider = 'ses';
    addressMode = data.generated_domain ? 'generate' : 'own';
  }

  function openEdit(m) {
    editing = m;
    creates = m.creates;
    provider = m.provider;
    addressMode = 'own';
  }

  /** The lead source a new lead address starts with: Email, when the org has it on. */
  let newLeadSource = $derived(
    sourceOptions(data.sources).some((s) => s.key === 'email') ? 'email' : ''
  );

  // The stored default assignee when the picker cannot offer it, because the
  // profile has been deactivated since it was chosen. `getOrgPeopleAndTeams`
  // returns active profiles only, `InboundMailbox.default_assignee` keeps
  // whoever was set. A select with no matching option submits nothing, which
  // `readValues` reads as `''` and `buildBody` sends as `null`, so an edit
  // made to change the address or the provider would also quietly move this
  // mailbox back to Unassigned.
  let missingAssignee = $derived(
    editing && editing !== 'new' ? missingOption(data.people, editing.default_assignee) : null
  );
</script>

<PageHeader title="Inbound email">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(delivering)}</span> of
    <span class="v2-num">{count(totals.count)}</span> addresses working{#if ticketsOn}
      · <span class="v2-num">{count(totals.cases_last_30d)}</span> tickets in the last 30 days
    {/if}
  {/snippet}
  {#snippet actions()}
    {#if data.can_edit && !editing}
      <button class="v2-btn v2-btn-primary" onclick={openCreate}><Plus />Add address</button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if editing}
      <SettingsFormPanel
        title={editing === 'new' ? 'New address' : `Edit ${editing.address}`}
        action={editing === 'new' ? '?/create' : '?/update'}
        error={editing === 'new' ? form?.create?.error : form?.update?.error}
        submitLabel={editing === 'new' ? 'Add address' : 'Save address'}
        oncancel={() => (editing = null)}
        ondone={() => (editing = null)}
      >
        {#snippet fields()}
          {#if editing !== 'new'}
            <input type="hidden" name="id" value={editing.id} />
          {/if}

          {#if offerLeads}
            <div class="v2-field">
              <label for="m-creates">Each email becomes</label>
              <select id="m-creates" class="v2-input" name="creates" bind:value={creates}>
                {#if ticketsOn || (editing !== 'new' && editing.creates === 'tickets')}
                  <option value="tickets">A ticket</option>
                {/if}
                <option value="leads">A lead</option>
              </select>
              {#if creates === 'leads'}
                <p class="v2-hint">
                  Forward enquiries here, or point a portal's notification email at it. The enquirer
                  becomes the lead, never the portal that sent it.
                </p>
              {/if}
            </div>
          {/if}

          {#if editing === 'new' && data.generated_domain}
            <div class="v2-field">
              <span class="v2-label" id="m-mode-label">Address</span>
              <div role="radiogroup" aria-labelledby="m-mode-label" class="v2-mbx-modes">
                <label>
                  <input
                    type="radio"
                    name="address_mode"
                    value="generate"
                    bind:group={addressMode}
                  />
                  Generate one at {data.generated_domain}
                </label>
                <label>
                  <input type="radio" name="address_mode" value="own" bind:group={addressMode} />
                  Use an address of our own
                </label>
              </div>
            </div>
          {/if}

          {#if serverOwned}
            {#if editing !== 'new'}
              <div class="v2-field">
                <span class="v2-label">Address</span>
                <p class="v2-hint" style="margin:0">
                  {editing.address}, made by this server. It cannot be changed; add a new one
                  instead.
                </p>
              </div>
            {/if}
          {:else}
            <div class="v2-field">
              <label for="m-address">Address</label>
              <input
                id="m-address"
                class="v2-input"
                type="email"
                name="address"
                required
                value={editing === 'new' ? '' : editing.address}
              />
              {#if editing !== 'new'}
                <p class="v2-hint">
                  Mail to the old address stops becoming {editing.creates === 'leads'
                    ? 'leads'
                    : 'tickets'}.
                </p>
              {/if}
            </div>

            <div class="v2-field">
              <label for="m-provider">Provider</label>
              <select id="m-provider" class="v2-input" name="provider" bind:value={provider}>
                {#each PROVIDERS as p (p)}
                  <option value={p}>
                    {providerChoiceLabel(p, MAILBOX_PROVIDER_LABEL[p])}
                  </option>
                {/each}
              </select>
              <p class="v2-hint">
                AWS SES, Postmark and Mailgun deliver. IMAP is stored and accepted, and mail sent to
                an address using it becomes nothing until that integration exists.
              </p>
            </div>

            {#if SECRET_PROVIDERS.includes(provider)}
              {@const setupUrl =
                editing === 'new' ? null : webhookSetupUrl(provider, editing.id, data.api_base)}
              <div class="v2-field">
                <label for="m-secret"
                  >{provider === 'postmark' ? 'Basic-auth password' : 'Webhook signing key'}</label
                >
                <input
                  id="m-secret"
                  class="v2-input"
                  type="password"
                  name="webhook_secret"
                  autocomplete="new-password"
                  autocapitalize="off"
                  spellcheck="false"
                  maxlength="128"
                  placeholder={editing !== 'new' && editing.has_webhook_secret
                    ? 'A secret is stored; type to replace it'
                    : ''}
                />
                <p class="v2-hint">
                  {editing !== 'new' && editing.has_webhook_secret
                    ? 'A secret is stored. It is never shown; leave blank to keep it.'
                    : 'No secret is stored, so every post to this address is refused.'}
                  {provider === 'postmark'
                    ? 'Postmark sends it as the basic-auth password in the webhook URL.'
                    : "This is your Mailgun account's HTTP webhook signing key."}
                </p>
                {#if setupUrl}
                  <p class="v2-hint">
                    {provider === 'postmark' ? 'Inbound webhook URL' : 'Route action'}:
                    <code style="word-break:break-all">{setupUrl}</code>
                  </p>
                {:else if editing === 'new'}
                  <p class="v2-hint">The setup URL appears here once the address is saved.</p>
                {/if}
              </div>
            {:else}
              <div class="v2-field">
                <label for="m-topic">SNS Topic ARN</label>
                <input
                  id="m-topic"
                  class="v2-input"
                  name="topic_arn"
                  autocomplete="off"
                  autocapitalize="off"
                  spellcheck="false"
                  placeholder="arn:aws:sns:us-east-1:123456789012:inbound-mail"
                  value={editing === 'new' ? '' : (editing.topic_arn ?? '')}
                />
                <input
                  type="hidden"
                  name="topic_arn_was"
                  value={editing === 'new' ? '' : (editing.topic_arn ?? '')}
                />
                <p class="v2-hint">
                  Mail is accepted only from this exact topic. Left blank, it is set by the first
                  subscription AWS confirms from an AWS account this server allows. Clearing it
                  stops mail until it is set again.
                </p>
              </div>
            {/if}
          {/if}

          {#if offerLeads}
            <!-- Drawn either way and only hidden, so switching what the
                 address makes and back keeps both sets of defaults. -->
            <div class="v2-field" hidden={creates !== 'leads'}>
              <label for="m-lead-source">Lead source</label>
              <select
                id="m-lead-source"
                class="v2-input"
                name="lead_source"
                value={editing === 'new' ? newLeadSource : editing.lead_source}
              >
                <option value="">Not specified</option>
                {#each sourceOptions(data.sources, editing === 'new' ? '' : editing.lead_source) as s (s.key)}
                  <option value={s.key}>{s.label}</option>
                {/each}
              </select>
            </div>
            <div class="v2-field" hidden={creates !== 'leads'}>
              <label for="m-lead-detail">Sub-source</label>
              <input
                id="m-lead-detail"
                class="v2-input"
                name="lead_source_detail"
                maxlength="100"
                placeholder="e.g. Zillow"
                value={editing === 'new' ? '' : editing.lead_source_detail}
              />
            </div>
          {/if}

          <div class="v2-field" hidden={creates === 'leads'}>
            <label for="m-priority">Opens as priority</label>
            <select id="m-priority" class="v2-input" name="default_priority">
              {#each PRIORITIES as p (p)}
                <option
                  value={p}
                  selected={editing === 'new' ? p === 'Normal' : editing.default_priority === p}
                >
                  {p}
                </option>
              {/each}
            </select>
          </div>

          <div class="v2-field" hidden={creates === 'leads'}>
            <label for="m-type">Opens as type</label>
            <select id="m-type" class="v2-input" name="default_case_type">
              <option value="" selected={editing === 'new' || !editing.default_case_type}>
                None
              </option>
              {#each CASE_TYPES as t (t)}
                <option value={t} selected={editing !== 'new' && editing.default_case_type === t}>
                  {t}
                </option>
              {/each}
            </select>
          </div>

          <div class="v2-field">
            <label for="m-assignee">Default assignee</label>
            <select id="m-assignee" class="v2-input" name="default_assignee_id">
              <option value="" selected={editing === 'new' || !editing.default_assignee}>
                Unassigned
              </option>
              {#if missingAssignee}
                <option value={missingAssignee.id} selected>
                  {inactiveOptionLabel(missingAssignee.name)}
                </option>
              {/if}
              {#each data.people as p (p.id)}
                <option
                  value={p.id}
                  selected={editing !== 'new' && editing.default_assignee?.id === p.id}
                >
                  {p.name}
                </option>
              {/each}
            </select>
            {#if missingAssignee}
              <p class="v2-hint">
                Deactivated users are not assigned. New tickets from this address go to routing
                until you choose someone else.
              </p>
            {:else if creates === 'leads'}
              <p class="v2-hint">
                Owns every lead this address makes. For leads that follow the agent, give each agent
                an address of their own.
              </p>
            {/if}
          </div>

          {#if editing === 'new'}
            <div class="v2-field">
              <label for="m-active">Active</label>
              <label style="display:flex;gap:8px;align-items:center;font-weight:400">
                <input id="m-active" type="checkbox" name="is_active" value="true" checked />
                Starts creating {creates === 'leads' ? 'leads' : 'tickets'} from mail to this address
                as soon as it is saved.
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

    <!-- On, and creating nothing. A turned-off address is not in here: that
         state was chosen, and the row already reads correctly. These two were
         drawn as working right up until this banner existed. -->
    {#if silent.length}
      <div class="v2-mbx-banner">
        <MailWarning size={17} style="color:var(--v2-clay);flex:none;margin-top:1px" />
        <div>
          <div style="font-weight:600;font-size:13px">
            {silent.map((m) => m.address).join(', ')}
            {silent.length === 1
              ? 'is switched on and creates nothing'
              : 'are switched on and create nothing'}
          </div>
          <p class="v2-sub" style="font-size:12px;margin:4px 0 0;line-height:1.5">
            Mail keeps arriving and nothing bounces, so anyone writing there gets no ticket and no
            error, just silence. Each address says below what is stopping it.
          </p>
        </div>
      </div>
    {/if}

    <div class="v2-label" style="margin-bottom:10px">Addresses</div>
    <div style="display:flex;flex-direction:column;gap:9px">
      {#each mailboxes as m (m.id)}
        {@const state = deliveryState(m)}
        {@const why = deliveryExplanation(
          state,
          MAILBOX_PROVIDER_LABEL[m.provider],
          m.creates,
          m.provider
        )}
        <div class="v2-card v2-mbx" style="opacity:{state === 'live' ? 1 : 0.68}">
          <div style="flex:1;min-width:0">
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <b style="font-size:13.5px;overflow-wrap:anywhere">{m.address}</b>
              <Pill tone={deliveryTone(state)}>{deliveryLabel(state, m.creates)}</Pill>
            </div>
            <div class="v2-sub" style="font-size:11.5px;margin-top:4px">
              {m.is_generated ? 'Made by this server' : MAILBOX_PROVIDER_LABEL[m.provider]} ·
              {#if m.creates === 'leads'}
                last mail {relativeDays(m.last_received_at)}
              {:else if m.cases_last_30d}
                <span class="v2-num">{count(m.cases_last_30d)}</span> tickets in 30 days · last mail
                {relativeDays(m.last_received_at)}
              {:else}
                no tickets in 30 days · last mail {relativeDays(m.last_received_at)}
              {/if}
            </div>
            {#if why}
              <p class="v2-sub" style="font-size:11.5px;margin:6px 0 0;line-height:1.5">{why}</p>
            {/if}

            <!-- What a ticket from here starts out as. These are the defaults
                 a routing rule then reads, so they are worth stating next to
                 the address rather than behind an edit dialog. -->
            {#if m.creates === 'leads'}
              <div class="v2-mbx-defaults">
                <span class="v2-sub">Makes leads</span>
                {#if m.lead_source}
                  <Pill tone="slate">{sourceLabel(data.sources, m.lead_source)}</Pill>
                {/if}
                {#if m.lead_source_detail}
                  <span class="v2-sub">{m.lead_source_detail}</span>
                {/if}
                <span class="v2-sub">
                  {m.default_assignee ? `owned by ${m.default_assignee.name}` : 'owned by nobody'}
                </span>
              </div>
            {:else}
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
            {/if}
          </div>

          {#if data.can_edit}
            <div style="display:flex;gap:6px;align-items:center;flex:none">
              <button class="v2-btn v2-btn-sm" type="button" onclick={() => openEdit(m)}>
                Edit
              </button>
              {#if m.is_active}
                <ConfirmAction
                  action="?/deactivate"
                  label="Turn off"
                  confirmLabel="Turn off"
                  explain="Stops {m.creates === 'leads'
                    ? 'making leads'
                    : 'opening tickets'} from this address. It stays in the list, off, until turned back on."
                  hidden={{ id: m.id }}
                />
              {:else}
                <form method="POST" action="?/activate" use:enhance>
                  <input type="hidden" name="id" value={m.id} />
                  <button class="v2-btn v2-btn-sm" type="submit">Turn on</button>
                </form>
              {/if}
              <ConfirmAction
                action="?/remove"
                label="Delete"
                confirmLabel="Delete"
                explain="Deleted permanently. Mail to this address stops becoming {m.creates ===
                'leads'
                  ? 'leads'
                  : 'tickets'}, and its topic pin goes with it."
                hidden={{ id: m.id }}
              />
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <!--
      What actually authenticates a delivery, which is not what this card used
      to claim. It described a per-address shared secret the server minted on
      create; the server mints nothing, nothing in the backend compares that
      column, and an admin reading the old wording would have believed their
      inbound mail was protected by a credential that is not in the path. The
      real pair, the SNS signature and the topic pin, is stated instead.
    -->
    <div class="v2-card" style="padding:15px 16px;margin-top:20px">
      <div style="display:flex;gap:10px;align-items:flex-start">
        <KeyRound size={16} style="color:var(--v2-slate);flex:none;margin-top:2px" />
        <div>
          <div style="font-weight:600;font-size:13px">How a delivery is proved genuine</div>
          <p class="v2-sub" style="font-size:12.5px;margin:5px 0 0;line-height:1.5">
            Two checks, and mail has to clear both: AWS signs each notification, and the address has
            to be pinned to the exact SNS topic it was subscribed to. The signature alone proves
            only that some AWS account sent it, so without the pin anyone who learned an address's
            id could have AWS sign forged mail into this organisation. An admin can enter the pin as
            the address's Topic ARN. Left blank, it is set by the first subscription AWS confirms
            from an AWS account this server allows; a subscription from any other account is
            refused. Only admins can see the ARN, because it carries the AWS account id.
          </p>
          {#if data.generated_domain}
            <p class="v2-sub" style="font-size:12.5px;margin:8px 0 0;line-height:1.5">
              An address this server generated has no pin of its own: one webhook receives mail for
              every generated address and checks it against the server's own topic.
            </p>
          {/if}
          <p class="v2-sub" style="font-size:12.5px;margin:8px 0 0;line-height:1.5">
            A Postmark or Mailgun address is proved by a secret an admin stores on it instead:
            Postmark's basic-auth password or Mailgun's signing key. With none stored, every post is
            refused. It is never readable back, here or anywhere.
          </p>
        </div>
      </div>
    </div>

    <p class="v2-sub" style="font-size:11.5px;margin-top:14px">
      Where a new ticket goes after it is created is decided by
      <a href={resolve('settings/routing')} style="color:inherit">ticket routing</a>, not by these
      defaults.
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
  .v2-mbx-modes {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .v2-mbx-modes label {
    display: flex;
    gap: 8px;
    align-items: center;
    min-height: 44px;
    font-weight: 400;
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
