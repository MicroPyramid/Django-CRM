<script>
    import { enhance } from '$app/forms';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { X, Save, Calendar, User, Building, AlertCircle, CheckCircle } from '@lucide/svelte';

    /** @type {import('./$types').PageData} */
    export let data;
    
    /** @type {import('./$types').ActionData} */
    export let form;

    // Reactive task data for the form
    let task = { ...data.task }; // Create a copy to avoid mutating prop directly initially
    
    // Ensure dueDate is in YYYY-MM-DD for the input, or empty string if null
    let dueDateString = '';
    if (task.dueDate) {
        /** @type {any} */
        const dateValue = task.dueDate;
        if (typeof dateValue === 'string') {
            dueDateString = dateValue.split('T')[0];
        } else if (dateValue instanceof Date) {
            dueDateString = dateValue.toISOString().split('T')[0];
        }
    }
    task = { ...task, dueDate: dueDateString };

    const users = data.users;
    const accounts = data.accounts;

    function handleCancel() {
        goto(`/tasks/${data.task.id}`);
    }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Header -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 mb-6">
            <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-xl flex items-center justify-center">
                            <CheckCircle class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                            <h1 class="text-xl font-semibold text-gray-900 dark:text-white">Edit Task</h1>
                            <p class="text-sm text-gray-500 dark:text-gray-400">Update task details and settings</p>
                        </div>
                    </div>
                    <button 
                        type="button" 
                        onclick={handleCancel} 
                        class="w-10 h-10 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center justify-center transition-colors duration-200"
                        aria-label="Close"
                    >
                        <X class="w-5 h-5 text-gray-600 dark:text-gray-300" />
                    </button>
                </div>
            </div>
        </div>

        <!-- Form -->
        <form method="POST" action="?/update" use:enhance class="space-y-6">
            <!-- Error Messages -->
            {#if form?.message || form?.fieldError}
                <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-red-200 dark:border-red-800">
                    <div class="p-6">
                        <div class="flex items-start space-x-3">
                            <AlertCircle class="w-5 h-5 text-red-500 dark:text-red-400 mt-0.5 flex-shrink-0" />
                            <div class="flex-1">
                                {#if form?.message}
                                    <p class="text-red-700 dark:text-red-300 font-medium">{form.message}</p>
                                {/if}
                                {#if form?.fieldError}
                                    <p class="text-red-700 dark:text-red-300">Error with field '{form.fieldError[0]}': {form.fieldError[1]}</p>
                                {/if}
                            </div>
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Main Form Content -->
            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                <div class="p-6 space-y-6">
                    <!-- Subject -->
                    <div class="space-y-2">
                        <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-subject">
                            Subject <span class="text-red-500 dark:text-red-400">*</span>
                        </label>
                        <input 
                            type="text" 
                            id="task-subject" 
                            name="subject" 
                            class="w-full h-12 px-4 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                            bind:value={task.subject} 
                            required 
                            placeholder="Enter task subject"
                        />
                    </div>

                    <!-- Description -->
                    <div class="space-y-2">
                        <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-description">
                            Description
                        </label>
                        <textarea 
                            id="task-description" 
                            name="description" 
                            class="w-full px-4 py-3 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 resize-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                            rows="4" 
                            bind:value={task.description}
                            placeholder="Add task description..."
                        ></textarea>
                    </div>

                    <!-- Status and Priority -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="space-y-2">
                            <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-status">
                                Status
                            </label>
                            <select
                                id="task-status"
                                name="status"
                                class="w-full h-12 px-4 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-gray-900 dark:text-white"
                                bind:value={task.status}
                            >
                                <option>New</option>
                                <option>In Progress</option>
                                <option>Completed</option>
                            </select>
                        </div>
                        <div class="space-y-2">
                            <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-priority">
                                Priority
                            </label>
                            <select
                                id="task-priority"
                                name="priority"
                                class="w-full h-12 px-4 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-gray-900 dark:text-white"
                                bind:value={task.priority}
                            >
                                <option>High</option>
                                <option>Medium</option>
                                <option>Low</option>
                            </select>
                        </div>
                    </div>

                    <!-- Due Date and Owner -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="space-y-2">
                            <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-duedate">
                                <div class="flex items-center space-x-2">
                                    <Calendar class="w-4 h-4" />
                                    <span>Due Date</span>
                                </div>
                            </label>
                            <input 
                                type="date" 
                                id="task-duedate" 
                                name="dueDate" 
                                class="w-full h-12 px-4 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-gray-900 dark:text-white" 
                                bind:value={task.dueDate} 
                            />
                        </div>
                        <div class="space-y-2">
                            <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-owner">
                                <div class="flex items-center space-x-2">
                                    <User class="w-4 h-4" />
                                    <span>Owner <span class="text-red-500 dark:text-red-400">*</span></span>
                                </div>
                            </label>
                            <select 
                                id="task-owner" 
                                name="ownerId" 
                                class="w-full h-12 px-4 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-gray-900 dark:text-white" 
                                bind:value={task.ownerId} 
                                required
                            >
                                {#each users as user}
                                    <option value={user.id}>{user.name}</option>
                                {/each}
                            </select>
                        </div>
                    </div>

                    <!-- Account -->
                    <div class="space-y-2">
                        <label class="block text-sm font-semibold text-gray-900 dark:text-white" for="task-account">
                            <div class="flex items-center space-x-2">
                                <Building class="w-4 h-4" />
                                <span>Account</span>
                                <span class="text-xs text-gray-500 dark:text-gray-400 font-normal">(Optional)</span>
                            </div>
                        </label>
                        <select 
                            id="task-account" 
                            name="accountId" 
                            class="w-full h-12 px-4 border border-gray-200 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-700 focus:bg-white dark:focus:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent transition-all duration-200 text-gray-900 dark:text-white" 
                            bind:value={task.accountId}
                        >
                            <option value={null}>No account selected</option>
                            {#each accounts as acc}
                                <option value={acc.id}>{acc.name}</option>
                            {/each}
                        </select>
                    </div>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700">
                <div class="px-6 py-4">
                    <div class="flex justify-end space-x-3">
                        <button 
                            type="button" 
                            class="h-11 px-6 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 font-medium transition-colors duration-200 flex items-center space-x-2" 
                            onclick={handleCancel}
                        >
                            <X class="w-4 h-4" />
                            <span>Cancel</span>
                        </button>
                        <button 
                            type="submit" 
                            class="h-11 px-6 rounded-xl bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 text-white font-medium transition-colors duration-200 flex items-center space-x-2 shadow-sm"
                        >
                            <Save class="w-4 h-4" />
                            <span>Save Changes</span>
                        </button>
                    </div>
                </div>
            </div>
        </form>
    </div>
</div>