<script lang="ts">
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import { fly } from 'svelte/transition';
	import {
		ArrowLeft,
		Save,
		X,
		User,
		Building,
		Mail,
		Phone,
		Calendar,
		Star,
		Target,
		AlertCircle
	} from '@lucide/svelte';

	export let data;

	let { lead, users } = data;
	let isSubmitting = false;
	let formSubmitted = false;
	let errorMessage = '';

	// Form validation
	let errors: Record<string, string> = {};

	function validateForm(formData: FormData) {
		errors = {};

		if (!formData.get('firstName')?.toString()?.trim()) {
			errors.firstName = 'First name is required';
		}

		if (!formData.get('lastName')?.toString()?.trim()) {
			errors.lastName = 'Last name is required';
		}

		const email = formData.get('email')?.toString()?.trim();
		if (email && !isValidEmail(email)) {
			errors.email = 'Please enter a valid email address';
		}

		return Object.keys(errors).length === 0;
	}

	function isValidEmail(email: string) {
		return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	}

	// Lead status options - must match Django LEAD_STATUS choices
	const statusOptions = [
		{ value: 'assigned', name: 'Assigned', color: 'bg-blue-100 text-blue-800' },
		{ value: 'in process', name: 'In Process', color: 'bg-yellow-100 text-yellow-800' },
		{ value: 'converted', name: 'Converted', color: 'bg-green-100 text-green-800' },
		{ value: 'recycled', name: 'Recycled', color: 'bg-purple-100 text-purple-800' },
		{ value: 'closed', name: 'Closed', color: 'bg-gray-100 text-gray-800' }
	];

	// Lead source options - must match Django LEAD_SOURCE choices
	const sourceOptions = [
		{ value: 'call', name: 'Call' },
		{ value: 'email', name: 'Email' },
		{ value: 'existing customer', name: 'Existing Customer' },
		{ value: 'partner', name: 'Partner' },
		{ value: 'public relations', name: 'Public Relations' },
		{ value: 'compaign', name: 'Campaign' },
		{ value: 'other', name: 'Other' }
	];

	// Rating options
	const ratingOptions = [
		{ value: 'Hot', name: 'Hot 🔥', color: 'text-red-600' },
		{ value: 'Warm', name: 'Warm 🌡️', color: 'text-orange-600' },
		{ value: 'Cold', name: 'Cold ❄️', color: 'text-blue-600' }
	];

	// Industry options (expanded)
	const industryOptions = [
		{ value: 'Technology', name: 'Technology' },
		{ value: 'Finance', name: 'Finance' },
		{ value: 'Healthcare', name: 'Healthcare' },
		{ value: 'Education', name: 'Education' },
		{ value: 'Manufacturing', name: 'Manufacturing' },
		{ value: 'Retail', name: 'Retail' },
		{ value: 'Real Estate', name: 'Real Estate' },
		{ value: 'Consulting', name: 'Consulting' },
		{ value: 'Marketing', name: 'Marketing' },
		{ value: 'Legal', name: 'Legal' },
		{ value: 'Construction', name: 'Construction' },
		{ value: 'Transportation', name: 'Transportation' },
		{ value: 'Hospitality', name: 'Hospitality' },
		{ value: 'Entertainment', name: 'Entertainment' },
		{ value: 'Other', name: 'Other' }
	];

	// Cancel edit and go back to lead view
	function cancelEdit() {
		goto(`/leads/${lead.id}`);
	}
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<header
		class="sticky top-0 z-20 border-b border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
	>
		<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
			<div class="flex h-16 items-center justify-between">
				<div class="flex items-center space-x-4">
					<button
						onclick={() => goto(`/leads/${lead.id}`)}
						class="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 transition-colors hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
					>
						<ArrowLeft class="h-5 w-5 text-gray-600 dark:text-gray-300" />
					</button>
					<div>
						<h1 class="text-2xl font-bold text-gray-900 dark:text-white">Edit Lead</h1>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							Editing {lead.firstName}
							{lead.lastName}
						</p>
					</div>
				</div>
			</div>
		</div>
	</header>

	<main class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
		<!-- Success/Error Messages -->
		{#if formSubmitted && !errorMessage}
			<div
				in:fly={{ y: -20 }}
				class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/50"
			>
				<div class="flex items-center">
					<div class="flex-shrink-0">
						<svg
							class="h-5 w-5 text-green-400 dark:text-green-300"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
								clip-rule="evenodd"
							/>
						</svg>
					</div>
					<div class="ml-3">
						<p class="text-sm font-medium text-green-800 dark:text-green-200">
							Lead updated successfully!
						</p>
					</div>
				</div>
			</div>
		{/if}

		{#if errorMessage}
			<div
				in:fly={{ y: -20 }}
				class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/50"
			>
				<div class="flex items-center">
					<AlertCircle class="h-5 w-5 flex-shrink-0 text-red-400 dark:text-red-300" />
					<div class="ml-3">
						<p class="text-sm font-medium text-red-800 dark:text-red-200">{errorMessage}</p>
					</div>
				</div>
			</div>
		{/if}

		<!-- Form -->
		<form
			method="POST"
			use:enhance={({ formData }) => {
				const isValid = validateForm(formData);
				if (!isValid) return;

				isSubmitting = true;
				return async ({ result, update }) => {
					isSubmitting = false;
					formSubmitted = true;

					if (result.type === 'success') {
						if (result.data?.success) {
							await update();
							setTimeout(() => {
								goto(`/leads/${lead.id}`);
							}, 1500);
						} else if (result.data?.error) {
							errorMessage = result.data.error as string;
						}
					} else {
						errorMessage = 'An unexpected error occurred';
					}
				};
			}}
			class="space-y-8"
		>
			<!-- Personal Information Section -->
			<div
				class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div
					class="border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-700/50"
				>
					<div class="flex items-center space-x-2">
						<User class="h-5 w-5 text-gray-600 dark:text-gray-300" />
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">
							Personal Information
						</h2>
					</div>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								for="firstName"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								First Name <span class="text-red-500 dark:text-red-400">*</span>
							</label>
							<input
								id="firstName"
								name="firstName"
								type="text"
								required
								value={lead.firstName}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400 {errors.firstName
									? 'border-red-500 ring-2 ring-red-200 dark:border-red-400 dark:ring-red-800'
									: ''}"
								placeholder="Enter first name"
							/>
							{#if errors.firstName}
								<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.firstName}</p>
							{/if}
						</div>

						<div>
							<label
								for="lastName"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								Last Name <span class="text-red-500 dark:text-red-400">*</span>
							</label>
							<input
								id="lastName"
								name="lastName"
								type="text"
								required
								value={lead.lastName}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400 {errors.lastName
									? 'border-red-500 ring-2 ring-red-200 dark:border-red-400 dark:ring-red-800'
									: ''}"
								placeholder="Enter last name"
							/>
							{#if errors.lastName}
								<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.lastName}</p>
							{/if}
						</div>

						<div>
							<label
								for="email"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Mail class="mr-1 inline h-4 w-4" />
								Email Address
							</label>
							<input
								id="email"
								name="email"
								type="email"
								value={lead.email || ''}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400 {errors.email
									? 'border-red-500 ring-2 ring-red-200 dark:border-red-400 dark:ring-red-800'
									: ''}"
								placeholder="email@example.com"
							/>
							{#if errors.email}
								<p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email}</p>
							{/if}
						</div>

						<div>
							<label
								for="phone"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Phone class="mr-1 inline h-4 w-4" />
								Phone Number
							</label>
							<input
								id="phone"
								name="phone"
								type="tel"
								value={lead.phone || ''}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								placeholder="+1 (555) 123-4567"
							/>
						</div>
					</div>
				</div>
			</div>

			<!-- Company Information Section -->
			<div
				class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div
					class="border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-700/50"
				>
					<div class="flex items-center space-x-2">
						<Building class="h-5 w-5 text-gray-600 dark:text-gray-300" />
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Company Information</h2>
					</div>
				</div>
				<div class="p-6">
					<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
						<div>
							<label
								for="company"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Company Name</label
							>
							<input
								id="company"
								name="company"
								type="text"
								value={lead.company || ''}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								placeholder="Enter company name"
							/>
						</div>

						<div>
							<label
								for="title"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Job Title</label
							>
							<input
								id="title"
								name="title"
								type="text"
								value={lead.title || ''}
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
								placeholder="Enter job title"
							/>
						</div>

						<div class="md:col-span-2">
							<label
								for="industry"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Industry</label
							>
							<select
								id="industry"
								name="industry"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-400"
							>
								<option value="">Select Industry</option>
								{#each industryOptions as option}
									<option value={option.value} selected={lead.industry === option.value}
										>{option.name}</option
									>
								{/each}
							</select>
						</div>
					</div>
				</div>
			</div>

			<!-- Lead Details Section -->
			<div
				class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div
					class="border-b border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-700/50"
				>
					<div class="flex items-center space-x-2">
						<Target class="h-5 w-5 text-gray-600 dark:text-gray-300" />
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white">Lead Details</h2>
					</div>
				</div>
				<div class="p-6">
					<div class="mb-6 grid grid-cols-1 gap-6 md:grid-cols-3">
						<div>
							<label
								for="status"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Status</label
							>
							<select
								id="status"
								name="status"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-400"
							>
								{#each statusOptions as option}
									<option value={option.value} selected={lead.status === option.value}
										>{option.name}</option
									>
								{/each}
							</select>
						</div>

						<div>
							<label
								for="leadSource"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Lead Source</label
							>
							<select
								id="leadSource"
								name="leadSource"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-400"
							>
								<option value="">Select Source</option>
								{#each sourceOptions as option}
									<option value={option.value} selected={lead.leadSource === option.value}
										>{option.name}</option
									>
								{/each}
							</select>
						</div>

						<div>
							<label
								for="rating"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>
								<Star class="mr-1 inline h-4 w-4" />
								Rating
							</label>
							<select
								id="rating"
								name="rating"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-400"
							>
								<option value="">Select Rating</option>
								{#each ratingOptions as option}
									<option value={option.value} selected={lead.rating === option.value}
										>{option.name}</option
									>
								{/each}
							</select>
						</div>
					</div>

					<div class="mb-6">
						<div>
							<label
								for="ownerId"
								class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
								>Lead Owner</label
							>
							<select
								id="ownerId"
								name="ownerId"
								class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:focus:ring-blue-400"
							>
								{#each users as userOrg}
									<option value={userOrg.user.id} selected={lead.ownerId === userOrg.user.id}
										>{userOrg.user.name}</option
									>
								{/each}
							</select>
						</div>
					</div>

					<div>
						<label
							for="description"
							class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
							>Description / Notes</label
						>
						<textarea
							id="description"
							name="description"
							rows="4"
							value={lead.description || ''}
							class="resize-vertical w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:ring-blue-400"
							placeholder="Add notes, requirements, or any additional information about this lead..."
						></textarea>
					</div>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="flex justify-end space-x-4 border-t border-gray-200 pt-6 dark:border-gray-700">
				<button
					type="button"
					onclick={cancelEdit}
					class="inline-flex items-center rounded-lg border border-gray-300 bg-white px-6 py-3 text-sm font-medium text-gray-700 transition-all hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-800"
				>
					<X class="mr-2 h-4 w-4" />
					Cancel
				</button>
				<button
					type="submit"
					disabled={isSubmitting}
					class="inline-flex items-center rounded-lg border border-transparent bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-all hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-500 dark:hover:bg-blue-600 dark:focus:ring-blue-400 dark:focus:ring-offset-gray-800"
				>
					{#if isSubmitting}
						<svg class="mr-2 -ml-1 h-4 w-4 animate-spin text-white" fill="none" viewBox="0 0 24 24">
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
					{:else}
						<Save class="mr-2 h-4 w-4" />
					{/if}
					Save Changes
				</button>
			</div>
		</form>
	</main>
</div>
