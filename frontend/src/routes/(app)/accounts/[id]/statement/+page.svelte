<script>
  /**
   * An account's statement (#810): per currency, the opening balance, the
   * period's invoices, payments and cancellations with a running balance, and
   * the closing balance.
   *
   * The API computes every figure, in the same order the PDF prints them; this
   * page only lays them out. It is admin-only on the backend, and a member who
   * reaches the URL gets a sentence saying so instead of numbers.
   *
   * On a phone each row is a card: the date leads, the amount sits in the
   * corner, and the invoice, details and running balance wrap beneath.
   */
  import { resolve } from '$app/paths';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import StatCard from '#lib/v2/components/StatCard.svelte';
  import { money, shortDate, longDate } from '#lib/v2/format.js';
  import { ChevronRight, Download } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let statement = $derived(data.statement);

  /** The query string for a period, as the page and the PDF route read it. */
  const query = (/** @type {{ start_date: string, end_date: string }} */ period) =>
    `?start_date=${period.start_date}&end_date=${period.end_date}`;
</script>

<PageHeader title="Statement" record>
  {#snippet crumb()}
    <a href={resolve('accounts')}>Accounts</a>
    <ChevronRight size={12} />
    <a href={resolve(`accounts/${data.accountId}`)}>{statement?.account.name || 'Account'}</a>
  {/snippet}
  {#snippet sub()}
    {#if statement}
      {longDate(statement.start_date)} to {longDate(statement.end_date)}
    {:else}
      What the account was billed, paid and owes
    {/if}
  {/snippet}
  {#snippet actions()}
    {#if statement}
      <a
        class="v2-btn"
        href={resolve(`accounts/${data.accountId}/statement/pdf${query(statement)}`)}
        target="_blank"
        rel="noopener"
      >
        <Download size={14} /> Download PDF
      </a>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#if !data.can_view}
      <div class="v2-card stmt-note">
        <strong>Statements are for administrators.</strong>
        <p>
          A statement adds up every invoice on the account, including ones you may not open, so it
          is limited to admins. The invoices you can open are on
          <a href={resolve(`accounts/${data.accountId}`)}>the account's page</a>.
        </p>
      </div>
    {:else}
      <form method="GET" class="stmt-period">
        <div class="v2-field">
          <label for="s-start">From</label>
          <input
            id="s-start"
            name="start_date"
            type="date"
            class="v2-input"
            value={data.period.start_date}
            required
          />
        </div>
        <div class="v2-field">
          <label for="s-end">To</label>
          <input
            id="s-end"
            name="end_date"
            type="date"
            class="v2-input"
            value={data.period.end_date}
            required
          />
        </div>
        <button class="v2-btn v2-btn-primary">Show</button>
      </form>
      <div class="stmt-presets">
        {#if data.previous}
          <a href={resolve(`accounts/${data.accountId}/statement${query(data.previous)}`)}
            >Previous month</a
          >
        {/if}
        <a href={resolve(`accounts/${data.accountId}/statement`)}>This month</a>
      </div>

      {#if data.error}
        <p class="v2-error" role="alert">{data.error}</p>
      {/if}

      {#if statement}
        {#each statement.currencies as section (section.currency)}
          {@const inCredit = section.closing_balance < 0}
          <section class="stmt-section">
            {#if statement.currencies.length > 1}
              <h2 class="v2-label">In {section.currency}</h2>
            {/if}
            <div class="v2-stats" style="margin-bottom:12px">
              <StatCard
                label="Opening balance"
                value={money(section.opening_balance, section.currency)}
                tone="slate"
              />
              <StatCard label="Invoiced" value={money(section.invoiced, section.currency)} />
              <StatCard
                label="Paid"
                value={money(section.paid, section.currency)}
                tone="moss"
                detail={section.cancelled
                  ? `${money(section.cancelled, section.currency)} cancelled`
                  : undefined}
              />
              <StatCard
                label={inCredit ? 'In credit' : 'Balance due'}
                value={money(Math.abs(section.closing_balance), section.currency)}
                tone={section.closing_balance > 0 ? 'rust' : 'moss'}
              />
            </div>
            <div class="v2-table-wrap" style="margin:0">
              <table class="v2-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Invoice</th>
                    <th>Details</th>
                    <th class="v2-r">Amount</th>
                    <th class="v2-r">Balance</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{shortDate(statement.start_date)}</td>
                    <td data-m="hide"></td>
                    <td data-m="meta" class="v2-muted">Opening balance</td>
                    <td data-m="hide"></td>
                    <td class="v2-r v2-num" data-m="tag"
                      >{money(section.opening_balance, section.currency)}</td
                    >
                  </tr>
                  {#each section.entries as entry, i (i)}
                    <tr>
                      <td>{shortDate(entry.date)}</td>
                      <td data-m="meta">
                        <a
                          class="v2-num stmt-invoice"
                          href={resolve(`invoices/${entry.invoice_id}`)}>{entry.invoice_number}</a
                        >
                      </td>
                      <td data-m="meta">{entry.description}</td>
                      <td
                        class="v2-r v2-num"
                        data-m="tag"
                        style={entry.amount < 0 ? 'color:var(--v2-moss)' : ''}
                      >
                        {money(entry.amount, section.currency)}
                      </td>
                      <td class="v2-r v2-num" data-m="meta" data-l="Balance"
                        >{money(entry.balance, section.currency)}</td
                      >
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </section>
        {:else}
          <p class="v2-sub stmt-empty">
            Nothing was billed or paid in this period, and nothing is owed.
          </p>
        {/each}
      {/if}
    {/if}
  </div>
</div>

<style>
  .stmt-period {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    gap: 10px;
    margin-top: 10px;
  }
  .stmt-period .v2-field {
    flex: 1 1 140px;
    max-width: 200px;
    margin-bottom: 0;
  }
  .stmt-presets {
    display: flex;
    gap: 16px;
    margin: 10px 0 4px;
    font-size: 12.5px;
  }
  .stmt-section {
    margin-top: 18px;
  }
  .stmt-section h2 {
    margin: 0 0 8px;
  }
  .stmt-empty {
    margin-top: 18px;
  }
  .stmt-note {
    padding: 16px 18px;
  }
  .stmt-note p {
    margin: 6px 0 0;
    font-size: 13px;
  }
  @media (max-width: 768px) {
    .stmt-period .v2-field {
      max-width: none;
    }
    .stmt-period .v2-input,
    .stmt-period .v2-btn {
      min-height: 44px;
    }
    .stmt-presets a {
      padding: 12px 0;
    }
    /* The whole card opens the invoice: the number alone is a 17px target.
       The row is `position: relative` at this width (`v2.css`). */
    .stmt-invoice::after {
      content: '';
      position: absolute;
      inset: 0;
    }
  }
</style>
