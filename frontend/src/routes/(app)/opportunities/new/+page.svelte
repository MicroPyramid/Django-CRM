<script>
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import {
		Target,
		Building2,
		DollarSign,
		Users,
		Link2,
		FileText,
		ArrowLeft,
		Plus,
		Calendar
	} from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData, form?: import('./$types').ActionData }} */
	let { data, form } = $props();

	let isSubmitting = $state(false);

	// Form data with defaults
	let formData = $state({
		// Core Opportunity Information
		name: '',
		account: data.data.preSelectedAccountId || '',
		stage: 'PROSPECTING',
		opportunity_type: '',
		// Financial Information
		currency: 'USD',
		amount: '',
		probability: '',
		closed_on: '',
		// Source & Context
		lead_source: '',
		// Relationships
		contacts: /** @type {string[]} */ ([]),
		// Assignment
		assigned_to: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		// Notes
		description: ''
	});

	/**
	 * Handle multi-select changes
	 * @param {Event} event
	 * @param {'contacts' | 'assigned_to' | 'teams'} field
	 */
	function handleMultiSelect(event, field) {
		const target = /** @type {HTMLSelectElement} */ (event.target);
		const selected = Array.from(target.selectedOptions).map((opt) => opt.value);
		formData[field] = selected;
	}

	/**
	 * Calculate expected revenue based on amount and probability
	 */
	function calculateExpectedRevenue() {
		const amount = parseFloat(formData.amount);
		const probability = parseFloat(formData.probability);
		if (amount && probability) {
			return (amount * (probability / 100)).toFixed(2);
		}
		return '0.00';
	}

	/**
	 * Handle form submission success
	 */
	function handleSuccess() {
		goto('/opportunities');
	}
</script>

