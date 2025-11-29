<script>
	import { Check, X, Calendar, FileText } from '@lucide/svelte';
	import { enhance } from '$app/forms';

	export let data;
	export let form;

	let opportunity = data.opportunity;
	let isSubmitting = false;
	let selectedStatus = 'CLOSED_WON';
	let closeDate = new Date().toISOString().split('T')[0];
	let closeReason = '';

	const statusOptions = [
		{ value: 'CLOSED_WON', label: 'Closed Won', color: 'text-green-600' },
		{ value: 'CLOSED_LOST', label: 'Closed Lost', color: 'text-red-600' }
	];
</script>

<div class="min-h-screen bg-gray-50 py-8 dark:bg-gray-900">
	<div class="mx-auto max-w-2xl px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div
			class="mb-6 rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
				<h1 class="flex items-center gap-3 text-2xl font-semibold text-gray-900 dark:text-white">
					<div class="rounded-lg bg-blue-100 p-2 dark:bg-blue-900">
						<Check class="h-6 w-6 text-blue-600 dark:text-blue-400" />
					</div>
					Close Opportunity
				</h1>
				<p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
					Update the status and close details for this opportunity
				</p>
			</div>
		</div>

		<!-- Opportunity Info -->
		<div
			class="mb-6 rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="px-6 py-4">
				<h2 class="mb-4 text-lg font-medium text-gray-900 dark:text-white">Opportunity Details</h2>
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
					<div>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Name</p>
						<p class="text-base text-gray-900 dark:text-white">{opportunity.name}</p>
					</div>
					<div>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Amount</p>
						<p class="text-base text-gray-900 dark:text-white">
							{opportunity.amount ? `$${opportunity.amount.toLocaleString()}` : 'Not specified'}
						</p>
					</div>
					<div>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Current Stage</p>
						<p class="text-base text-gray-900 dark:text-white">
							{opportunity.stage.replace('_', ' ')}
						</p>
					</div>
					<div>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300">Probability</p>
						<p class="text-base text-gray-900 dark:text-white">
							{opportunity.probability ? `${opportunity.probability}%` : 'Not specified'}
						</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Close Form -->
		<div
			class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
				<h2 class="text-lg font-medium text-gray-900 dark:text-white">Close Opportunity</h2>
			</div>

			<form
				method="POST"
				use:enhance={() => {
					return async ({ update }) => {
						isSubmitting = true;
						await update();
						isSubmitting = false;
					};
				}}
				class="space-y-6 p-6"
			>
				{#if form?.error}
					<div
						class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
					>
						<div class="flex items-center gap-2">
							<X class="h-5 w-5 text-red-600 dark:text-red-400" />
							<span class="text-sm font-medium text-red-800 dark:text-red-400">Error</span>
						</div>
						<p class="mt-1 text-sm text-red-700 dark:text-red-300">{form.error}</p>
					</div>
				{/if}

				<!-- Status Selection -->
				<div>
					<label
						for="status"
						class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						Closing Status *
					</label>
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
						{#each statusOptions as option}
							<label class="relative cursor-pointer">
								<input
									type="radio"
									name="status"
									value={option.value}
									bind:group={selectedStatus}
									class="sr-only"
									required
								/>
								<div
									class="rounded-lg border-2 p-4 transition-all duration-200 {selectedStatus ===
									option.value
										? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
										: 'border-gray-200 hover:border-gray-300 dark:border-gray-600 dark:hover:border-gray-500'}"
								>
									<div class="flex items-center justify-between">
										<span class="font-medium {option.color} dark:opacity-90">{option.label}</span>
										{#if selectedStatus === option.value}
											<Check class="h-5 w-5 text-blue-600 dark:text-blue-400" />
										{/if}
									</div>
								</div>
							</label>
						{/each}
					</div>
				</div>

				<!-- Close Date -->
				<div>
					<label
						for="closeDate"
						class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						<Calendar class="mr-1 inline h-4 w-4" />
						Close Date *
					</label>
					<input
						type="date"
						id="closeDate"
						name="closeDate"
						bind:value={closeDate}
						required
						class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2
                   text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500
                   disabled:bg-gray-50 disabled:text-gray-500 dark:border-gray-600
                   dark:bg-gray-700 dark:text-white"
					/>
				</div>

				<!-- Close Reason -->
				<div>
					<label
						for="closeReason"
						class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						<FileText class="mr-1 inline h-4 w-4" />
						Reason for Closing
					</label>
					<textarea
						id="closeReason"
						name="closeReason"
						bind:value={closeReason}
						rows="4"
						placeholder="Provide details about why this opportunity is being closed..."
						class="w-full resize-none rounded-lg border border-gray-300 bg-white px-3
                   py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500
                   focus:ring-2 focus:ring-blue-500 dark:border-gray-600
                   dark:bg-gray-700 dark:text-white dark:placeholder-gray-500"
					></textarea>
				</div>

				<!-- Action Buttons -->
				<div class="flex flex-col gap-3 pt-4 sm:flex-row">
					<button
						type="submit"
						disabled={isSubmitting}
						class="flex flex-1 items-center justify-center
                   gap-2 rounded-lg bg-blue-600 px-4 py-2
                   font-medium text-white transition-colors duration-200 hover:bg-blue-700 disabled:cursor-not-allowed
                   disabled:bg-blue-400"
					>
						{#if isSubmitting}
							<div
								class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
							></div>
							Closing Opportunity...
						{:else}
							<Check class="h-4 w-4" />
							Close Opportunity
						{/if}
					</button>

					<a
						href={`/opportunities/${opportunity.id}`}
						class="flex-1 rounded-lg border border-gray-300 bg-white px-6
                   py-2 text-center font-medium text-gray-700 transition-colors
                   duration-200 hover:bg-gray-50 sm:flex-none
                   dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
					>
						Cancel
					</a>
				</div>
			</form>
		</div>
	</div>
</div>

<style>
	@media (max-width: 640px) {
		.max-w-md {
			max-width: 100%;
			padding: 0.5rem;
		}
	}
</style>
