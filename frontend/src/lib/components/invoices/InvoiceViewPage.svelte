<script>
  import { formatCurrency, formatDate } from '$lib/utils/formatting.js';

  /**
   * @typedef {Object} LineItem
   * @property {string} id
   * @property {string} [name]
   * @property {string} description
   * @property {number} quantity
   * @property {number} rate
   * @property {number} amount
   */

  /**
   * @typedef {Object} Company
   * @property {string} [name]
   * @property {string} [companyName]
   * @property {string} [addressLine]
   * @property {string} [city]
   * @property {string} [state]
   * @property {string} [postcode]
   * @property {string} [country]
   * @property {string} [phone]
   * @property {string} [email]
   * @property {string} [website]
   * @property {string} [taxId]
   * @property {string} [logoUrl]
   * @property {string} [logo]
   */

  /**
   * @typedef {Object} Template
   * @property {string} [id]
   * @property {string} [name]
   * @property {string} [primaryColor]
   * @property {string} [secondaryColor]
   * @property {string} [footerText]
   * @property {string} [defaultNotes]
   * @property {string} [defaultTerms]
   */

  /**
   * @typedef {Object} Invoice
   * @property {string} id
   * @property {string} invoiceNumber
   * @property {string} [invoiceTitle]
   * @property {string} status
   * @property {string} clientName
   * @property {string} [clientEmail]
   * @property {string} [clientPhone]
   * @property {string} [clientAddressLine]
   * @property {string} [clientCity]
   * @property {string} [clientState]
   * @property {string} [clientPostcode]
   * @property {string} [clientCountry]
   * @property {string} [issueDate]
   * @property {string} [dueDate]
   * @property {string} [paymentTerms]
   * @property {string} [billingPeriod]
   * @property {string} [poNumber]
   * @property {string|number} subtotal
   * @property {string|number} [discountAmount]
   * @property {string|number} [taxRate]
   * @property {string|number} [taxAmount]
   * @property {string|number} [shippingAmount]
   * @property {string|number} totalAmount
   * @property {string|number} [amountPaid]
   * @property {string|number} [amountDue]
   * @property {string} currency
   * @property {string} [notes]
   * @property {string} [terms]
   * @property {LineItem[]} lineItems
   */

  /** @type {{ invoice: Invoice, company?: Company, template?: Template, class?: string }} */
  let { invoice, company = {}, template = {}, class: className = '' } = $props();

  // Template colors with defaults
  const primaryColor = $derived(template?.primaryColor || '#3B82F6');
  const secondaryColor = $derived(template?.secondaryColor || '#1E40AF');
  const footerText = $derived(template?.footerText || '');

  // Format payment terms for display
  function formatPaymentTerms(terms) {
    const termsMap = {
      DUE_ON_RECEIPT: 'Due on Receipt',
      NET_15: 'Net 15',
      NET_30: 'Net 30',
      NET_45: 'Net 45',
      NET_60: 'Net 60',
      CUSTOM: 'Custom'
    };
    return termsMap[terms] || terms || 'Net 30';
  }

  // Get company display name
  const companyDisplayName = $derived(company?.companyName || company?.name || 'Your Company');

  // Format city, state, postcode line
  function formatCityStateZip(city, state, postcode) {
    const parts = [];
    if (city) parts.push(city);
    if (state) parts.push(state);
    if (postcode) parts.push(postcode);
    if (parts.length === 0) return '';
    if (city && state) return `${city}, ${state} ${postcode || ''}`.trim();
    return parts.join(' ');
  }

  const companyCityLine = $derived(
    formatCityStateZip(company?.city, company?.state, company?.postcode)
  );
  const clientCityLine = $derived(
    formatCityStateZip(invoice.clientCity, invoice.clientState, invoice.clientPostcode)
  );
</script>

<div
  class="invoice-view {className}"
  style="--primary-color: {primaryColor}; --secondary-color: {secondaryColor};"
