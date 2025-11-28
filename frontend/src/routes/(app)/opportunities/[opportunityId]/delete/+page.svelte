<script>
    import { enhance } from '$app/forms';
    import { goto } from '$app/navigation';
    import { AlertTriangle, ArrowLeft } from '@lucide/svelte';

    /** @type {{ data: import('./$types').PageData }} */
    let { data } = $props();

    let deleteLoading = $state(false);
</script>

<svelte:head>
    <title>Delete Opportunity - BottleCRM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <div class="bg-white dark:bg-gray-800 shadow">
        <div class="px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <a 
                        href="/opportunities/{data.opportunity.id}"
                        class="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 mr-4"
                    >
                        <ArrowLeft class="h-5 w-5" />
                    </a>
                    <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">Delete Opportunity</h1>
                </div>
            </div>
        </div>
    </div>

    <!-- Content -->
    <div class="py-10">
        <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="bg-white dark:bg-gray-800 shadow rounded-lg">
                <div class="px-6 py-8">
                    <div class="flex items-center mb-6">
                        <div class="flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900">
                            <AlertTriangle class="h-6 w-6 text-red-600 dark:text-red-400" />
                        </div>
                        <div class="ml-4">
                            <h3 class="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                                Confirm Deletion
                            </h3>
                            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                This action cannot be undone.
                            </p>
                        </div>
                    </div>

                    <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 mb-6">
                        <h4 class="text-sm font-medium text-red-800 dark:text-red-400 mb-2">
                            You are about to delete:
                        </h4>
                        <div class="text-sm text-red-700 dark:text-red-300 space-y-1">
                            <div><strong>Opportunity:</strong> {data.opportunity.name}</div>
                            <div><strong>Account:</strong> {data.opportunity.account?.name || 'N/A'}</div>
                            <div><strong>Amount:</strong> {data.opportunity.amount ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(data.opportunity.amount) : 'N/A'}</div>
                            <div><strong>Stage:</strong> {data.opportunity.stage}</div>
                        </div>
                    </div>

                    <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4 mb-6">
                        <p class="text-sm text-yellow-700 dark:text-yellow-300">
                            <strong>Warning:</strong> Deleting this opportunity will also remove all associated:
                        </p>
                        <ul class="mt-2 text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside space-y-1">
                            <li>Tasks and activities</li>
                            <li>Events and meetings</li>
                            <li>Comments and notes</li>
                            <li>Quote associations</li>
                        </ul>
                    </div>

                    <div class="flex justify-end space-x-3">
                        <a
                            href="/opportunities/{data.opportunity.id}"
                            class="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            Cancel
                        </a>
                        
                        <form method="POST" use:enhance={() => {
                            deleteLoading = true;
                            return ({ result }) => {
                                deleteLoading = false;
                                if (result.type === 'success') {
                                    // Navigate to opportunities list on successful deletion
                                    goto('/opportunities');
                                } else if (result.type === 'failure') {
                                    // Handle error case - you could show a toast notification here
                                    console.error('Failed to delete opportunity:', result.data?.message);
                                    alert(result.data?.message || 'Failed to delete opportunity');
                                }
                            };
                        }}>
                            <button
                                type="submit"
                                disabled={deleteLoading}
                                class="px-4 py-2 bg-red-600 border border-transparent rounded-md text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {deleteLoading ? 'Deleting...' : 'Delete Opportunity'}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
