<script>
	import { formatCurrency } from '$lib/utils/formatting.js';

	/** @type {import('./$types').PageData} - for external reference */
	export let data;

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

<!-- Super Rich Invoice List Page - Uniform Blue-Purple Theme -->
<div class="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 p-8">
	<div class="mx-auto max-w-5xl">
		<div class="mb-10 flex items-center justify-between">
			<h1 class="text-4xl font-extrabold tracking-tight text-blue-900">Invoices</h1>
			<a
				href="/invoices/new"
				class="inline-flex items-center rounded-xl bg-gradient-to-r from-blue-700 to-purple-700 px-6 py-3 text-lg font-semibold text-white shadow-lg transition hover:from-blue-800 hover:to-purple-800"
				>+ New Invoice</a
			>
		</div>

		<!-- Search and Filter Controls -->
		<div class="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
			<!-- Search -->
			<div
				class="flex flex-1 items-center rounded-xl border border-blue-200 bg-white/80 px-4 py-2 shadow backdrop-blur-md"
			>
				<svg
					class="mr-2 h-5 w-5 text-blue-400"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
				>
					<circle cx="11" cy="11" r="8" />
					<line x1="21" y1="21" x2="16.65" y2="16.65" />
				</svg>
				<label for="invoice-search" class="sr-only">Search invoices</label>
				<input
					id="invoice-search"
					type="text"
					placeholder="Search invoices..."
					class="flex-1 bg-transparent text-blue-900 placeholder-blue-400 outline-none"
				/>
			</div>

			<!-- Status Filter -->
			<div
				class="flex items-center rounded-xl border border-blue-200 bg-white/80 px-4 py-2 shadow backdrop-blur-md"
			>
				<svg
					class="mr-2 h-5 w-5 text-purple-400"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
				>
					<rect x="3" y="7" width="18" height="13" rx="2" />
					<path d="M16 3v4M8 3v4" />
				</svg>
				<label for="invoice-status-filter" class="sr-only">Filter by status</label>
				<select
					id="invoice-status-filter"
					class="bg-transparent font-semibold text-blue-900 outline-none"
				>
					<option>All Statuses</option>
					<option>Paid</option>
					<option>Unpaid</option>
					<option>Overdue</option>
				</select>
			</div>

			<!-- Date Range -->
			<div
				class="flex items-center rounded-xl border border-blue-200 bg-white/80 px-4 py-2 shadow backdrop-blur-md"
			>
				<svg
					class="mr-2 h-5 w-5 text-blue-400"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
				>
					<rect x="3" y="4" width="18" height="18" rx="2" />
					<path d="M16 2v4M8 2v4M3 10h18" />
				</svg>
				<label for="invoice-date-range" class="sr-only">Date range filter</label>
				<input
					id="invoice-date-range"
					type="text"
					placeholder="Date range"
					class="w-28 bg-transparent text-blue-900 placeholder-blue-400 outline-none"
				/>
			</div>
		</div>

		<!-- Invoice Cards -->
		<div class="flex flex-col gap-5">
			{#each data.invoices as invoice}
				<div
					class="relative flex flex-col gap-4 overflow-hidden rounded-2xl border-t-8 border-blue-600 bg-white/80 p-5 shadow-xl backdrop-blur-md md:flex-row md:items-center md:justify-between"
				>
					<div class="flex flex-1 flex-col gap-4 md:flex-row md:items-center">
						<div class="flex min-w-[120px] flex-col gap-1">
							<span
								class="w-fit rounded-full px-2 py-0.5 text-xs font-bold tracking-widest uppercase {getStatusClass(
									invoice.status
								)}">{invoice.status.toLowerCase()}</span
							>
							<span class="text-xs text-blue-500"
								>Due: {invoice.expirationDate
									? new Date(invoice.expirationDate).toLocaleDateString()
									: 'N/A'}</span
							>
						</div>
						<div class="flex-1">
							<h2 class="mb-0.5 text-xl font-bold text-blue-900">{invoice.quoteNumber}</h2>
							<p class="mb-1 text-sm text-blue-500">{invoice.account.name}</p>
							<div class="mb-1">
								{#each invoice.lineItems as item}
									<div class="mb-0.5 flex justify-between text-xs text-blue-700">
										<span>{item.description || item.product?.name}</span>
										<span>{formatCurrency(Number(item.totalPrice))}</span>
									</div>
								{/each}
							</div>
						</div>
					</div>
					<div class="flex-shrink-0 text-right">
						<div class="mb-1 text-2xl font-extrabold text-purple-700">
							{formatCurrency(Number(invoice.grandTotal))}
						</div>
						<div class="flex gap-2">
							<a
								href="/invoices/{invoice.id}"
								class="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-blue-700"
								>View</a
							>
							<a
								href="/invoices/{invoice.id}/edit"
								class="rounded-full bg-purple-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-purple-700"
								>Edit</a
							>
						</div>
					</div>
					<!-- Decorative gradient -->
					<div
						class="absolute top-0 right-0 h-32 w-32 translate-x-16 -translate-y-16 rounded-full bg-gradient-to-bl from-purple-200/30 to-transparent"
					></div>
				</div>
			{/each}

			<!-- Empty State -->
			{#if data.invoices.length === 0}
				<div class="rounded-2xl bg-white/80 p-12 text-center shadow-xl backdrop-blur-md">
					<div class="mb-4 text-6xl">📄</div>
					<h3 class="mb-2 text-2xl font-bold text-blue-900">No invoices yet</h3>
					<p class="mb-6 text-blue-600">Create your first invoice to get started</p>
					<a
						href="/invoices/new"
						class="inline-flex items-center rounded-xl bg-gradient-to-r from-blue-700 to-purple-700 px-6 py-3 font-semibold text-white shadow-lg transition hover:from-blue-800 hover:to-purple-800"
					>
						Create Invoice
					</a>
				</div>
			{/if}
		</div>
	</div>
</div>
