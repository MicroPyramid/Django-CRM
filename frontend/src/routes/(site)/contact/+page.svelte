<!-- contact page -->
<script>
  import { onMount } from 'svelte';
  import { fly } from 'svelte/transition';
  import { enhance } from '$app/forms';
  import { 
    MessageCircle, 
    Mail, 
    Clock,
    Send,
    Check,
    Star,
    HeadphonesIcon,
    Settings,
    Zap,
    Code,
    Server,
    Users,
    Shield,
    AlertCircle,
    Github,
    Download
  } from '@lucide/svelte';

  // Form data - now handled by server
  let formData = {
    name: '',
    email: '',
    serviceType: '',
    message: ''
  };

  // Form state
  let isSubmitting = false;
  let mounted = false;

  // Get form data from server response
  export let form;

  // Update formData if server returns validation errors
  $: if (form && !form.success) {
    formData = {
      name: form.name || '',
      email: form.email || '',
      serviceType: form.serviceType || '',
      message: form.message || ''
    };
  }

  // Reset form on successful submission
  $: if (form?.success) {
    formData = {
      name: '',
      email: '',
      serviceType: '',
      message: ''
    };
  }

  onMount(() => {
    mounted = true;
  });
</script>

<svelte:head>
  <title>Contact BottleCRM | Free CRM & Professional Services</title>
  <meta name="description" content="Contact BottleCRM for free CRM software, setup, hosting, customization, and expert support. Get started or request professional CRM services today." />
  <meta name="keywords" content="free crm, open source crm, bottlecrm, crm setup, crm hosting, crm customization, crm support, crm development, crm training" />
  <link rel="canonical" href="https://bottlecrm.io/contact" />

  <!-- Open Graph -->
  <meta property="og:title" content="Contact BottleCRM | Free CRM & Professional Services" />
  <meta property="og:description" content="Contact BottleCRM for free CRM software, setup, hosting, customization, and expert support. Get started or request professional CRM services today." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/contact" />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Contact BottleCRM | Free CRM & Professional Services" />
  <meta name="twitter:description" content="Contact BottleCRM for free CRM software, setup, hosting, customization, and expert support. Get started or request professional CRM services today." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Organization & Contact Schema -->
  {@html `
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "BottleCRM",
      "url": "https://bottlecrm.io",
      "logo": "https://bottlecrm.io/logo.png",
      "contactPoint": [{
        "@type": "ContactPoint",
        "email": "bottlecrm@micropyramid.com",
        "contactType": "customer support",
        "areaServed": "Global",
        "availableLanguage": ["English"]
      }]
    }
    </script>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "ContactPage",
      "name": "Contact BottleCRM",
      "description": "Contact BottleCRM for free CRM software, setup, hosting, customization, and expert support.",
      "url": "https://bottlecrm.io/contact"
    }
    </script>
  `}
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-green-500 text-white text-sm font-semibold mb-6">
        <MessageCircle class="w-4 h-4 mr-2" />
        Free Software • Professional Support Available
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold mb-6">
        Get Expert Help with <span class="text-green-300">BottleCRM</span>
      </h1>
      
      <p class="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
        The software is free forever. Get professional setup, hosting, customization, and training services to accelerate your CRM implementation and maximize your ROI.
      </p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <MessageCircle class="w-8 h-8 text-green-300 mx-auto mb-2" />
          <div class="text-sm font-medium">Free Community Support</div>
          <div class="text-xs text-blue-200">GitHub</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <HeadphonesIcon class="w-8 h-8 text-yellow-300 mx-auto mb-2" />
          <div class="text-sm font-medium">Professional Setup</div>
          <div class="text-xs text-blue-200">Starting at $197</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <Code class="w-8 h-8 text-purple-300 mx-auto mb-2" />
          <div class="text-sm font-medium">Custom Development</div>
          <div class="text-xs text-blue-200">Bespoke solutions</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Quick Contact Options -->
