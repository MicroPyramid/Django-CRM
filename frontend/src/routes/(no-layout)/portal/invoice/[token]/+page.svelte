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

	function getStatusColor(status) {
		const colors = {
			Draft: 'bg-gray-100 text-gray-700',
			Sent: 'bg-blue-100 text-blue-700',
			Viewed: 'bg-indigo-100 text-indigo-700',
			Partially_Paid: 'bg-yellow-100 text-yellow-700',
			Paid: 'bg-green-100 text-green-700',
			Overdue: 'bg-red-100 text-red-700',
			Cancelled: 'bg-gray-200 text-gray-500'
		};
		return colors[status] || 'bg-gray-100 text-gray-700';
	}

	function downloadPDF() {
		window.open(`/api/public/invoice/${token}/pdf/`, '_blank');
	}
</script>

<svelte:head>
	<title>Invoice #{invoice.invoiceNumber} | {invoice.org?.name || 'Invoice'}</title>
</svelte:head>

<div class="min-h-screen bg-gray-50" style="--primary-color: {primaryColor}; --secondary-color: {secondaryColor};">
	<!-- Header -->
	<div class="bg-white border-b shadow-sm" style="border-bottom-color: {primaryColor};">
		<div class="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold" style="color: {primaryColor};">{invoice.org?.name || 'Invoice'}</h1>
					<p class="text-gray-500">Invoice #{invoice.invoiceNumber}</p>
				</div>
				<button
					onclick={downloadPDF}
					class="inline-flex items-center gap-2 px-4 py-2 text-white rounded-lg transition-colors"
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
	<div class="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
		<div class="bg-white rounded-xl shadow-lg overflow-hidden">
			<!-- Invoice Header -->
			<div class="p-6 sm:p-8 border-b bg-gray-50">
				<div class="flex flex-col sm:flex-row justify-between gap-6">
					<div>
						<h2 class="text-lg font-semibold text-gray-900">Bill To:</h2>
						<p class="text-gray-700 mt-1">{invoice.clientName}</p>
						{#if invoice.clientEmail}
							<p class="text-gray-500 text-sm">{invoice.clientEmail}</p>
						{/if}
						{#if invoice.billingAddress?.line}
							<p class="text-gray-500 text-sm mt-2">
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
								class="inline-flex self-start sm:self-end items-center rounded-full px-3 py-1 text-sm font-medium {getStatusColor(
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
								<span class={invoice.status === 'Overdue' ? 'text-red-600 font-medium' : ''}>
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
					<h3 class="text-lg font-medium text-gray-900 mb-4">{invoice.invoiceTitle}</h3>
				{/if}

				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b text-left text-sm text-gray-500">
								<th class="pb-3 font-medium">Description</th>
								<th class="pb-3 font-medium text-right">Qty</th>
								<th class="pb-3 font-medium text-right">Unit Price</th>
								<th class="pb-3 font-medium text-right">Total</th>
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
						<div class="flex justify-between w-full sm:w-64 text-sm">
							<span class="text-gray-500">Subtotal:</span>
							<span class="text-gray-900"
								>{formatCurrency(Number(invoice.subtotal), invoice.currency)}</span
							>
						</div>
						{#if Number(invoice.discountAmount) > 0}
							<div class="flex justify-between w-full sm:w-64 text-sm">
								<span class="text-gray-500">Discount:</span>
								<span class="text-green-600"
									>-{formatCurrency(Number(invoice.discountAmount), invoice.currency)}</span
								>
							</div>
						{/if}
						{#if Number(invoice.taxAmount) > 0}
							<div class="flex justify-between w-full sm:w-64 text-sm">
								<span class="text-gray-500">Tax:</span>
								<span class="text-gray-900"
									>{formatCurrency(Number(invoice.taxAmount), invoice.currency)}</span
								>
							</div>
						{/if}
						<div
							class="flex justify-between w-full sm:w-64 text-lg font-semibold border-t pt-2 mt-2"
							style="color: {primaryColor};"
						>
							<span>Total:</span>
							<span>{formatCurrency(Number(invoice.totalAmount), invoice.currency)}</span>
						</div>
						{#if Number(invoice.amountPaid) > 0}
							<div class="flex justify-between w-full sm:w-64 text-sm">
								<span class="text-gray-500">Amount Paid:</span>
								<span class="text-green-600"
									>{formatCurrency(Number(invoice.amountPaid), invoice.currency)}</span
								>
							</div>
						{/if}
						{#if Number(invoice.amountDue) > 0}
							<div
								class="flex justify-between w-full sm:w-64 text-lg font-bold border-t pt-2 mt-2"
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
				<div class="p-6 sm:p-8 border-t bg-green-50">
					<h3 class="text-lg font-medium text-gray-900 mb-4">Payment History</h3>
					<div class="space-y-3">
						{#each invoice.payments as payment}
							<div class="flex justify-between items-center text-sm">
								<div>
									<span class="text-gray-700">{formatDate(payment.payment_date)}</span>
									<span class="text-gray-500 ml-2">via {payment.payment_method}</span>
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
				<div class="p-6 sm:p-8 border-t bg-gray-50">
					{#if invoice.notes}
						<div class="mb-4">
							<h4 class="text-sm font-medium text-gray-700 mb-2">Notes</h4>
							<p class="text-sm text-gray-600 whitespace-pre-wrap">{invoice.notes}</p>
						</div>
					{/if}
					{#if invoice.terms}
						<div>
							<h4 class="text-sm font-medium text-gray-700 mb-2">Terms & Conditions</h4>
							<p class="text-sm text-gray-600 whitespace-pre-wrap">{invoice.terms}</p>
						</div>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Footer -->
		<div class="mt-8 text-center text-sm text-gray-500">
			{#if footerText}
				<p class="italic mb-2" style="color: {primaryColor};">{footerText}</p>
			{/if}
			<p>Thank you for your business!</p>
			<p class="mt-2">
				If you have any questions about this invoice, please contact us.
			</p>
		</div>
	</div>
</div>
