<script>
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import {
		ArrowLeft,
		User,
		Mail,
		Phone,
		Building,
		MapPin,
		FileText,
		Save,
		Users,
		Linkedin,
		PhoneOff
	} from '@lucide/svelte';
	import { validatePhoneNumber } from '$lib/utils/phone.js';

	/** @type {{ data: import('./$types').PageData, form: import('./$types').ActionData }} */
	let { data, form } = $props();

	let isSubmitting = $state(false);
	let phoneError = $state('');

	// Form data with all fields
	let formData = $state({
		// Core Contact Information
		first_name: '',
		last_name: '',
		email: '',
		phone: '',
		// Professional Information
		organization: '',
		title: '',
		department: '',
		// Communication Preferences
		do_not_call: false,
		linked_in_url: '',
		// Address
		address_line: '',
		city: '',
		state: '',
		postcode: '',
		country: '',
		// Assignment
		assigned_to: [],
		teams: [],
		// Notes
		description: ''
	});

	// Handle form submission result
	$effect(() => {
		if (form?.status === 'success') {
			goto('/contacts');
		}
	});

	function handleSubmit() {
		isSubmitting = true;
		return async ({ update }) => {
			await update();
			isSubmitting = false;
		};
	}

	// Validate phone number on input
	function validatePhone() {
		if (!formData.phone.trim()) {
			phoneError = '';
			return;
		}

		const validation = validatePhoneNumber(formData.phone);
		if (!validation.isValid) {
			phoneError = validation.error || 'Invalid phone number';
		} else {
			phoneError = '';
		}
	}

	function resetForm() {
		formData = {
			first_name: '',
			last_name: '',
			email: '',
			phone: '',
			organization: '',
			title: '',
			department: '',
			do_not_call: false,
			linked_in_url: '',
			address_line: '',
			city: '',
			state: '',
			postcode: '',
			country: '',
			assigned_to: [],
			teams: [],
			description: ''
		};
	}
</script>

