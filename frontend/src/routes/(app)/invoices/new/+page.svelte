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
		const newId = Math.max(...lineItems.map((item) => item.id), 0) + 1;
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
<div
	class="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-100 to-purple-100 px-4 py-12"
>
	<div
		class="w-full max-w-4xl rounded-3xl border border-blue-200 bg-white/80 p-10 shadow-2xl backdrop-blur-md"
	>
		<div class="mb-8 flex items-center justify-between">
			<div>
				<h1 class="text-3xl font-extrabold tracking-tight text-blue-800">New Invoice</h1>
				<p class="mt-1 text-blue-400">Create a professional invoice for your client</p>
			</div>
			<div class="flex items-center space-x-2">
				<span
					class="inline-block rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700"
					>DRAFT</span
				>
			</div>
		</div>

		<form method="POST" use:enhance class="space-y-8">
			<!-- Basic Invoice Information -->
			<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
				<div>
					<label for="invoice_number" class="mb-2 block font-semibold text-blue-600"
						>Invoice Number</label
					>
					<input
						id="invoice_number"
						name="invoice_number"
						type="text"
						bind:value={formData.invoiceNumber}
						readonly
						class="w-full rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 font-mono text-lg text-blue-900"
					/>
				</div>
				<div>
					<label for="account_select" class="mb-2 block font-semibold text-blue-600"
						>Account *</label
					>
					<select
						id="account_select"
						name="account_id"
						bind:value={formData.accountId}
						required
						class="w-full rounded-lg border border-blue-200 px-4 py-3 text-lg text-blue-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
					>
						<option value="">Select Account</option>
						{#each data.accounts as account}
							<option value={account.id}>{account.name}</option>
						{/each}
					</select>
				</div>
				<div>
					<label for="invoice_date" class="mb-2 block font-semibold text-blue-600"
						>Invoice Date *</label
					>
					<input
						id="invoice_date"
						name="invoice_date"
						type="date"
						bind:value={formData.invoiceDate}
						required
						class="w-full rounded-lg border border-blue-200 px-4 py-3 text-lg text-blue-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div>
					<label for="due_date" class="mb-2 block font-semibold text-blue-600">Due Date *</label>
					<input
						id="due_date"
						name="due_date"
						type="date"
						bind:value={formData.dueDate}
						required
						class="w-full rounded-lg border border-blue-200 px-4 py-3 text-lg text-blue-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
					/>
				</div>
				<div class="md:col-span-2">
					<label for="status_select" class="mb-2 block font-semibold text-blue-600">Status</label>
					<select
						id="status_select"
						name="status"
						bind:value={formData.status}
						class="w-full rounded-lg border border-blue-200 px-4 py-3 text-lg text-blue-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
					>
						<option value="DRAFT">Draft</option>
						<option value="SENT">Sent</option>
						<option value="PAID">Paid</option>
					</select>
				</div>
			</div>

			<!-- Line Items Section -->
			<div>
				<div class="mb-3 flex items-center justify-between">
					<h3 class="text-lg font-semibold text-blue-600">Line Items</h3>
					<button
						type="button"
						onclick={addLineItem}
						class="flex items-center gap-2 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 font-semibold text-white shadow transition hover:from-blue-700 hover:to-purple-700"
					>
						<Plus class="h-4 w-4" />
						Add Item
					</button>
				</div>

				<div class="overflow-x-auto rounded-xl border border-blue-200 bg-white/90 shadow-sm">
					<table class="min-w-full">
						<thead>
							<tr class="bg-gradient-to-r from-blue-50 to-purple-50 text-sm text-blue-700">
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
											class="w-full rounded border-none bg-transparent px-2 py-1 focus:ring-2 focus:ring-blue-500"
											placeholder="Description"
										/>
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
											class="w-20 rounded border-none bg-transparent px-2 py-1 text-right focus:ring-2 focus:ring-blue-500"
											min="1"
										/>
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
											class="w-24 rounded border-none bg-transparent px-2 py-1 text-right focus:ring-2 focus:ring-blue-500"
											min="0"
											step="0.01"
										/>
									</td>
									<td class="p-3 text-right font-semibold text-blue-800">
										${item.total.toFixed(2)}
									</td>
									<td class="p-3">
										<button
											type="button"
											onclick={() => removeLineItem(index)}
											class="p-1 text-red-500 hover:text-red-700"
										>
											<Trash2 class="h-4 w-4" />
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
						<tfoot>
							<tr>
								<td class="p-3 text-right font-bold text-blue-700" colspan="3">Subtotal:</td>
								<td class="p-3 text-right text-lg font-extrabold text-purple-700"
									>${subtotal.toFixed(2)}</td
								>
								<td></td>
							</tr>
							<tr>
								<td class="p-3 text-right font-bold text-blue-700" colspan="3">Total:</td>
								<td class="p-3 text-right text-xl font-extrabold text-purple-700"
									>${grandTotal.toFixed(2)}</td
								>
								<td></td>
							</tr>
						</tfoot>
					</table>
				</div>
			</div>

			<!-- Notes Section -->
			<div>
				<label for="notes" class="mb-2 block font-semibold text-blue-600">Notes</label>
				<textarea
					id="notes"
					name="notes"
					bind:value={formData.notes}
					rows="3"
					class="resize-vertical w-full rounded-lg border border-blue-200 px-4 py-3 text-blue-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
					placeholder="Additional notes for the invoice..."
				></textarea>
			</div>

			<!-- Action Buttons -->
			<div class="flex justify-end space-x-4">
				<button
					type="button"
					onclick={() => goto('/invoices')}
					class="flex items-center gap-2 rounded-lg bg-blue-100 px-6 py-3 font-semibold text-blue-700 shadow transition hover:bg-blue-200"
				>
					<X class="h-4 w-4" />
					Cancel
				</button>
				<button
					type="submit"
					class="flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-700 to-purple-700 px-8 py-3 text-lg font-bold text-white shadow-lg transition hover:from-blue-800 hover:to-purple-800"
				>
					<Save class="h-5 w-5" />
					Save Invoice
				</button>
			</div>
		</form>
	</div>
</div>
