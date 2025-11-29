<script>
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { invalidateAll } from '$app/navigation';
	import {
		User,
		Mail,
		Phone,
		Building,
		MapPin,
		FileText,
		Star,
		Save,
		X,
		ArrowLeft
	} from '@lucide/svelte';
	import { validatePhoneNumber } from '$lib/utils/phone.js';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	const { contact } = data;
	let account = data.account;
	let isPrimary = data.isPrimary;
	let role = data.role;

	let firstName = $state(contact?.firstName || '');
	let lastName = $state(contact?.lastName || '');
	let email = $state(contact?.email || '');
	let phone = $state(contact?.phone || '');
	let title = $state(contact?.title || '');
	let department = $state(contact?.department || '');
	let street = $state(contact?.street || '');
	let city = $state(contact?.city || '');
	let stateField = $state(contact?.state || ''); // Renamed to avoid conflict with Svelte's $state
	let postalCode = $state(contact?.postalCode || '');
	let country = $state(contact?.country || '');
	let description = $state(contact?.description || '');
	let submitting = $state(false);
	let errorMsg = $state('');
	let phoneError = $state('');

	// Validate phone number on input
	function validatePhone() {
		if (!phone.trim()) {
			phoneError = '';
			return;
		}

		const validation = validatePhoneNumber(phone);
		if (!validation.isValid) {
			phoneError = validation.error || 'Invalid phone number';
		} else {
			phoneError = '';
		}
	}

	/** @param {Event} e */
	async function handleSubmit(e) {
		e.preventDefault();
		submitting = true;
		errorMsg = '';
		const formData = new FormData();
		formData.append('firstName', firstName);
		formData.append('lastName', lastName);
		formData.append('email', email);
		formData.append('phone', phone);
		formData.append('title', title);
		formData.append('department', department);
		formData.append('street', street);
		formData.append('city', city);
		formData.append('state', stateField);
		formData.append('postalCode', postalCode);
		formData.append('country', country);
		formData.append('description', description);
		// Remove isPrimary and role from form submission

		const res = await fetch('', {
			method: 'POST',
			body: formData
		});
		if (res.ok) {
			await invalidateAll();
			goto(`/contacts/${contact?.id}`);
		} else {
			const data = await res.json();
			errorMsg = data?.message || 'Failed to update contact.';
		}
		submitting = false;
	}
</script>

