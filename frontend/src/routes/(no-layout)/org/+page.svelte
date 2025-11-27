<script>
    import '../../../app.css'
    import { Building, LogOut, Plus } from '@lucide/svelte';
    import { enhance } from '$app/forms';

    // Get the data from the server load function
    export let data;
    const { orgs } = data;

    let loading = false;
</script>

<div class="min-h-screen bg-gray-50 p-4">
    <div class="max-w-6xl mx-auto">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold text-gray-900 mb-2">Select Organization</h1>
                <p class="text-gray-600">Choose an organization to continue</p>
            </div>
            <a 
                href="/logout" 
                class="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-200"
                title="Logout"
            >
                <LogOut class="w-5 h-5" />
                <span class="hidden sm:inline">Logout</span>
            </a>
        </div>

        <!-- Organizations Grid -->
        {#if orgs.length > 0}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each orgs as org}
                    <form
                        method="POST"
                        action="?/selectOrg"
                        use:enhance={() => {
                            loading = true;
                            return async ({ update }) => {
                                await update();
                                loading = false;
                            };
                        }}
                        class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all duration-200 cursor-pointer group"
                    >
                        <input type="hidden" name="org_id" value={org.id} />
                        <input type="hidden" name="org_name" value={org.name} />
                        <button
                            type="submit"
                            disabled={loading}
                            class="w-full text-left"
                            aria-label="Select {org.name} organization"
                        >
                            <div class="p-6">
                                <div class="flex items-start justify-between mb-4">
                                    <div class="flex items-center gap-3">
                                        <div class="p-3 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                                            <Building class="w-6 h-6 text-blue-600" />
                                        </div>
                                        <div>
                                            <h3 class="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                                                {org.name}
                                            </h3>
                                            <p class="text-sm text-gray-500 capitalize">{org.role?.toLowerCase() || 'Member'}</p>
                                        </div>
                                    </div>
                                </div>

                                <div class="w-full py-2.5 px-4 bg-blue-600 group-hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200 text-center">
                                    {loading ? 'Switching...' : 'Select Organization'}
                                </div>
                            </div>
                        </button>
                    </form>
                {/each}
            </div>
        {:else}
            <div class="text-center py-16">
                <div class="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Building class="w-8 h-8 text-gray-400" />
                </div>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">No organizations found</h3>
                <p class="text-gray-600 mb-6">Create your first organization to get started</p>
                <a 
                    href="/org/new"
                    class="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200"
                >
                    <Plus class="w-5 h-5" />
                    Create Organization
                </a>
            </div>
        {/if}

        <!-- Floating Action Button -->
        {#if orgs.length > 0}
            <a 
                href="/org/new"
                class="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl flex items-center justify-center transition-all duration-200 z-50"
                title="Create New Organization"
            >
                <Plus class="w-6 h-6" />
            </a>
        {/if}
    </div>
</div>