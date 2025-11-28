<script>
  export let data;
  let account = data.account;
  let name = account.name;
  let industry = account.industry || '';
  let type = account.type || '';
  let website = account.website || '';
  let phone = account.phone || '';
</script>

<div class="max-w-xl mx-auto mt-8 p-6 bg-white dark:bg-gray-800 rounded shadow">
  <h2 class="text-2xl font-bold mb-4 text-gray-900 dark:text-white">Edit Account</h2>
  <form method="POST" class="space-y-4">
    <div>
      <label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name<span class="text-red-500">*</span></label>
      <input id="name" name="name" bind:value={name} required class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    </div>
    <div>
      <label for="industry" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Industry</label>
      <input id="industry" name="industry" bind:value={industry} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    </div>
    <div>
      <label for="type" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
      <input id="type" name="type" bind:value={type} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    </div>
    <div>
      <label for="website" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Website</label>
      <input id="website" name="website" bind:value={website} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    </div>
    <div>
      <label for="phone" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
      <input id="phone" name="phone" bind:value={phone} class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    </div>
    <div class="flex gap-2 mt-6">
      <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500">Save</button>
      <a href={`/accounts/${account.id}`} class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600">Cancel</a>
    </div>
  </form>
</div>
