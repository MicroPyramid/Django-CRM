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
	<div class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
		<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between h-16">
				<div class="flex items-center space-x-4">
					<button
						onclick={() => history.back()}
						class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
					>
						<ArrowLeft class="w-5 h-5" />
					</button>
					<div class="flex items-center space-x-3">
						<div class="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
							<Target class="w-6 h-6 text-purple-600 dark:text-purple-400" />
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
	<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		{#if form?.error}
			<div
				class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
			>
				<p class="text-red-600 dark:text-red-400">{form.error}</p>
			</div>
		{/if}

		{#if form?.status === 'success'}
			<div
				class="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
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
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
			>
				<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-6 flex items-center">
					<Target class="w-5 h-5 mr-2 text-purple-500" />
					Opportunity Information
				</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					<!-- Name -->
					<div class="md:col-span-2">
						<label
							for="name"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Opportunity Name *
						</label>
						<input
							type="text"
							id="name"
							name="name"
							bind:value={formData.name}
							required
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
							placeholder="Enter opportunity name"
						/>
					</div>

					<!-- Account -->
					<div>
						<label
							for="account"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Account
						</label>
						<select
							id="account"
							name="account"
							bind:value={formData.account}
							disabled={!!data.data.preSelectedAccountId}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50"
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
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Stage *
						</label>
						<select
							id="stage"
							name="stage"
							bind:value={formData.stage}
							required
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Type
						</label>
						<select
							id="opportunity_type"
							name="opportunity_type"
							bind:value={formData.opportunity_type}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Lead Source
						</label>
						<select
							id="lead_source"
							name="lead_source"
							bind:value={formData.lead_source}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
			>
				<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-6 flex items-center">
					<DollarSign class="w-5 h-5 mr-2 text-green-500" />
					Financial Information
				</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
					<!-- Amount -->
					<div>
						<label
							for="amount"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
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
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:focus:ring-green-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
							placeholder="0.00"
						/>
					</div>

					<!-- Currency -->
					<div>
						<label
							for="currency"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Currency
						</label>
						<select
							id="currency"
							name="currency"
							bind:value={formData.currency}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:focus:ring-green-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
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
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:focus:ring-green-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
							placeholder="0"
						/>
					</div>

					<!-- Expected Close Date -->
					<div>
						<label
							for="closed_on"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Expected Close Date
						</label>
						<input
							type="date"
							id="closed_on"
							name="closed_on"
							bind:value={formData.closed_on}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 dark:focus:ring-green-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						/>
					</div>

					<!-- Expected Revenue (calculated) -->
					<div class="md:col-span-2">
						<div class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Expected Revenue
						</div>
						<div
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 text-gray-900 dark:text-white"
						>
							${calculateExpectedRevenue()}
						</div>
						<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
							Amount × Probability / 100
						</p>
					</div>
				</div>
			</div>

			<!-- Section 3: Assignment -->
			<div
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
			>
				<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-6 flex items-center">
					<Users class="w-5 h-5 mr-2 text-purple-500" />
					Assignment
				</h2>

				<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
					<!-- Assigned To -->
					<div>
						<label
							for="assigned_to"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Assign to Users
						</label>
						<select
							id="assigned_to"
							name="assigned_to"
							multiple
							size="4"
							onchange={(e) => handleMultiSelect(e, 'assigned_to')}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Assign to Teams
						</label>
						<select
							id="teams"
							name="teams"
							multiple
							size="4"
							onchange={(e) => handleMultiSelect(e, 'teams')}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
					class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
				>
					<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-6 flex items-center">
						<Link2 class="w-5 h-5 mr-2 text-blue-500" />
						Related Contacts
					</h2>

					<div>
						<label
							for="contacts"
							class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
						>
							Associate Contacts
						</label>
						<select
							id="contacts"
							name="contacts"
							multiple
							size="5"
							onchange={(e) => handleMultiSelect(e, 'contacts')}
							class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						>
							{#each data.data.contacts as contact (contact.id)}
								<option value={contact.id} selected={formData.contacts.includes(contact.id)}>
									{contact.firstName} {contact.lastName} {contact.email ? `(${contact.email})` : ''}
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
				class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6"
			>
				<h2 class="text-lg font-medium text-gray-900 dark:text-white mb-6 flex items-center">
					<FileText class="w-5 h-5 mr-2 text-gray-500" />
					Notes
				</h2>

				<div>
					<label
						for="description"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
					>
						Description
					</label>
					<textarea
						id="description"
						name="description"
						bind:value={formData.description}
						rows="4"
						class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
						placeholder="Additional details about this opportunity..."
					></textarea>
				</div>
			</div>

			<!-- Form Actions -->
			<div class="flex items-center justify-end space-x-4 pt-6">
				<button
					type="button"
					onclick={() => history.back()}
					class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 dark:focus:ring-purple-400 transition-colors"
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={isSubmitting}
					class="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
				>
					{#if isSubmitting}
						<div
							class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"
						></div>
						Creating...
					{:else}
						<Plus class="w-4 h-4 mr-2" />
						Create Opportunity
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
