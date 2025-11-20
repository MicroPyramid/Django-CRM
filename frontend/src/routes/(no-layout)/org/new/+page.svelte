<script>
    import '../../../../app.css'
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
    <div class="max-w-lg mx-auto">
        <!-- Header -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                <Building2 class="w-8 h-8 text-blue-600" />
            </div>
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Create Organization</h1>
            <p class="text-gray-600">Set up your new organization to get started</p>
        </div>

        <!-- Form Card -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 sm:p-8">
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
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 bg-gray-50 focus:bg-white"
                        placeholder="Enter organization name"
                    />
                </div>

                <!-- Error Message -->
                {#if form?.error}
                    <div class="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <AlertCircle class="w-5 h-5 text-red-500 flex-shrink-0" />
                        <span class="text-red-700 text-sm">{form.error.name}</span>
                    </div>
                {/if}

                <!-- Success Message -->
                {#if form?.data}
                    <div class="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg">
                        <Check class="w-5 h-5 text-green-500 flex-shrink-0" />
                        <span class="text-green-700 text-sm">
                            Organization "{form.data.name}" created successfully!
                        </span>
                    </div>
                {/if}

                <!-- Submit Button -->
                <button 
                    type="submit" 
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors duration-200 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    Create Organization
                </button>

                <!-- Back Link -->
                <div class="text-center">
                    <a 
                        href="/org" 
                        class="inline-flex items-center gap-2 text-gray-600 hover:text-gray-800 text-sm font-medium transition-colors duration-200"
                    >
                        <ArrowLeft class="w-4 h-4" />
                        Back to Organizations
                    </a>
                </div>
            </form>
        </div>
    </div>
</div>
