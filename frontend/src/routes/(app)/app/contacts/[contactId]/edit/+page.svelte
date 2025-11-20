<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { invalidateAll } from '$app/navigation';
  import { User, Mail, Phone, Building, MapPin, FileText, Star, Save, X, ArrowLeft } from '@lucide/svelte';
  import { validatePhoneNumber } from '$lib/utils/phone.js';
  
  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  const { contact } = data;
  let account = data.account;
  let isPrimary = data.isPrimary;
  let role = data.role;

  let firstName = $state(contact?.firstName || '');
  let lastName = $state(contact?.lastName || '');
  let email = $state(contact?.email || '');
  let phone = $state(contact?.phone || '');
  let title = $state(contact?.title || '');
  let department = $state(contact?.department || '');
  let street = $state(contact?.street || '');
  let city = $state(contact?.city || '');
  let stateField = $state(contact?.state || ''); // Renamed to avoid conflict with Svelte's $state
  let postalCode = $state(contact?.postalCode || '');
  let country = $state(contact?.country || '');
  let description = $state(contact?.description || '');
  let submitting = $state(false);
  let errorMsg = $state('');
  let phoneError = $state('');

  // Validate phone number on input
  function validatePhone() {
    if (!phone.trim()) {
      phoneError = '';
      return;
    }
    
    const validation = validatePhoneNumber(phone);
    if (!validation.isValid) {
      phoneError = validation.error || 'Invalid phone number';
    } else {
      phoneError = '';
    }
  }

  /** @param {Event} e */
  async function handleSubmit(e) {
    e.preventDefault();
    submitting = true;
    errorMsg = '';
    const formData = new FormData();
    formData.append('firstName', firstName);
    formData.append('lastName', lastName);
    formData.append('email', email);
    formData.append('phone', phone);
    formData.append('title', title);
    formData.append('department', department);
    formData.append('street', street);
    formData.append('city', city);
    formData.append('state', stateField);
    formData.append('postalCode', postalCode);
    formData.append('country', country);
    formData.append('description', description);
    // Remove isPrimary and role from form submission
    
    const res = await fetch('', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      await invalidateAll();
      goto(`/app/contacts/${contact?.id}`);
    } else {
      const data = await res.json();
      errorMsg = data?.message || 'Failed to update contact.';
    }
    submitting = false;
  }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-6">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center gap-4 mb-4">
        <button 
          onclick={() => goto(`/app/contacts/${contact?.id}`)}
          class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <ArrowLeft class="w-5 h-5" />
        </button>
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Contact</h1>
          <p class="text-gray-600 dark:text-gray-400 mt-1">Update contact information and details</p>
        </div>
      </div>
    </div>

    <!-- Form -->
    <form onsubmit={handleSubmit} class="space-y-8">
      <!-- Basic Information Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <User class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Basic Information</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="firstName">
                First Name *
              </label>
              <input 
                id="firstName" 
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                bind:value={firstName} 
                required 
                placeholder="Enter first name"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="lastName">
                Last Name *
              </label>
              <input 
                id="lastName" 
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                bind:value={lastName} 
                required 
                placeholder="Enter last name"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="title">
                Job Title
              </label>
              <input 
                id="title" 
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                bind:value={title} 
                placeholder="e.g. Marketing Director"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="department">
                Department
              </label>
              <input 
                id="department" 
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                bind:value={department} 
                placeholder="e.g. Marketing"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Contact Information Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <Mail class="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Contact Information</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="email">
                Email Address
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail class="w-5 h-5 text-gray-400" />
                </div>
                <input 
                  id="email" 
                  type="email"
                  class="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                  bind:value={email} 
                  placeholder="contact@company.com"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="phone">
                Phone Number
              </label>
              <div class="relative">
                <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Phone class="w-5 h-5 text-gray-400" />
                </div>
                <input 
                  id="phone" 
                  type="tel"
                  class="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                  bind:value={phone} 
                  placeholder="+1 (555) 123-4567"
                  oninput={validatePhone}
                />
              </div>
              {#if phoneError}
                <p class="mt-2 text-sm text-red-600 dark:text-red-400">{phoneError}</p>
              {/if}
            </div>
          </div>
        </div>
      </div>

      <!-- Address Information Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <MapPin class="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Address Information</h2>
          </div>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-1 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="street">
                Street Address
              </label>
              <input 
                id="street" 
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                bind:value={street} 
                placeholder="123 Main Street"
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="city">
                  City
                </label>
                <input 
                  id="city" 
                  class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                  bind:value={city} 
                  placeholder="San Francisco"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="state">
                  State/Province
                </label>
                <input 
                  id="state" 
                  class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                  bind:value={stateField} 
                  placeholder="CA"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="postalCode">
                  Postal Code
                </label>
                <input 
                  id="postalCode" 
                  class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                  bind:value={postalCode} 
                  placeholder="94102"
                />
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="country">
                Country
              </label>
              <input 
                id="country" 
                class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
                bind:value={country} 
                placeholder="United States"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Account Relationship Card -->
      {#if account}
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center gap-3">
              <div class="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <Building class="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Account Relationship</h2>
            </div>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Account</div>
                <div class="text-gray-900 dark:text-white font-medium">{account.name}</div>
              </div>
              {#if role}
                <div>
                  <div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Role</div>
                  <div class="text-gray-900 dark:text-white">{role}</div>
                </div>
              {/if}
              {#if isPrimary}
                <div class="md:col-span-2">
                  <div class="flex items-center gap-2 text-sm">
                    <Star class="w-4 h-4 text-yellow-500" />
                    <span class="text-gray-700 dark:text-gray-300 font-medium">Primary Contact</span>
                  </div>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}

      <!-- Additional Information Card -->
      <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
              <FileText class="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Additional Information</h2>
          </div>
        </div>
        <div class="p-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" for="description">
              Notes & Description
            </label>
            <textarea 
              id="description" 
              class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400" 
              rows="4" 
              bind:value={description}
              placeholder="Add any additional notes or important information about this contact..."
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      {#if errorMsg}
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div class="flex">
            <div class="flex-shrink-0">
              <X class="w-5 h-5 text-red-400" />
            </div>
            <div class="ml-3">
              <p class="text-sm text-red-800 dark:text-red-200">{errorMsg}</p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Action Buttons -->
      <div class="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onclick={() => goto(`/app/contacts/${contact?.id}`)}
          class="px-6 py-3 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          class="px-6 py-3 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 dark:bg-blue-600 dark:hover:bg-blue-700 dark:disabled:bg-blue-500 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors flex items-center gap-2"
        >
          {#if submitting}
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            Saving...
          {:else}
            <Save class="w-4 h-4" />
            Save Changes
          {/if}
        </button>
      </div>
    </form>
  </div>
</div>
