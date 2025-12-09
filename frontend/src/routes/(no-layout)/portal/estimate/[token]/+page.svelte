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

	function getStatusColor(status) {
		const colors = {
			Draft: 'bg-gray-100 text-gray-700',
			Sent: 'bg-blue-100 text-blue-700',
			Viewed: 'bg-indigo-100 text-indigo-700',
			Accepted: 'bg-green-100 text-green-700',
			Declined: 'bg-red-100 text-red-700',
			Expired: 'bg-orange-100 text-orange-700'
		};
		return colors[status] || 'bg-gray-100 text-gray-700';
	}

	function isExpired() {
		if (!estimate.expiryDate) return false;
		return new Date(estimate.expiryDate) < new Date();
	}

	function canRespond() {
		return (
			(estimate.status === 'Sent' || estimate.status === 'Viewed') &&
			!isExpired()
		);
	}

	function downloadPDF() {
		window.open(`/api/public/estimate/${token}/pdf/`, '_blank');
	}
</script>

<svelte:head>
	<title>Estimate #{estimate.estimateNumber} | {estimate.org?.name || 'Estimate'}</title>
</svelte:head>

<div class="min-h-screen bg-gray-50" style="--primary-color: {primaryColor}; --secondary-color: {secondaryColor};">
	<!-- Header -->
	<div class="bg-white border-b shadow-sm" style="border-bottom-color: {primaryColor};">
		<div class="max-w-4xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold" style="color: {primaryColor};">{estimate.org?.name || 'Estimate'}</h1>
					<p class="text-gray-500">Estimate #{estimate.estimateNumber}</p>
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

	<!-- Success/Error Messages -->
	{#if form?.success}
		<div class="max-w-4xl mx-auto px-4 pt-4 sm:px-6 lg:px-8">
			<div class="bg-green-50 border border-green-200 rounded-lg p-4">
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
		<div class="max-w-4xl mx-auto px-4 pt-4 sm:px-6 lg:px-8">
			<div class="bg-red-50 border border-red-200 rounded-lg p-4">
				<p class="text-red-800">{form.error}</p>
			</div>
		</div>
	{/if}

	<!-- Estimate Content -->
	<div class="max-w-4xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
		<div class="bg-white rounded-xl shadow-lg overflow-hidden">
			<!-- Estimate Header -->
			<div class="p-6 sm:p-8 border-b bg-gray-50">
				<div class="flex flex-col sm:flex-row justify-between gap-6">
					<div>
						<h2 class="text-lg font-semibold text-gray-900">Prepared For:</h2>
						<p class="text-gray-700 mt-1">{estimate.clientName}</p>
						{#if estimate.clientEmail}
							<p class="text-gray-500 text-sm">{estimate.clientEmail}</p>
						{/if}
						{#if estimate.clientAddress?.line}
							<p class="text-gray-500 text-sm mt-2">
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
								class="inline-flex self-start sm:self-end items-center rounded-full px-3 py-1 text-sm font-medium {getStatusColor(
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
									<span class={isExpired() ? 'text-red-600 font-medium' : ''}>
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
					<h3 class="text-lg font-medium text-gray-900 mb-4">{estimate.title}</h3>
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
						<div class="flex justify-between w-full sm:w-64 text-sm">
							<span class="text-gray-500">Subtotal:</span>
							<span class="text-gray-900"
								>{formatCurrency(Number(estimate.subtotal), estimate.currency)}</span
							>
						</div>
						{#if Number(estimate.discountAmount) > 0}
							<div class="flex justify-between w-full sm:w-64 text-sm">
								<span class="text-gray-500">Discount:</span>
								<span class="text-green-600"
									>-{formatCurrency(Number(estimate.discountAmount), estimate.currency)}</span
								>
							</div>
						{/if}
						{#if Number(estimate.taxAmount) > 0}
							<div class="flex justify-between w-full sm:w-64 text-sm">
								<span class="text-gray-500">Tax:</span>
								<span class="text-gray-900"
									>{formatCurrency(Number(estimate.taxAmount), estimate.currency)}</span
								>
							</div>
						{/if}
						<div
							class="flex justify-between w-full sm:w-64 text-xl font-bold border-t pt-2 mt-2"
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
				<div class="p-6 sm:p-8 border-t bg-blue-50">
					<h3 class="text-lg font-medium text-gray-900 mb-4">Your Response</h3>
					<p class="text-gray-600 mb-6">
						Please review this estimate and let us know if you'd like to proceed.
					</p>
					<div class="flex flex-col sm:flex-row gap-4">
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
								class="w-full sm:w-auto px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
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
								class="w-full sm:w-auto px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors disabled:opacity-50"
							>
								Decline
							</button>
						</form>
					</div>
				</div>
			{:else if estimate.status === 'Accepted'}
				<div class="p-6 sm:p-8 border-t bg-green-50">
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
						<p class="text-green-800 font-medium">
							You have accepted this estimate. Thank you!
						</p>
					</div>
				</div>
			{:else if estimate.status === 'Declined'}
				<div class="p-6 sm:p-8 border-t bg-gray-100">
					<p class="text-gray-600">This estimate was declined.</p>
				</div>
			{:else if isExpired()}
				<div class="p-6 sm:p-8 border-t bg-orange-50">
					<p class="text-orange-800">
						This estimate has expired. Please contact us if you'd like an updated quote.
					</p>
				</div>
			{/if}

			<!-- Notes & Terms -->
			{#if estimate.notes || estimate.terms}
				<div class="p-6 sm:p-8 border-t bg-gray-50">
					{#if estimate.notes}
						<div class="mb-4">
							<h4 class="text-sm font-medium text-gray-700 mb-2">Notes</h4>
							<p class="text-sm text-gray-600 whitespace-pre-wrap">{estimate.notes}</p>
						</div>
					{/if}
					{#if estimate.terms}
						<div>
							<h4 class="text-sm font-medium text-gray-700 mb-2">Terms & Conditions</h4>
							<p class="text-sm text-gray-600 whitespace-pre-wrap">{estimate.terms}</p>
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
			<p>Thank you for considering our services!</p>
			<p class="mt-2">
				If you have any questions about this estimate, please contact us.
			</p>
		</div>
	</div>
</div>
