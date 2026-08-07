<script>
  import { resolve } from '$app/paths';
  /**
   * New invoice.
   *
   * ── THE ONE THING THIS PAGE IS FOR ───────────────────────────────────────
   * Getting the arithmetic and the due date right BEFORE the document goes to
   * a customer, because both are hard to take back. So the right-hand panel is
   * not a decoration: it renders the running totals through
   * `PortalLineItems`: the very same component the customer's portal page
   * uses. If the number here is wrong, it is wrong in the same way there, and
   * you find that out now rather than from a reply.
   *
   * ── WHAT IS DERIVED, AND BY WHOM ─────────────────────────────────────────
   * Three fields on `invoices.Invoice` are computed by `save()` and are NOT
   * asked for here, because asking would invite a value the server throws
   * away:
   *
   *   invoice_number   generate_invoice_number() → INV-YYYYMMDD-XXXX
   *   public_token     secrets.token_urlsafe(32), with a collision re-roll
   *   due_date         calculate_due_date() from issue_date + payment_terms
   *
   * And `recalculate_totals()` recomputes subtotal, discount, tax, total and
   * amount_due from the line items on every save. THE SERVER IS THE AUTHORITY
   * ON THE MONEY. Everything computed in this file is a preview of what it
   * will decide, mirroring its order exactly: subtotal, then discount, then
   * tax on the discounted amount, then shipping added untaxed. If the two ever
   * disagree, the server is right and this file has a bug.
   *
   * `org` and `created_by` are absent for a different reason: they are
   * server-derived from the JWT and the profile. A form that collects them is
   * a form that can be edited to claim them.
   */
  import { enhance } from '$app/forms';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SectionTabs from '$lib/v2/components/SectionTabs.svelte';
  import PortalLineItems from '$lib/v2/components/PortalLineItems.svelte';
  import { PAYMENT_TERMS_LABEL } from '$lib/v2/enums.js';
  import { money, longDate } from '$lib/v2/format.js';
  import { Plus, Trash2, Info } from '@lucide/svelte';

  /** @type {{ data: { products: any[], accounts: any[], contacts: any[] }, form: any }} */
  let { data, form } = $props();

  const CURRENCY = 'USD';
  const TERM_DAYS = { DUE_ON_RECEIPT: 0, NET_15: 15, NET_30: 30, NET_45: 45, NET_60: 60 };

  let accountId = $state('');
  let contactId = $state('');
  let title = $state('');
  let issueDate = $state(new Date().toISOString().slice(0, 10));
  let paymentTerms = $state('NET_30');
  let customDueDate = $state('');
  let discountType = $state('');
  let discountValue = $state(0);
  let taxRate = $state(0);
  let shipping = $state(0);
  let notes = $state('');

  let items = $state([{ name: '', description: '', quantity: 1, unit_price: 0, product: null }]);

  /**
   * Contacts whose primary account is this account, plus contacts with no
   * account (they attach to anyone). The server enforces the same rule. A
   * contact bound to another account is a 400, so offering only these keeps the
   * form from proposing a pairing the API will refuse.
   */
  let contactOptions = $derived(
    data.contacts.filter((c) => !c.account_id || c.account_id === accountId)
  );

  const num = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);

  /** Per-line total. `quantity × unit_price`, matching InvoiceLineItem. */
  let lines = $derived(items.map((i) => ({ ...i, total: num(i.quantity) * num(i.unit_price) })));

  /* The ladder, in the server's order. Do not reorder these. */
  let subtotal = $derived(lines.reduce((a, l) => a + l.total, 0));
  let discountAmount = $derived(
    discountType === 'PERCENTAGE'
      ? subtotal * (num(discountValue) / 100)
      : discountType === 'FIXED'
        ? num(discountValue)
        : 0
  );
  let taxable = $derived(subtotal - discountAmount);
  let taxAmount = $derived(taxable * (num(taxRate) / 100));
  let total = $derived(taxable + taxAmount + num(shipping));

  /**
   * `calculate_due_date()`. The interesting case is CUSTOM: it is not in the
   * server's `term_days` map, so `.get(terms, 30)` quietly returns 30 and the
   * invoice gets a Net-30 date nobody chose. The banner below says so.
   */
  let derivedDueDate = $derived.by(() => {
    if (!issueDate) return null;
    if (paymentTerms === 'CUSTOM') return customDueDate || null;
    // UTC arithmetic on the parsed date, so no mutable Date instance and no
    // local-timezone drift; the server recomputes this authoritatively anyway.
    const days = TERM_DAYS[paymentTerms] ?? 30;
    const parsed = Date.parse(issueDate);
    if (Number.isNaN(parsed)) return null;
    return new Date(parsed + days * 86_400_000).toISOString().slice(0, 10);
  });

  let customFallsBack = $derived(paymentTerms === 'CUSTOM' && !customDueDate);

  /** A line with a name and a positive amount is a line worth invoicing. */
  let usableLines = $derived(lines.filter((l) => l.name.trim() && l.total > 0));
  let ready = $derived(
    Boolean(accountId) && Boolean(contactId) && Boolean(title.trim()) && usableLines.length > 0
  );

  /**
   * The whole builder as the API body, carried in one hidden field so the
   * dynamic line-item list survives the form post intact. Only what the server
   * accepts is sent; org/created_by/number/token/totals are its to derive, and
   * status is server-forced to Draft, so none are here.
   */
  let payload = $derived.by(() => {
    /** @type {Record<string, any>} */
    const body = {
      account_id: accountId,
      contact_id: contactId,
      currency: CURRENCY,
      issue_date: issueDate,
      payment_terms: paymentTerms,
      line_items: usableLines.map((l) => {
        /** @type {Record<string, any>} */
        const row = {
          name: l.name.trim(),
          description: (l.description || '').trim(),
          quantity: num(l.quantity),
          unit_price: num(l.unit_price)
        };
        if (l.product) row.product = l.product;
        return row;
      })
    };
    // Required by the API (Invoice.invoice_title is not blank), so always sent;
    // `ready` blocks submit until it has a value.
    body.invoice_title = title.trim();
    if (paymentTerms === 'CUSTOM' && customDueDate) body.due_date = customDueDate;
    if (discountType) {
      body.discount_type = discountType;
      body.discount_value = num(discountValue);
    }
    if (num(taxRate)) body.tax_rate = num(taxRate);
    if (num(shipping)) body.shipping_amount = num(shipping);
    if (notes.trim()) body.notes = notes.trim();
    return body;
  });

  function addLine() {
    items.push({ name: '', description: '', quantity: 1, unit_price: 0, product: null });
  }

  function addProduct(id) {
    const p = data.products.find((x) => x.id === id);
    if (!p) return;
    // Price is copied AND the product is linked. `InvoiceLineItem` stores its
    // own `unit_price` so a later catalogue change never rewrites a sent
    // invoice; the `product` FK (server-validated to this org) records what it
    // came from. A hand-typed line has no product and that is fine.
    items.push({
      name: p.name,
      description: p.sku,
      quantity: 1,
      unit_price: p.price,
      product: p.id
    });
  }

  function removeLine(i) {
    items.splice(i, 1);
    if (!items.length) addLine();
  }