<svelte:head>
	<title>New Contact - CRM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
		<div class="mx-auto max-w-5xl px-4 py-4 sm:px-6 lg:px-8">
			<div class="flex items-center justify-between">
				<div class="flex items-center space-x-4">
					<a
						href="/contacts"
						class="inline-flex items-center text-gray-500 transition-colors hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
					>
						<ArrowLeft class="mr-2 h-5 w-5" />
						Back to Contacts
					</a>
					<div class="border-l border-gray-300 pl-4 dark:border-gray-600">
						<h1 class="text-2xl font-semibold text-gray-900 dark:text-white">New Contact</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">Add a new contact to your CRM</p>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Error Alert -->
		{#if form?.error}
			<div
				class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
			>
				<p class="text-red-800 dark:text-red-200">{form.error}</p>
			</div>
		{/if}

		<!-- Success Alert -->
		{#if form?.status === 'success'}
			<div
				class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20"
			>
				<p class="text-green-800 dark:text-green-200">{form.message}</p>
			</div>
		{/if}

		<form method="POST" use:enhance={handleSubmit} class="space-y-8">
			<!-- Section 1: Contact Information -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center">
						<User class="mr-2 h-5 w-5 text-blue-500" />
						<h2 class="text-lg font-medium text-gray-900 dark:text-white">Contact Information</h2>
					</div>
				</div>
				<div class="space-y-6 p-6">
					<!-- Name Fields -->
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								for="first_name"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								First Name *
							</label>
							<input
								type="text"
								id="first_name"
								name="first_name"
								bind:value={formData.first_name}
								required
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="Enter first name"
							/>
						</div>
						<div>
							<label
								for="last_name"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Last Name *
							</label>
							<input
								type="text"
								id="last_name"
								name="last_name"
								bind:value={formData.last_name}
								required
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="Enter last name"
							/>
						</div>
					</div>

					<!-- Contact Fields -->
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								for="email"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Mail class="mr-1 inline h-4 w-4" />
								Email
							</label>
							<input
								type="email"
								id="email"
								name="email"
								bind:value={formData.email}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="contact@example.com"
							/>
						</div>
						<div>
							<label
								for="phone"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Phone class="mr-1 inline h-4 w-4" />
								Phone
							</label>
							<input
								type="tel"
								id="phone"
								name="phone"
								bind:value={formData.phone}
								oninput={validatePhone}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="+1 (555) 123-4567"
							/>
							{#if phoneError}
								<p class="mt-1 text-sm text-red-600 dark:text-red-400">{phoneError}</p>
							{/if}
						</div>
					</div>

					<!-- LinkedIn -->
					<div>
						<label
							for="linked_in_url"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							<Linkedin class="mr-1 inline h-4 w-4" />
							LinkedIn URL
						</label>
						<input
							type="url"
							id="linked_in_url"
							name="linked_in_url"
							bind:value={formData.linked_in_url}
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							placeholder="https://linkedin.com/in/username"
						/>
					</div>
				</div>
			</div>

			<!-- Section 2: Professional Information -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center">
						<Building class="mr-2 h-5 w-5 text-green-500" />
						<h2 class="text-lg font-medium text-gray-900 dark:text-white">
							Professional Information
						</h2>
					</div>
				</div>
				<div class="space-y-6 p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
						<div>
							<label
								for="organization"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Company
							</label>
							<input
								type="text"
								id="organization"
								name="organization"
								bind:value={formData.organization}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="Company name"
							/>
						</div>
						<div>
							<label
								for="title"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Job Title
							</label>
							<input
								type="text"
								id="title"
								name="title"
								bind:value={formData.title}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="e.g., Sales Manager"
							/>
						</div>
						<div>
							<label
								for="department"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Department
							</label>
							<input
								type="text"
								id="department"
								name="department"
								bind:value={formData.department}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="e.g., Sales"
							/>
						</div>
					</div>

					<!-- Do Not Call -->
					<div class="flex items-center">
						<input
							type="checkbox"
							id="do_not_call"
							name="do_not_call"
							bind:checked={formData.do_not_call}
							class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
						/>
						<label
							for="do_not_call"
							class="ml-2 flex items-center text-sm text-gray-700 dark:text-gray-300"
						>
							<PhoneOff class="mr-1 h-4 w-4 text-red-500" />
							Do Not Call
						</label>
					</div>
				</div>
			</div>

			<!-- Section 3: Assignment -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center">
						<Users class="mr-2 h-5 w-5 text-purple-500" />
						<h2 class="text-lg font-medium text-gray-900 dark:text-white">Assignment</h2>
					</div>
				</div>
				<div class="space-y-6 p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								for="assigned_to"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Assigned To
							</label>
							<select
								id="assigned_to"
								name="assigned_to"
								multiple
								bind:value={formData.assigned_to}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								size="4"
							>
								{#each data.data?.users || [] as user}
									<option value={user.id}>{user.name} ({user.email})</option>
								{/each}
							</select>
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Hold Ctrl/Cmd to select multiple
							</p>
						</div>
						<div>
							<label
								for="teams"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Teams
							</label>
							<select
								id="teams"
								name="teams"
								multiple
								bind:value={formData.teams}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								size="4"
							>
								{#each data.data?.teams || [] as team}
									<option value={team.id}>{team.name}</option>
								{/each}
							</select>
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Hold Ctrl/Cmd to select multiple
							</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Section 4: Address -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center">
						<MapPin class="mr-2 h-5 w-5 text-orange-500" />
						<h2 class="text-lg font-medium text-gray-900 dark:text-white">Address</h2>
					</div>
				</div>
				<div class="space-y-6 p-6">
					<div>
						<label
							for="address_line"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
						>
							Street Address
						</label>
						<input
							type="text"
							id="address_line"
							name="address_line"
							bind:value={formData.address_line}
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							placeholder="123 Main Street"
						/>
					</div>
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
						<div>
							<label
								for="city"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								City
							</label>
							<input
								type="text"
								id="city"
								name="city"
								bind:value={formData.city}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="New York"
							/>
						</div>
						<div>
							<label
								for="state"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								State/Province
							</label>
							<input
								type="text"
								id="state"
								name="state"
								bind:value={formData.state}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="NY"
							/>
						</div>
						<div>
							<label
								for="postcode"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Postal Code
							</label>
							<input
								type="text"
								id="postcode"
								name="postcode"
								bind:value={formData.postcode}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
								placeholder="10001"
							/>
						</div>
						<div>
							<label
								for="country"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Country
							</label>
							<select
								id="country"
								name="country"
								bind:value={formData.country}
								class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							>
								<option value="">Select country</option>
								{#each data.data?.countries || [] as country}
									<option value={country[0]}>{country[1]}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>

			<!-- Section 5: Notes -->
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center">
						<FileText class="mr-2 h-5 w-5 text-gray-500" />
						<h2 class="text-lg font-medium text-gray-900 dark:text-white">Notes</h2>
					</div>
				</div>
				<div class="p-6">
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
							class="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
							placeholder="Add any additional notes about this contact..."
						></textarea>
					</div>
				</div>
			</div>

			<!-- Form Actions -->
			<div
				class="flex items-center justify-end space-x-4 border-t border-gray-200 pt-6 dark:border-gray-700"
			>
				<a
					href="/contacts"
					class="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
				>
					Cancel
				</a>
				<button
					type="submit"
					disabled={isSubmitting}
					class="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
				>
					{#if isSubmitting}
						<div
							class="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
						></div>
						Creating...
					{:else}
						<Save class="mr-2 h-4 w-4" />
						Create Contact
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
