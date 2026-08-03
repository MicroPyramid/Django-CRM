<script>
  /**
   * An invoice, as its customer sees it.
   *
   * The page answers one question and everything else on it is evidence for
   * the answer: DO I OWE ANYTHING, HOW MUCH, AND BY WHEN. So the amount due
   * is the largest thing on the screen, the date sits under it, and the line
   * items, which are what a v1-style invoice page leads with, come after,
   * because nobody opens an invoice to read a table.
   *
   * ── FOUR THINGS THIS PAGE REFUSES TO DO ─────────────────────────────────
   *
   * 1. It does not show `status`. `Sent`, `Viewed` and `Partially_Paid` are
   *    facts about our workflow, not theirs, and one of them is actively
   *    misleading: `Viewed` is set BY THIS PAGE LOAD. What they need is derived
   *    below: paid, part-paid, due, or overdue.
   *
   * 2. It does not draw a "Pay now" button. There is no payment processor in
   *    this product: `invoices.models.Payment` rows are entered by a human in
   *    the CRM after money arrives, and no model field holds a checkout URL. A
   *    button that opens nothing is worse than no button, so the page gives the
   *    terms and the reference to quote instead.
   *
   * 3. It does not render the org's custom invoice template. See
   *    `invoice-template-pdf-sink`: `template_html` is an org-authored blob
   *    that WeasyPrint turns into a PDF server-side, and putting it in this
   *    page's DOM would make a PDF setting into stored XSS on a public URL.
   *    Only `primary_color` and `footer_text` cross over.
   *
   * 4. It does not show the token. It is in the address bar because it has to
   *    be; it is not in the body, where it would survive a screenshot pasted
   *    into a support thread.
   */
  import PortalShell from '$lib/v2/components/PortalShell.svelte';
  import PortalLineItems from '$lib/v2/components/PortalLineItems.svelte';
  import { money, longDate } from '$lib/v2/format.js';
  import { Download, CheckCircle2 } from '@lucide/svelte';

  /** @type {{ data: { invoice: any, token: string } }} */
  let { data } = $props();

  let inv = $derived(data.invoice);
  let token = $derived(data.token);

  /** Whole days from today to the due date. Negative means it has passed. */
  let daysToDue = $derived.by(() => {
    if (!inv.due_date) return null;
    const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    return Math.round((startOfDay(new Date(inv.due_date)) - startOfDay(new Date())) / 86400000);
  });

  /**
   * The customer-facing state, derived from money and dates only, never from
   * `status`. Four outcomes, because there are four different things to do.
   */
  let state = $derived.by(() => {
    if (Number(inv.amount_due) <= 0) return 'paid';
    if (daysToDue !== null && daysToDue < 0) return 'overdue';
    if (Number(inv.amount_paid) > 0) return 'part-paid';
    return 'due';
  });

  /** "in 5 days" / "today" / "9 days ago". A date alone makes people count. */
  let duePhrase = $derived.by(() => {
    if (daysToDue === null) return 'on receipt';
    if (daysToDue === 0) return 'today';
    if (daysToDue > 0) return `in ${daysToDue} ${daysToDue === 1 ? 'day' : 'days'}`;
    const n = Math.abs(daysToDue);
    return `${n} ${n === 1 ? 'day' : 'days'} ago`;
  });

  let addr = $derived(inv.billing_address || {});
  let addressLines = $derived(
    [addr.line, addr.city, addr.state, addr.postcode, addr.country].filter(Boolean)
  );
</script>

<svelte:head>
  <!-- The number is the thing a customer searches their inbox for. -->
  <title>{inv.invoice_number} from {inv.org.name}</title>
</svelte:head>

