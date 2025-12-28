<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { formatCurrency, formatDate } from '$lib/utils/formatting.js';

  /** @type {{ data: import('./$types').PageData, form: import('./$types').ActionData }} */
  let { data, form } = $props();

  const estimate = $derived(data.estimate);
  /** @type {{ primaryColor?: string, secondaryColor?: string, footerText?: string }} */
  const template = $derived(data.template || {});
  const token = $derived(data.token);

  // Template colors
  const primaryColor = $derived(template?.primaryColor || '#3B82F6');
  const secondaryColor = $derived(template?.secondaryColor || '#1E40AF');
  const footerText = $derived(template?.footerText || '');

  let isSubmitting = $state(false);

  // Status colors - using design system tokens
  function getStatusColor(status) {
    const colors = {
      Draft: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]',
      Sent: 'bg-[var(--stage-contacted-bg)] text-[var(--stage-contacted)]',
      Viewed: 'bg-[var(--stage-qualified-bg)] text-[var(--stage-qualified)]',
      Accepted: 'bg-[var(--color-success-light)] text-[var(--color-success-default)]',
      Declined: 'bg-[var(--color-negative-light)] text-[var(--color-negative-default)]',
      Expired: 'bg-[var(--color-primary-light)] text-[var(--color-primary-default)]'
    };
    return colors[status] || 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]';
  }

  function isExpired() {
    if (!estimate.expiryDate) return false;
    return new Date(estimate.expiryDate) < new Date();
  }

  function canRespond() {
    return (estimate.status === 'Sent' || estimate.status === 'Viewed') && !isExpired();
  }

  function downloadPDF() {
    window.open(`/api/public/estimate/${token}/pdf/`, '_blank');
  }
</script>