</script>

<PageHeader title="New invoice">
  {#snippet sub()}
    Nothing is sent until you send it. Saving leaves it as a draft
  {/snippet}
  {#snippet actions()}
    <a class="v2-btn" href={resolve('/invoices')}>Cancel</a>
    <button type="submit" form="invoice-form" class="v2-btn v2-btn-primary" disabled={!ready}>
      Save as draft
    </button>
  {/snippet}
</PageHeader>

<SectionTabs set="invoices" />

{#if form?.error}
  <div class="v2-pad" style="padding-top:12px">
    <p class="new-error" role="alert">{form.error}</p>
  </div>
{/if}

<!-- The builder posts as one JSON field so the dynamic line list travels whole.
     The submit button lives in the header and is wired to this form by id. -->
<form id="invoice-form" method="POST" action="?/create" use:enhance>
  <input type="hidden" name="payload" value={JSON.stringify(payload)} />
</form>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    <div class="v2-split">
      <!-- ── the form ─────────────────────────────────────────────────── -->
      <div>
        <div class="v2-card" style="padding:16px 18px">
          <div class="v2-label" style="margin-bottom:12px">Who and when</div>

          <div class="grid2">
            <label class="f">
              <span>Account</span>
              <select bind:value={accountId} onchange={() => (contactId = '')}>
                <option value="">Choose an account</option>
                {#each data.accounts as a (a.id)}
                  <option value={a.id}>{a.name}</option>
                {/each}
              </select>
            </label>

            <label class="f">
              <span>Contact</span>
              <select bind:value={contactId} disabled={!accountId}>
                <option value="">{accountId ? 'Choose a contact' : 'Pick an account first'}</option>
                {#each contactOptions as c (c.id)}
                  <option value={c.id}
                    >{c.name}{c.account_name ? ` · ${c.account_name}` : ''}</option
                  >
                {/each}
              </select>
            </label>

            <label class="f">
              <span>Title</span>
              <input bind:value={title} placeholder="What this invoice covers" required />
            </label>

            <label class="f">
              <span>Issue date</span>
              <input type="date" bind:value={issueDate} />
            </label>

            <label class="f">
              <span>Payment terms</span>
              <select bind:value={paymentTerms}>
                {#each Object.entries(PAYMENT_TERMS_LABEL) as [value, label] (value)}
                  <option {value}>{label}</option>
                {/each}
              </select>
            </label>

            {#if paymentTerms === 'CUSTOM'}
              <label class="f">
                <span>Due date</span>
                <input type="date" bind:value={customDueDate} />
              </label>
            {/if}
          </div>

          {#if customFallsBack}
            <!-- Not a style nit. CUSTOM is missing from the server's term_days
                 map and `.get(terms, 30)` supplies 30, so leaving this empty
                 produces a date the customer will hold you to. -->
            <p class="warn">
              <Info size={13} />
              <span>
                Custom terms with no date set becomes <b>Net 30</b> on save, the server falls back to
                30 days rather than leaving the date empty.
              </span>
            </p>
          {/if}
        </div>

        <div class="v2-card" style="padding:16px 18px;margin-top:14px">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
            <div class="v2-label">Lines</div>
            <select
              class="catalogue"
              value=""
              onchange={(e) => {
                addProduct(e.currentTarget.value);
                e.currentTarget.value = '';
              }}
            >
              <option value="">Add from catalogue…</option>
              {#each data.products as p (p.id)}
                <option value={p.id}>{p.name}, {money(p.price, CURRENCY)}</option>
              {/each}
            </select>
          </div>

          {#each items as item, i (i)}
            <div class="line">
              <div class="line-main">
                <input class="line-name" bind:value={item.name} placeholder="Description" />
                <input
                  class="line-desc"
                  bind:value={item.description}
                  placeholder="Detail the customer sees under the name (optional)"
                />
              </div>
              <label class="line-n">
                <span>Qty</span>
                <input type="number" min="0" step="1" bind:value={item.quantity} />
              </label>
              <label class="line-n">
                <span>Unit price</span>
                <input type="number" min="0" step="0.01" bind:value={item.unit_price} />
              </label>
              <div class="line-total v2-num">
                {money(num(item.quantity) * num(item.unit_price), CURRENCY)}
              </div>
              <button
                class="line-del"
                onclick={() => removeLine(i)}
                aria-label="Remove this line"
                title="Remove this line"
              >
                <Trash2 size={14} />
              </button>
            </div>
          {/each}

          <button class="v2-btn v2-btn-sm" style="margin-top:10px" onclick={addLine}>
            <Plus size={13} />Add a line
          </button>
        </div>

        <div class="v2-card" style="padding:16px 18px;margin-top:14px">
          <div class="v2-label" style="margin-bottom:12px">Adjustments</div>
          <div class="grid2">
            <label class="f">
              <span>Discount</span>
              <select bind:value={discountType}>
                <option value="">None</option>
                <option value="PERCENTAGE">Percentage</option>
                <option value="FIXED">Fixed amount</option>
              </select>
            </label>
            {#if discountType}
              <label class="f">
                <span>{discountType === 'PERCENTAGE' ? 'Percent off' : 'Amount off'}</span>
                <input type="number" min="0" step="0.01" bind:value={discountValue} />
              </label>
            {/if}
            <label class="f">
              <span>Tax rate %</span>
              <input type="number" min="0" step="0.01" bind:value={taxRate} />
            </label>
            <label class="f">
              <span>Shipping</span>
              <input type="number" min="0" step="0.01" bind:value={shipping} />
            </label>
          </div>
          <p class="hint">
            Tax applies to the subtotal after the discount. Shipping is added afterwards and is not
            taxed.
          </p>
        </div>

        <div class="v2-card" style="padding:16px 18px;margin-top:14px">
          <div class="v2-label" style="margin-bottom:8px">Notes to the customer</div>
          <textarea rows="3" bind:value={notes} placeholder="Appears on the invoice"></textarea>
        </div>
      </div>

      <!-- ── what the customer will get ───────────────────────────────── -->
      <div>
        <div class="v2-card preview">
          <div class="v2-card-head">
            <span class="v2-label">What the customer will see</span>
          </div>
          <div style="padding:14px 16px 16px">
            {#if usableLines.length}
              <PortalLineItems
                items={usableLines}
                currency={CURRENCY}
                {subtotal}
                {discountAmount}
                {discountType}
                {discountValue}
                {taxRate}
                {taxAmount}
                shippingAmount={num(shipping)}
                {total}
              />
            {:else}
              <p class="empty">
                Add a line with a description and an amount, and the customer's copy appears here.
              </p>
            {/if}
          </div>
        </div>

        <div class="v2-card" style="padding:15px 16px;margin-top:14px">
          <div class="v2-label" style="margin-bottom:9px">When it falls due</div>
          {#if derivedDueDate}
            <div class="due">{longDate(derivedDueDate)}</div>
            <p class="hint" style="margin-top:5px">
              {#if paymentTerms === 'CUSTOM'}
                Set by hand.
              {:else}
                {PAYMENT_TERMS_LABEL[paymentTerms]} from the issue date. The server recalculates this
                on save from the same two fields.
              {/if}
            </p>
          {:else}
            <p class="hint" style="margin:0">Set an issue date to see the due date.</p>
          {/if}
        </div>

        <div class="v2-card" style="padding:15px 16px;margin-top:14px">
          <div class="v2-label" style="margin-bottom:9px">Assigned on save</div>
          <dl class="derived">
            <dt>Invoice number</dt>
            <dd>INV-<span class="v2-num">{issueDate.replace(/-/g, '')}</span>-nnnn</dd>
            <dt>Customer link</dt>
            <dd>Generated, and only sent when you send the invoice</dd>
          </dl>
          <p class="hint" style="margin-top:9px">
            Both come from the server so that two people saving at once cannot collide.
          </p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .grid2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 14px;
  }
  .f {
    display: block;
    min-width: 0;
  }
  .f > span {
    display: block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--v2-slate);
    margin-bottom: 4px;
  }
  input,
  select,
  textarea {
    width: 100%;
    padding: 7px 9px;
    font: inherit;
    font-size: 13px;
    color: var(--v2-ink);
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 6px;
  }
  textarea {
    resize: vertical;
    line-height: 1.5;
  }
  input:focus,
  select:focus,
  textarea:focus {
    outline: 2px solid var(--v2-ember);
    outline-offset: -1px;
  }
  input[type='number'] {
    font-family: var(--v2-mono);
    font-size: 12.5px;
  }

  .catalogue {
    width: auto;
    margin-left: auto;
    font-size: 12px;
    padding: 5px 8px;
  }

  .line {
    /* Two rows, always. Squeezing the description into the leftover 1fr
       beside four numeric columns leaves it about 85px wide inside this
       column, the widest field in the record rendered as the narrowest box
       on the screen. The numbers are fixed-width because they are short; the
       description gets the whole row because it is not. */
    display: grid;
    grid-template-columns: 72px 116px 1fr 26px;
    gap: 9px;
    align-items: end;
    padding: 9px 0;
    border-bottom: 1px solid var(--v2-line-soft);
  }
  .line-main {
    grid-column: 1 / -1;
    min-width: 0;
  }
  .line-desc {
    margin-top: 5px;
    font-size: 12px;
    color: var(--v2-slate);
  }
  .line-n > span {
    display: block;
    font-size: 10px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--v2-slate);
    margin-bottom: 3px;
  }
  .line-total {
    font-size: 13px;
    font-weight: 600;
    text-align: right;
    min-width: 74px;
    padding-bottom: 8px;
  }
  .line-del {
    background: none;
    border: 0;
    padding: 0 0 9px;
    color: var(--v2-slate);
    cursor: pointer;
  }
  .line-del:hover {
    color: var(--v2-rust);
  }

  .hint {
    margin: 10px 0 0;
    font-size: 11.5px;
    color: var(--v2-slate);
    line-height: 1.5;
  }
  .warn {
    display: flex;
    gap: 7px;
    align-items: flex-start;
    margin: 12px 0 0;
    font-size: 12px;
    color: var(--v2-clay);
    line-height: 1.5;
  }
  #invoice-form {
    display: contents;
  }
  .new-error {
    margin: 0;
    padding: 9px 12px;
    font-size: 12.5px;
    color: var(--v2-clay);
    background: color-mix(in srgb, var(--v2-clay) 8%, transparent);
    border: 1px solid color-mix(in srgb, var(--v2-clay) 25%, transparent);
    border-radius: 7px;
  }
  .warn :global(svg) {
    flex: none;
    margin-top: 2px;
  }

  .preview {
    position: sticky;
    top: 0;
  }
  .empty {
    margin: 0;
    font-size: 12.5px;
    color: var(--v2-slate);
    line-height: 1.5;
  }
  .due {
    font-size: 16px;
    font-weight: 640;
  }
  .derived {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 5px 14px;
    margin: 0;
    font-size: 12.5px;
  }
  .derived dt {
    color: var(--v2-slate);
  }
  .derived dd {
    margin: 0;
  }

  @media (max-width: 768px) {
    /* Removing a line is destructive and had a 23px target. Widened to 40px,
       with the column widened to match so it does not steal room from the
       inputs. */
    .line-del {
      min-width: 40px;
      min-height: 40px;
      padding: 0 0 9px;
    }
  }
  @media (max-width: 560px) {
    /* Qty and unit price share the row; the total keeps its own column so it
       never wraps under the inputs it belongs to. */
    .line {
      grid-template-columns: 1fr 1fr auto 40px;
    }
    .grid2 {
      grid-template-columns: 1fr;
    }
  }
</style>
