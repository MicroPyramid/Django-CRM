<script>
	import {
		DollarSign,
		Calendar,
		Target,
		TrendingUp,
		FileText,
		User,
		Building,
		ArrowLeft,
		Save,
		X
	} from '@lucide/svelte';

	export let data;
	let opportunity = { ...data.opportunity };
	let error = '';
	let isSubmitting = false;

	let closeDateStr = opportunity.closeDate
		? new Date(opportunity.closeDate).toISOString().slice(0, 10)
		: '';

	$: {
		if (closeDateStr) {
			opportunity.closeDate = new Date(closeDateStr);
		} else {
			opportunity.closeDate = null;
		}
	}

	/**
	 * @param {SubmitEvent} e
	 */
	async function handleSubmit(e) {
		e.preventDefault();
		isSubmitting = true;
		error = '';

		const target = /** @type {HTMLFormElement} */ (e.target);
		const formData = new FormData(target);
		const res = await fetch('', { method: 'POST', body: formData });

		if (res.ok) {
			window.location.href = `/opportunities/${opportunity.id}`;
		} else {
			const result = await res.json();
			error = result?.message || 'Failed to update opportunity.';
		}
		isSubmitting = false;
	}

	const leadSources = [
		{ value: 'WEB', label: 'Web' },
		{ value: 'PHONE_INQUIRY', label: 'Phone Inquiry' },
		{ value: 'PARTNER_REFERRAL', label: 'Partner Referral' },
		{ value: 'COLD_CALL', label: 'Cold Call' },
		{ value: 'TRADE_SHOW', label: 'Trade Show' },
		{ value: 'EMPLOYEE_REFERRAL', label: 'Employee Referral' },
		{ value: 'ADVERTISEMENT', label: 'Advertisement' },
		{ value: 'OTHER', label: 'Other' }
	];

	const forecastCategories = [
		{ value: 'Pipeline', label: 'Pipeline' },
		{ value: 'Best Case', label: 'Best Case' },
		{ value: 'Commit', label: 'Commit' },
		{ value: 'Closed', label: 'Closed' }
	];
</script>

