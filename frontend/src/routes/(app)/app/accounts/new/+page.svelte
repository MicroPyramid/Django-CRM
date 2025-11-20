<script>
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';

	// Lucide icons
	import {
		Building,
		Mail,
		Phone,
		Globe,
		MapPin,
		DollarSign,
		Users,
		Save,
		X,
		CheckCircle,
		AlertCircle,
		Briefcase,
		FileText
	} from '@lucide/svelte';

	/** @type {{ data: import('./$types').PageData, form: import('./$types').ActionData }} */
	let { data, form } = $props();

	// Toast state
	let showToast = $state(false);
	let toastMessage = $state('');
	let toastType = $state('success'); // 'success' | 'error'

	// Form data
	let formData = $state({
		// Core Account Information
		name: '',
		email: '',
		phone: '',
		website: '',
		// Business Information
		industry: '',
		number_of_employees: '',
		annual_revenue: '',
		// Address
		address_line: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		// Assignment
		assigned_to: /** @type {string[]} */ ([]),
		teams: /** @type {string[]} */ ([]),
		// Notes
		description: ''
	});

	/** @type {Record<string, string>} */
	let errors = $state({});

	/**
	 * Handles changes to form inputs
	 * @param {Event} event
	 */
	function handleChange(event) {
		const target = /** @type {HTMLInputElement} */ (event.target);
		const { name, value } = target;
		// @ts-ignore
		formData[name] = value;
		// Clear error when user starts typing
		if (errors[name]) {
			errors[name] = '';
		}
	}

	/**
	 * Handle multi-select changes
	 * @param {Event} event
	 * @param {'assigned_to' | 'teams'} field
	 */
	function handleMultiSelect(event, field) {
		const target = /** @type {HTMLSelectElement} */ (event.target);
		const selected = Array.from(target.selectedOptions).map((opt) => opt.value);
		formData[field] = selected;
	}

	/**
	 * Validates the form before submission.
	 */
	function validateForm() {
		errors = {};
		let isValid = true;

		// Required fields
		if (!formData.name?.trim()) {
			errors.name = 'Account name is required';
			isValid = false;
		}

		// Validate website URL if provided
		if (formData.website && !/^https?:\/\/.+/.test(formData.website)) {
			errors.website = 'Please enter a valid website URL (include http:// or https://)';
			isValid = false;
		}

		// Validate phone format if provided
		if (formData.phone && !/^[\d\s\-+()]*$/.test(formData.phone)) {
			errors.phone = 'Please enter a valid phone number';
			isValid = false;
		}

		// Validate number of employees if provided
		if (
			formData.number_of_employees &&
			(isNaN(Number(formData.number_of_employees)) || Number(formData.number_of_employees) < 0)
		) {
			errors.number_of_employees = 'Please enter a valid number';
			isValid = false;
		}

		// Validate annual revenue if provided
		if (
			formData.annual_revenue &&
			(isNaN(Number(formData.annual_revenue)) || Number(formData.annual_revenue) < 0)
		) {
			errors.annual_revenue = 'Please enter a valid amount';
			isValid = false;
		}

		return isValid;
	}

	// Submitting indicator
	let isSubmitting = $state(false);

	/**
	 * Resets the form to its initial state
	 */
	function resetForm() {
		formData = {
			name: '',
			email: '',
			phone: '',
			website: '',
			industry: '',
			number_of_employees: '',
			annual_revenue: '',
			address_line: '',
			city: '',
			state: '',
			postcode: '',
			country: '',
			assigned_to: [],
			teams: [],
			description: ''
		};
		errors = {};
	}

	/**
	 * @param {string} message
	 * @param {string} type
	 */
	function showNotification(message, type = 'success') {
		toastMessage = message;
		toastType = type;
		showToast = true;
		setTimeout(() => (showToast = false), 5000);
	}
</script>