<section class="py-16 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <h2 class="text-3xl font-extrabold text-gray-900 mb-4">
        Choose Your Support Level
      </h2>
      <p class="text-xl text-gray-600">
        From free community help to enterprise-grade professional services
      </p>
    </div>

    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl border border-gray-100 relative">
          <div class="text-center mb-6">
            <div class="mb-4">
              <MessageCircle class="w-10 h-10 text-blue-600 mx-auto" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Free Community Support</h3>
            <p class="text-gray-600 text-sm mb-3">Get help from our community and documentation</p>
            <div class="text-2xl font-bold text-blue-600">Free</div>
          </div>
          
          <ul class="space-y-2 mb-6">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Community forum access
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Documentation & guides
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              GitHub issue support
            </li>
          </ul>
          
          <button 
            onclick={() => formData.serviceType = 'free-support'}
            class="w-full py-2 px-4 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium transition-colors duration-200">
            Select This Service
          </button>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 100 }}"
             class="bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl border border-gray-100 relative ring-2 ring-blue-500">
          
          <div class="absolute -top-3 left-1/2 transform -translate-x-1/2">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold text-white bg-blue-500">
              <Star class="w-3 h-3 mr-1" />
              Most Popular
            </span>
          </div>
          
          <div class="text-center mb-6">
            <div class="mb-4">
              <HeadphonesIcon class="w-10 h-10 text-blue-600 mx-auto" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Professional Setup & Installation</h3>
            <p class="text-gray-600 text-sm mb-3">Expert installation, configuration, and basic customization</p>
            <div class="text-2xl font-bold text-blue-600">$197 one-time</div>
          </div>
          
          <ul class="space-y-2 mb-6">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Professional installation
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              SSL & domain setup
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Basic customization
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              1-month support
            </li>
          </ul>
          
          <button 
            onclick={() => formData.serviceType = 'professional-setup'}
            class="w-full py-2 px-4 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-medium transition-colors duration-200">
            Select This Service
          </button>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 200 }}"
             class="bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl border border-gray-100 relative">
          <div class="text-center mb-6">
            <div class="mb-4">
              <Settings class="w-10 h-10 text-blue-600 mx-auto" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Enterprise Setup & Customization</h3>
            <p class="text-gray-600 text-sm mb-3">Complete enterprise deployment with advanced features</p>
            <div class="text-2xl font-bold text-blue-600">$497 one-time</div>
          </div>
          
          <ul class="space-y-2 mb-6">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Advanced customization
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Third-party integrations
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Team training
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              3-month support
            </li>
          </ul>
          
          <button 
            onclick={() => formData.serviceType = 'enterprise-setup'}
            class="w-full py-2 px-4 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium transition-colors duration-200">
            Select This Service
          </button>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl border border-gray-100 relative">
          <div class="text-center mb-6">
            <div class="mb-4">
              <Code class="w-10 h-10 text-blue-600 mx-auto" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Custom Development</h3>
            <p class="text-gray-600 text-sm mb-3">Bespoke features and integrations for your specific needs</p>
            <div class="text-2xl font-bold text-blue-600">Custom quote</div>
          </div>
          
          <ul class="space-y-2 mb-6">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Custom feature development
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              API integrations
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Workflow automation
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Ongoing maintenance
            </li>
          </ul>
          
          <button 
            onclick={() => formData.serviceType = 'custom-development'}
            class="w-full py-2 px-4 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium transition-colors duration-200">
            Select This Service
          </button>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 400 }}"
             class="bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl border border-gray-100 relative">
          <div class="text-center mb-6">
            <div class="mb-4">
              <Server class="w-10 h-10 text-blue-600 mx-auto" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Managed Hosting & Maintenance</h3>
            <p class="text-gray-600 text-sm mb-3">We handle hosting, updates, backups, and maintenance</p>
            <div class="text-2xl font-bold text-blue-600">$97-297/month</div>
          </div>
          
          <ul class="space-y-2 mb-6">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Managed hosting
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Automatic updates
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Daily backups
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              24/7 monitoring
            </li>
          </ul>
          
          <button 
            onclick={() => formData.serviceType = 'hosting-management'}
            class="w-full py-2 px-4 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium transition-colors duration-200">
            Select This Service
          </button>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 500 }}"
             class="bg-white rounded-2xl shadow-lg p-6 transition-all duration-300 hover:shadow-xl border border-gray-100 relative">
          <div class="text-center mb-6">
            <div class="mb-4">
              <Users class="w-10 h-10 text-blue-600 mx-auto" />
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Training & Consultation</h3>
            <p class="text-gray-600 text-sm mb-3">Team training and strategic CRM consultation</p>
            <div class="text-2xl font-bold text-blue-600">$97-197/hour</div>
          </div>
          
          <ul class="space-y-2 mb-6">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Team training sessions
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Best practices consultation
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              CRM strategy planning
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Ongoing support
            </li>
          </ul>
          
          <button 
            onclick={() => formData.serviceType = 'training-consultation'}
            class="w-full py-2 px-4 rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium transition-colors duration-200">
            Select This Service
          </button>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Contact Form Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid gap-12 lg:grid-cols-2">
      <!-- Form -->
      <div>
        <h2 class="text-3xl font-extrabold text-gray-900 mb-4">
          Get in Touch
        </h2>
        <p class="text-gray-600 mb-8">
          Tell us about your project and we'll get back to you within 24 hours.
        </p>
        
        {#if form?.success}
          <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
            <div class="flex items-center">
              <Check class="w-6 h-6 text-green-500 mr-3" />
              <div>
                <h3 class="text-lg font-semibold text-green-800">Message Sent Successfully!</h3>
                <p class="text-green-700 mt-1">{form.message}</p>
              </div>
            </div>
          </div>
        {:else if form?.error}
          <div class="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
            <div class="flex items-center">
              <AlertCircle class="w-6 h-6 text-red-500 mr-3" />
              <div>
                <h3 class="text-lg font-semibold text-red-800">Error</h3>
                <p class="text-red-700 mt-1">{form.error}</p>
              </div>
            </div>
          </div>
        {/if}
        
        <form method="POST" 
              use:enhance={() => {
                isSubmitting = true;
                return async ({ update }) => {
                  await update();
                  isSubmitting = false;
                };
              }}
              class="space-y-6">
          <!-- Basic Information -->
          <div class="grid gap-6 md:grid-cols-2">
            <div>
              <label for="name" class="block text-sm font-medium text-gray-700 mb-2">
                Name *
              </label>
              <input type="text" 
                     id="name" 
                     name="name"
                     bind:value={formData.name}
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 {form?.errors?.name ? 'border-red-500' : ''}"
                     placeholder="John Doe">
              {#if form?.errors?.name}
                <p class="text-red-500 text-sm mt-1">{form.errors.name}</p>
              {/if}
            </div>
            
            <div>
              <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
                Email *
              </label>
              <input type="email" 
                     id="email" 
                     name="email"
                     bind:value={formData.email}
                     class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 {form?.errors?.email ? 'border-red-500' : ''}"
                     placeholder="john@company.com">
              {#if form?.errors?.email}
                <p class="text-red-500 text-sm mt-1">{form.errors.email}</p>
              {/if}
            </div>
          </div>
          
          <!-- Service Type -->
          <div>
            <fieldset>
              <legend class="block text-sm font-medium text-gray-700 mb-2">
                What can we help you with? *
              </legend>
            <div class="grid gap-3 md:grid-cols-2">
              <label class="flex items-start p-4 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 {formData.serviceType === 'professional-setup' ? 'border-blue-500 bg-blue-50' : ''}">
                <input type="radio" name="serviceType" bind:group={formData.serviceType} value="professional-setup" class="mt-1 mr-3">
                <div>
                  <div class="font-medium text-gray-900 text-sm">Professional Setup ($197)</div>
                  <div class="text-xs text-gray-600">Expert installation & setup</div>
                </div>
              </label>
              
              <label class="flex items-start p-4 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 {formData.serviceType === 'custom-development' ? 'border-blue-500 bg-blue-50' : ''}">
                <input type="radio" name="serviceType" bind:group={formData.serviceType} value="custom-development" class="mt-1 mr-3">
                <div>
                  <div class="font-medium text-gray-900 text-sm">Custom Development</div>
                  <div class="text-xs text-gray-600">Bespoke features & integrations</div>
                </div>
              </label>
              
              <label class="flex items-start p-4 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 {formData.serviceType === 'hosting-management' ? 'border-blue-500 bg-blue-50' : ''}">
                <input type="radio" name="serviceType" bind:group={formData.serviceType} value="hosting-management" class="mt-1 mr-3">
                <div>
                  <div class="font-medium text-gray-900 text-sm">Managed Hosting</div>
                  <div class="text-xs text-gray-600">We handle hosting & maintenance</div>
                </div>
              </label>
              
              <label class="flex items-start p-4 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 {formData.serviceType === 'other' ? 'border-blue-500 bg-blue-50' : ''}">
                <input type="radio" name="serviceType" bind:group={formData.serviceType} value="other" class="mt-1 mr-3">
                <div>
                  <div class="font-medium text-gray-900 text-sm">Other / Not Sure</div>
                  <div class="text-xs text-gray-600">Let's discuss your needs</div>
                </div>
              </label>
            </div>
            {#if form?.errors?.serviceType}
              <p class="text-red-500 text-sm mt-1">{form.errors.serviceType}</p>
            {/if}
            </fieldset>
          </div>
          
          <div>
            <label for="message" class="block text-sm font-medium text-gray-700 mb-2">
              Tell us about your project *
            </label>
            <textarea id="message" 
                      name="message"
                      rows="5" 
                      bind:value={formData.message}
                      class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 {form?.errors?.message ? 'border-red-500' : ''}"
                      placeholder="Describe your project, requirements, timeline, team size, or any questions you have..."></textarea>
            {#if form?.errors?.message}
              <p class="text-red-500 text-sm mt-1">{form.errors.message}</p>
            {/if}
          </div>
          
          <button type="submit" disabled={isSubmitting}
                  class="w-full inline-flex items-center justify-center px-6 py-4 text-lg font-semibold rounded-lg text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200">
            {#if isSubmitting}
              <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
              Sending Message...
            {:else}
              <Send class="w-5 h-5 mr-2" />
              Send Message
            {/if}
          </button>
          
          <p class="text-sm text-gray-500 text-center">
            We typically respond within 24 hours during business days
          </p>
        </form>
      </div>
      
      <!-- Contact Information -->
      <div class="lg:pl-8">
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 mb-8">
          <h3 class="text-2xl font-bold text-gray-900 mb-6">
            Contact Information
          </h3>
          
          <div class="space-y-4">
            <div class="flex items-start">
              <Mail class="w-6 h-6 text-blue-600 mr-4 mt-1" />
              <div>
                <div class="font-semibold text-gray-900">Email</div>
                <div class="text-gray-600">bottlecrm@micropyramid.com</div>
                <div class="text-sm text-gray-500">Response within 24 hours</div>
              </div>
            </div>
            
            
            <div class="flex items-start">
              <Github class="w-6 h-6 text-blue-600 mr-4 mt-1" />
              <div>
                <div class="font-semibold text-gray-900">GitHub Issues</div>
                <div class="text-gray-600">Bug reports & feature requests</div>
                <a href="https://github.com/MicroPyramid/opensource-startup-crm/issues" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-700 text-sm">Open an issue →</a>
              </div>
            </div>
            
            <div class="flex items-start">
              <Clock class="w-6 h-6 text-blue-600 mr-4 mt-1" />
              <div>
                <div class="font-semibold text-gray-900">Business Hours</div>
                <div class="text-gray-600">Monday - Friday</div>
                <div class="text-sm text-gray-500">9 AM - 6 PM IST</div>
              </div>
            </div>
          </div>
        </div>

        <!-- FAQ -->
        <div>
          <h4 class="text-lg font-bold text-gray-900 mb-4">Frequently Asked Questions</h4>
          <div class="space-y-3">
            <details class="bg-white rounded-lg border border-gray-200 p-4">
              <summary class="font-medium text-gray-900 cursor-pointer">How quickly can you set up BottleCRM for my business?</summary>
              <p class="text-gray-600 text-sm mt-2 leading-relaxed">Basic setup can be completed within 24-48 hours. Professional Setup typically takes 3-5 business days, while Enterprise Setup with custom features may take 1-2 weeks depending on complexity.</p>
            </details>
            <details class="bg-white rounded-lg border border-gray-200 p-4">
              <summary class="font-medium text-gray-900 cursor-pointer">Do you provide training for my team?</summary>
              <p class="text-gray-600 text-sm mt-2 leading-relaxed">Yes! Training is included in our Professional and Enterprise Setup packages. We also offer dedicated training sessions at $97-197/hour for teams who need additional support.</p>
            </details>
            <details class="bg-white rounded-lg border border-gray-200 p-4">
              <summary class="font-medium text-gray-900 cursor-pointer">Can you migrate data from our current CRM?</summary>
              <p class="text-gray-600 text-sm mt-2 leading-relaxed">We're currently developing data migration scripts for popular CRM platforms including Salesforce, HubSpot, and Pipedrive. These tools will be available soon. In the meantime, we can help you manually export/import your data and provide guidance on the best migration approach for your specific needs.</p>
            </details>
            <details class="bg-white rounded-lg border border-gray-200 p-4">
              <summary class="font-medium text-gray-900 cursor-pointer">What if I need ongoing support after setup?</summary>
              <p class="text-gray-600 text-sm mt-2 leading-relaxed">We offer various ongoing support options from monthly managed hosting ($97-297/month) to hourly consultation ($97-197/hour). You can also access our free community support anytime.</p>
            </details>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Service Benefits -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Why Choose Our Professional Services?
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        While BottleCRM is free, our professional services save you time and ensure optimal implementation.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
      <div class="text-center">
        <div class="bg-blue-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Zap class="w-8 h-8 text-blue-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Faster Implementation</h3>
        <p class="text-gray-600">Get up and running in days, not weeks. Our experts handle the technical setup.</p>
      </div>
      
      <div class="text-center">
        <div class="bg-green-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Shield class="w-8 h-8 text-green-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Best Practices</h3>
        <p class="text-gray-600">Benefit from our experience with dozens of CRM implementations.</p>
      </div>
      
      <div class="text-center">
        <div class="bg-purple-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <Users class="w-8 h-8 text-purple-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Team Training</h3>
        <p class="text-gray-600">Ensure your team knows how to use BottleCRM effectively from day one.</p>
      </div>
      
      <div class="text-center">
        <div class="bg-yellow-100 rounded-full p-4 w-16 h-16 mx-auto mb-4 flex items-center justify-center">
          <HeadphonesIcon class="w-8 h-8 text-yellow-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Ongoing Support</h3>
        <p class="text-gray-600">Get priority support when you need help or have questions.</p>
      </div>
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Get Started?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      The software is free forever. Professional services help you implement it faster and more effectively.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="https://github.com/MicroPyramid/opensource-startup-crm" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Download class="w-6 h-6 mr-3" />
        Try BottleCRM Free
      </a>
      <button onclick={() => document.querySelector('form')?.scrollIntoView({behavior: 'smooth'})} class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Send class="w-6 h-6 mr-3" />
        Get Professional Help
      </button>
    </div>
    
    
  </div>
</section>
