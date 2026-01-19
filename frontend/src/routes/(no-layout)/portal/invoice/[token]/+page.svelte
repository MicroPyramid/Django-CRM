<script>
  import { formatCurrency, formatDate } from '$lib/utils/formatting.js';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  const invoice = $derived(data.invoice);
  /** @type {{ primaryColor?: string, secondaryColor?: string, footerText?: string }} */
  const template = $derived(data.template || {});
  const token = $derived(data.token);

  // Template colors
  const primaryColor = $derived(template?.primaryColor || '#3B82F6');
  const secondaryColor = $derived(template?.secondaryColor || '#1E40AF');
  const footerText = $derived(template?.footerText || '');

  // Status colors - using design system tokens
  function getStatusColor(status) {
    const colors = {
      Draft: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]',
      Sent: 'bg-[var(--stage-contacted-bg)] text-[var(--stage-contacted)]',
      Viewed: 'bg-[var(--stage-qualified-bg)] text-[var(--stage-qualified)]',
      Partially_Paid: 'bg-[var(--stage-negotiation-bg)] text-[var(--stage-negotiation)]',
      Paid: 'bg-[var(--color-success-light)] text-[var(--color-success-default)]',
      Overdue: 'bg-[var(--color-negative-light)] text-[var(--color-negative-default)]',
      Cancelled: 'bg-[var(--surface-sunken)] text-[var(--text-tertiary)]'
    };
    return colors[status] || 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]';
  }

  function downloadPDF() {
    window.open(`/api/public/invoice/${token}/pdf/`, '_blank');
  }
</script>

<svelte:head>
  <title>Invoice #{invoice.invoiceNumber} | {invoice.org?.name || 'Invoice'}</title>
</svelte:head>

<div
  class="min-h-screen bg-gray-50"
  style="--primary-color: {primaryColor}; --secondary-color: {secondaryColor};"
