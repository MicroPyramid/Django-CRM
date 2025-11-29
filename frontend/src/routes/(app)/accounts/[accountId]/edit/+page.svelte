<script>
	export let data;
	let account = data.account;
	let name = account.name;
	let industry = account.industry || '';
	let type = account.type || '';
	let website = account.website || '';
	let phone = account.phone || '';
</script>

<div class="mx-auto mt-8 max-w-xl rounded bg-white p-6 shadow dark:bg-gray-800">
	<h2 class="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Edit Account</h2>
	<form method="POST" class="space-y-4">
		<div>
			<label for="name" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>Name<span class="text-red-500">*</span></label
			>
			<input
				id="name"
				name="name"
				bind:value={name}
				required
				class="w-full rounded border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			/>
		</div>
		<div>
			<label for="industry" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>Industry</label
			>
			<input
				id="industry"
				name="industry"
				bind:value={industry}
				class="w-full rounded border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			/>
		</div>
		<div>
			<label for="type" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>Type</label
			>
			<input
				id="type"
				name="type"
				bind:value={type}
				class="w-full rounded border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			/>
		</div>
		<div>
			<label for="website" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>Website</label
			>
			<input
				id="website"
				name="website"
				bind:value={website}
				class="w-full rounded border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			/>
		</div>
		<div>
			<label for="phone" class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
				>Phone</label
			>
			<input
				id="phone"
				name="phone"
				bind:value={phone}
				class="w-full rounded border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700 dark:text-white"
			/>
		</div>
		<div class="mt-6 flex gap-2">
			<button
				type="submit"
				class="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:outline-none"
				>Save</button
			>
			<a
				href={`/accounts/${account.id}`}
				class="rounded bg-gray-200 px-4 py-2 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
				>Cancel</a
			>
		</div>
	</form>
</div>
