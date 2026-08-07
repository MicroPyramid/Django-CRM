<script>
  import { resolve } from '$app/paths';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import NextAction from '$lib/v2/components/NextAction.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import { money, longDate, relativeDays, daysSince } from '$lib/v2/format.js';
  import { INVOICE_STATUS_TONE, invoiceStatusLabel } from '$lib/v2/enums.js';
  import { enhance } from '$app/forms';
  import { ChevronRight } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let { invoice, lineItems } = $derived(data);

  let daysLate = $derived(invoice.due_date ? daysSince(invoice.due_date) : null);
  let busy = $state(false);

  /** The real INVOICE_STATUS progression, up to whatever this invoice is. */
  const PATH = ['Draft', 'Sent', 'Viewed', 'Paid'];
  let reached = $derived(
    invoice.status === 'Overdue'
      ? ['Draft', 'Sent', 'Viewed']
      : PATH.slice(0, PATH.indexOf(invoice.status) + 1)
  );

  /** A form submit that flips `busy` so the buttons show they are working. */
  const working = () => {
    busy = true;
    return async (/** @type {any} */ { update }) => {
      await update();
      busy = false;
    };
  };
</script>

<PageHeader title={invoice.invoice_number} record>
  {#snippet crumb()}
    <a href={resolve('/invoices')}>Invoices</a>
    <ChevronRight size={12} />
    <a href={resolve(`/accounts/${invoice.account.id}`)}>{invoice.account.name}</a>
  {/snippet}
  {#snippet actions()}
    <a class="v2-btn" href={resolve(`/invoices/${invoice.id}/pdf`)} target="_blank" rel="noopener">
      Download PDF
    </a>
    <form method="POST" action="?/duplicate" use:enhance={working} style="display:inline">
      <button class="v2-btn" disabled={busy}>Duplicate</button>
    </form>
    {#if !invoice.is_settled}
      <!-- In the header, not the rail: the rail is hidden below 1180px, and a
           destructive action a phone cannot reach is worse than one it can.

           One condition is the whole rule. `is_settled` is Paid or Cancelled
           (SETTLED in $lib/server/v2/invoices.js), which is exactly what
           InvoiceCancelView refuses, so a second `status !== 'Cancelled'`
           test here could never change the answer. It used to be there. -->
      <form method="POST" action="?/cancel" use:enhance={working} style="display:inline">
        <button class="v2-btn" disabled={busy} style="color:var(--v2-rust)">Cancel</button>
      </form>
    {/if}
  {/snippet}
</PageHeader>

<div style="display:flex;flex:1;min-height:0;overflow:hidden">
  <div class="v2-main">
    <div class="v2-scroll">
      <div class="v2-pad" style="padding-top:16px;padding-bottom:32px">
        {#if form?.error}
          <div style="margin-bottom:16px">
            <NextAction label="That did not work" text={form.error} tone="rust" />
          </div>
        {:else if form?.sent}
          <!-- The re-send has no other visible effect: it updates sent_at and
               re-mails the client, but the reminder counters are the automated
               schedule's, not this button's. Say so, or the click looks inert. -->
          <p
            class="v2-sub"
            style="color:var(--v2-moss);font-size:12.5px;margin:0 0 16px;font-weight:550"
          >
            Sent to the client.
          </p>
        {/if}

        {#if invoice.is_overdue}
          <div style="margin-bottom:20px">
            <NextAction
              label="{daysLate} days past due"
              text={invoice.reminder_count
                ? `${invoice.reminder_count} reminder${invoice.reminder_count === 1 ? '' : 's'} sent${
                    invoice.last_reminder_sent
                      ? `, last ${relativeDays(invoice.last_reminder_sent)}`
                      : ''
                  }.`
                : 'No reminder sent yet.'}
              tone="rust"
            />
            <form method="POST" action="?/send" use:enhance={working} style="margin-top:8px">
              <button class="v2-btn v2-btn-sm" disabled={busy}>Send a reminder</button>
            </form>
          </div>
        {:else if invoice.status === 'Draft'}
          <div style="margin-bottom:20px">
            <NextAction text="This invoice has never been sent." />
            <form method="POST" action="?/send" use:enhance={working} style="margin-top:8px">
              <button class="v2-btn v2-btn-sm" disabled={busy}>Send it</button>
            </form>
          </div>
        {/if}

        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:20px">
          {#each PATH as step, i (step)}
            {#if i > 0}<ChevronRight size={12} style="color:var(--v2-slate)" />{/if}
            <span
              class="v2-pill"
              style={reached.includes(step)
                ? `color:var(--v2-ink);background:color-mix(in srgb, var(--v2-ink) 9%, transparent)`
                : 'color:var(--v2-slate);background:var(--v2-line-soft)'}
            >
              {step}
            </span>
          {/each}
          {#if invoice.is_overdue}
            <ChevronRight size={12} style="color:var(--v2-slate)" />
            <Pill tone="rust">Overdue</Pill>
          {:else if invoice.status === 'Cancelled'}
            <ChevronRight size={12} style="color:var(--v2-slate)" />
            <Pill tone="slate">Cancelled</Pill>
          {/if}
          <span class="v2-sub" style="margin-left:10px">
            Issued {longDate(invoice.issued_date)} · due {longDate(invoice.due_date)}
          </span>
        </div>

        <div class="v2-card" style="overflow:hidden;margin-bottom:18px">
          <table class="v2-table">
            <thead>
              <tr>
                <th>Item</th>
                <th class="v2-r">Qty</th>
                <th class="v2-r">Rate</th>
                <th class="v2-r">Tax</th>
                <th class="v2-r">Amount</th>
              </tr>
            </thead>
            <tbody>
              {#each lineItems as li (li.id)}
                <tr>
                  <td>
                    <div>{li.name}</div>
                    {#if li.detail}<div class="v2-table-secondary">{li.detail}</div>{/if}
                  </td>
                  <td class="v2-r v2-num">{li.quantity}</td>
                  <td class="v2-r v2-num">{money(li.rate, invoice.currency)}</td>
                  <td class="v2-r v2-num">{li.tax_rate}%</td>
                  <td class="v2-r v2-num">{money(li.amount, invoice.currency)}</td>
                </tr>
              {:else}
                <tr>
                  <td colspan="5" class="v2-sub" style="padding:14px 15px;font-size:12.5px">
                    No line items on this invoice.
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <div style="display:flex;justify-content:flex-end">
          <dl class="v2-kv" style="grid-template-columns:160px 120px;width:280px">
            <dt>Subtotal</dt>
            <dd class="v2-num" style="text-align:right">
              {money(invoice.subtotal, invoice.currency)}
            </dd>
            {#if invoice.discount_amount > 0}
              <dt>Discount</dt>
              <dd class="v2-num" style="text-align:right">
                −{money(invoice.discount_amount, invoice.currency)}
              </dd>
            {/if}
            <dt>Tax</dt>
            <dd class="v2-num" style="text-align:right">
              {money(invoice.tax_amount, invoice.currency)}
            </dd>
            {#if invoice.shipping_amount > 0}
              <dt>Shipping</dt>
              <dd class="v2-num" style="text-align:right">
                {money(invoice.shipping_amount, invoice.currency)}
              </dd>
            {/if}
            <dt>Paid</dt>
            <dd class="v2-num" style="text-align:right">
              {money(invoice.amount_paid, invoice.currency)}
            </dd>
            <dt style="color:var(--v2-ink);font-weight:600">Outstanding</dt>
            <dd
              class="v2-num"
              style="text-align:right;font-weight:700;font-size:16px;color:{invoice.amount_due > 0
                ? 'var(--v2-rust)'
                : 'var(--v2-moss)'}"
            >
              {money(invoice.amount_due, invoice.currency)}
            </dd>
          </dl>
        </div>

        {#if !invoice.is_settled}
          <div style="display:flex;justify-content:flex-end;margin-top:18px">
            <form
              method="POST"
              action="?/markPaid"
              use:enhance={working}
              style="display:flex;gap:8px;align-items:flex-end"
            >
              <div>
                <label class="v2-label" for="amount" style="display:block;margin-bottom:4px">
                  Record a payment
                </label>
                <input
                  id="amount"
                  name="amount"
                  class="v2-input"
                  style="width:150px"
                  placeholder={money(invoice.amount_due, invoice.currency)}
                  inputmode="decimal"
                />
              </div>
              <button class="v2-btn v2-btn-primary" disabled={busy}>Record</button>
            </form>
          </div>
          <p class="v2-sub" style="text-align:right;font-size:11.5px;margin-top:6px">
            Leave the amount blank to settle the full {money(invoice.amount_due, invoice.currency)} balance.
          </p>
        {/if}
      </div>
    </div>
  </div>

  <aside class="v2-rail">
    <div class="v2-label v2-rail-head">Invoice</div>
    <dl class="v2-kv">
      <dt>Status</dt>
      <dd>
        <Pill tone={INVOICE_STATUS_TONE[invoice.status]}>{invoiceStatusLabel(invoice.status)}</Pill>
      </dd>
      <dt>Number</dt>
      <dd class="v2-num">{invoice.invoice_number}</dd>
      <dt>Issued</dt>
      <dd>{longDate(invoice.issued_date)}</dd>
      <dt>Due</dt>
      <dd>{longDate(invoice.due_date)}</dd>
      <dt>Terms</dt>
      <dd>{invoiceStatusLabel(invoice.payment_terms)}</dd>
      <dt>Currency</dt>
      <dd>{invoice.currency}</dd>
    </dl>

    <div class="v2-label v2-rail-head">Bill to</div>
    <a
      href={resolve(`/accounts/${invoice.account.id}`)}
      class="v2-sub"
      style="font-size:12.5px;line-height:1.65;text-decoration:none;display:block"
    >
      {invoice.account.name}
    </a>

    <div class="v2-label v2-rail-head">Reminders</div>
    <dl class="v2-kv">
      <dt>Automatic</dt>
      <dd>{invoice.reminder_enabled ? (invoice.reminder_frequency ?? 'On') : 'Off'}</dd>
      <dt>Sent</dt>
      <dd class="v2-num">{invoice.reminder_count}</dd>
      {#if invoice.last_reminder_sent}
        <dt>Last</dt>
        <dd>{relativeDays(invoice.last_reminder_sent)}</dd>
      {/if}
    </dl>
  </aside>
</div>
