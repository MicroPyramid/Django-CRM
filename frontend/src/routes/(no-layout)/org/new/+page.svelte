<script>
	import '../../../../app.css';
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import { Building2, ArrowLeft, Check, AlertCircle } from '@lucide/svelte';

	export let form; // This contains the result of your form action

	// Handle form submission success
	$: if (form?.data) {
		// Redirect after a short delay to show success message
		setTimeout(() => {
			goto('/org');
		}, 1500);
	}
</script>

<div class="min-h-screen bg-gray-50 px-4 py-8">
	<div class="mx-auto max-w-lg">
		<!-- Header -->
		<div class="mb-8 text-center">
			<div class="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-blue-100">
				<Building2 class="h-8 w-8 text-blue-600" />
			</div>
			<h1 class="mb-2 text-3xl font-bold text-gray-900">Create Organization</h1>
			<p class="text-gray-600">Set up your new organization to get started</p>
		</div>

		<!-- Form Card -->
		<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
			<form action="/org/new" method="POST" use:enhance class="space-y-6">
				<!-- Organization Name Field -->
				<div class="space-y-2">
					<label for="org_name" class="block text-sm font-medium text-gray-700">
						Organization Name
					</label>
					<input
						type="text"
						id="org_name"
						name="org_name"
						required
						class="w-full rounded-lg border border-gray-300 bg-gray-50 px-4 py-3 transition-colors duration-200 focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-500"
						placeholder="Enter organization name"
					/>
				</div>

				<!-- Error Message -->
				{#if form?.error}
					<div class="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-4">
						<AlertCircle class="h-5 w-5 flex-shrink-0 text-red-500" />
						<span class="text-sm text-red-700">{form.error.name}</span>
					</div>
				{/if}

				<!-- Success Message -->
				{#if form?.data}
					<div class="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 p-4">
						<Check class="h-5 w-5 flex-shrink-0 text-green-500" />
						<span class="text-sm text-green-700">
							Organization "{form.data.name}" created successfully!
						</span>
					</div>
				{/if}

				<!-- Submit Button -->
				<button
					type="submit"
					class="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition-colors duration-200 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
				>
					Create Organization
				</button>

				<!-- Back Link -->
				<div class="text-center">
					<a
						href="/org"
						class="inline-flex items-center gap-2 text-sm font-medium text-gray-600 transition-colors duration-200 hover:text-gray-800"
					>
						<ArrowLeft class="h-4 w-4" />
						Back to Organizations
					</a>
				</div>
			</form>
		</div>
	</div>
</div>