<PortalShell>
  <article class="doc">
    <!-- Who this is from. A customer may hold invoices from a dozen suppliers
         and the sender is how they tell them apart, so it leads. -->
    <header class="doc-head">
      <div>
        <div class="from">{inv.org.name}</div>
        <h1>{inv.invoice_title || 'Invoice'}</h1>
        <div class="ref">
          Invoice <span class="v2-num">{inv.invoice_number}</span> · issued
          {longDate(inv.issue_date)}
        </div>
      </div>
      <!-- A backend download endpoint, not a SvelteKit route: rel="external"
           forces a real navigation (and the file download) rather than a
           client-side one. -->
      <a
        class="v2-btn v2-btn-sm"
        href="/api/public/invoice/{token}/pdf/"
        rel="external"
        aria-label="Download this invoice as a PDF"
      >
        <Download size={13} />PDF
      </a>
    </header>

    <!-- The answer. -->
    <section class="amount" class:overdue={state === 'overdue'} class:settled={state === 'paid'}>
      {#if state === 'paid'}
        <div class="paid-mark"><CheckCircle2 size={20} /></div>
        <div>
          <div class="amount-label">Paid in full</div>
          <div class="amount-sub">
            Nothing is outstanding on this invoice. It is here for your records.
          </div>
        </div>
      {:else}
        <div>
          <div class="amount-label">Amount due</div>
          <div class="amount-value v2-num">{money(inv.amount_due, inv.currency)}</div>
          <div class="amount-sub">
            {#if state === 'overdue'}
              Due {longDate(inv.due_date)}, {duePhrase}
            {:else}
              Due {longDate(inv.due_date)}, {duePhrase}
            {/if}
            {#if state === 'part-paid'}
              · {money(inv.amount_paid, inv.currency)} of {money(inv.total_amount, inv.currency)} already
              received
            {/if}
          </div>
        </div>
      {/if}
    </section>

    {#if state !== 'paid'}
      <!-- How to pay. This is the action, in the absence of a payment
           processor, so it gets the weight a button would have had. -->
      <section class="pay">
        <div class="v2-label">How to pay</div>
        <p>{inv.terms}</p>
        <dl class="pay-ref">
          <dt>Reference</dt>
          <dd class="v2-num">{inv.invoice_number}</dd>
          <dt>Amount</dt>
          <dd class="v2-num">{money(inv.amount_due, inv.currency)}</dd>
        </dl>
      </section>
    {/if}

    <!-- Evidence. -->
    <section class="block">
      <div class="v2-label">Billed to</div>
      <div class="addr">
        <div class="addr-name">{inv.client_name}</div>
        {#each addressLines as line, i (i)}
          <div>{line}</div>
        {/each}
      </div>
    </section>

    <section class="block">
      <div class="v2-label">What this covers</div>
      <PortalLineItems
        items={inv.line_items}
        currency={inv.currency}
        subtotal={inv.subtotal}
        discountAmount={inv.discount_amount}
        discountType={inv.discount_type}
        discountValue={inv.discount_value}
        taxRate={inv.tax_rate}
        taxAmount={inv.tax_amount}
        shippingAmount={inv.shipping_amount}
        total={inv.total_amount}
      />
    </section>

    {#if inv.payments.length}
      <!-- What they have already sent. Without this the page asserts a balance
           with nothing behind it, and the first reply is always "we paid that". -->
      <section class="block">
        <div class="v2-label">Payments received</div>
        <ul class="payments">
          {#each inv.payments as p, i (i)}
            <li>
              <span class="v2-num">{money(p.amount, inv.currency)}</span>
              <span class="pay-meta">{p.payment_method} · {longDate(p.payment_date)}</span>
            </li>
          {/each}
          <li class="payments-balance">
            <span class="v2-num">{money(inv.amount_due, inv.currency)}</span>
            <span class="pay-meta">remaining</span>
          </li>
        </ul>
      </section>
    {/if}

    {#if inv.notes}
      <section class="block">
        <div class="v2-label">Notes</div>
        <p class="note">{inv.notes}</p>
      </section>
    {/if}

    <footer class="doc-foot">
      <!-- No mailto here. The only address in the public payload is
           `client_email`, which is the CUSTOMER's own, linking it under the
           words "write to us" opens a message addressed to the person reading
           the page. The org's address is in `footer_text`, put there by
           whoever wrote the template, and that is the one to use. -->
      <p>Questions about this invoice? Reply to the email it arrived with.</p>
      {#if inv.template?.footer_text}
        <p class="foot-org">{inv.template.footer_text}</p>
      {/if}
    </footer>
  </article>
</PortalShell>

<style>
  .doc {
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    padding: 30px 32px 26px;
  }
  .doc-head {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding-bottom: 22px;
    border-bottom: 1px solid var(--v2-line);
  }
  .doc-head > div:first-child {
    min-width: 0;
  }
  .doc-head .v2-btn {
    flex: none;
    margin-left: auto;
  }
  .from {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
    color: var(--v2-slate);
  }
  h1 {
    margin: 4px 0 0;
    font-size: 21.9px;
    font-weight: 640;
    line-height: 1.2;
    letter-spacing: -0.01em;
  }
  .ref {
    margin-top: 5px;
    font-size: 12.5px;
    color: var(--v2-slate);
  }

  .amount {
    display: flex;
    align-items: center;
    gap: 13px;
    margin: 22px 0;
    padding: 18px 20px;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    background: var(--v2-line-soft);
  }
  .amount.overdue {
    border-color: var(--v2-ember-line);
    background: var(--v2-ember-soft);
  }
  .amount-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--v2-slate);
  }
  .amount-value {
    margin-top: 3px;
    font-size: 32px;
    font-weight: 650;
    letter-spacing: -0.02em;
    line-height: 1.1;
  }
  .amount.overdue .amount-value {
    color: var(--v2-ember);
  }
  .amount-sub {
    margin-top: 5px;
    font-size: 12.5px;
    color: var(--v2-slate);
  }
  .settled .paid-mark {
    color: var(--v2-moss);
    display: flex;
  }

  .pay {
    margin: 22px 0;
    padding: 16px 18px;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
  }
  .pay p {
    margin: 7px 0 0;
    font-size: 13px;
    line-height: 1.55;
    white-space: pre-wrap;
  }
  .pay-ref {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 4px 16px;
    margin: 13px 0 0;
    font-size: 12.5px;
  }
  .pay-ref dt {
    color: var(--v2-slate);
  }
  .pay-ref dd {
    margin: 0;
    font-weight: 600;
  }

  .block {
    margin-top: 26px;
  }
  .addr {
    margin-top: 7px;
    font-size: 13px;
    line-height: 1.55;
    color: var(--v2-slate);
  }
  .addr-name {
    color: var(--v2-ink);
    font-weight: 500;
  }
  .note {
    margin: 7px 0 0;
    font-size: 13px;
    line-height: 1.55;
    white-space: pre-wrap;
  }

  .payments {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
    font-size: 13px;
  }
  .payments li {
    display: flex;
    align-items: baseline;
    gap: 10px;
    padding: 7px 0;
    border-bottom: 1px solid var(--v2-line-soft);
  }
  .payments-balance {
    /* The balance is a different kind of fact from a payment. It is the sum,
       not another entry, so it sits under a rule rather than reading as one
       more identical row in the list. */
    font-weight: 600;
    border-bottom: 0;
    border-top: 1px solid var(--v2-line);
    margin-top: 1px;
  }
  .pay-meta {
    color: var(--v2-slate);
    font-size: 12px;
  }

  .doc-foot {
    margin-top: 30px;
    padding-top: 18px;
    border-top: 1px solid var(--v2-line);
    font-size: 12px;
    color: var(--v2-slate);
    line-height: 1.55;
  }
  .doc-foot p {
    margin: 0;
  }
  .foot-org {
    margin-top: 7px !important;
    font-size: 11px;
  }

  @media (max-width: 560px) {
    .doc {
      padding: 22px 18px 20px;
    }
    .amount-value {
      font-size: 27px;
    }
  }
</style>
