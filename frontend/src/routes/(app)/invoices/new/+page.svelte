<script>
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { Save, X, Plus, Trash2 } from '@lucide/svelte';

  /** @type {import('./$types').ActionData} - for external reference */
  export const form = /** @type {any} */ (undefined);
  
  /** @type {import('./$types').PageData} */
  export let data;

    let lineItems = [
    { id: 1, description: 'Consulting Services', quantity: 10, rate: 100, total: 1000 },
    { id: 2, description: 'Setup Fee', quantity: 1, rate: 500, total: 500 }
  ];

  let formData = {
    invoiceNumber: 'INV-0001',
    accountId: '',
    invoiceDate: new Date().toISOString().split('T')[0],
    dueDate: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 14 days from now
    status: 'DRAFT',
    notes: 'Thank you for your business!'
  };

  function addLineItem() {
    const newId = Math.max(...lineItems.map(item => item.id), 0) + 1;
    lineItems = [...lineItems, { id: newId, description: '', quantity: 1, rate: 0, total: 0 }];
  }

  /**
   * @param {number} index
   */
  function removeLineItem(index) {
    lineItems = lineItems.filter((_, i) => i !== index);
  }

  /**
   * @param {number} index
   * @param {'description' | 'quantity' | 'rate'} field
   * @param {any} value
   */
  function updateLineItem(index, field, value) {
    if (field === 'description') {
      lineItems[index].description = value;
    } else if (field === 'quantity') {
      lineItems[index].quantity = value;
    } else if (field === 'rate') {
      lineItems[index].rate = value;
    }
    if (field === 'quantity' || field === 'rate') {
      lineItems[index].total = lineItems[index].quantity * lineItems[index].rate;
    }
    lineItems = [...lineItems]; // Trigger reactivity
  }

  $: subtotal = lineItems.reduce((sum, item) => sum + item.total, 0);
  $: grandTotal = subtotal; // Can add tax logic later
</script>