>
  <div class="invoice-container">
    <!-- Header Section -->
    <header class="header">
      <div class="company-details">
        <h1>{companyDisplayName}</h1>
        {#if company?.companyName && company?.name && company.companyName !== company.name}
          <p>{company.name}</p>
        {/if}
        {#if company?.addressLine}
          <p>{company.addressLine}</p>
        {/if}
        {#if companyCityLine}
          <p>{companyCityLine}</p>
        {/if}
        {#if company?.phone}
          <p>Tel: {company.phone}</p>
        {/if}
        {#if company?.email}
          <p>Email: <a href="mailto:{company.email}">{company.email}</a></p>
        {/if}
        {#if company?.website}
          <p>
            Web: <a href={company.website} target="_blank" rel="noopener noreferrer"
              >{company.website.replace(/^https?:\/\//, '')}</a
            >
          </p>
        {/if}
      </div>

      <div class="invoice-branding">
        <div class="invoice-title">Invoice</div>
        {#if company?.logoUrl}
          <div class="logo-container">
            <img src={company.logoUrl} alt="{companyDisplayName} Logo" class="logo" />
          </div>
        {:else}
          <div class="logo-container">
            <span class="logo-text">{companyDisplayName.substring(0, 4).toUpperCase()}</span>
          </div>
        {/if}
      </div>
    </header>

    <!-- Client & Invoice Details Section -->
    <section class="info-section">
      <div class="client-address">
        <h3>{invoice.clientName || 'Client Name'}</h3>
        {#if invoice.clientAddressLine}
          <p>{invoice.clientAddressLine}</p>
        {/if}
        {#if clientCityLine}
          <p>{clientCityLine}</p>
        {/if}
        {#if invoice.clientCountry}
          <p>{invoice.clientCountry}</p>
        {/if}
      </div>

      <div class="invoice-meta">
        {#if invoice.invoiceTitle}
          <div class="meta-row">
            <span class="meta-label">Reference:</span>
            <span class="meta-value">{invoice.invoiceTitle}</span>
          </div>
        {/if}
        <div class="meta-row">
          <span class="meta-label">Invoice #:</span>
          <span class="meta-value">{invoice.invoiceNumber}</span>
        </div>
        {#if invoice.poNumber}
          <div class="meta-row">
            <span class="meta-label">PO Number:</span>
            <span class="meta-value">{invoice.poNumber}</span>
          </div>
        {/if}
        {#if invoice.billingPeriod}
          <div class="meta-row">
            <span class="meta-label">Billing Period:</span>
            <span class="meta-value">{invoice.billingPeriod}</span>
          </div>
        {/if}
        {#if invoice.paymentTerms}
          <div class="meta-row">
            <span class="meta-label">Terms:</span>
            <span class="meta-value">{formatPaymentTerms(invoice.paymentTerms)}</span>
          </div>
        {/if}
        {#if invoice.issueDate}
          <div class="meta-row">
            <span class="meta-label">Invoice Date:</span>
            <span class="meta-value">{formatDate(invoice.issueDate)}</span>
          </div>
        {/if}
        {#if invoice.dueDate}
          <div class="meta-row">
            <span class="meta-label">Due Date:</span>
            <span class="meta-value">{formatDate(invoice.dueDate)}</span>
          </div>
        {/if}
      </div>
    </section>

    <!-- Line Items Table -->
    <table class="line-items-table">
      <thead>
        <tr>
          <th class="desc-col">Description</th>
          <th class="qty-col">Quantity</th>
          <th class="price-col">Price</th>
          <th class="total-col">Total</th>
        </tr>
      </thead>
      <tbody>
        {#if invoice.lineItems && invoice.lineItems.length > 0}
          {#each invoice.lineItems as item}
            <tr>
              <td class="desc-col">
                {#if item.name}
                  <span class="item-title">{item.name}</span>
                  {#if item.description}
                    <span class="item-desc">{item.description}</span>
                  {/if}
                {:else}
                  <span class="item-title">{item.description || 'Item'}</span>
                {/if}
              </td>
              <td class="qty-col">{item.quantity?.toFixed(2) || '1.00'}</td>
              <td class="price-col">{formatCurrency(Number(item.rate || 0), invoice.currency)}</td>
              <td class="total-col">{formatCurrency(Number(item.amount || 0), invoice.currency)}</td
              >
            </tr>
          {/each}
        {:else}
          <tr>
            <td colspan="4" class="no-items">No line items</td>
          </tr>
        {/if}
      </tbody>
    </table>

    <!-- Totals Section -->
    <div class="totals-container">
      <table class="totals-table">
        <tbody>
          <tr>
            <td class="totals-label">Subtotal</td>
            <td class="totals-value"
              >{formatCurrency(Number(invoice.subtotal || 0), invoice.currency)}</td
            >
          </tr>
          <tr>
            <td class="totals-label">Shipping</td>
            <td class="totals-value">
              {formatCurrency(Number(invoice.shippingAmount || 0), invoice.currency)}
            </td>
          </tr>
          {#if Number(invoice.discountAmount || 0) > 0}
            <tr>
              <td class="totals-label">Discount</td>
              <td class="totals-value"
                >-{formatCurrency(Number(invoice.discountAmount), invoice.currency)}</td
              >
            </tr>
          {/if}
          <tr>
            <td class="totals-label">Tax</td>
            <td class="totals-value">
              {formatCurrency(Number(invoice.taxAmount || 0), invoice.currency)}
            </td>
          </tr>
          <tr class="grand-total">
            <td class="totals-label">Total</td>
            <td class="totals-value"
              >{formatCurrency(Number(invoice.totalAmount || 0), invoice.currency)}</td
            >
          </tr>
          {#if Number(invoice.amountPaid || 0) > 0}
            <tr>
              <td class="totals-label">Amount Paid</td>
              <td class="totals-value paid"
                >-{formatCurrency(Number(invoice.amountPaid), invoice.currency)}</td
              >
            </tr>
            <tr class="amount-due">
              <td class="totals-label">Amount Due</td>
              <td class="totals-value"
                >{formatCurrency(Number(invoice.amountDue || 0), invoice.currency)}</td
              >
            </tr>
          {/if}
        </tbody>
      </table>
    </div>

    <!-- Notes Section -->
    {#if invoice.notes}
      <div class="footer-notes">
        <h4>Description:</h4>
        <p>{invoice.notes}</p>
      </div>
    {/if}

    <!-- Footer Section -->
    <div class="sign-off">
      <p>Yours Sincerely,</p>
      <br />
      <p class="sign-company">{companyDisplayName}</p>
      {#if invoice.clientName}
        <p class="sign-client">{invoice.clientName}</p>
      {/if}
    </div>

    <!-- Copyright Footer -->
    <div class="copyright">
      {#if footerText}
        <p class="footer-text">{footerText}</p>
      {/if}
      {#if company?.taxId}
        <p>Tax ID: {company.taxId}</p>
      {/if}
      <p>Copyright &copy; {new Date().getFullYear()}. {companyDisplayName}. All rights reserved.</p>
    </div>
  </div>
</div>

<style>
  /* General Reset and Page Setup */
  .invoice-view {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background-color: #eef2f5;
    display: flex;
    justify-content: center;
    padding: 40px;
    color: #333;
  }

  .invoice-container {
    background-color: #ffffff;
    width: 800px;
    min-height: 1000px;
    padding: 50px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    position: relative;
  }

  /* Header Section */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 60px;
  }

  .company-details h1 {
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 5px;
    color: #222;
  }

  .company-details p {
    font-size: 14px;
    line-height: 1.4;
    color: #444;
    margin: 0;
  }

  .company-details a {
    color: var(--primary-color, #0056b3);
    text-decoration: underline;
  }

  .invoice-branding {
    text-align: right;
  }

  .invoice-title {
    font-size: 32px;
    font-weight: bold;
    color: #222;
    margin-bottom: 10px;
    letter-spacing: 0.5px;
  }

  .logo-container {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
  }

  .logo {
    max-height: 50px;
    width: auto;
  }

  .logo-text {
    font-size: 32px;
    font-weight: 700;
    color: var(--primary-color, #2c5475);
    letter-spacing: 1px;
  }

  /* Client & Meta Data Section */
  .info-section {
    display: flex;
    justify-content: space-between;
    margin-bottom: 40px;
  }

  .client-address h3 {
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 5px;
    color: #333;
  }

  .client-address p {
    font-size: 14px;
    line-height: 1.4;
    color: #444;
    margin: 0;
  }

  .invoice-meta {
    width: 40%;
  }

  .meta-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
    font-size: 14px;
  }

  .meta-label {
    font-weight: 700;
    color: #333;
  }

  .meta-value {
    color: #444;
    text-align: right;
  }

  /* Table Styling */
  .line-items-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 0;
  }

  .line-items-table th {
    background-color: var(--primary-color, #d1d9e1);
    text-align: left;
    padding: 10px 12px;
    font-size: 14px;
    font-weight: 700;
    border: 1px solid color-mix(in srgb, var(--primary-color, #bcc4cc) 80%, black);
    color: #fff;
  }

  .line-items-table th.qty-col,
  .line-items-table th.price-col,
  .line-items-table th.total-col {
    text-align: right;
  }

  .line-items-table td {
    border: 1px solid #bcc4cc;
    padding: 12px;
    font-size: 14px;
    vertical-align: top;
    color: #333;
  }

  .line-items-table .desc-col {
    width: 55%;
  }

  .line-items-table .qty-col,
  .line-items-table .price-col,
  .line-items-table .total-col {
    text-align: right;
  }

  .item-title {
    font-weight: 500;
    display: block;
    margin-bottom: 4px;
  }

  .item-desc {
    font-size: 12px;
    color: #555;
    line-height: 1.3;
    display: block;
  }

  .no-items {
    text-align: center;
    color: #666;
    padding: 20px;
  }

  /* Totals Section */
  .totals-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 0;
  }

  .totals-table {
    width: 40%;
    border-collapse: collapse;
  }

  .totals-table td {
    border: none;
    padding: 8px 12px;
    text-align: right;
    font-size: 14px;
  }

  .totals-table tr td.totals-label {
    border-right: 1px solid #bcc4cc;
    background-color: #e8ecef;
    width: 50%;
  }

  .totals-table tr td.totals-value {
    background-color: #e8ecef;
    border-right: 1px solid #bcc4cc;
  }

  .totals-table .grand-total td {
    background-color: var(--primary-color, #d1d9e1);
    font-weight: 700;
    border-top: 1px solid color-mix(in srgb, var(--primary-color, #bcc4cc) 80%, black);
    border-bottom: 1px solid color-mix(in srgb, var(--primary-color, #bcc4cc) 80%, black);
    color: #fff;
  }

  .totals-table .paid {
    color: #16a34a;
  }

  .totals-table .amount-due td {
    background-color: var(--secondary-color, #d1d9e1);
    font-weight: 700;
    border-top: 1px solid color-mix(in srgb, var(--secondary-color, #bcc4cc) 80%, black);
    border-bottom: 1px solid color-mix(in srgb, var(--secondary-color, #bcc4cc) 80%, black);
    color: #fff;
  }

  .totals-table .amount-due .totals-value {
    color: #fff;
  }

  /* Footer Text */
  .footer-notes {
    margin-top: 50px;
    font-size: 14px;
    color: #333;
  }

  .footer-notes h4 {
    font-size: 14px;
    font-weight: 700;
    margin-bottom: 5px;
  }

  .footer-notes p {
    margin: 0;
    white-space: pre-wrap;
  }

  .sign-off {
    margin-top: 30px;
    font-size: 14px;
    line-height: 1.5;
  }

  .sign-off p {
    margin: 0;
  }

  .sign-company {
    font-weight: 500;
  }

  .sign-client {
    color: #444;
  }

  .copyright {
    margin-top: 60px;
    text-align: center;
    font-size: 12px;
    color: #555;
    border-top: 1px solid #ddd;
    padding-top: 15px;
  }

  .copyright p {
    margin: 0 0 4px 0;
  }

  .copyright .footer-text {
    font-style: italic;
    color: var(--primary-color, #333);
    margin-bottom: 10px;
  }

  /* Print styles */
  @media print {
    .invoice-view {
      background: white !important;
      padding: 0 !important;
    }

    .invoice-container {
      box-shadow: none;
      width: 100%;
      padding: 20px;
    }
  }
</style>