<svelte:head>
  <title>Estimate #{estimate.estimateNumber} | {estimate.org?.name || 'Estimate'}</title>
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
            {estimate.org?.name || 'Estimate'}
          </h1>
          <p class="text-gray-500">Estimate #{estimate.estimateNumber}</p>
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

  <!-- Success/Error Messages -->
  {#if form?.success}
    <div class="mx-auto max-w-4xl px-4 pt-4 sm:px-6 lg:px-8">
      <div class="rounded-lg border border-green-200 bg-green-50 p-4">
        <p class="text-green-800">
          {#if form.action === 'accepted'}
            Thank you! You have accepted this estimate. We will be in touch shortly.
          {:else if form.action === 'declined'}
            You have declined this estimate. Thank you for your response.
          {/if}
        </p>
      </div>
    </div>
  {/if}

  {#if form?.error}
    <div class="mx-auto max-w-4xl px-4 pt-4 sm:px-6 lg:px-8">
      <div class="rounded-lg border border-red-200 bg-red-50 p-4">
        <p class="text-red-800">{form.error}</p>
      </div>
    </div>
  {/if}

  <!-- Estimate Content -->
  <div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="overflow-hidden rounded-xl bg-white shadow-lg">
      <!-- Estimate Header -->
      <div class="border-b bg-gray-50 p-6 sm:p-8">
        <div class="flex flex-col justify-between gap-6 sm:flex-row">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">Prepared For:</h2>
            <p class="mt-1 text-gray-700">{estimate.clientName}</p>
            {#if estimate.clientEmail}
              <p class="text-sm text-gray-500">{estimate.clientEmail}</p>
            {/if}
            {#if estimate.clientAddress?.line}
              <p class="mt-2 text-sm text-gray-500">
                {estimate.clientAddress.line}<br />
                {#if estimate.clientAddress.city}
                  {estimate.clientAddress.city},
                {/if}
                {estimate.clientAddress.state}
                {estimate.clientAddress.postcode}<br />
                {estimate.clientAddress.country}
              </p>
            {/if}
          </div>
          <div class="text-left sm:text-right">
            <div class="flex flex-col gap-2">
              <span
                class="inline-flex items-center self-start rounded-full px-3 py-1 text-sm font-medium sm:self-end {getStatusColor(
                  estimate.status
                )}"
              >
                {estimate.status}
              </span>
              <div class="text-sm text-gray-600">
                <span class="font-medium">Issue Date:</span>
                {formatDate(estimate.issueDate)}
              </div>
              {#if estimate.expiryDate}
                <div class="text-sm text-gray-600">
                  <span class="font-medium">Valid Until:</span>
                  <span class={isExpired() ? 'font-medium text-red-600' : ''}>
                    {formatDate(estimate.expiryDate)}
                    {#if isExpired()}
                      (Expired)
                    {/if}
                  </span>
                </div>
              {/if}
            </div>
          </div>
        </div>
      </div>

      <!-- Line Items -->
      <div class="p-6 sm:p-8">
        {#if estimate.title}
          <h3 class="mb-4 text-lg font-medium text-gray-900">{estimate.title}</h3>
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
              {#each estimate.lineItems as item}
                <tr class="border-b last:border-b-0">
                  <td class="py-4 text-gray-700">{item.description}</td>
                  <td class="py-4 text-right text-gray-600">{item.quantity}</td>
                  <td class="py-4 text-right text-gray-600">
                    {formatCurrency(Number(item.unit_price), estimate.currency)}
                  </td>
                  <td class="py-4 text-right font-medium text-gray-900">
                    {formatCurrency(Number(item.total), estimate.currency)}
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
                >{formatCurrency(Number(estimate.subtotal), estimate.currency)}</span
              >
            </div>
            {#if Number(estimate.discountAmount) > 0}
              <div class="flex w-full justify-between text-sm sm:w-64">
                <span class="text-gray-500">Discount:</span>
                <span class="text-green-600"
                  >-{formatCurrency(Number(estimate.discountAmount), estimate.currency)}</span
                >
              </div>
            {/if}
            {#if Number(estimate.taxAmount) > 0}
              <div class="flex w-full justify-between text-sm sm:w-64">
                <span class="text-gray-500">Tax:</span>
                <span class="text-gray-900"
                  >{formatCurrency(Number(estimate.taxAmount), estimate.currency)}</span
                >
              </div>
            {/if}
            <div
              class="mt-2 flex w-full justify-between border-t pt-2 text-xl font-bold sm:w-64"
              style="color: {primaryColor};"
            >
              <span>Total:</span>
              <span>{formatCurrency(Number(estimate.totalAmount), estimate.currency)}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Accept/Decline Actions -->
      {#if canRespond()}
        <div class="border-t bg-blue-50 p-6 sm:p-8">
          <h3 class="mb-4 text-lg font-medium text-gray-900">Your Response</h3>
          <p class="mb-6 text-gray-600">
            Please review this estimate and let us know if you'd like to proceed.
          </p>
          <div class="flex flex-col gap-4 sm:flex-row">
            <form
              method="POST"
              action="?/accept"
              use:enhance={() => {
                isSubmitting = true;
                return async ({ update }) => {
                  isSubmitting = false;
                  await update();
                  invalidateAll();
                };
              }}
            >
              <button
                type="submit"
                disabled={isSubmitting}
                class="w-full rounded-lg bg-green-600 px-6 py-3 font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50 sm:w-auto"
              >
                Accept Estimate
              </button>
            </form>
            <form
              method="POST"
              action="?/decline"
              use:enhance={() => {
                isSubmitting = true;
                return async ({ update }) => {
                  isSubmitting = false;
                  await update();
                  invalidateAll();
                };
              }}
            >
              <button
                type="submit"
                disabled={isSubmitting}
                class="w-full rounded-lg border border-gray-300 bg-white px-6 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50 sm:w-auto"
              >
                Decline
              </button>
            </form>
          </div>
        </div>
      {:else if estimate.status === 'Accepted'}
        <div class="border-t bg-green-50 p-6 sm:p-8">
          <div class="flex items-center gap-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="text-green-600"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <p class="font-medium text-green-800">You have accepted this estimate. Thank you!</p>
          </div>
        </div>
      {:else if estimate.status === 'Declined'}
        <div class="border-t bg-gray-100 p-6 sm:p-8">
          <p class="text-gray-600">This estimate was declined.</p>
        </div>
      {:else if isExpired()}
        <div class="border-t bg-orange-50 p-6 sm:p-8">
          <p class="text-orange-800">
            This estimate has expired. Please contact us if you'd like an updated quote.
          </p>
        </div>
      {/if}

      <!-- Notes & Terms -->
      {#if estimate.notes || estimate.terms}
        <div class="border-t bg-gray-50 p-6 sm:p-8">
          {#if estimate.notes}
            <div class="mb-4">
              <h4 class="mb-2 text-sm font-medium text-gray-700">Notes</h4>
              <p class="text-sm whitespace-pre-wrap text-gray-600">{estimate.notes}</p>
            </div>
          {/if}
          {#if estimate.terms}
            <div>
              <h4 class="mb-2 text-sm font-medium text-gray-700">Terms & Conditions</h4>
              <p class="text-sm whitespace-pre-wrap text-gray-600">{estimate.terms}</p>
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
      <p>Thank you for considering our services!</p>
      <p class="mt-2">If you have any questions about this estimate, please contact us.</p>
    </div>
  </div>
</div>
