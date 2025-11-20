<script lang="ts">
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { fly } from 'svelte/transition';
  import { ArrowLeft, Save, X, User, Building, Mail, Phone, Calendar, Star, Target, AlertCircle } from '@lucide/svelte';

  export let data;
  
  let { lead, users } = data;
  let isSubmitting = false;
  let formSubmitted = false;
  let errorMessage = '';

  // Form validation
  let errors: Record<string, string> = {};
  
  function validateForm(formData: FormData) {
    errors = {};
    
    if (!formData.get('firstName')?.toString()?.trim()) {
      errors.firstName = 'First name is required';
    }
    
    if (!formData.get('lastName')?.toString()?.trim()) {
      errors.lastName = 'Last name is required';
    }
    
    const email = formData.get('email')?.toString()?.trim();
    if (email && !isValidEmail(email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    return Object.keys(errors).length === 0;
  }
  
  function isValidEmail(email: string) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
  
  // Lead status options - must match Django LEAD_STATUS choices
  const statusOptions = [
    { value: 'assigned', name: 'Assigned', color: 'bg-blue-100 text-blue-800' },
    { value: 'in process', name: 'In Process', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'converted', name: 'Converted', color: 'bg-green-100 text-green-800' },
    { value: 'recycled', name: 'Recycled', color: 'bg-purple-100 text-purple-800' },
    { value: 'closed', name: 'Closed', color: 'bg-gray-100 text-gray-800' }
  ];

  // Lead source options - must match Django LEAD_SOURCE choices
  const sourceOptions = [
    { value: 'call', name: 'Call' },
    { value: 'email', name: 'Email' },
    { value: 'existing customer', name: 'Existing Customer' },
    { value: 'partner', name: 'Partner' },
    { value: 'public relations', name: 'Public Relations' },
    { value: 'compaign', name: 'Campaign' },
    { value: 'other', name: 'Other' }
  ];
  
  // Rating options
  const ratingOptions = [
    { value: 'Hot', name: 'Hot 🔥', color: 'text-red-600' },
    { value: 'Warm', name: 'Warm 🌡️', color: 'text-orange-600' },
    { value: 'Cold', name: 'Cold ❄️', color: 'text-blue-600' }
  ];
  
  // Industry options (expanded)
  const industryOptions = [
    { value: 'Technology', name: 'Technology' },
    { value: 'Finance', name: 'Finance' },
    { value: 'Healthcare', name: 'Healthcare' },
    { value: 'Education', name: 'Education' },
    { value: 'Manufacturing', name: 'Manufacturing' },
    { value: 'Retail', name: 'Retail' },
    { value: 'Real Estate', name: 'Real Estate' },
    { value: 'Consulting', name: 'Consulting' },
    { value: 'Marketing', name: 'Marketing' },
    { value: 'Legal', name: 'Legal' },
    { value: 'Construction', name: 'Construction' },
    { value: 'Transportation', name: 'Transportation' },
    { value: 'Hospitality', name: 'Hospitality' },
    { value: 'Entertainment', name: 'Entertainment' },
    { value: 'Other', name: 'Other' }
  ];

  // Cancel edit and go back to lead view
  function cancelEdit() {
    goto(`/app/leads/${lead.id}`);
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Header -->
  <header class="sticky top-0 z-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center space-x-4">
          <button 
            onclick={() => goto(`/app/leads/${lead.id}`)}
            class="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            <ArrowLeft class="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
          <div>
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Edit Lead</h1>
            <p class="text-sm text-gray-500 dark:text-gray-400">Editing {lead.firstName} {lead.lastName}</p>
          </div>
        </div>
      </div>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Success/Error Messages -->
    {#if formSubmitted && !errorMessage}
      <div in:fly={{ y: -20 }} class="mb-6 bg-green-50 dark:bg-green-900/50 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <div class="flex items-center">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-green-400 dark:text-green-300" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm font-medium text-green-800 dark:text-green-200">Lead updated successfully!</p>
          </div>
        </div>
      </div>
    {/if}

    {#if errorMessage}
      <div in:fly={{ y: -20 }} class="mb-6 bg-red-50 dark:bg-red-900/50 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <div class="flex items-center">
          <AlertCircle class="w-5 h-5 text-red-400 dark:text-red-300 flex-shrink-0" />
          <div class="ml-3">
            <p class="text-sm font-medium text-red-800 dark:text-red-200">{errorMessage}</p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Form -->
    <form 
      method="POST" 
      use:enhance={({ formData }) => {
        const isValid = validateForm(formData);
        if (!isValid) return;
        
        isSubmitting = true;
        return async ({ result, update }) => {
          isSubmitting = false;
          formSubmitted = true;
          
          if (result.type === 'success') {
            if (result.data?.success) {
              await update();
              setTimeout(() => {
                goto(`/app/leads/${lead.id}`);
              }, 1500);
            } else if (result.data?.error) {
              errorMessage = result.data.error as string;
            }
          } else {
            errorMessage = 'An unexpected error occurred';
          }
        };
      }}
      class="space-y-8"
    >
      <!-- Personal Information Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <div class="flex items-center space-x-2">
            <User class="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Personal Information</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label for="firstName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                First Name <span class="text-red-500 dark:text-red-400">*</span>
              </label>
              <input
                id="firstName"
                name="firstName"
                type="text"
                required
                value={lead.firstName}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all {errors.firstName ? 'border-red-500 dark:border-red-400 ring-2 ring-red-200 dark:ring-red-800' : ''}"
                placeholder="Enter first name"
              />
              {#if errors.firstName}
                <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.firstName}</p>
              {/if}
            </div>
            
            <div>
              <label for="lastName" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Last Name <span class="text-red-500 dark:text-red-400">*</span>
              </label>
              <input
                id="lastName"
                name="lastName"
                type="text"
                required
                value={lead.lastName}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all {errors.lastName ? 'border-red-500 dark:border-red-400 ring-2 ring-red-200 dark:ring-red-800' : ''}"
                placeholder="Enter last name"
              />
              {#if errors.lastName}
                <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.lastName}</p>
              {/if}
            </div>
            
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Mail class="w-4 h-4 inline mr-1" />
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={lead.email || ''}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all {errors.email ? 'border-red-500 dark:border-red-400 ring-2 ring-red-200 dark:ring-red-800' : ''}"
                placeholder="email@example.com"
              />
              {#if errors.email}
                <p class="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email}</p>
              {/if}
            </div>
            
            <div>
              <label for="phone" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Phone class="w-4 h-4 inline mr-1" />
                Phone Number
              </label>
              <input
                id="phone"
                name="phone"
                type="tel"
                value={lead.phone || ''}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all"
                placeholder="+1 (555) 123-4567"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Company Information Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <div class="flex items-center space-x-2">
            <Building class="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Company Information</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label for="company" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Company Name</label>
              <input
                id="company"
                name="company"
                type="text"
                value={lead.company || ''}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all"
                placeholder="Enter company name"
              />
            </div>
            
            <div>
              <label for="title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Job Title</label>
              <input
                id="title"
                name="title"
                type="text"
                value={lead.title || ''}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all"
                placeholder="Enter job title"
              />
            </div>
            
            <div class="md:col-span-2">
              <label for="industry" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Industry</label>
              <select
                id="industry"
                name="industry"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
              >
                <option value="">Select Industry</option>
                {#each industryOptions as option}
                  <option value={option.value} selected={lead.industry === option.value}>{option.name}</option>
                {/each}
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Lead Details Section -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <div class="flex items-center space-x-2">
            <Target class="w-5 h-5 text-gray-600 dark:text-gray-300" />
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Lead Details</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <label for="status" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Status</label>
              <select
                id="status"
                name="status"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
              >
                {#each statusOptions as option}
                  <option value={option.value} selected={lead.status === option.value}>{option.name}</option>
                {/each}
              </select>
            </div>
            
            <div>
              <label for="leadSource" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Lead Source</label>
              <select
                id="leadSource"
                name="leadSource"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
              >
                <option value="">Select Source</option>
                {#each sourceOptions as option}
                  <option value={option.value} selected={lead.leadSource === option.value}>{option.name}</option>
                {/each}
              </select>
            </div>
            
            <div>
              <label for="rating" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                <Star class="w-4 h-4 inline mr-1" />
                Rating
              </label>
              <select
                id="rating"
                name="rating"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
              >
                <option value="">Select Rating</option>
                {#each ratingOptions as option}
                  <option value={option.value} selected={lead.rating === option.value}>{option.name}</option>
                {/each}
              </select>
            </div>
          </div>
          
          <div class="mb-6">
            <div>
              <label for="ownerId" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Lead Owner</label>
              <select
                id="ownerId"
                name="ownerId"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-all"
              >
                {#each users as userOrg}
                  <option value={userOrg.user.id} selected={lead.ownerId === userOrg.user.id}>{userOrg.user.name}</option>
                {/each}
              </select>
            </div>
          </div>

          <div>
            <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description / Notes</label>
            <textarea
              id="description"
              name="description"
              rows="4"
              value={lead.description || ''}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all resize-vertical"
              placeholder="Add notes, requirements, or any additional information about this lead..."
            ></textarea>
          </div>
        </div>
      </div>
        
      <!-- Action Buttons -->
      <div class="flex justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onclick={cancelEdit}
          class="inline-flex items-center px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800 focus:ring-blue-500 dark:focus:ring-blue-400 transition-all"
        >
          <X class="w-4 h-4 mr-2" />
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          class="inline-flex items-center px-6 py-3 border border-transparent rounded-lg text-sm font-medium text-white bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-gray-800 focus:ring-blue-500 dark:focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {#if isSubmitting}
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          {:else}
            <Save class="w-4 h-4 mr-2" />
          {/if}
          Save Changes
        </button>
      </div>
    </form>
  </main>
</div>