<!-- Main container -->
<div class="min-h-screen bg-gray-50 py-8 dark:bg-gray-900">
	<!-- Toast notification -->
	{#if showToast}
		<div class="fixed right-4 top-4 z-50" in:fade>
			<div
				class="flex items-center rounded-lg p-4 shadow-lg {toastType === 'success'
					? 'border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
					: 'border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'}"
			>
				<div class="flex-shrink-0">
					{#if toastType === 'success'}
						<CheckCircle class="h-5 w-5 text-green-400 dark:text-green-400" />
					{:else}
						<AlertCircle class="h-5 w-5 text-red-400 dark:text-red-400" />
					{/if}
				</div>
				<div class="ml-3">
					<p
						class="text-sm font-medium {toastType === 'success'
							? 'text-green-800 dark:text-green-200'
							: 'text-red-800 dark:text-red-200'}"
					>
						{toastMessage}
					</p>
				</div>
				<button
					onclick={() => (showToast = false)}
					class="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 {toastType === 'success'
						? 'text-green-500 hover:bg-green-100 dark:text-green-400 dark:hover:bg-green-800/30'
						: 'text-red-500 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-800/30'}"
				>
					<X class="h-4 w-4" />
				</button>
			</div>
		</div>
	{/if}

	<div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div
			class="mb-6 rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
				<div class="flex items-center justify-between">
					<div>
						<h1
							class="flex items-center gap-2 text-2xl font-bold text-gray-900 dark:text-white"
						>
							<Building class="h-6 w-6 text-blue-600 dark:text-blue-400" />
							Create New Account
						</h1>
						<p class="mt-1 text-gray-600 dark:text-gray-300">
							Add a new company or organization to your CRM
						</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Show error if returned from server -->
		{#if form?.error}
			<div
				class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
			>
				<div class="flex items-center">
					<AlertCircle class="mr-2 h-5 w-5 text-red-400 dark:text-red-400" />
					<span class="font-medium text-red-800 dark:text-red-200">Error:</span>
					<span class="ml-1 text-red-700 dark:text-red-300">{form.error}</span>
				</div>
			</div>
		{/if}

		<!-- Main Form -->
		<form
			method="POST"
			use:enhance={({ cancel }) => {
				if (!validateForm()) {
					cancel();
					return;
				}

				isSubmitting = true;

				return async ({ result }) => {
					isSubmitting = false;

					if (result.type === 'success') {
						showNotification('Account created successfully!', 'success');
						resetForm();
						setTimeout(() => goto('/app/accounts'), 1500);
					} else if (result.type === 'failure') {
						const errorMessage =
							result.data &&
							typeof result.data === 'object' &&
							'error' in result.data &&
							typeof result.data.error === 'string'
								? result.data.error
								: 'Failed to create account';
						showNotification(errorMessage, 'error');
					}
				};
			}}
			class="space-y-6"
		>
			<!-- Account Information Section -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<h2
						class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
					>
						<Briefcase class="h-5 w-5 text-blue-600 dark:text-blue-400" />
						Account Information
					</h2>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<!-- Account Name -->
						<div class="md:col-span-2">
							<label
								for="name"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Account Name *
							</label>
							<input
								id="name"
								name="name"
								type="text"
								bind:value={formData.name}
								oninput={handleChange}
								placeholder="Enter company name"
								required
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400 {errors.name
									? 'border-red-500 ring-1 ring-red-500 dark:border-red-400 dark:ring-red-400'
									: ''}"
							/>
							{#if errors.name}
								<p class="mt-1 text-sm text-red-500 dark:text-red-400">{errors.name}</p>
							{/if}
						</div>

						<!-- Email -->
						<div>
							<label
								for="email"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Mail class="mr-1 inline h-4 w-4" />
								Email
							</label>
							<input
								id="email"
								name="email"
								type="email"
								bind:value={formData.email}
								oninput={handleChange}
								placeholder="company@example.com"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							/>
						</div>

						<!-- Phone -->
						<div>
							<label
								for="phone"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Phone class="mr-1 inline h-4 w-4" />
								Phone
							</label>
							<input
								id="phone"
								name="phone"
								type="tel"
								bind:value={formData.phone}
								oninput={handleChange}
								placeholder="+1 (555) 123-4567"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400 {errors.phone
									? 'border-red-500 ring-1 ring-red-500 dark:border-red-400 dark:ring-red-400'
									: ''}"
							/>
							{#if errors.phone}
								<p class="mt-1 text-sm text-red-500 dark:text-red-400">{errors.phone}</p>
							{/if}
						</div>

						<!-- Website -->
						<div class="md:col-span-2">
							<label
								for="website"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Globe class="mr-1 inline h-4 w-4" />
								Website
							</label>
							<input
								id="website"
								name="website"
								type="url"
								bind:value={formData.website}
								oninput={handleChange}
								placeholder="https://company.com"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400 {errors.website
									? 'border-red-500 ring-1 ring-red-500 dark:border-red-400 dark:ring-red-400'
									: ''}"
							/>
							{#if errors.website}
								<p class="mt-1 text-sm text-red-500 dark:text-red-400">{errors.website}</p>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<!-- Business Information Section -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<h2
						class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
					>
						<DollarSign class="h-5 w-5 text-green-600 dark:text-green-400" />
						Business Information
					</h2>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
						<!-- Industry -->
						<div>
							<label
								for="industry"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Industry
							</label>
							<select
								id="industry"
								name="industry"
								bind:value={formData.industry}
								onchange={handleChange}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
							>
								<option value="">Select industry</option>
								{#each data.data.industries as [value, label] (value)}
									<option {value}>{label}</option>
								{/each}
							</select>
						</div>

						<!-- Number of Employees -->
						<div>
							<label
								for="number_of_employees"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Users class="mr-1 inline h-4 w-4" />
								Employees
							</label>
							<input
								id="number_of_employees"
								name="number_of_employees"
								type="number"
								min="0"
								bind:value={formData.number_of_employees}
								oninput={handleChange}
								placeholder="100"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400 {errors.number_of_employees
									? 'border-red-500 ring-1 ring-red-500 dark:border-red-400 dark:ring-red-400'
									: ''}"
							/>
							{#if errors.number_of_employees}
								<p class="mt-1 text-sm text-red-500 dark:text-red-400">
									{errors.number_of_employees}
								</p>
							{/if}
						</div>

						<!-- Annual Revenue -->
						<div>
							<label
								for="annual_revenue"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<DollarSign class="mr-1 inline h-4 w-4" />
								Annual Revenue
							</label>
							<input
								id="annual_revenue"
								name="annual_revenue"
								type="number"
								min="0"
								step="0.01"
								bind:value={formData.annual_revenue}
								oninput={handleChange}
								placeholder="1000000"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400 {errors.annual_revenue
									? 'border-red-500 ring-1 ring-red-500 dark:border-red-400 dark:ring-red-400'
									: ''}"
							/>
							{#if errors.annual_revenue}
								<p class="mt-1 text-sm text-red-500 dark:text-red-400">
									{errors.annual_revenue}
								</p>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<!-- Assignment Section -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<h2
						class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
					>
						<Users class="h-5 w-5 text-purple-600 dark:text-purple-400" />
						Assignment
					</h2>
				</div>
				<div class="p-6">
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
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
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
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
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
			</div>

			<!-- Address Section -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<h2
						class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
					>
						<MapPin class="h-5 w-5 text-orange-600 dark:text-orange-400" />
						Address
					</h2>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<!-- Street Address -->
						<div class="md:col-span-2">
							<label
								for="address_line"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Street Address
							</label>
							<input
								id="address_line"
								name="address_line"
								type="text"
								bind:value={formData.address_line}
								oninput={handleChange}
								placeholder="123 Business Ave"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							/>
						</div>

						<div>
							<label
								for="city"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>City</label
							>
							<input
								id="city"
								name="city"
								type="text"
								bind:value={formData.city}
								oninput={handleChange}
								placeholder="City"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							/>
						</div>

						<div>
							<label
								for="state"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>State</label
							>
							<input
								id="state"
								name="state"
								type="text"
								bind:value={formData.state}
								oninput={handleChange}
								placeholder="State"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							/>
						</div>

						<div>
							<label
								for="postcode"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Postal Code</label
							>
							<input
								id="postcode"
								name="postcode"
								type="text"
								bind:value={formData.postcode}
								oninput={handleChange}
								placeholder="12345"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
							/>
						</div>

						<div>
							<label
								for="country"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Country</label
							>
							<select
								id="country"
								name="country"
								bind:value={formData.country}
								onchange={handleChange}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-400"
							>
								<option value="">Select country</option>
								{#each data.data.countries as [value, label] (value)}
									<option {value}>{label}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>

			<!-- Notes Section -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<h2
						class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white"
					>
						<FileText class="h-5 w-5 text-gray-600 dark:text-gray-400" />
						Notes
					</h2>
				</div>
				<div class="p-6">
					<textarea
						id="description"
						name="description"
						bind:value={formData.description}
						oninput={handleChange}
						placeholder="Additional notes about this account..."
						rows="4"
						class="w-full resize-vertical rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
					></textarea>
				</div>
			</div>

			<!-- Submit Button -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="px-6 py-4">
					<div class="flex justify-end gap-4">
						<button
							type="button"
							onclick={() => goto('/app/accounts')}
							disabled={isSubmitting}
							class="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-6 py-2 text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-800"
						>
							<X class="h-4 w-4" />
							Cancel
						</button>
						<button
							type="submit"
							disabled={isSubmitting}
							class="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2 text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-800"
						>
							{#if isSubmitting}
								<div
									class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
								></div>
								Creating...
							{:else}
								<Save class="h-4 w-4" />
								Create Account
							{/if}
						</button>
					</div>
				</div>
			</div>
		</form>
	</div>
</div>
