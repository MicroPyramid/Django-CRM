<script>
	import { fly } from 'svelte/transition';
	import { enhance } from '$app/forms';
	import { invalidateAll, goto } from '$app/navigation';
	import {
		UserCircle,
		Edit3,
		CheckCircle,
		Mail,
		Phone,
		Building,
		MapPin,
		Star,
		MessageSquare,
		ChevronRight,
		Calendar,
		TrendingUp,
		DollarSign,
		Briefcase,
		Globe,
		User,
		Clock,
		Target,
		Users,
		Plus,
		X,
		Loader2,
		ExternalLink,
		MapPin as Location,
		Award,
		Activity,
		Send,
		Copy,
		MoreVertical
	} from '@lucide/svelte';

	export let data;
	export let form;
	const { lead } = data;

	let newComment = '';
	let isSubmittingComment = false;
	let isConverting = false;

	// Toast state variables
	let showToast = false;
	let toastMessage = '';
	let toastType = 'success';

	// Confirmation modal state
	let showConfirmModal = false;

	// Function to get the full name of a lead
	/**
	 * @param {any} lead
	 */
	function getFullName(lead) {
		return `${lead.firstName} ${lead.lastName}`.trim();
	}

	// Function to format date
	/**
	 * @param {string | Date | null | undefined} dateString
	 */
	function formatDate(dateString) {
		if (!dateString) return 'N/A';
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	// Function to format date (short)
	/**
	 * @param {string | Date | null | undefined} dateString
	 */
	function formatDateShort(dateString) {
		if (!dateString) return 'N/A';
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// Function to map lead status to colors
	/**
	 * @param {string} status
	 */
	function getStatusColor(status) {
		switch (status) {
			case 'NEW':
				return 'bg-blue-50 text-blue-700 border-blue-200 ring-blue-600/20';
			case 'PENDING':
				return 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-600/20';
			case 'CONTACTED':
				return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20';
			case 'QUALIFIED':
				return 'bg-purple-50 text-purple-700 border-purple-200 ring-purple-600/20';
			case 'UNQUALIFIED':
				return 'bg-red-50 text-red-700 border-red-200 ring-red-600/20';
			case 'CONVERTED':
				return 'bg-gray-50 text-gray-700 border-gray-200 ring-gray-600/20';
			default:
				return 'bg-gray-50 text-gray-700 border-gray-200 ring-gray-600/20';
		}
	}

	// Function to get lead source display name
	/**
	 * @param {string | null | undefined} source
	 */
	function getLeadSourceDisplay(source) {
		if (!source) return 'Unknown';
		return source
			.replace('_', ' ')
			.toLowerCase()
			.replace(/\b\w/g, (/** @type {string} */ l) => l.toUpperCase());
	}

	// Function to get initials for avatar
	/**
	 * @param {any} lead
	 */
	function getInitials(lead) {
		const first = lead.firstName?.[0] || '';
		const last = lead.lastName?.[0] || '';
		return (first + last).toUpperCase();
	}

	// Function to copy email to clipboard
	async function copyEmail() {
		if (lead.email) {
			await navigator.clipboard.writeText(lead.email);
			toastMessage = 'Email copied to clipboard';
			toastType = 'success';
			showToast = true;
		}
	}

	// Function to copy phone to clipboard
	async function copyPhone() {
		if (lead.phone) {
			await navigator.clipboard.writeText(lead.phone);
			toastMessage = 'Phone number copied to clipboard';
			toastType = 'success';
			showToast = true;
		}
	}

	// Function to show confirmation modal
	function showConvertConfirmation() {
		showConfirmModal = true;
	}

	// Function to hide confirmation modal
	function hideConvertConfirmation() {
		showConfirmModal = false;
	}

	// Function to handle confirmed conversion
	function confirmConversion() {
		showConfirmModal = false;
		// Submit the form programmatically
		const form = document.getElementById('convertForm');
		if (form) {
			// Use dispatchEvent as a cross-browser solution
			const event = new Event('submit', { cancelable: true, bubbles: true });
			form.dispatchEvent(event);
		}
	}

	const enhanceConvertForm = () => {
		isConverting = true;
		return async (/** @type {{ update: any }} */ { update }) => {
			await update({ reset: false });
			// Note: If conversion is successful, the server will redirect automatically
			// This will only execute if there's an error
			isConverting = false;
		};
	};

	const enhanceCommentForm = () => {
		isSubmittingComment = true;
		return async (/** @type {{ update: any }} */ { update }) => {
			await update({ reset: false });
			// Reset the loading state after update
			isSubmittingComment = false;
		};
	};

	function closeToast() {
		showToast = false;
	}

	$: if (form?.status === 'success') {
		toastMessage = form.message || 'Action completed successfully!';
		toastType = 'success';
		showToast = true;
		invalidateAll();
		isConverting = false;
		isSubmittingComment = false;
		if (form.commentAdded) {
			newComment = '';
		}
		// Handle redirect for lead conversion
		if (form.redirectTo) {
			setTimeout(() => {
				goto(form.redirectTo);
			}, 1500); // Wait 1.5 seconds to show the success message before redirecting
		}
	} else if (form?.status === 'error') {
		toastMessage = form.message || 'An error occurred.';
		toastType = 'error';
		showToast = true;
		isConverting = false;
		isSubmittingComment = false;
	} else {
		// Reset loading states if no form response
		isConverting = false;
		isSubmittingComment = false;
	}
</script>

<!-- Confirmation Modal -->
{#if showConfirmModal}
	<div
		class="bg-opacity-50 fixed inset-0 z-50 flex items-center justify-center bg-black p-4"
		transition:fly={{ duration: 200 }}
	>
		<div
			class="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-6 shadow-xl dark:border-gray-700 dark:bg-gray-800"
			transition:fly={{ y: 20, duration: 300 }}
		>
			<div class="mb-4 flex items-center gap-4">
				<div
					class="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900"
				>
					<CheckCircle class="h-6 w-6 text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">Convert Lead</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">This action cannot be undone</p>
				</div>
			</div>

			<p class="mb-6 text-sm text-gray-700 dark:text-gray-300">
				Are you sure you want to convert <strong>{getFullName(lead)}</strong> into an account and contact?
				This will create new records and mark the lead as converted.
			</p>

			<div class="flex justify-end gap-3">
				<button
					onclick={hideConvertConfirmation}
					class="rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600"
				>
					Cancel
				</button>
				<button
					onclick={confirmConversion}
					class="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800"
				>
					<CheckCircle class="h-4 w-4" />
					Yes, Convert Lead
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Toast -->
{#if showToast}
	<div class="fixed top-4 right-4 z-50 max-w-md" transition:fly={{ y: -20, duration: 300 }}>
		<div
			class="flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-lg dark:border-gray-700 dark:bg-gray-800"
		>
			<div class="flex-shrink-0">
				{#if toastType === 'success'}
					<div
						class="flex h-6 w-6 items-center justify-center rounded-full bg-green-100 dark:bg-green-900"
					>
						<CheckCircle class="h-4 w-4 text-green-600 dark:text-green-400" />
					</div>
				{:else}
					<div
						class="flex h-6 w-6 items-center justify-center rounded-full bg-red-100 dark:bg-red-900"
					>
						<X class="h-4 w-4 text-red-600 dark:text-red-400" />
					</div>
				{/if}
			</div>
			<p class="flex-1 text-sm font-medium text-gray-900 dark:text-gray-100">{toastMessage}</p>
			<button
				onclick={closeToast}
				class="flex-shrink-0 rounded-lg p-1 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
			>
				<X class="h-4 w-4 text-gray-400 dark:text-gray-500" />
			</button>
		</div>
	</div>
{/if}

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<main class="container mx-auto max-w-7xl px-4 py-8">
		<!-- Breadcrumbs -->
		<nav aria-label="breadcrumb" class="mb-8">
			<ol class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
				<li>
					<a
						href="/leads"
						class="font-medium transition-colors hover:text-blue-600 dark:hover:text-blue-400"
						>Leads</a
					>
				</li>
				<li><ChevronRight class="h-4 w-4 text-gray-400 dark:text-gray-500" /></li>
				<li class="max-w-xs truncate font-medium text-gray-900 dark:text-gray-100">
					{getFullName(lead)}
				</li>
			</ol>
		</nav>

		<div class="grid grid-cols-1 gap-8 lg:grid-cols-3">
			<!-- Main Content -->
			<div class="space-y-8 lg:col-span-2">
				<!-- Header Card -->
				<div
					class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="p-8">
						<div class="flex flex-col items-start gap-6 sm:flex-row">
							<div class="flex-shrink-0">
								<div
									class="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg dark:from-blue-600 dark:to-blue-700"
								>
									<span class="text-xl font-bold text-white">{getInitials(lead)}</span>
								</div>
							</div>
							<div class="min-w-0 flex-1">
								<h1 class="mb-3 text-3xl font-bold text-gray-900 dark:text-gray-100">
									{getFullName(lead)}
								</h1>
								<div class="mb-4 flex flex-wrap items-center gap-3">
									<span
										class="inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium {getStatusColor(
											lead.status
										)} ring-1 ring-inset"
									>
										{lead.status}
									</span>
									{#if lead.company}
										<div
											class="flex items-center gap-2 rounded-full bg-gray-50 px-3 py-1 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
										>
											<Building class="h-4 w-4" />
											<span class="font-medium">{lead.company}</span>
										</div>
									{/if}
									{#if lead.title}
										<div
											class="flex items-center gap-2 rounded-full bg-gray-50 px-3 py-1 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
										>
											<Briefcase class="h-4 w-4" />
											<span>{lead.title}</span>
										</div>
									{/if}
								</div>

								<!-- Contact Information Grid -->
								<div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
									{#if lead.email}
										<div
											class="group flex items-center gap-3 rounded-xl bg-gray-50 p-3 transition-colors hover:bg-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600"
										>
											<div
												class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 dark:bg-blue-900"
											>
												<Mail class="h-5 w-5 text-blue-600 dark:text-blue-400" />
											</div>
											<div class="min-w-0 flex-1">
												<p
													class="text-xs font-medium tracking-wide text-gray-500 uppercase dark:text-gray-400"
												>
													Email
												</p>
												<a
													href="mailto:{lead.email}"
													class="block truncate text-sm font-medium text-gray-900 transition-colors hover:text-blue-600 dark:text-gray-100 dark:hover:text-blue-400"
												>
													{lead.email}
												</a>
											</div>
											<button
												onclick={copyEmail}
												class="rounded-lg p-1 opacity-0 transition-all group-hover:opacity-100 hover:bg-white dark:hover:bg-gray-500"
											>
												<Copy class="h-4 w-4 text-gray-400 dark:text-gray-500" />
											</button>
										</div>
									{/if}

									{#if lead.phone}
										<div
											class="group flex items-center gap-3 rounded-xl bg-gray-50 p-3 transition-colors hover:bg-gray-100 dark:bg-gray-700 dark:hover:bg-gray-600"
										>
											<div
												class="flex h-10 w-10 items-center justify-center rounded-xl bg-green-100 dark:bg-green-900"
											>
												<Phone class="h-5 w-5 text-green-600 dark:text-green-400" />
											</div>
											<div class="min-w-0 flex-1">
												<p
													class="text-xs font-medium tracking-wide text-gray-500 uppercase dark:text-gray-400"
												>
													Phone
												</p>
												<a
													href="tel:{lead.phone}"
													class="text-sm font-medium text-gray-900 transition-colors hover:text-green-600 dark:text-gray-100 dark:hover:text-green-400"
												>
													{lead.phone}
												</a>
											</div>
											<button
												onclick={copyPhone}
												class="rounded-lg p-1 opacity-0 transition-all group-hover:opacity-100 hover:bg-white dark:hover:bg-gray-500"
											>
												<Copy class="h-4 w-4 text-gray-400 dark:text-gray-500" />
											</button>
										</div>
									{/if}
								</div>

								<!-- Quick Actions -->
								<div class="flex flex-wrap gap-3">
									{#if lead.email}
										<a
											href="mailto:{lead.email}"
											class="inline-flex items-center gap-2 rounded-xl bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
										>
											<Send class="h-4 w-4" />
											Send Email
										</a>
									{/if}
									{#if lead.phone}
										<a
											href="tel:{lead.phone}"
											class="inline-flex items-center gap-2 rounded-xl bg-green-50 px-4 py-2 text-sm font-medium text-green-700 transition-colors hover:bg-green-100 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800"
										>
											<Phone class="h-4 w-4" />
											Call
										</a>
									{/if}
								</div>
							</div>

							<!-- Action Buttons -->
							<div class="flex flex-col gap-3">
								{#if lead.status !== 'CONVERTED'}
									<form
										id="convertForm"
										method="POST"
										action="?/convert"
										use:enhance={enhanceConvertForm}
									>
										<!-- Hidden form - will be submitted via JavaScript -->
									</form>
									<button
										type="button"
										onclick={showConvertConfirmation}
										disabled={isConverting}
										class="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-3 text-sm font-semibold text-white shadow-lg transition-all hover:from-blue-700 hover:to-blue-800 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50 dark:from-blue-700 dark:to-blue-800 dark:hover:from-blue-800 dark:hover:to-blue-900"
									>
										{#if isConverting}
											<Loader2 class="h-4 w-4 animate-spin" />
											Converting...
										{:else}
											<CheckCircle class="h-4 w-4" />
											Convert Lead
										{/if}
									</button>
								{/if}
								<a
									href="/leads/{lead.id}/edit"
									class="inline-flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-6 py-3 text-sm font-semibold text-gray-700 shadow-sm transition-all hover:border-gray-400 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:border-gray-500 dark:hover:bg-gray-600"
								>
									<Edit3 class="h-4 w-4" />
									Edit Lead
								</a>
							</div>
						</div>
					</div>
				</div>

				<!-- Lead Details Card -->
				<div
					class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="p-8">
						<h2
							class="mb-6 flex items-center gap-3 text-xl font-bold text-gray-900 dark:text-gray-100"
						>
							<div
								class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900"
							>
								<Activity class="h-5 w-5 text-blue-600 dark:text-blue-400" />
							</div>
							Lead Information
						</h2>

						<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
							<!-- Lead Source -->
							{#if lead.leadSource}
								<div class="space-y-2">
									<div class="flex items-center gap-2">
										<Target class="h-4 w-4 text-gray-400 dark:text-gray-500" />
										<span
											class="text-xs font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
											>Lead Source</span
										>
									</div>
									<p
										class="rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium text-gray-900 dark:bg-gray-700 dark:text-gray-100"
									>
										{getLeadSourceDisplay(lead.leadSource)}
									</p>
								</div>
							{/if}

							<!-- Industry -->
							{#if lead.industry}
								<div class="space-y-2">
									<div class="flex items-center gap-2">
										<Briefcase class="h-4 w-4 text-gray-400 dark:text-gray-500" />
										<span
											class="text-xs font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
											>Industry</span
										>
									</div>
									<p
										class="rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium text-gray-900 capitalize dark:bg-gray-700 dark:text-gray-100"
									>
										{lead.industry}
									</p>
								</div>
							{/if}

							<!-- Rating -->
							{#if lead.rating}
								<div class="space-y-2">
									<div class="flex items-center gap-2">
										<Award class="h-4 w-4 text-gray-400 dark:text-gray-500" />
										<span
											class="text-xs font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
											>Rating</span
										>
									</div>
									<div
										class="flex items-center gap-2 rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-700"
									>
										{#each Array(parseInt(lead.rating) || 0) as _, i}
											<Star class="h-4 w-4 fill-current text-yellow-400" />
										{/each}
										{#each Array(5 - (parseInt(lead.rating) || 0)) as _, i}
											<Star class="h-4 w-4 fill-current text-gray-300 dark:text-gray-600" />
										{/each}
										<span class="ml-1 text-sm font-medium text-gray-700 dark:text-gray-300"
											>{lead.rating}/5</span
										>
									</div>
								</div>
							{/if}

							<!-- Lead Owner -->
							<div class="space-y-2">
								<div class="flex items-center gap-2">
									<User class="h-4 w-4 text-gray-400 dark:text-gray-500" />
									<span
										class="text-xs font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
										>Lead Owner</span
									>
								</div>
								<p
									class="rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium text-gray-900 dark:bg-gray-700 dark:text-gray-100"
								>
									{lead.owner?.name || 'Unassigned'}
								</p>
							</div>

							<!-- Created Date -->
							<div class="space-y-2">
								<div class="flex items-center gap-2">
									<Calendar class="h-4 w-4 text-gray-400 dark:text-gray-500" />
									<span
										class="text-xs font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
										>Created</span
									>
								</div>
								<p
									class="rounded-lg bg-gray-50 px-3 py-2 text-sm font-medium text-gray-900 dark:bg-gray-700 dark:text-gray-100"
								>
									{formatDateShort(lead.createdAt)}
								</p>
							</div>
						</div>

						<!-- Description -->
						{#if lead.description}
							<div class="mt-8 border-t border-gray-200 pt-6 dark:border-gray-700">
								<div class="mb-3 flex items-center gap-2">
									<MessageSquare class="h-5 w-5 text-gray-400 dark:text-gray-500" />
									<span
										class="text-sm font-semibold tracking-wide text-gray-500 uppercase dark:text-gray-400"
										>Description</span
									>
								</div>
								<div class="rounded-xl bg-gray-50 p-4 dark:bg-gray-700">
									<div class="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
										{@html lead.description}
									</div>
								</div>
							</div>
						{/if}

						<!-- Conversion Information -->
						{#if lead.isConverted}
							<div class="mt-8 border-t border-gray-200 pt-6 dark:border-gray-700">
								<div
									class="rounded-xl border border-green-200 bg-green-50 p-4 dark:border-green-700 dark:bg-green-900"
								>
									<div class="mb-2 flex items-center gap-3">
										<div
											class="flex h-8 w-8 items-center justify-center rounded-lg bg-green-100 dark:bg-green-800"
										>
											<CheckCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
										</div>
										<h3 class="text-sm font-semibold text-green-800 dark:text-green-300">
											Lead Converted
										</h3>
									</div>
									{#if lead.convertedAt}
										<p class="text-sm text-green-700 dark:text-green-400">
											Converted on {formatDate(lead.convertedAt)}
										</p>
									{/if}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Sidebar -->
			<div class="space-y-8">
				<!-- Activity Feed -->
				<div
					class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="border-b border-gray-200 p-6 dark:border-gray-700">
						<h2 class="flex items-center gap-3 text-lg font-bold text-gray-900 dark:text-gray-100">
							<div
								class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900"
							>
								<MessageSquare class="h-5 w-5 text-blue-600 dark:text-blue-400" />
							</div>
							Activity & Notes
						</h2>
					</div>

					<div class="p-6">
						<!-- Add Note Form -->
						<form method="POST" action="?/addComment" use:enhance={enhanceCommentForm} class="mb-6">
							<div class="space-y-4">
								<textarea
									name="comment"
									bind:value={newComment}
									placeholder="Add a note or log activity..."
									rows="4"
									class="w-full resize-none rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
								></textarea>
								<div class="flex justify-end">
									<button
										type="submit"
										disabled={!newComment.trim() || isSubmittingComment}
										class="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-all hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-blue-700 dark:hover:bg-blue-800"
									>
										{#if isSubmittingComment}
											<Loader2 class="h-4 w-4 animate-spin" />
											Adding...
										{:else}
											<Plus class="h-4 w-4" />
											Add Note
										{/if}
									</button>
								</div>
							</div>
						</form>

						<!-- Activity List -->
						<div class="space-y-4">
							{#if lead.comments && lead.comments.length > 0}
								{#each lead.comments as comment, i (comment.id || i)}
									<div
										class="flex gap-4 rounded-xl bg-gray-50 p-4 dark:bg-gray-700"
										in:fly={{ y: 10, delay: i * 60, duration: 200 }}
									>
										<div class="flex-shrink-0">
											<div
												class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-600 dark:to-gray-700"
											>
												<User class="h-5 w-5 text-gray-600 dark:text-gray-400" />
											</div>
										</div>
										<div class="min-w-0 flex-1">
											<div class="mb-2 flex items-center gap-3">
												<p class="text-sm font-semibold text-gray-900 dark:text-gray-100">
													{comment.author?.name || 'Unknown User'}
												</p>
												<p
													class="rounded-md bg-white px-2 py-1 text-xs text-gray-500 dark:bg-gray-600 dark:text-gray-400"
												>
													{formatDate(comment.createdAt)}
												</p>
											</div>
											<p
												class="text-sm leading-relaxed whitespace-pre-line text-gray-700 dark:text-gray-300"
											>
												{comment.body}
											</p>
										</div>
									</div>
								{/each}
							{:else}
								<div class="py-12 text-center">
									<div
										class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gray-100 dark:bg-gray-700"
									>
										<MessageSquare class="h-8 w-8 text-gray-400 dark:text-gray-500" />
									</div>
									<p class="mb-1 text-sm font-semibold text-gray-900 dark:text-gray-100">
										No activity yet
									</p>
									<p class="text-xs text-gray-500 dark:text-gray-400">
										Be the first to add a note or log an interaction.
									</p>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- Related Contact (if converted) -->
				{#if lead.convertedContactId && lead.contact}
					<div
						class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
					>
						<div class="border-b border-gray-200 p-6 dark:border-gray-700">
							<h2
								class="flex items-center gap-3 text-lg font-bold text-gray-900 dark:text-gray-100"
							>
								<div
									class="flex h-8 w-8 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900"
								>
									<Users class="h-5 w-5 text-green-600 dark:text-green-400" />
								</div>
								Related Contact
							</h2>
						</div>

						<div class="p-6">
							<div class="space-y-4">
								<div class="flex items-center gap-3">
									<div
										class="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-green-600 dark:from-green-600 dark:to-green-700"
									>
										<User class="h-6 w-6 text-white" />
									</div>
									<div>
										<p class="font-semibold text-gray-900 dark:text-gray-100">
											{lead.contact.firstName}
											{lead.contact.lastName}
										</p>
										<p class="text-xs text-gray-500 dark:text-gray-400">Contact</p>
									</div>
								</div>

								{#if lead.contact.email}
									<div class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
										<Mail class="h-4 w-4" />
										<span>{lead.contact.email}</span>
									</div>
								{/if}

								{#if lead.contact.phone}
									<div class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
										<Phone class="h-4 w-4" />
										<span>{lead.contact.phone}</span>
									</div>
								{/if}

								<a
									href="/contacts/{lead.contact.id}"
									class="inline-flex w-full items-center justify-center rounded-xl bg-green-50 px-4 py-3 text-sm font-semibold text-green-700 transition-colors hover:bg-green-100 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800"
								>
									<ExternalLink class="mr-2 h-4 w-4" />
									View Contact
								</a>
							</div>
						</div>
					</div>
				{/if}

				<!-- Quick Stats -->
				<div
					class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800"
				>
					<div class="border-b border-gray-200 p-6 dark:border-gray-700">
						<h2 class="flex items-center gap-3 text-lg font-bold text-gray-900 dark:text-gray-100">
							<div
								class="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900"
							>
								<TrendingUp class="h-5 w-5 text-purple-600 dark:text-purple-400" />
							</div>
							Quick Stats
						</h2>
					</div>

					<div class="space-y-4 p-6">
						<div class="flex items-center justify-between">
							<span class="text-sm text-gray-600 dark:text-gray-300">Comments</span>
							<span class="text-sm font-semibold text-gray-900 dark:text-gray-100"
								>{lead.comments?.length || 0}</span
							>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-sm text-gray-600 dark:text-gray-300">Days Since Created</span>
							<span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
								{Math.floor(
									(new Date().getTime() - new Date(lead.createdAt).getTime()) /
										(1000 * 60 * 60 * 24)
								)}
							</span>
						</div>
						{#if lead.convertedAt}
							<div class="flex items-center justify-between">
								<span class="text-sm text-gray-600 dark:text-gray-300">Days to Convert</span>
								<span class="text-sm font-semibold text-green-600 dark:text-green-400">
									{Math.floor(
										(new Date(lead.convertedAt).getTime() - new Date(lead.createdAt).getTime()) /
											(1000 * 60 * 60 * 24)
									)}
								</span>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	</main>
</div>
