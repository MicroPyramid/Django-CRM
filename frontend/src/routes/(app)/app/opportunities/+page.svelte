<script>
    import { 
        Search, 
        Plus, 
        Filter, 
        SortAsc, 
        MoreVertical, 
        Eye, 
        Edit, 
        Trash2,
        DollarSign,
        TrendingUp,
        Users,
        Calendar,
        Building2,
        User,
        CheckCircle,
        XCircle,
        Clock,
        Target,
        X,
        AlertTriangle
    } from '@lucide/svelte';
    import { goto } from '$app/navigation';
    import { enhance } from '$app/forms';
    import { page } from '$app/stores';

    /** @type {{ data: import('./$types').PageData, form?: any }} */
    let { data, form } = $props();

    let searchTerm = $state('');
    let selectedStage = $state('all');
    let sortField = $state('createdAt');
    let sortDirection = $state('desc');
    let showFilters = $state(false);
    let showDeleteModal = $state(false);
    /** @type {any} */
    let opportunityToDelete = $state(null);
    let deleteLoading = $state(false);

    // Stage configurations
    const stageConfig = {
        PROSPECTING: { label: 'Prospecting', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300', icon: Target },
        QUALIFICATION: { label: 'Qualification', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300', icon: Search },
        PROPOSAL: { label: 'Proposal', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300', icon: Edit },
        NEGOTIATION: { label: 'Negotiation', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300', icon: Users },
        CLOSED_WON: { label: 'Closed Won', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300', icon: CheckCircle },
        CLOSED_LOST: { label: 'Closed Lost', color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300', icon: XCircle }
    };


    // Simple filtering function that we'll call explicitly
    function getFilteredOpportunities() {

        if (!data?.opportunities || !Array.isArray(data.opportunities)) {
            return [];
        }

        let filtered = [...data.opportunities];

        // Search filter
        if (searchTerm && searchTerm.trim()) {
            const searchLower = searchTerm.toLowerCase().trim();
            filtered = filtered.filter(opp => {
                const nameMatch = opp.name?.toLowerCase().includes(searchLower);
                const accountMatch = opp.account?.name?.toLowerCase().includes(searchLower);
                const ownerMatch = opp.owner?.name?.toLowerCase().includes(searchLower) || 
                                 opp.owner?.email?.toLowerCase().includes(searchLower);
                return nameMatch || accountMatch || ownerMatch;
            });
        }

        // Stage filter
        if (selectedStage && selectedStage !== 'all') {
            filtered = filtered.filter(opp => opp.stage === selectedStage);
        }

        return filtered;
    }

    // Use $derived with the function
    const filteredOpportunities = $derived(getFilteredOpportunities());


    /**
     * @param {number | null} amount
     * @returns {string}
     */
    function formatCurrency(amount) {
        if (!amount) return '-';
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    /**
     * @param {string | Date | null} date
     * @returns {string}
     */
    function formatDate(date) {
        if (!date) return '-';
        return new Date(date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    /**
     * @param {string} field
     */
    function toggleSort(field) {
        if (sortField === field) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            sortField = field;
            sortDirection = 'asc';
        }
    }

    /**
     * @param {any} opportunity
     */
    function openDeleteModal(opportunity) {
        opportunityToDelete = opportunity;
        showDeleteModal = true;
    }

    function closeDeleteModal() {
        showDeleteModal = false;
        opportunityToDelete = null;
        deleteLoading = false;
    }
</script>

<svelte:head>
    <title>Opportunities - BottleCRM</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Success/Error Messages -->
    {#if form?.success}
        <div class="fixed top-4 right-4 z-50 max-w-md">
            <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Success!</strong>
                <span class="block sm:inline">{form.message || 'Opportunity deleted successfully.'}</span>
            </div>
        </div>
    {/if}
    
    {#if form?.message && !form?.success}
        <div class="fixed top-4 right-4 z-50 max-w-md">
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Error!</strong>
                <span class="block sm:inline">{form.message}</span>
            </div>
        </div>
    {/if}
    
    <!-- Header -->
    <div class="bg-white dark:bg-gray-800 shadow">
        <div class="px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">Opportunities</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <a
                        href="/app/opportunities/new"
                        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-500 dark:hover:bg-blue-600"
                    >
                        <Plus class="mr-2 h-4 w-4" />
                        New Opportunity
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- Stats Cards -->
    <div class="px-4 sm:px-6 lg:px-8 py-6">
        <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <Target class="h-6 w-6 text-gray-400" />
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Opportunities</dt>
                                <dd class="text-lg font-medium text-gray-900 dark:text-white">{data.stats.total}</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <DollarSign class="h-6 w-6 text-gray-400" />
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Value</dt>
                                <dd class="text-lg font-medium text-gray-900 dark:text-white">{formatCurrency(data.stats.totalValue)}</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <TrendingUp class="h-6 w-6 text-green-400" />
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Pipeline Value</dt>
                                <dd class="text-lg font-medium text-gray-900 dark:text-white">{formatCurrency(data.stats.pipeline)}</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <CheckCircle class="h-6 w-6 text-green-400" />
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Won Value</dt>
                                <dd class="text-lg font-medium text-gray-900 dark:text-white">{formatCurrency(data.stats.wonValue)}</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Filters and Search -->
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg mb-6">
            <div class="p-6">
                <div class="flex flex-col sm:flex-row gap-4">
                    <!-- Search -->
                    <div class="flex-1">
                        <div class="relative">
                            <label for="opportunities-search" class="sr-only">Search opportunities</label>
                            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Search class="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                type="text"
                                id="opportunities-search"
                                bind:value={searchTerm}
                                placeholder="Search opportunities, accounts, or owners..."
                                class="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    </div>

                    <!-- Stage Filter -->
                    <div class="sm:w-48">
                        <label for="opportunities-stage-filter" class="sr-only">Filter opportunities by stage</label>
                        <select
                            id="opportunities-stage-filter"
                            bind:value={selectedStage}
                            class="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="all">All Stages</option>
                            {#each Object.entries(stageConfig) as [stage, config]}
                                <option value={stage}>{config.label}</option>
                            {/each}
                        </select>
                    </div>

                    <!-- Filter Toggle -->
                    <button
                        type="button"
                        onclick={() => showFilters = !showFilters}
                        class="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        <Filter class="mr-2 h-4 w-4" />
                        Filters
                    </button>
                </div>
            </div>
        </div>

        <!-- Opportunities Table -->
        <div class="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg">
            <div class="min-w-full overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead class="bg-gray-50 dark:bg-gray-700">
                        <tr>
                            <th 
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                                onclick={() => toggleSort('name')}
                            >
                                <div class="flex items-center space-x-1">
                                    <span>Opportunity</span>
                                    <SortAsc class="h-4 w-4" />
                                </div>
                            </th>
                            <th 
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                                onclick={() => toggleSort('account.name')}
                            >
                                <div class="flex items-center space-x-1">
                                    <span>Account</span>
                                    <SortAsc class="h-4 w-4" />
                                </div>
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                Stage
                            </th>
                            <th 
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                                onclick={() => toggleSort('amount')}
                            >
                                <div class="flex items-center space-x-1">
                                    <span>Amount</span>
                                    <SortAsc class="h-4 w-4" />
                                </div>
                            </th>
                            <th 
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                                onclick={() => toggleSort('closeDate')}
                            >
                                <div class="flex items-center space-x-1">
                                    <span>Close Date</span>
                                    <SortAsc class="h-4 w-4" />
                                </div>
                            </th>
                            <th 
                                class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600"
                                onclick={() => toggleSort('owner.name')}
                            >
                                <div class="flex items-center space-x-1">
                                    <span>Owner</span>
                                    <SortAsc class="h-4 w-4" />
                                </div>
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                Activities
                            </th>
                            <th class="relative px-6 py-3">
                                <span class="sr-only">Actions</span>
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {#each filteredOpportunities as opportunity (opportunity.id)}
                            {@const config = stageConfig[opportunity.stage] || stageConfig.PROSPECTING}
                            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <div>
                                            <div class="text-sm font-medium text-gray-900 dark:text-white">
                                                {opportunity.name || 'Unnamed Opportunity'}
                                            </div>
                                            {#if opportunity.type}
                                                <div class="text-sm text-gray-500 dark:text-gray-400">
                                                    {opportunity.type}
                                                </div>
                                            {/if}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <Building2 class="h-4 w-4 text-gray-400 mr-2" />
                                        <div>
                                            <div class="text-sm font-medium text-gray-900 dark:text-white">
                                                {opportunity.account?.name || 'No Account'}
                                            </div>
                                            {#if opportunity.account?.type}
                                                <div class="text-sm text-gray-500 dark:text-gray-400">
                                                    {opportunity.account.type}
                                                </div>
                                            {/if}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {config.color}">
                                        {#if config.icon}
                                            {@const IconComponent = config.icon}
                                            <IconComponent class="mr-1 h-3 w-3" />
                                        {/if}
                                        {config.label}
                                    </span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                    {formatCurrency(opportunity.amount)}
                                    {#if opportunity.probability}
                                        <div class="text-xs text-gray-500 dark:text-gray-400">
                                            {opportunity.probability}% probability
                                        </div>
                                    {/if}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                    <div class="flex items-center">
                                        <Calendar class="h-4 w-4 text-gray-400 mr-2" />
                                        {formatDate(opportunity.closeDate)}
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <User class="h-4 w-4 text-gray-400 mr-2" />
                                        <div class="text-sm font-medium text-gray-900 dark:text-white">
                                            {opportunity.owner?.name || opportunity.owner?.email || 'No Owner'}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                    <div class="flex items-center space-x-4">
                                        {#if opportunity._count?.tasks > 0}
                                            <span class="flex items-center">
                                                <Clock class="h-4 w-4 mr-1" />
                                                {opportunity._count.tasks}
                                            </span>
                                        {/if}
                                        {#if opportunity._count?.events > 0}
                                            <span class="flex items-center">
                                                <Calendar class="h-4 w-4 mr-1" />
                                                {opportunity._count.events}
                                            </span>
                                        {/if}
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <div class="flex items-center justify-end space-x-2">
                                        <a
                                            href="/app/opportunities/{opportunity.id}"
                                            class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                                            title="View"
                                        >
                                            <Eye class="h-4 w-4" />
                                        </a>
                                        <a
                                            href="/app/opportunities/{opportunity.id}/edit"
                                            class="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-300"
                                            title="Edit"
                                        >
                                            <Edit class="h-4 w-4" />
                                        </a>
                                        <button
                                            type="button"
                                            onclick={() => openDeleteModal(opportunity)}
                                            class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                            title="Delete"
                                        >
                                            <Trash2 class="h-4 w-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>

            {#if filteredOpportunities.length === 0}
                <div class="text-center py-12">
                    <Target class="mx-auto h-12 w-12 text-gray-400" />
                    <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">No opportunities</h3>
                    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        {searchTerm || selectedStage !== 'all' ? 'No opportunities match your current filters.' : 'Get started by creating a new opportunity.'}
                    </p>
                    {#if !searchTerm && selectedStage === 'all'}
                        <div class="mt-6">
                            <a
                                href="/app/opportunities/new"
                                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                            >
                                <Plus class="mr-2 h-4 w-4" />
                                New Opportunity
                            </a>
                        </div>
                    {/if}
                </div>
            {/if}
        </div>
    </div>

    
</div>

<!-- Delete Confirmation Modal -->
{#if showDeleteModal && opportunityToDelete}
    <div 
        class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" 
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabindex="-1"
        onclick={closeDeleteModal}
        onkeydown={(e) => e.key === 'Escape' && closeDeleteModal()}
    >
        <div 
            class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800" 
            role="button" 
            tabindex="0" 
            onkeydown={(e) => e.key === 'Escape' && closeDeleteModal()} 
            onclick={(e) => e.stopPropagation()}
        >
            <div class="mt-3">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center">
                        <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900">
                            <AlertTriangle class="h-6 w-6 text-red-600 dark:text-red-400" />
                        </div>
                        <div class="ml-4">
                            <h3 id="modal-title" class="text-lg leading-6 font-medium text-gray-900 dark:text-white">Delete Opportunity</h3>
                        </div>
                    </div>
                    <button
                        type="button"
                        onclick={closeDeleteModal}
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                        <X class="h-5 w-5" />
                    </button>
                </div>
                
                <div class="mt-2">
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                        Are you sure you want to delete the opportunity <strong>"{opportunityToDelete?.name || 'Unknown'}"</strong>? 
                        This action cannot be undone and will also delete all associated tasks, events, and comments.
                    </p>
                </div>

                <div class="mt-6 flex justify-end space-x-3">
                    <button
                        type="button"
                        onclick={closeDeleteModal}
                        disabled={deleteLoading}
                        class="px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    
                    <form method="POST" action="?/delete" use:enhance={({ formElement, formData }) => {
                        deleteLoading = true;
                        
                        return async ({ result }) => {
                            deleteLoading = false;
                            
                            if (result.type === 'success') {
                                closeDeleteModal();
                                // Use goto with replaceState and invalidateAll for a clean refresh
                                await goto($page.url.pathname, { 
                                    replaceState: true, 
                                    invalidateAll: true 
                                });
                            } else if (result.type === 'failure') {
                                console.error('Delete failed:', result.data?.message);
                                alert('Failed to delete opportunity: ' + (result.data?.message || 'Unknown error'));
                            } else if (result.type === 'error') {
                                console.error('Delete error:', result.error);
                                alert('An error occurred while deleting the opportunity.');
                            }
                        };
                    }}>
                        <input type="hidden" name="opportunityId" value={opportunityToDelete?.id || ''} />
                        <button
                            type="submit"
                            disabled={deleteLoading}
                            class="px-4 py-2 bg-red-600 border border-transparent rounded-md text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {deleteLoading ? 'Deleting...' : 'Delete'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
{/if}