<svelte:head>
	<title>New Opportunity - CRM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
		<div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
			<div class="flex h-16 items-center justify-between">
				<div class="flex items-center space-x-4">
					<button
						onclick={() => history.back()}
						class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-gray-200"
					>
						<ArrowLeft class="h-5 w-5" />
					</button>
					<div class="flex items-center space-x-3">
						<div class="rounded-lg bg-purple-100 p-2 dark:bg-purple-900">
							<Target class="h-6 w-6 text-purple-600 dark:text-purple-400" />
						</div>
						<div>
							<h1 class="text-xl font-semibold text-gray-900 dark:text-white">New Opportunity</h1>
							<p class="text-sm text-gray-500 dark:text-gray-400">Create a new sales opportunity</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Form -->
	<div class="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
		{#if form?.error}
			<div
				class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
			>
				<p class="text-red-600 dark:text-red-400">{form.error}</p>
			</div>
		{/if}

		{#if form?.status === 'success'}
			<div
				class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20"
			>
				<p class="text-green-600 dark:text-green-400">{form.message}</p>
			</div>
			<script>
				setTimeout(() => {
					window.location.href = '/opportunities';
				}, 1500);
			</script>
		{/if}

		<form
			method="POST"
			use:enhance={() => {
				isSubmitting = true;
				return async ({ result, update }) => {
					isSubmitting = false;
					await update();
					if (result.type === 'success' && result.data?.status === 'success') {
						handleSuccess();
					}
				};
			}}
			class="space-y-8"
		>
			<!-- Section 1: Opportunity Information -->
			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<h2 class="mb-6 flex items-center text-lg font-medium text-gray-900 dark:text-white">
					<Target class="mr-2 h-5 w-5 text-purple-500" />
					Opportunity Information
				</h2>

				<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
					<!-- Name -->
					<div class="md:col-span-2">
						<label
							for="name"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Opportunity Name *
						</label>
						<input
							type="text"
							id="name"
							name="name"
							bind:value={formData.name}
							required
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
							placeholder="Enter opportunity name"
						/>
					</div>

					<!-- Account -->
					<div>
						<label
							for="account"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Account
						</label>
						<select
							id="account"
							name="account"
							bind:value={formData.account}
							disabled={!!data.data.preSelectedAccountId}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
						>
							<option value="">Select an account</option>
							{#each data.data.accounts as account}
								<option value={account.id}>{account.name}</option>
							{/each}
						</select>
						{#if data.data.preSelectedAccountId}
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Account pre-selected from {data.data.preSelectedAccountName}
							</p>
						{/if}
					</div>

					<!-- Stage -->
					<div>
						<label
							for="stage"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Stage *
						</label>
						<select
							id="stage"
							name="stage"
							bind:value={formData.stage}
							required
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
						>
							{#each data.data.stages as stage}
								<option value={stage.value}>{stage.label}</option>
							{/each}
						</select>
					</div>

					<!-- Opportunity Type -->
					<div>
						<label
							for="opportunity_type"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Type
						</label>
						<select
							id="opportunity_type"
							name="opportunity_type"
							bind:value={formData.opportunity_type}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
						>
							<option value="">Select type</option>
							{#each data.data.opportunityTypes as type}
								<option value={type.value}>{type.label}</option>
							{/each}
						</select>
					</div>

					<!-- Lead Source -->
					<div>
						<label
							for="lead_source"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Lead Source
						</label>
						<select
							id="lead_source"
							name="lead_source"
							bind:value={formData.lead_source}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
						>
							<option value="">Select source</option>
							{#each data.data.leadSources as source}
								<option value={source.value}>{source.label}</option>
							{/each}
						</select>
					</div>
				</div>
			</div>

			<!-- Section 2: Financial Information -->
			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<h2 class="mb-6 flex items-center text-lg font-medium text-gray-900 dark:text-white">
					<DollarSign class="mr-2 h-5 w-5 text-green-500" />
					Financial Information
				</h2>

				<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
					<!-- Amount -->
					<div>
						<label
							for="amount"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Amount
						</label>
						<input
							type="number"
							id="amount"
							name="amount"
							bind:value={formData.amount}
							min="0"
							step="0.01"
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-green-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-green-400"
							placeholder="0.00"
						/>
					</div>

					<!-- Currency -->
					<div>
						<label
							for="currency"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Currency
						</label>
						<select
							id="currency"
							name="currency"
							bind:value={formData.currency}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-green-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-green-400"
						>
							<option value="USD">USD - US Dollar</option>
							<option value="EUR">EUR - Euro</option>
							<option value="GBP">GBP - British Pound</option>
							<option value="INR">INR - Indian Rupee</option>
							<option value="JPY">JPY - Japanese Yen</option>
							<option value="CAD">CAD - Canadian Dollar</option>
							<option value="AUD">AUD - Australian Dollar</option>
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
							type="number"
							id="probability"
							name="probability"
							bind:value={formData.probability}
							min="0"
							max="100"
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-green-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-green-400"
							placeholder="0"
						/>
					</div>

					<!-- Expected Close Date -->
					<div>
						<label
							for="closed_on"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Expected Close Date
						</label>
						<input
							type="date"
							id="closed_on"
							name="closed_on"
							bind:value={formData.closed_on}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-green-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-green-400"
						/>
					</div>

					<!-- Expected Revenue (calculated) -->
					<div class="md:col-span-2">
						<div class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
							Expected Revenue
						</div>
						<div
							class="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-gray-900 dark:border-gray-600 dark:bg-gray-600 dark:text-white"
						>
							${calculateExpectedRevenue()}
						</div>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">Amount × Probability / 100</p>
					</div>
				</div>
			</div>

			<!-- Section 3: Assignment -->
			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<h2 class="mb-6 flex items-center text-lg font-medium text-gray-900 dark:text-white">
					<Users class="mr-2 h-5 w-5 text-purple-500" />
					Assignment
				</h2>

				<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
					<!-- Assigned To -->
					<div>
						<label
							for="assigned_to"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Assign to Users
						</label>
						<select
							id="assigned_to"
							name="assigned_to"
							multiple
							size="4"
							onchange={(e) => handleMultiSelect(e, 'assigned_to')}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
						>
							{#each data.data.users as user (user.id)}
								<option value={user.id} selected={formData.assigned_to.includes(user.id)}>
									{user.name} ({user.email})
								</option>
							{/each}
						</select>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
							Hold Ctrl/Cmd to select multiple
						</p>
					</div>

					<!-- Teams -->
					<div>
						<label
							for="teams"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Assign to Teams
						</label>
						<select
							id="teams"
							name="teams"
							multiple
							size="4"
							onchange={(e) => handleMultiSelect(e, 'teams')}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-purple-400"
						>
							{#each data.data.teams as team (team.id)}
								<option value={team.id} selected={formData.teams.includes(team.id)}>
									{team.name}
								</option>
							{/each}
						</select>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
							Hold Ctrl/Cmd to select multiple
						</p>
					</div>
				</div>
			</div>

			<!-- Section 4: Related Contacts -->
			{#if data.data.contacts.length > 0}
				<div
					class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<h2 class="mb-6 flex items-center text-lg font-medium text-gray-900 dark:text-white">
						<Link2 class="mr-2 h-5 w-5 text-blue-500" />
						Related Contacts
					</h2>

					<div>
						<label
							for="contacts"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Associate Contacts
						</label>
						<select
							id="contacts"
							name="contacts"
							multiple
							size="5"
							onchange={(e) => handleMultiSelect(e, 'contacts')}
							class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-400"
						>
							{#each data.data.contacts as contact (contact.id)}
								<option value={contact.id} selected={formData.contacts.includes(contact.id)}>
									{contact.firstName}
									{contact.lastName}
									{contact.email ? `(${contact.email})` : ''}
								</option>
							{/each}
						</select>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
							Hold Ctrl/Cmd to select multiple contacts
						</p>
					</div>
				</div>
			{/if}

			<!-- Section 5: Notes -->
			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<h2 class="mb-6 flex items-center text-lg font-medium text-gray-900 dark:text-white">
					<FileText class="mr-2 h-5 w-5 text-gray-500" />
					Notes
				</h2>

				<div>
					<label
						for="description"
						class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
					>
						Description
					</label>
					<textarea
						id="description"
						name="description"
						bind:value={formData.description}
						rows="4"
						class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-gray-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-gray-400"
						placeholder="Additional details about this opportunity..."
					></textarea>
				</div>
			</div>

			<!-- Form Actions -->
			<div class="flex items-center justify-end space-x-4 pt-6">
				<button
					type="button"
					onclick={() => history.back()}
					class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-purple-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-purple-400"
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={isSubmitting}
					class="flex items-center rounded-lg border border-transparent bg-purple-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-purple-700 focus:ring-2 focus:ring-purple-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
				>
					{#if isSubmitting}
						<div
							class="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
						></div>
						Creating...
					{:else}
						<Plus class="mr-2 h-4 w-4" />
						Create Opportunity
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