<!-- Super Rich Invoice Creation Page - Uniform Blue-Purple Theme -->
<div class="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 py-12 px-4 flex items-center justify-center">
  <div class="bg-white/80 backdrop-blur-md shadow-2xl rounded-3xl max-w-4xl w-full p-10 border border-blue-200">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-extrabold text-blue-800 tracking-tight">New Invoice</h1>
        <p class="text-blue-400 mt-1">Create a professional invoice for your client</p>
      </div>
      <div class="flex items-center space-x-2">
        <span class="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold">DRAFT</span>
      </div>
    </div>

    <form method="POST" use:enhance class="space-y-8">
      <!-- Basic Invoice Information -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label for="invoice_number" class="block text-blue-600 font-semibold mb-2">Invoice Number</label>
          <input 
            id="invoice_number"
            name="invoice_number"
            type="text"
            bind:value={formData.invoiceNumber}
            readonly
            class="w-full bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-lg font-mono text-blue-900" />
        </div>
        <div>
          <label for="account_select" class="block text-blue-600 font-semibold mb-2">Account *</label>
          <select 
            id="account_select"
            name="account_id"
            bind:value={formData.accountId}
            required
            class="w-full border border-blue-200 rounded-lg px-4 py-3 text-lg text-blue-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
            <option value="">Select Account</option>
            {#each data.accounts as account}
              <option value={account.id}>{account.name}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for="invoice_date" class="block text-blue-600 font-semibold mb-2">Invoice Date *</label>
          <input 
            id="invoice_date"
            name="invoice_date"
            type="date"
            bind:value={formData.invoiceDate}
            required
            class="w-full border border-blue-200 rounded-lg px-4 py-3 text-lg text-blue-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <div>
          <label for="due_date" class="block text-blue-600 font-semibold mb-2">Due Date *</label>
          <input 
            id="due_date"
            name="due_date"
            type="date"
            bind:value={formData.dueDate}
            required
            class="w-full border border-blue-200 rounded-lg px-4 py-3 text-lg text-blue-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <div class="md:col-span-2">
          <label for="status_select" class="block text-blue-600 font-semibold mb-2">Status</label>
          <select 
            id="status_select"
            name="status"
            bind:value={formData.status}
            class="w-full border border-blue-200 rounded-lg px-4 py-3 text-lg text-blue-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
            <option value="DRAFT">Draft</option>
            <option value="SENT">Sent</option>
            <option value="PAID">Paid</option>
          </select>
        </div>
      </div>

      <!-- Line Items Section -->
      <div>
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-blue-600 font-semibold text-lg">Line Items</h3>
          <button 
            type="button"
            onclick={addLineItem}
            class="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-full shadow hover:from-blue-700 hover:to-purple-700 transition font-semibold flex items-center gap-2">
            <Plus class="w-4 h-4" />
            Add Item
          </button>
        </div>
        
        <div class="overflow-x-auto rounded-xl border border-blue-200 shadow-sm bg-white/90">
          <table class="min-w-full">
            <thead>
              <tr class="bg-gradient-to-r from-blue-50 to-purple-50 text-blue-700 text-sm">
                <th class="p-3 text-left font-semibold">Description</th>
                <th class="p-3 text-right font-semibold">Quantity</th>
                <th class="p-3 text-right font-semibold">Rate</th>
                <th class="p-3 text-right font-semibold">Total</th>
                <th class="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {#each lineItems as item, index (index)}
                <tr class="border-b hover:bg-blue-50/60">
                  <td class="p-3">
                    <input 
                      type="text"
                      bind:value={item.description}
                      oninput={(e) => {
                        const target = e.target;
                        if (target instanceof HTMLInputElement) {
                          updateLineItem(index, 'description', target.value);
                        }
                      }}
                      class="w-full border-none bg-transparent focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                      placeholder="Description" />
                  </td>
                  <td class="p-3 text-right">
                    <input 
                      type="number"
                      bind:value={item.quantity}
                      oninput={(e) => {
                        const target = e.target;
                        if (target instanceof HTMLInputElement) {
                          updateLineItem(index, 'quantity', Number(target.value));
                        }
                      }}
                      class="w-20 border-none bg-transparent focus:ring-2 focus:ring-blue-500 rounded px-2 py-1 text-right"
                      min="1" />
                  </td>
                  <td class="p-3 text-right">
                    <input 
                      type="number"
                      bind:value={item.rate}
                      oninput={(e) => {
                        const target = e.target;
                        if (target instanceof HTMLInputElement) {
                          updateLineItem(index, 'rate', Number(target.value));
                        }
                      }}
                      class="w-24 border-none bg-transparent focus:ring-2 focus:ring-blue-500 rounded px-2 py-1 text-right"
                      min="0"
                      step="0.01" />
                  </td>
                  <td class="p-3 text-right font-semibold text-blue-800">
                    ${item.total.toFixed(2)}
                  </td>
                  <td class="p-3">
                    <button 
                      type="button"
                      onclick={() => removeLineItem(index)}
                      class="text-red-500 hover:text-red-700 p-1">
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
            <tfoot>
              <tr>
                <td class="p-3 text-right font-bold text-blue-700" colspan="3">Subtotal:</td>
                <td class="p-3 text-right font-extrabold text-lg text-purple-700">${subtotal.toFixed(2)}</td>
                <td></td>
              </tr>
              <tr>
                <td class="p-3 text-right font-bold text-blue-700" colspan="3">Total:</td>
                <td class="p-3 text-right font-extrabold text-xl text-purple-700">${grandTotal.toFixed(2)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      <!-- Notes Section -->
      <div>
        <label for="notes" class="block text-blue-600 font-semibold mb-2">Notes</label>
        <textarea
          id="notes"
          name="notes"
          bind:value={formData.notes}
          rows="3"
          class="w-full border border-blue-200 rounded-lg px-4 py-3 text-blue-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-vertical"
          placeholder="Additional notes for the invoice..."></textarea>
      </div>

      <!-- Action Buttons -->
      <div class="flex justify-end space-x-4">
        <button 
          type="button"
          onclick={() => goto('/invoices')}
          class="px-6 py-3 bg-blue-100 text-blue-700 rounded-lg font-semibold shadow hover:bg-blue-200 transition flex items-center gap-2">
          <X class="w-4 h-4" />
          Cancel
        </button>
        <button 
          type="submit"
          class="px-8 py-3 bg-gradient-to-r from-blue-700 to-purple-700 text-white rounded-lg font-bold shadow-lg hover:from-blue-800 hover:to-purple-800 transition text-lg flex items-center gap-2">
          <Save class="w-5 h-5" />
          Save Invoice
        </button>
      </div>
    </form>
  </div>
</div>
