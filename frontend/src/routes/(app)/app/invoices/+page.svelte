<script>
  /** @type {import('./$types').PageData} - for external reference */
  export let data;

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

  /**
   * @param {number} amount
   */
  function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  }
</script>

<!-- Super Rich Invoice List Page - Uniform Blue-Purple Theme -->
<div class="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 p-8">
  <div class="max-w-5xl mx-auto">
    <div class="flex justify-between items-center mb-10">
      <h1 class="text-4xl font-extrabold text-blue-900 tracking-tight">Invoices</h1>
      <a href="/app/invoices/new" class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-700 to-purple-700 text-white text-lg font-semibold rounded-xl shadow-lg hover:from-blue-800 hover:to-purple-800 transition">+ New Invoice</a>
    </div>
    
    <!-- Search and Filter Controls -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
      <!-- Search -->
      <div class="flex-1 flex items-center bg-white/80 backdrop-blur-md rounded-xl shadow px-4 py-2 border border-blue-200">
        <svg class="w-5 h-5 text-blue-400 mr-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <label for="invoice-search" class="sr-only">Search invoices</label>
        <input 
          id="invoice-search" 
          type="text" 
          placeholder="Search invoices..." 
          class="bg-transparent outline-none flex-1 text-blue-900 placeholder-blue-400" />
      </div>
      
      <!-- Status Filter -->
      <div class="flex items-center bg-white/80 backdrop-blur-md rounded-xl shadow px-4 py-2 border border-blue-200">
        <svg class="w-5 h-5 text-purple-400 mr-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <rect x="3" y="7" width="18" height="13" rx="2"/>
          <path d="M16 3v4M8 3v4"/>
        </svg>
        <label for="invoice-status-filter" class="sr-only">Filter by status</label>
        <select 
          id="invoice-status-filter" 
          class="bg-transparent outline-none text-blue-900 font-semibold">
          <option>All Statuses</option>
          <option>Paid</option>
          <option>Unpaid</option>
          <option>Overdue</option>
        </select>
      </div>
      
      <!-- Date Range -->
      <div class="flex items-center bg-white/80 backdrop-blur-md rounded-xl shadow px-4 py-2 border border-blue-200">
        <svg class="w-5 h-5 text-blue-400 mr-2" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <rect x="3" y="4" width="18" height="18" rx="2"/>
          <path d="M16 2v4M8 2v4M3 10h18"/>
        </svg>
        <label for="invoice-date-range" class="sr-only">Date range filter</label>
        <input 
          id="invoice-date-range" 
          type="text" 
          placeholder="Date range" 
          class="bg-transparent outline-none text-blue-900 placeholder-blue-400 w-28" />
      </div>
    </div>
    
    <!-- Invoice Cards -->
    <div class="flex flex-col gap-5">
      {#each data.invoices as invoice}
        <div class="bg-white/80 backdrop-blur-md rounded-2xl shadow-xl p-5 border-t-8 border-blue-600 relative overflow-hidden flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div class="flex-1 flex flex-col md:flex-row md:items-center gap-4">
            <div class="flex flex-col gap-1 min-w-[120px]">
              <span class="text-xs font-bold uppercase tracking-widest px-2 py-0.5 rounded-full w-fit {getStatusClass(invoice.status)}">{invoice.status.toLowerCase()}</span>
              <span class="text-blue-500 text-xs">Due: {invoice.expirationDate ? new Date(invoice.expirationDate).toLocaleDateString() : 'N/A'}</span>
            </div>
            <div class="flex-1">
              <h2 class="text-xl font-bold text-blue-900 mb-0.5">{invoice.quoteNumber}</h2>
              <p class="text-blue-500 mb-1 text-sm">{invoice.account.name}</p>
              <div class="mb-1">
                {#each invoice.lineItems as item}
                  <div class="flex justify-between text-blue-700 text-xs mb-0.5">
                    <span>{item.description || item.product?.name}</span>
                    <span>{formatCurrency(Number(item.totalPrice))}</span>
                  </div>
                {/each}
              </div>
            </div>
          </div>
          <div class="text-right flex-shrink-0">
            <div class="text-2xl font-extrabold text-purple-700 mb-1">{formatCurrency(Number(invoice.grandTotal))}</div>
            <div class="flex gap-2">
              <a href="/app/invoices/{invoice.id}" class="px-3 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold hover:bg-blue-700 transition">View</a>
              <a href="/app/invoices/{invoice.id}/edit" class="px-3 py-1 bg-purple-600 text-white rounded-full text-xs font-semibold hover:bg-purple-700 transition">Edit</a>
            </div>
          </div>
          <!-- Decorative gradient -->
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-purple-200/30 to-transparent rounded-full -translate-y-16 translate-x-16"></div>
        </div>
      {/each}
      
      <!-- Empty State -->
      {#if data.invoices.length === 0}
        <div class="bg-white/80 backdrop-blur-md rounded-2xl shadow-xl p-12 text-center">
          <div class="text-6xl mb-4">📄</div>
          <h3 class="text-2xl font-bold text-blue-900 mb-2">No invoices yet</h3>
          <p class="text-blue-600 mb-6">Create your first invoice to get started</p>
          <a href="/app/invoices/new" class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-700 to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:from-blue-800 hover:to-purple-800 transition">
            Create Invoice
          </a>
        </div>
      {/if}
    </div>
  </div>
</div>
