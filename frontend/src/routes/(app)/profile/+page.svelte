<script>
	import { enhance } from '$app/forms';
	import { User, Mail, Phone, Building, Calendar, Settings, Edit, Save, X } from '@lucide/svelte';
	import { validatePhoneNumber, formatPhoneNumber } from '$lib/utils/phone.js';

	/** @type {{ data: import('./$types').PageData, form: import('./$types').ActionData }} */
	let { data, form } = $props();

	let isEditing = $state(false);
	let isSubmitting = $state(false);
	let phoneError = $state('');

	// Form data state
	let formData = $state({
		name: data.user.name || '',
		phone: data.user.phone || ''
	});

	// Reset form data when not editing or when data changes
	$effect(() => {
		if (!isEditing) {
			formData = {
				name: data.user.name || '',
				phone: data.user.phone || ''
			};
			phoneError = '';
		}
	});

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

	function toggleEdit() {
		isEditing = !isEditing;
		if (!isEditing) {
			// Reset form data when canceling edit
			formData = {
				name: data.user.name || '',
				phone: data.user.phone || ''
			};
			phoneError = '';
		}
	}

	/**
	 * @param {string | Date | null | undefined} date
	 */
	function formatDate(date) {
		if (!date) return 'Never';
		const dateObj = date instanceof Date ? date : new Date(date);
		return dateObj.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	/**
	 * @param {string | null | undefined} name
	 */
	function getInitials(name) {
		if (!name) return 'U';
		return name
			.split(' ')
			.map(/** @param {string} n */ (n) => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	// Handle form submission
	function handleSubmit() {
		isSubmitting = true;
		return async (
			/** @type {{ result: any, update: () => Promise<void> }} */ { result, update }
		) => {
			isSubmitting = false;
			if (result.type === 'success') {
				isEditing = false;
			}
			await update();
		};
	}
</script>

<svelte:head>
	<title>Profile - BottleCRM</title>
</svelte:head>

<div class="mx-auto max-w-4xl">
	<!-- Header -->
	<div class="mb-8">
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Profile</h1>
				<p class="mt-2 text-gray-600 dark:text-gray-400">
					Manage your personal information and account settings
				</p>
			</div>
			<button
				onclick={toggleEdit}
				class="inline-flex items-center gap-2 rounded-lg border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none dark:focus:ring-offset-gray-900"
				disabled={isSubmitting}
			>
				{#if isEditing}
					<X class="h-4 w-4" />
					Cancel
				{:else}
					<Edit class="h-4 w-4" />
					Edit Profile
				{/if}
			</button>
		</div>
	</div>

	<!-- Success/Error Messages -->
	{#if form?.success}
		<div
			class="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20"
		>
			<div class="flex items-center">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<div class="ml-3">
					<p class="text-sm font-medium text-green-800 dark:text-green-200">
						{form.message}
					</p>
				</div>
			</div>
		</div>
	{/if}

	{#if form?.error}
		<div
			class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20"
		>
			<div class="flex items-center">
				<div class="flex-shrink-0">
					<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
							clip-rule="evenodd"
						/>
					</svg>
				</div>
				<div class="ml-3">
					<p class="text-sm font-medium text-red-800 dark:text-red-200">
						{form.error}
					</p>
				</div>
			</div>
		</div>
	{/if}

	<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
		<!-- Profile Card -->
		<div class="lg:col-span-1">
			<div
				class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				<div class="text-center">
					<!-- Profile Photo -->
					<div class="relative inline-block">
						{#if data.user.profilePhoto}
							<img
								src={data.user.profilePhoto}
								alt={data.user.name || 'Profile'}
								class="h-24 w-24 rounded-full border-4 border-white object-cover shadow-lg dark:border-gray-800"
							/>
						{:else}
							<div
								class="flex h-24 w-24 items-center justify-center rounded-full border-4 border-white bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg dark:border-gray-800"
							>
								<span class="text-2xl font-bold text-white">
									{getInitials(data.user.name)}
								</span>
							</div>
						{/if}
					</div>

					<h2 class="mt-4 text-xl font-semibold text-gray-900 dark:text-white">
						{data.user.name || 'Unnamed User'}
					</h2>
					<p class="text-gray-600 dark:text-gray-400">{data.user.email}</p>
				</div>

				<!-- Status Badge -->
				<div class="mt-6 flex justify-center">
					<span
						class="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium {data.user
							.isActive
							? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
							: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'}"
					>
						{data.user.isActive ? 'Active' : 'Inactive'}
					</span>
				</div>
			</div>
		</div>

		<!-- Profile Information -->
		<div class="lg:col-span-2">
			<div
				class="rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
			>
				{#if isEditing}
					<!-- Edit Form -->
					<form method="POST" action="?/updateProfile" use:enhance={handleSubmit}>
						<div class="p-6">
							<h3 class="mb-6 text-lg font-semibold text-gray-900 dark:text-white">
								Edit Profile Information
							</h3>

							<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
								<!-- Name -->
								<div class="md:col-span-2">
									<label
										for="name"
										class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										Full Name *
									</label>
									<input
										type="text"
										id="name"
										name="name"
										bind:value={formData.name}
										required
										class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
										placeholder="Enter your full name"
									/>
								</div>

								<!-- Phone -->
								<div>
									<label
										for="phone"
										class="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300"
									>
										Phone Number
									</label>
									<input
										type="tel"
										id="phone"
										name="phone"
										bind:value={formData.phone}
										oninput={validatePhone}
										class="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white dark:placeholder-gray-400 dark:focus:border-blue-400 dark:focus:ring-blue-400"
										placeholder="Enter your phone number"
									/>
									{#if phoneError}
										<p class="mt-2 text-sm text-red-600 dark:text-red-400">
											{phoneError}
										</p>
									{/if}
								</div>
							</div>
						</div>

						<div
							class="rounded-b-lg border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-600 dark:bg-gray-700/50"
						>
							<div class="flex justify-end gap-3">
								<button
									type="button"
									onclick={toggleEdit}
									disabled={isSubmitting}
									class="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:opacity-50 dark:border-gray-500 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500 dark:focus:ring-offset-gray-800"
								>
									Cancel
								</button>
								<button
									type="submit"
									disabled={isSubmitting || !!phoneError}
									class="inline-flex items-center gap-2 rounded-lg border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:opacity-50 dark:focus:ring-offset-gray-800"
								>
									{#if isSubmitting}
										<svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
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
										Saving...
									{:else}
										<Save class="h-4 w-4" />
										Save Changes
									{/if}
								</button>
							</div>
						</div>
					</form>
				{:else}
					<!-- View Mode -->
					<div class="p-6">
						<h3 class="mb-6 text-lg font-semibold text-gray-900 dark:text-white">
							Profile Information
						</h3>

						<dl class="grid grid-cols-1 gap-6 md:grid-cols-2">
							<!-- Email -->
							<div>
								<dt
									class="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400"
								>
									<Mail class="h-4 w-4" />
									Email Address
								</dt>
								<dd class="mt-1 text-sm text-gray-900 dark:text-white">{data.user.email}</dd>
							</div>

							<!-- Phone -->
							<div>
								<dt
									class="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400"
								>
									<Phone class="h-4 w-4" />
									Phone Number
								</dt>
								<dd class="mt-1 text-sm text-gray-900 dark:text-white">
									{data.user.phone ? formatPhoneNumber(data.user.phone) : 'Not provided'}
								</dd>
							</div>

							<!-- Last Login -->
							<div>
								<dt
									class="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400"
								>
									<Calendar class="h-4 w-4" />
									Last Login
								</dt>
								<dd class="mt-1 text-sm text-gray-900 dark:text-white">
									{formatDate(data.user.lastLogin)}
								</dd>
							</div>

							<!-- Member Since -->
							<div>
								<dt
									class="flex items-center gap-2 text-sm font-medium text-gray-500 dark:text-gray-400"
								>
									<Calendar class="h-4 w-4" />
									Member Since
								</dt>
								<dd class="mt-1 text-sm text-gray-900 dark:text-white">
									{formatDate(data.user.createdAt)}
								</dd>
							</div>
						</dl>
					</div>
				{/if}
			</div>

			<!-- Organizations -->
			{#if data.user.organizations && data.user.organizations.length > 0}
				<div
					class="mt-8 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<h3 class="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Organizations</h3>
					<div class="space-y-4">
						{#each data.user.organizations as userOrg}
							<div
								class="flex items-center justify-between rounded-lg bg-gray-50 p-4 dark:bg-gray-700/50"
							>
								<div class="flex items-center gap-3">
									<div
										class="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600"
									>
										<Building class="h-5 w-5 text-white" />
									</div>
									<div>
										<h4 class="font-medium text-gray-900 dark:text-white">
											{userOrg.organization.name}
										</h4>
										<p class="text-sm text-gray-500 dark:text-gray-400">
											Joined {formatDate(userOrg.joinedAt)}
										</p>
									</div>
								</div>
								<span
									class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium {userOrg.role ===
									'ADMIN'
										? 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400'
										: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400'}"
								>
									{userOrg.role}
								</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
