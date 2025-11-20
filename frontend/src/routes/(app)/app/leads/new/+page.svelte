<script>
    import { enhance } from '$app/forms';
    import { goto } from '$app/navigation';
    import { fade } from 'svelte/transition';
    import { validatePhoneNumber } from '$lib/utils/phone.js';

    import {
      User,
      Building,
      Mail,
      Phone,
      Globe,
      MapPin,
      DollarSign,
      Calendar,
      Save,
      X,
      CheckCircle,
      AlertCircle,
      Target,
      Users,
      Linkedin,
      TrendingUp
    } from '@lucide/svelte';

    /** @type {import('./$types').ActionData} */
    export let form;
    export let data;

    let showToast = false;
    let toastMessage = '';
    let toastType = 'success';
    let phoneError = '';
    let isSubmitting = false;

    /** @type {Record<string, string | string[]>} */
    let formData = {
      title: '',
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      account_name: '',
      contact_title: '',
      website: '',
      linkedin_url: '',
      status: 'assigned',
      source: '',
      industry: '',
      rating: '',
      opportunity_amount: '',
      probability: '',
      close_date: '',
      address_line: '',
      city: '',
      state: '',
      postcode: '',
      country: '',
      assigned_to: [],
      teams: [],
      last_contacted: '',
      next_follow_up: '',
      description: ''
    };

    /** @type {Record<string, string>} */
    let errors = {};

    function handleChange(event) {
      const target = event.target;
      if (!target || !('name' in target && 'value' in target)) return;
      const name = target.name;
      const value = target.value;
      if (typeof name === 'string') {
        formData[name] = value;
        if (errors[name]) errors[name] = '';
      }
    }

    function validateForm() {
      errors = {};
      let isValid = true;

      if (!formData.title?.trim()) {
        errors.title = 'Lead title is required';
        isValid = false;
      }

      if (!formData.first_name?.trim()) {
        errors.first_name = 'First name is required';
        isValid = false;
      }

      if (!formData.last_name?.trim()) {
        errors.last_name = 'Last name is required';
        isValid = false;
      }

      if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        errors.email = 'Please enter a valid email address';
        isValid = false;
      }

      if (formData.phone && formData.phone.trim().length > 0) {
        const phoneValidation = validatePhoneNumber(formData.phone);
        if (!phoneValidation.isValid) {
          errors.phone = phoneValidation.error || 'Invalid phone number';
          isValid = false;
        }
      }

      if (formData.probability && (Number(formData.probability) < 0 || Number(formData.probability) > 100)) {
        errors.probability = 'Must be between 0 and 100';
        isValid = false;
      }

      return isValid;
    }

    function resetForm() {
      formData = {
        title: '',
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        account_name: '',
        contact_title: '',
        website: '',
        linkedin_url: '',
        status: 'assigned',
        source: '',
        industry: '',
        rating: '',
        opportunity_amount: '',
        probability: '',
        close_date: '',
        address_line: '',
        city: '',
        state: '',
        postcode: '',
        country: '',
        assigned_to: [],
        teams: [],
        last_contacted: '',
        next_follow_up: '',
        description: ''
      };
      errors = {};
    }

    function showNotification(message, type = 'success') {
      toastMessage = message;
      toastType = type;
      showToast = true;
      setTimeout(() => showToast = false, 5000);
    }

    function validatePhone() {
      if (!formData.phone.trim()) {
        phoneError = '';
        return;
      }
      const validation = validatePhoneNumber(formData.phone);
      phoneError = validation.isValid ? '' : (validation.error || 'Invalid phone number');
    }
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
  {#if showToast}
    <div class="fixed top-4 right-4 z-50" in:fade>
      <div class="flex items-center p-4 rounded-lg shadow-lg {toastType === 'success' ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800'}">
        <div class="flex-shrink-0">
          {#if toastType === 'success'}
            <CheckCircle class="w-5 h-5 text-green-400" />
          {:else}
            <AlertCircle class="w-5 h-5 text-red-400" />
          {/if}
        </div>
        <div class="ml-3">
          <p class="text-sm font-medium {toastType === 'success' ? 'text-green-800 dark:text-green-200' : 'text-red-800 dark:text-red-200'}">{toastMessage}</p>
        </div>
        <button onclick={() => showToast = false} class="ml-auto -mx-1.5 -my-1.5 rounded-lg p-1.5 {toastType === 'success' ? 'text-green-500 hover:bg-green-100 dark:hover:bg-green-800/30' : 'text-red-500 hover:bg-red-100 dark:hover:bg-red-800/30'}">
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>
  {/if}

  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <Target class="w-6 h-6 text-blue-600 dark:text-blue-400" />
        Create Lead
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mt-1">Capture new sales opportunity</p>
    </div>

    {#if form?.error}
      <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
        <div class="flex items-center">
          <AlertCircle class="w-5 h-5 text-red-400 mr-2" />
          <span class="text-red-700 dark:text-red-300">{form.error}</span>
        </div>
      </div>
    {/if}

    <form method="POST" use:enhance={({ cancel }) => {
      if (!validateForm()) {
        cancel();
        return;
      }
      isSubmitting = true;
      return async ({ result }) => {
        isSubmitting = false;
        if (result.type === 'success') {
          showNotification('Lead created successfully!', 'success');
          resetForm();
          setTimeout(() => goto('/app/leads/open'), 1500);
        } else if (result.type === 'failure') {
          const errorMessage = result.data?.error || 'Failed to create lead';
          showNotification(errorMessage, 'error');
        }
      };
    }} class="space-y-6">

      <!-- Contact Information -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <User class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Contact Information
          </h2>
        </div>
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label for="title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Lead Title *</label>
            <input id="title" name="title" type="text" bind:value={formData.title} oninput={handleChange} placeholder="e.g., Enterprise Software Deal" required
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white {errors.title ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:ring-2 focus:ring-blue-500" />
            {#if errors.title}<p class="text-red-500 text-sm mt-1">{errors.title}</p>{/if}
          </div>

          <div>
            <label for="first_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">First Name *</label>
            <input id="first_name" name="first_name" type="text" bind:value={formData.first_name} oninput={handleChange} required
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white {errors.first_name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:ring-2 focus:ring-blue-500" />
            {#if errors.first_name}<p class="text-red-500 text-sm mt-1">{errors.first_name}</p>{/if}
          </div>

          <div>
            <label for="last_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Last Name *</label>
            <input id="last_name" name="last_name" type="text" bind:value={formData.last_name} oninput={handleChange} required
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white {errors.last_name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:ring-2 focus:ring-blue-500" />
            {#if errors.last_name}<p class="text-red-500 text-sm mt-1">{errors.last_name}</p>{/if}
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <Mail class="w-4 h-4 inline mr-1" />Email
            </label>
            <input id="email" name="email" type="email" bind:value={formData.email} oninput={handleChange}
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white {errors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:ring-2 focus:ring-blue-500" />
            {#if errors.email}<p class="text-red-500 text-sm mt-1">{errors.email}</p>{/if}
          </div>

          <div>
            <label for="phone" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <Phone class="w-4 h-4 inline mr-1" />Phone
            </label>
            <input id="phone" name="phone" type="tel" bind:value={formData.phone} oninput={handleChange} onblur={validatePhone}
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white {errors.phone || phoneError ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:ring-2 focus:ring-blue-500" />
            {#if errors.phone || phoneError}<p class="text-red-500 text-sm mt-1">{errors.phone || phoneError}</p>{/if}
          </div>

          <div>
            <label for="account_name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <Building class="w-4 h-4 inline mr-1" />Company
            </label>
            <input id="account_name" name="account_name" type="text" bind:value={formData.account_name} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="contact_title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Job Title</label>
            <input id="contact_title" name="contact_title" type="text" bind:value={formData.contact_title} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="website" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <Globe class="w-4 h-4 inline mr-1" />Website
            </label>
            <input id="website" name="website" type="url" bind:value={formData.website} oninput={handleChange} placeholder="https://"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="linkedin_url" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <Linkedin class="w-4 h-4 inline mr-1" />LinkedIn
            </label>
            <input id="linkedin_url" name="linkedin_url" type="url" bind:value={formData.linkedin_url} oninput={handleChange} placeholder="https://linkedin.com/in/"
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
      </div>

      <!-- Sales Pipeline -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <TrendingUp class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Sales Pipeline
          </h2>
        </div>
        <div class="p-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label for="status" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <select id="status" name="status" bind:value={formData.status} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500">
              {#each data.data.statuses as [value, label]}
                <option value={value}>{label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label for="source" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Source</label>
            <select id="source" name="source" bind:value={formData.source} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500">
              <option value="">Select source</option>
              {#each data.data.sources as [value, label]}
                <option value={value}>{label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label for="industry" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Industry</label>
            <select id="industry" name="industry" bind:value={formData.industry} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500">
              <option value="">Select industry</option>
              {#each data.data.industries as [value, label]}
                <option value={value}>{label}</option>
              {/each}
            </select>
          </div>

          <div>
            <label for="rating" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rating</label>
            <select id="rating" name="rating" bind:value={formData.rating} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500">
              <option value="">Select rating</option>
              <option value="HOT">🔥 Hot</option>
              <option value="WARM">🟡 Warm</option>
              <option value="COLD">🔵 Cold</option>
            </select>
          </div>

          <div>
            <label for="opportunity_amount" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <DollarSign class="w-4 h-4 inline mr-1" />Deal Value
            </label>
            <input id="opportunity_amount" name="opportunity_amount" type="number" min="0" step="0.01" bind:value={formData.opportunity_amount} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="probability" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Win Probability %</label>
            <input id="probability" name="probability" type="number" min="0" max="100" bind:value={formData.probability} oninput={handleChange}
              class="w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white {errors.probability ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:ring-2 focus:ring-blue-500" />
            {#if errors.probability}<p class="text-red-500 text-sm mt-1">{errors.probability}</p>{/if}
          </div>

          <div>
            <label for="close_date" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              <Calendar class="w-4 h-4 inline mr-1" />Expected Close
            </label>
            <input id="close_date" name="close_date" type="date" bind:value={formData.close_date} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
      </div>

      <!-- Assignment -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Users class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Assignment
          </h2>
        </div>
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label for="assigned_to" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Assigned To</label>
            <select id="assigned_to" name="assigned_to" multiple bind:value={formData.assigned_to} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 min-h-[80px]">
              {#each data.data.users as user}
                <option value={user.id}>{user.name}</option>
              {/each}
            </select>
            <p class="text-xs text-gray-500 mt-1">Ctrl/Cmd + click to select multiple</p>
          </div>

          <div>
            <label for="teams" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Teams</label>
            <select id="teams" name="teams" multiple bind:value={formData.teams} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 min-h-[80px]">
              {#each data.data.teams as team}
                <option value={team.id}>{team.name}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>

      <!-- Address -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <MapPin class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Address
          </h2>
        </div>
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="md:col-span-2">
            <label for="address_line" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Address</label>
            <input id="address_line" name="address_line" type="text" bind:value={formData.address_line} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="city" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">City</label>
            <input id="city" name="city" type="text" bind:value={formData.city} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="state" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">State</label>
            <input id="state" name="state" type="text" bind:value={formData.state} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="postcode" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Postal Code</label>
            <input id="postcode" name="postcode" type="text" bind:value={formData.postcode} oninput={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label for="country" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Country</label>
            <select id="country" name="country" bind:value={formData.country} onchange={handleChange}
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500">
              <option value="">Select country</option>
              {#each data.data.countries as [value, label]}
                <option value={value}>{label}</option>
              {/each}
            </select>
          </div>
        </div>
      </div>

      <!-- Activity & Notes -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Calendar class="w-5 h-5 text-blue-600 dark:text-blue-400" />
            Activity & Notes
          </h2>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="last_contacted" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Last Contacted</label>
              <input id="last_contacted" name="last_contacted" type="date" bind:value={formData.last_contacted} oninput={handleChange}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
            </div>

            <div>
              <label for="next_follow_up" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Next Follow-up</label>
              <input id="next_follow_up" name="next_follow_up" type="date" bind:value={formData.next_follow_up} oninput={handleChange}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div>
            <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
            <textarea id="description" name="description" rows="3" bind:value={formData.description} oninput={handleChange} placeholder="Additional notes about this lead..."
              class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 resize-vertical"></textarea>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3">
        <button type="button" onclick={() => goto('/app/leads/')} disabled={isSubmitting}
          class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 flex items-center gap-2">
          <X class="w-4 h-4" />
          Cancel
        </button>
        <button type="submit" disabled={isSubmitting}
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
          {#if isSubmitting}
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            Creating...
          {:else}
            <Save class="w-4 h-4" />
            Create Lead
          {/if}
        </button>
      </div>
    </form>
  </div>
</div>
