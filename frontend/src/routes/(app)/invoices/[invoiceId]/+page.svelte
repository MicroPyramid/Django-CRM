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
			ACCEPTED: 'bg-green-100 text-green-700',
			PRESENTED: 'bg-blue-100 text-blue-700',
			DRAFT: 'bg-gray-100 text-gray-700',
			APPROVED: 'bg-purple-100 text-purple-700',
			REJECTED: 'bg-red-100 text-red-700'
		};
		return classes[status] || 'bg-gray-100 text-gray-700';
	}
</script>

<!-- Super Rich Invoice View Page - Uniform Blue-Purple Theme -->
<div class="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 py-10">
	<div
		class="relative mx-auto max-w-3xl rounded-3xl border border-blue-200 bg-white/80 p-10 shadow-2xl backdrop-blur-md"
	>
		<div class="mb-10 flex items-center justify-between">
			<div>
				<h1 class="mb-2 text-4xl font-extrabold text-blue-900">Invoice</h1>
				<div class="text-lg font-bold text-blue-600">{invoice.quoteNumber}</div>
			</div>
			<div class="text-right text-blue-600">
				<div class="text-lg font-semibold">Prepared by:</div>
				<div class="text-sm">{invoice.preparedBy.name}</div>
				<div class="text-sm">{invoice.preparedBy.email}</div>
			</div>
		</div>

		<div class="mb-8 grid grid-cols-1 gap-8 md:grid-cols-2">
			<div>
				<div class="mb-2 font-bold text-blue-700">From:</div>
				<div class="font-semibold text-blue-900">{invoice.account.name}</div>
				<div class="text-sm text-blue-500">
					{#if invoice.account.street}
						{invoice.account.street}<br />
					{/if}
					{#if invoice.account.city}
						{invoice.account.city}{#if invoice.account.state}, {invoice.account.state}{/if}
						{invoice.account.postalCode}<br />
					{/if}
					{#if invoice.account.country}
						{invoice.account.country}
					{/if}
				</div>
			</div>
			<div>
				<div class="mb-2 font-bold text-blue-700">To:</div>
				<div class="font-semibold text-blue-900">
					{#if invoice.contact}
						{invoice.contact.firstName} {invoice.contact.lastName}
					{:else}
						{invoice.account.name}
					{/if}
				</div>
				<div class="text-sm text-blue-500">
					{#if invoice.contact && invoice.contact.email}
						{invoice.contact.email}
					{/if}
				</div>
			</div>
			<div>
				<div class="mb-1 flex justify-between text-sm text-blue-600">
					<span>Status:</span>
					<span
						class="inline-block rounded-full px-3 py-1 text-xs font-semibold {getStatusClass(
							invoice.status
						)}"
					>
						{invoice.status.toLowerCase()}
					</span>
				</div>
				<div class="mb-1 flex justify-between text-sm text-blue-600">
					<span>Created:</span><span>{new Date(invoice.createdAt).toLocaleDateString()}</span>
				</div>
				<div class="flex justify-between text-sm text-blue-600">
					<span>Due Date:</span><span
						>{invoice.expirationDate
							? new Date(invoice.expirationDate).toLocaleDateString()
							: 'N/A'}</span
					>
				</div>
			</div>
		</div>

		<div class="mb-8 border-t border-b border-blue-200">
			<table class="w-full text-sm">
				<thead>
					<tr class="bg-gradient-to-r from-blue-50 to-purple-50 text-xs text-blue-700 uppercase">
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
							<td class="p-3 text-right font-semibold text-blue-800"
								>{formatCurrency(Number(item.totalPrice))}</td
							>
						</tr>
					{/each}
				</tbody>
				<tfoot>
					<tr class="bg-gradient-to-r from-blue-50 to-purple-50">
						<td class="p-3 text-right font-bold text-blue-700" colspan="3">Subtotal:</td>
						<td class="p-3 text-right font-bold text-blue-800"
							>{formatCurrency(Number(invoice.subtotal))}</td
						>
					</tr>
					<tr class="bg-gradient-to-r from-blue-50 to-purple-50">
						<td class="p-3 text-right text-lg font-extrabold text-blue-900" colspan="3">Total:</td>
						<td class="p-3 text-right text-lg font-extrabold text-purple-700"
							>{formatCurrency(Number(invoice.grandTotal))}</td
						>
					</tr>
				</tfoot>
			</table>
		</div>

		{#if invoice.description}
			<div class="mb-8">
				<div class="mb-2 font-semibold text-blue-700">Notes:</div>
				<div class="rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-600">
					{invoice.description}
				</div>
			</div>
		{/if}

		<div class="flex items-center justify-between">
			<a
				href="/invoices"
				class="rounded-lg bg-blue-100 px-6 py-3 font-semibold text-blue-700 shadow transition hover:bg-blue-200"
			>
				← Back to Invoices
			</a>
			<div class="flex space-x-3">
				<a
					href="/invoices/{invoice.id}/edit"
					class="rounded-lg bg-purple-600 px-6 py-3 font-semibold text-white shadow transition hover:bg-purple-700"
				>
					Edit Invoice
				</a>
				<button
					class="rounded-lg bg-gradient-to-r from-blue-700 to-purple-700 px-6 py-3 font-bold text-white shadow-lg transition hover:from-blue-800 hover:to-purple-800"
				>
					Download PDF
				</button>
			</div>
		</div>

		<!-- Decorative elements -->
		<div
			class="absolute top-0 right-0 h-32 w-32 translate-x-16 -translate-y-16 rounded-full bg-gradient-to-bl from-purple-200/30 to-transparent"
		></div>
		<div
			class="absolute bottom-0 left-0 h-24 w-24 -translate-x-12 translate-y-12 rounded-full bg-gradient-to-tr from-blue-200/30 to-transparent"
		></div>
	</div>
</div>
