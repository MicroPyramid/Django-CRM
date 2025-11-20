<script>
  /** @type {import('./$types').PageData} - for external reference */
  export let data;

  // Use actual invoice data from server
  $: invoice = data.invoice;

  /**
   * @param {number} amount
   */
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }

  /**
   * @param {string} status
   */
  function getStatusClass(status) {
    /** @type {{ [key: string]: string }} */
    const classes = {
      'ACCEPTED': 'bg-green-100 text-green-700',
      'PRESENTED': 'bg-blue-100 text-blue-700', 
      'DRAFT': 'bg-gray-100 text-gray-700',
      'APPROVED': 'bg-purple-100 text-purple-700',
      'REJECTED': 'bg-red-100 text-red-700'
    };
    return classes[status] || 'bg-gray-100 text-gray-700';
  }
</script>

<!-- Super Rich Invoice View Page - Uniform Blue-Purple Theme -->
<div class="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 py-10">
  <div class="max-w-3xl mx-auto bg-white/80 backdrop-blur-md rounded-3xl shadow-2xl p-10 relative border border-blue-200">
    <div class="flex justify-between items-center mb-10">
      <div>
                <h1 class="text-4xl font-extrabold text-blue-900 mb-2">Invoice</h1>
        <div class="text-lg text-blue-600 font-bold">{invoice.quoteNumber}</div>
      </div>
      <div class="text-right text-blue-600">
        <div class="text-lg font-semibold">Prepared by:</div>
        <div class="text-sm">{invoice.preparedBy.name}</div>
        <div class="text-sm">{invoice.preparedBy.email}</div>
      </div>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
      <div>
        <div class="font-bold text-blue-700 mb-2">From:</div>
        <div class="text-blue-900 font-semibold">{invoice.account.name}</div>
        <div class="text-blue-500 text-sm">
          {#if invoice.account.street}
          {invoice.account.street}<br>
          {/if}
          {#if invoice.account.city}
          {invoice.account.city}{#if invoice.account.state}, {invoice.account.state}{/if} {invoice.account.postalCode}<br>
          {/if}
          {#if invoice.account.country}
          {invoice.account.country}
          {/if}
        </div>
      </div>
      <div>
        <div class="font-bold text-blue-700 mb-2">To:</div>
        <div class="text-blue-900 font-semibold">
          {#if invoice.contact}
            {invoice.contact.firstName} {invoice.contact.lastName}
          {:else}
            {invoice.account.name}
          {/if}
        </div>
        <div class="text-blue-500 text-sm">
          {#if invoice.contact && invoice.contact.email}
            {invoice.contact.email}
          {/if}
        </div>
      </div>
      <div>
        <div class="flex justify-between text-sm text-blue-600 mb-1">
          <span>Status:</span>
          <span class="inline-block px-3 py-1 rounded-full font-semibold text-xs {getStatusClass(invoice.status)}">
            {invoice.status.toLowerCase()}
          </span>
        </div>
        <div class="flex justify-between text-sm text-blue-600 mb-1">
          <span>Created:</span><span>{new Date(invoice.createdAt).toLocaleDateString()}</span>
        </div>
        <div class="flex justify-between text-sm text-blue-600">
          <span>Due Date:</span><span>{invoice.expirationDate ? new Date(invoice.expirationDate).toLocaleDateString() : 'N/A'}</span>
        </div>
      </div>
    </div>
    
    <div class="mb-8 border-t border-b border-blue-200">
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 uppercase text-xs">
            <th class="p-3 text-left">Description</th>
            <th class="p-3 text-right">Quantity</th>
            <th class="p-3 text-right">Rate</th>
            <th class="p-3 text-right">Total</th>
          </tr>
        </thead>
        <tbody>
          {#each invoice.lineItems as item}
            <tr class="border-b border-blue-100 hover:bg-blue-50/60">
              <td class="p-3">{item.description || item.product?.name || 'N/A'}</td>
              <td class="p-3 text-right">{item.quantity}</td>
              <td class="p-3 text-right">{formatCurrency(Number(item.unitPrice))}</td>
              <td class="p-3 text-right font-semibold text-blue-800">{formatCurrency(Number(item.totalPrice))}</td>
            </tr>
          {/each}
        </tbody>
        <tfoot>
          <tr class="bg-gradient-to-r from-blue-50 to-purple-50">
            <td class="p-3 text-right font-bold text-blue-700" colspan="3">Subtotal:</td>
            <td class="p-3 text-right font-bold text-blue-800">{formatCurrency(Number(invoice.subtotal))}</td>
          </tr>
          <tr class="bg-gradient-to-r from-blue-50 to-purple-50">
            <td class="p-3 text-right font-extrabold text-blue-900 text-lg" colspan="3">Total:</td>
            <td class="p-3 text-right font-extrabold text-purple-700 text-lg">{formatCurrency(Number(invoice.grandTotal))}</td>
          </tr>
        </tfoot>
      </table>
    </div>
    
    {#if invoice.description}
      <div class="mb-8">
        <div class="font-semibold text-blue-700 mb-2">Notes:</div>
        <div class="text-blue-600 bg-blue-50 p-4 rounded-lg border border-blue-200">
          {invoice.description}
        </div>
      </div>
    {/if}
    
    <div class="flex justify-between items-center">
      <a 
        href="/app/invoices" 
        class="px-6 py-3 bg-blue-100 text-blue-700 rounded-lg font-semibold shadow hover:bg-blue-200 transition">
        ← Back to Invoices
      </a>
      <div class="flex space-x-3">
        <a 
          href="/app/invoices/{invoice.id}/edit" 
          class="px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold shadow hover:bg-purple-700 transition">
          Edit Invoice
        </a>
        <button 
          class="px-6 py-3 bg-gradient-to-r from-blue-700 to-purple-700 text-white rounded-lg font-bold shadow-lg hover:from-blue-800 hover:to-purple-800 transition">
          Download PDF
        </button>
      </div>
    </div>
    
        <!-- Decorative elements -->
    <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-200/30 to-transparent rounded-full -translate-y-16 translate-x-16"></div>
    <div class="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-blue-200/30 to-transparent rounded-full translate-y-12 -translate-x-12"></div>
  </div>
</div>