>
  <!-- Header -->
  <div class="border-b bg-white shadow-sm" style="border-bottom-color: {primaryColor};">
    <div class="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold" style="color: {primaryColor};">
            {invoice.org?.name || 'Invoice'}
          </h1>
          <p class="text-gray-500">Invoice #{invoice.invoiceNumber}</p>
        </div>
        <button
          onclick={downloadPDF}
          class="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-white transition-colors"
          style="background-color: {primaryColor};"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Download PDF
        </button>
      </div>
    </div>
  </div>

  <!-- Invoice Content -->
  <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="overflow-hidden rounded-xl bg-white shadow-lg">
      <!-- Invoice Header -->
      <div class="border-b bg-gray-50 p-6 sm:p-8">
        <div class="flex flex-col justify-between gap-6 sm:flex-row">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Bill To:</h2>
            <p class="mt-1 text-gray-700">{invoice.clientName}</p>
            {#if invoice.clientEmail}
              <p class="text-sm text-gray-500">{invoice.clientEmail}</p>
            {/if}
            {#if invoice.billingAddress?.line}
              <p class="mt-2 text-sm text-gray-500">
                {invoice.billingAddress.line}<br />
                {#if invoice.billingAddress.city}
                  {invoice.billingAddress.city},
                {/if}
                {invoice.billingAddress.state}
                {invoice.billingAddress.postcode}<br />
                {invoice.billingAddress.country}
              </p>
            {/if}
          </div>
          <div class="text-left sm:text-right">
            <div class="flex flex-col gap-2">
              <span
                class="inline-flex items-center self-start rounded-full px-3 py-1 text-sm font-medium sm:self-end {getStatusColor(
                  invoice.status
                )}"
              >
                {invoice.status.replace('_', ' ')}
              </span>
              <div class="text-sm text-gray-600">
                <span class="font-medium">Issue Date:</span>
                {formatDate(invoice.issueDate)}
              </div>
              <div class="text-sm text-gray-600">
                <span class="font-medium">Due Date:</span>
                <span class={invoice.status === 'Overdue' ? 'font-medium text-red-600' : ''}>
                  {formatDate(invoice.dueDate)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Line Items -->
      <div class="p-6 sm:p-8">
        {#if invoice.invoiceTitle}
          <h3 class="mb-4 text-lg font-medium text-gray-900">{invoice.invoiceTitle}</h3>
        {/if}

        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b text-left text-sm text-gray-500">
                <th class="pb-3 font-medium">Description</th>
                <th class="pb-3 text-right font-medium">Qty</th>
                <th class="pb-3 text-right font-medium">Unit Price</th>
                <th class="pb-3 text-right font-medium">Total</th>
              </tr>
            </thead>
            <tbody>
              {#each invoice.lineItems as item}
                <tr class="border-b last:border-b-0">
                  <td class="py-4 text-gray-700">{item.description}</td>
                  <td class="py-4 text-right text-gray-600">{item.quantity}</td>
                  <td class="py-4 text-right text-gray-600">
                    {formatCurrency(Number(item.unit_price), invoice.currency)}
                  </td>
                  <td class="py-4 text-right font-medium text-gray-900">
                    {formatCurrency(Number(item.total), invoice.currency)}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        <!-- Totals -->
        <div class="mt-6 border-t pt-6">
          <div class="flex flex-col items-end gap-2">
            <div class="flex w-full justify-between text-sm sm:w-64">
              <span class="text-gray-500">Subtotal:</span>
              <span class="text-gray-900"
                >{formatCurrency(Number(invoice.subtotal), invoice.currency)}</span
              >
            </div>
            {#if Number(invoice.discountAmount) > 0}
              <div class="flex w-full justify-between text-sm sm:w-64">
                <span class="text-gray-500">Discount:</span>
                <span class="text-green-600"
                  >-{formatCurrency(Number(invoice.discountAmount), invoice.currency)}</span
                >
              </div>
            {/if}
            {#if Number(invoice.taxAmount) > 0}
              <div class="flex w-full justify-between text-sm sm:w-64">
                <span class="text-gray-500">Tax:</span>
                <span class="text-gray-900"
                  >{formatCurrency(Number(invoice.taxAmount), invoice.currency)}</span
                >
              </div>
            {/if}
            <div
              class="mt-2 flex w-full justify-between border-t pt-2 text-lg font-semibold sm:w-64"
              style="color: {primaryColor};"
            >
              <span>Total:</span>
              <span>{formatCurrency(Number(invoice.totalAmount), invoice.currency)}</span>
            </div>
            {#if Number(invoice.amountPaid) > 0}
              <div class="flex w-full justify-between text-sm sm:w-64">
                <span class="text-gray-500">Amount Paid:</span>
                <span class="text-green-600"
                  >{formatCurrency(Number(invoice.amountPaid), invoice.currency)}</span
                >
              </div>
            {/if}
            {#if Number(invoice.amountDue) > 0}
              <div
                class="mt-2 flex w-full justify-between border-t pt-2 text-lg font-bold sm:w-64"
                style="color: {secondaryColor};"
              >
                <span>Amount Due:</span>
                <span>{formatCurrency(Number(invoice.amountDue), invoice.currency)}</span>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Payment History -->
      {#if invoice.payments && invoice.payments.length > 0}
        <div class="border-t bg-green-50 p-6 sm:p-8">
          <h3 class="mb-4 text-lg font-medium text-gray-900">Payment History</h3>
          <div class="space-y-3">
            {#each invoice.payments as payment}
              <div class="flex items-center justify-between text-sm">
                <div>
                  <span class="text-gray-700">{formatDate(payment.payment_date)}</span>
                  <span class="ml-2 text-gray-500">via {payment.payment_method}</span>
                </div>
                <span class="font-medium text-green-600">
                  {formatCurrency(Number(payment.amount), invoice.currency)}
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Notes & Terms -->
      {#if invoice.notes || invoice.terms}
        <div class="border-t bg-gray-50 p-6 sm:p-8">
          {#if invoice.notes}
            <div class="mb-4">
              <h4 class="mb-2 text-sm font-medium text-gray-700">Notes</h4>
              <p class="text-sm whitespace-pre-wrap text-gray-600">{invoice.notes}</p>
            </div>
          {/if}
          {#if invoice.terms}
            <div>
              <h4 class="mb-2 text-sm font-medium text-gray-700">Terms & Conditions</h4>
              <p class="text-sm whitespace-pre-wrap text-gray-600">{invoice.terms}</p>
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="mt-8 text-center text-sm text-gray-500">
      {#if footerText}
        <p class="mb-2 italic" style="color: {primaryColor};">{footerText}</p>
      {/if}
      <p>Thank you for your business!</p>
      <p class="mt-2">If you have any questions about this invoice, please contact us.</p>
    </div>
  </div>
</div>