<div class="min-h-screen bg-gray-50 py-6 dark:bg-gray-900">
	<div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
		<!-- Header -->
		<div class="mb-8">
			<div class="mb-4 flex items-center gap-4">
				<button
					onclick={() => goto(`/contacts/${contact?.id}`)}
					class="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-200"
				>
					<ArrowLeft class="h-5 w-5" />
				</button>
				<div>
					<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Contact</h1>
					<p class="mt-1 text-gray-600 dark:text-gray-400">
						Update contact information and details
					</p>
				</div>
			</div>
		</div>

		<!-- Form -->
		<form onsubmit={handleSubmit} class="space-y-8">
			<!-- Basic Information Card -->
			<div
				class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center gap-3">
						<div class="rounded-lg bg-blue-50 p-2 dark:bg-blue-900/20">
							<User class="h-5 w-5 text-blue-600 dark:text-blue-400" />
						</div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h2>
					</div>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="firstName"
							>
								First Name *
							</label>
							<input
								id="firstName"
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								bind:value={firstName}
								required
								placeholder="Enter first name"
							/>
						</div>
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="lastName"
							>
								Last Name *
							</label>
							<input
								id="lastName"
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								bind:value={lastName}
								required
								placeholder="Enter last name"
							/>
						</div>
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="title"
							>
								Job Title
							</label>
							<input
								id="title"
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								bind:value={title}
								placeholder="e.g. Marketing Director"
							/>
						</div>
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="department"
							>
								Department
							</label>
							<input
								id="department"
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								bind:value={department}
								placeholder="e.g. Marketing"
							/>
						</div>
					</div>
				</div>
			</div>

			<!-- Contact Information Card -->
			<div
				class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center gap-3">
						<div class="rounded-lg bg-green-50 p-2 dark:bg-green-900/20">
							<Mail class="h-5 w-5 text-green-600 dark:text-green-400" />
						</div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Contact Information</h2>
					</div>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="email"
							>
								Email Address
							</label>
							<div class="relative">
								<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
									<Mail class="h-5 w-5 text-gray-400" />
								</div>
								<input
									id="email"
									type="email"
									class="w-full rounded-lg border border-gray-300 bg-white py-3 pr-4 pl-10 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
									bind:value={email}
									placeholder="contact@company.com"
								/>
							</div>
						</div>
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="phone"
							>
								Phone Number
							</label>
							<div class="relative">
								<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
									<Phone class="h-5 w-5 text-gray-400" />
								</div>
								<input
									id="phone"
									type="tel"
									class="w-full rounded-lg border border-gray-300 bg-white py-3 pr-4 pl-10 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
									bind:value={phone}
									placeholder="+1 (555) 123-4567"
									oninput={validatePhone}
								/>
							</div>
							{#if phoneError}
								<p class="mt-2 text-sm text-red-600 dark:text-red-400">{phoneError}</p>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<!-- Address Information Card -->
			<div
				class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center gap-3">
						<div class="rounded-lg bg-purple-50 p-2 dark:bg-purple-900/20">
							<MapPin class="h-5 w-5 text-purple-600 dark:text-purple-400" />
						</div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Address Information</h2>
					</div>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6">
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="street"
							>
								Street Address
							</label>
							<input
								id="street"
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								bind:value={street}
								placeholder="123 Main Street"
							/>
						</div>
						<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
							<div>
								<label
									class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
									for="city"
								>
									City
								</label>
								<input
									id="city"
									class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
									bind:value={city}
									placeholder="San Francisco"
								/>
							</div>
							<div>
								<label
									class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
									for="state"
								>
									State/Province
								</label>
								<input
									id="state"
									class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
									bind:value={stateField}
									placeholder="CA"
								/>
							</div>
							<div>
								<label
									class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
									for="postalCode"
								>
									Postal Code
								</label>
								<input
									id="postalCode"
									class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
									bind:value={postalCode}
									placeholder="94102"
								/>
							</div>
						</div>
						<div>
							<label
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								for="country"
							>
								Country
							</label>
							<input
								id="country"
								class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								bind:value={country}
								placeholder="United States"
							/>
						</div>
					</div>
				</div>
			</div>

			<!-- Account Relationship Card -->
			{#if account}
				<div
					class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
						<div class="flex items-center gap-3">
							<div class="rounded-lg bg-orange-50 p-2 dark:bg-orange-900/20">
								<Building class="h-5 w-5 text-orange-600 dark:text-orange-400" />
							</div>
							<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
								Account Relationship
							</h2>
						</div>
					</div>
					<div class="p-6">
						<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
							<div>
								<div class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Account</div>
								<div class="font-medium text-gray-900 dark:text-white">{account.name}</div>
							</div>
							{#if role}
								<div>
									<div class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Role</div>
									<div class="text-gray-900 dark:text-white">{role}</div>
								</div>
							{/if}
							{#if isPrimary}
								<div class="md:col-span-2">
									<div class="flex items-center gap-2 text-sm">
										<Star class="h-4 w-4 text-yellow-500" />
										<span class="font-medium text-gray-700 dark:text-gray-300">Primary Contact</span
										>
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>
			{/if}

			<!-- Additional Information Card -->
			<div
				class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="border-b border-gray-200 px-6 py-4 dark:border-gray-700">
					<div class="flex items-center gap-3">
						<div class="rounded-lg bg-indigo-50 p-2 dark:bg-indigo-900/20">
							<FileText class="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
						</div>
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
							Additional Information
						</h2>
					</div>
				</div>
				<div class="p-6">
					<div>
						<label
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							for="description"
						>
							Notes & Description
						</label>
						<textarea
							id="description"
							class="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder-gray-500 focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
							rows="4"
							bind:value={description}
							placeholder="Add any additional notes or important information about this contact..."
						></textarea>
					</div>
				</div>
			</div>

			<!-- Error Message -->
			{#if errorMsg}
				<div
					class="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
				>
					<div class="flex">
						<div class="flex-shrink-0">
							<X class="h-5 w-5 text-red-400" />
						</div>
						<div class="ml-3">
							<p class="text-sm text-red-800 dark:text-red-200">{errorMsg}</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- Action Buttons -->
			<div class="flex justify-end gap-3 border-t border-gray-200 pt-6 dark:border-gray-700">
				<button
					type="button"
					onclick={() => goto(`/contacts/${contact?.id}`)}
					class="rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-gray-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:focus:ring-gray-400"
				>
					Cancel
				</button>
				<button
					type="submit"
					disabled={submitting}
					class="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 disabled:bg-blue-400 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-400 dark:disabled:bg-blue-500"
				>
					{#if submitting}
						<div
							class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
						></div>
						Saving...
					{:else}
						<Save class="h-4 w-4" />
						Save Changes
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