<div class="min-h-screen bg-gray-50 py-8 dark:bg-gray-900">
	<div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<div class="flex items-center justify-between">
				<div class="flex items-center space-x-4">
					<a
						href={`/opportunities/${opportunity.id}`}
						class="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-gray-300 bg-white text-gray-600 transition-colors hover:bg-gray-50 hover:text-gray-900 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-100"
					>
						<ArrowLeft class="h-5 w-5" />
					</a>
					<div>
						<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Opportunity</h1>
						<p class="mt-1 text-gray-600 dark:text-gray-400">
							Update opportunity details and track progress
						</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Form Card -->
		<div
			class="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<form onsubmit={handleSubmit} class="p-6 sm:p-8">
				<!-- Basic Information Section -->
				<div class="mb-8">
					<h2 class="mb-6 flex items-center text-lg font-semibold text-gray-900 dark:text-white">
						<Building class="mr-2 h-5 w-5 text-blue-600 dark:text-blue-400" />
						Basic Information
					</h2>

					<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
						<!-- Name -->
						<div class="lg:col-span-2">
							<label
								for="name"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Opportunity Name *
							</label>
							<input
								id="name"
								name="name"
								type="text"
								bind:value={opportunity.name}
								required
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="Enter opportunity name"
							/>
						</div>

						<!-- Amount -->
						<div>
							<label
								for="amount"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<DollarSign class="mr-1 inline h-4 w-4" />
								Amount
							</label>
							<input
								id="amount"
								name="amount"
								type="number"
								step="0.01"
								min="0"
								bind:value={opportunity.amount}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="0.00"
							/>
						</div>

						<!-- Expected Revenue -->
						<div>
							<label
								for="expectedRevenue"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<TrendingUp class="mr-1 inline h-4 w-4" />
								Expected Revenue
							</label>
							<input
								id="expectedRevenue"
								name="expectedRevenue"
								type="number"
								step="0.01"
								min="0"
								bind:value={opportunity.expectedRevenue}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="0.00"
							/>
						</div>

						<!-- Stage -->
						<div>
							<label
								for="stage"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Target class="mr-1 inline h-4 w-4" />
								Stage *
							</label>
							<select
								id="stage"
								name="stage"
								bind:value={opportunity.stage}
								required
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							>
								<option value="PROSPECTING">Prospecting</option>
								<option value="QUALIFICATION">Qualification</option>
								<option value="PROPOSAL">Proposal</option>
								<option value="NEGOTIATION">Negotiation</option>
								<option value="CLOSED_WON">Closed Won</option>
								<option value="CLOSED_LOST">Closed Lost</option>
							</select>
						</div>

						<!-- Probability -->
						<div>
							<label
								for="probability"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Probability (%)
							</label>
							<input
								id="probability"
								name="probability"
								type="number"
								min="0"
								max="100"
								bind:value={opportunity.probability}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="0"
							/>
						</div>

						<!-- Close Date -->
						<div>
							<label
								for="closeDate"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Calendar class="mr-1 inline h-4 w-4" />
								Close Date
							</label>
							<input
								id="closeDate"
								name="closeDate"
								type="date"
								bind:value={closeDateStr}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							/>
						</div>

						<!-- Lead Source -->
						<div>
							<label
								for="leadSource"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<User class="mr-1 inline h-4 w-4" />
								Lead Source
							</label>
							<select
								id="leadSource"
								name="leadSource"
								bind:value={opportunity.leadSource}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							>
								<option value="">Select source...</option>
								{#each leadSources as source}
									<option value={source.value}>{source.label}</option>
								{/each}
							</select>
						</div>

						<!-- Forecast Category -->
						<div>
							<label
								for="forecastCategory"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Forecast Category
							</label>
							<select
								id="forecastCategory"
								name="forecastCategory"
								bind:value={opportunity.forecastCategory}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							>
								<option value="">Select category...</option>
								{#each forecastCategories as category}
									<option value={category.value}>{category.label}</option>
								{/each}
							</select>
						</div>

						<!-- Type -->
						<div>
							<label
								for="type"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Type
							</label>
							<input
								id="type"
								name="type"
								type="text"
								bind:value={opportunity.type}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="e.g., New Business, Existing Business"
							/>
						</div>

						<!-- Next Step -->
						<div class="lg:col-span-2">
							<label
								for="nextStep"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Next Step
							</label>
							<input
								id="nextStep"
								name="nextStep"
								type="text"
								bind:value={opportunity.nextStep}
								class="w-full rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="What's the next action to take?"
							/>
						</div>

						<!-- Description -->
						<div class="lg:col-span-2">
							<label
								for="description"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<FileText class="mr-1 inline h-4 w-4" />
								Description
							</label>
							<textarea
								id="description"
								name="description"
								rows="4"
								bind:value={opportunity.description}
								class="w-full resize-none rounded-lg border border-gray-300 px-4 py-3 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="Provide additional details about this opportunity..."
							></textarea>
						</div>
					</div>
				</div>

				<!-- Error Message -->
				{#if error}
					<div
						class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
					>
						<div class="flex items-center">
							<X class="mr-2 h-5 w-5 text-red-400" />
							<p class="text-sm text-red-800 dark:text-red-400">{error}</p>
						</div>
					</div>
				{/if}

				<!-- Action Buttons -->
				<div
					class="flex items-center justify-end space-x-4 border-t border-gray-200 pt-6 dark:border-gray-700"
				>
					<a
						href={`/opportunities/${opportunity.id}`}
						class="rounded-lg border border-gray-300 px-6 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
					>
						Cancel
					</a>
					<button
						type="submit"
						disabled={isSubmitting}
						class="flex items-center rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:bg-blue-400"
					>
						{#if isSubmitting}
							<div
								class="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
							></div>
							Saving...
						{:else}
							<Save class="mr-2 h-4 w-4" />
							Save Changes
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
</div>
