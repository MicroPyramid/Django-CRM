<script>
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { 
    ChevronDown,
    HelpCircle,
    DollarSign,
    Settings,
    HeadphonesIcon,
    Briefcase,
    Download,
    Github,
    MessageCircle,
    Zap,
    ExternalLink
  } from '@lucide/svelte';

  /** @type {string|null} */
  let activeFaq = null;

  /**
   * @param {string} faqId
   */
  function toggleFaq(faqId) {
    activeFaq = activeFaq === faqId ? null : faqId;
  }
</script>

<svelte:head>
  <title>BottleCRM FAQ | Free Open Source CRM for Startups & SMBs</title>
  <meta name="description" content="Answers to common questions about BottleCRM, the free open-source CRM for startups and small businesses. Learn about features, pricing, support, and self-hosting." />
  <meta name="keywords" content="free crm, open source crm, bottlecrm, crm faq, self hosted crm, startup crm, small business crm, crm support, crm pricing, crm features" />
  <link rel="canonical" href="https://bottlecrm.io/faq" />
  <meta name="robots" content="index, follow" />

  <!-- Open Graph -->
  <meta property="og:title" content="BottleCRM FAQ | Free Open Source CRM for Startups & SMBs" />
  <meta property="og:description" content="Find answers to your questions about BottleCRM, the free open-source CRM for startups and small businesses." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/faq" />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="BottleCRM FAQ | Free Open Source CRM for Startups & SMBs" />
  <meta name="twitter:description" content="Answers to common questions about BottleCRM, the free open-source CRM for startups and small businesses." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image.png" />

  <!-- FAQPage Schema.org Structured Data -->
  {@html `
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "Is BottleCRM really free?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Yes, BottleCRM is 100% free and open-source with no user limits or hidden fees."
          }
        },
        {
          "@type": "Question",
          "name": "Can I self-host BottleCRM?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Absolutely! You can deploy BottleCRM on your own server or cloud for full data control."
          }
        },
        {
          "@type": "Question",
          "name": "What features are included in BottleCRM?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "All core CRM features: contact management, sales pipeline, tasks, analytics, and more are included for free."
          }
        },
        {
          "@type": "Question",
          "name": "How does BottleCRM make money?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "We offer optional paid services like setup, support, and custom development. The software itself is always free."
          }
        }
      ]
    }
    </script>
  `}
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <div class="max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <HelpCircle class="w-4 h-4 mr-2" />
        Frequently Asked Questions
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold mb-6">
        Everything About <span class="text-yellow-300">BottleCRM</span>
      </h1>
      
      <p class="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
        Get answers to common questions about our free, open-source CRM software. Learn about pricing, features, technical requirements, and how to get started.
      </p>
    </div>
  </div>
</section>

<!-- FAQ Categories Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Category Overview -->
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Browse FAQ Categories
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Find answers organized by topic to help you get started with BottleCRM.
      </p>
    </div>

    <!-- Category Cards -->
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-16">
      <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="flex items-center mb-4">
          <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
            <HelpCircle class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">General Questions</h3>
        </div>
        <p class="text-gray-600 mb-4">5 questions</p>
        <a href="#general" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
          View Questions
          <ChevronDown class="ml-2 w-4 h-4" />
        </a>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="flex items-center mb-4">
          <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
            <DollarSign class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">Pricing & Business Model</h3>
        </div>
        <p class="text-gray-600 mb-4">6 questions</p>
        <a href="#pricing" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
          View Questions
          <ChevronDown class="ml-2 w-4 h-4" />
        </a>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="flex items-center mb-4">
          <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
            <Settings class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">Technical Questions</h3>
        </div>
        <p class="text-gray-600 mb-4">7 questions</p>
        <a href="#technical" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
          View Questions
          <ChevronDown class="ml-2 w-4 h-4" />
        </a>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="flex items-center mb-4">
          <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
            <HeadphonesIcon class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">Support & Community</h3>
        </div>
        <p class="text-gray-600 mb-4">6 questions</p>
        <a href="#support" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
          View Questions
          <ChevronDown class="ml-2 w-4 h-4" />
        </a>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
        <div class="flex items-center mb-4">
          <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
            <Briefcase class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">Business & Legal</h3>
        </div>
        <p class="text-gray-600 mb-4">6 questions</p>
        <a href="#business" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
          View Questions
          <ChevronDown class="ml-2 w-4 h-4" />
        </a>
      </div>
    </div>

    <!-- General Questions -->
    <div id="general" class="mb-16">
      <div class="text-center mb-12">
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 mb-4">
          <HelpCircle class="w-5 h-5 mr-2" />
          General Questions
        </div>
        <h2 class="text-3xl font-extrabold text-gray-900">General Questions</h2>
      </div>

      <div class="max-w-4xl mx-auto space-y-4">
        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('general-0')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'general-0'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What is BottleCRM and why is it free?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'general-0' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'general-0'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM is a 100% free, open-source Customer Relationship Management (CRM) software built specifically for startups and small businesses. It's free because we believe every business should have access to powerful CRM tools without expensive subscription fees. We make revenue through optional paid support services, not by charging for the software itself.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('general-1')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'general-1'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Is BottleCRM really completely free forever?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'general-1' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'general-1'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! BottleCRM core software is completely free with no hidden costs, user limits, trial periods, or subscription fees. You can download, use, modify, and distribute it under the MIT open-source license. The only costs are optional professional services like setup assistance, customization, and hosting support.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('general-2')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'general-2'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">How does BottleCRM compare to commercial CRM platforms?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'general-2' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'general-2'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM provides many of the same core features as commercial CRM platforms but without monthly subscription costs. While enterprise solutions might have more advanced features, BottleCRM includes everything most startups and small businesses need: contact management, sales pipeline, task management, reporting, and email integration. You can save significant costs compared to paid alternatives.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('general-3')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'general-3'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Who should use BottleCRM?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'general-3' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'general-3'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM is perfect for startups, small businesses, consulting firms, freelancers, real estate agencies, and any organization that needs to manage customer relationships without paying expensive subscription fees. It's also ideal for developers who want a customizable, self-hosted CRM solution.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('general-4')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'general-4'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What features are included in the free version?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'general-4' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'general-4'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">All features are included! You get unlimited contacts and leads, complete sales pipeline management, task and project management, basic reporting and analytics, email integration, mobile responsive interface, full source code access, and community support. There are no premium tiers or feature restrictions.</p>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Pricing & Business Model Questions -->
    <div id="pricing" class="mb-16">
      <div class="text-center mb-12">
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 mb-4">
          <DollarSign class="w-5 h-5 mr-2" />
          Pricing & Business Model
        </div>
        <h2 class="text-3xl font-extrabold text-gray-900">Pricing & Business Model</h2>
      </div>

      <div class="max-w-4xl mx-auto space-y-4">
        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('pricing-0')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'pricing-0'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">If the software is free, how do you make money?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'pricing-0' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'pricing-0'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">We offer optional paid professional services including setup assistance ($197), enterprise deployment ($497), custom development, hosting services, training, and ongoing technical support. This sustainable model allows us to maintain and improve the free software while helping businesses that need expert assistance.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('pricing-1')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'pricing-1'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What's included in the Professional Support ($197)?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'pricing-1' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'pricing-1'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Professional Support includes: professional installation & setup, custom domain configuration, SSL certificate setup, database optimization, basic customization (colors, logo), email configuration, 1-month support, video walkthrough session, and comprehensive documentation.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('pricing-2')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'pricing-2'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What's included in the Enterprise Setup ($497)?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'pricing-2' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'pricing-2'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Enterprise Setup includes everything in Professional Support plus: advanced custom development, third-party integrations, advanced reporting setup, custom workflows & automation, team training sessions (2 hours), advanced security configuration, performance optimization, 3-month priority support, and migration from existing CRM.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('pricing-3')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'pricing-3'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Do you offer refunds for support services?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'pricing-3' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'pricing-3'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! We offer a 30-day money-back guarantee on all support services. If you're not satisfied with our professional setup, customization, or support, we'll refund your payment. The free software remains yours to keep regardless.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('pricing-4')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'pricing-4'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Can I switch from paid support back to free?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'pricing-4' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'pricing-4'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Absolutely! There are no contracts or ongoing commitments. Support services are one-time purchases to help you get started. Once your CRM is set up, you maintain full control over your self-hosted installation and can manage it yourself.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('pricing-5')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'pricing-5'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Do you offer custom pricing for large organizations?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'pricing-5' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'pricing-5'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! For organizations with specific requirements, we offer custom development, enterprise consulting, dedicated hosting, and bespoke CRM solutions. Contact us to discuss your needs and get custom pricing that fits your budget and requirements.</p>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Technical Questions -->
    <div id="technical" class="mb-16">
      <div class="text-center mb-12">
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 mb-4">
          <Settings class="w-5 h-5 mr-2" />
          Technical Questions
        </div>
        <h2 class="text-3xl font-extrabold text-gray-900">Technical Questions</h2>
      </div>

      <div class="max-w-4xl mx-auto space-y-4">
        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-0')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-0'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What technology stack does BottleCRM use?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-0' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-0'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM is built with modern web technologies: SvelteKit 2.21+ for the frontend, Prisma for database management, TailwindCSS 4.1+ for styling, and @lucide/svelte for icons. It supports multiple databases including PostgreSQL, MySQL, and SQLite.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-1')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-1'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Can I self-host BottleCRM on my own servers?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-1' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-1'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! BottleCRM is designed to be self-hosted. You can deploy it on your own servers, cloud infrastructure (AWS, Google Cloud, Azure), VPS, or even run it locally. This gives you complete control over your data and eliminates vendor lock-in.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-2')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-2'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What are the system requirements for BottleCRM?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-2' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-2'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM has minimal system requirements: Node.js 18+, any modern database (PostgreSQL, MySQL, SQLite), and at least 512MB RAM. It can run on a basic VPS, cloud instance, or even a Raspberry Pi for small deployments.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-3')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-3'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Is BottleCRM mobile-friendly?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-3' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-3'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! BottleCRM features a fully responsive design that works perfectly on smartphones, tablets, and desktops. The interface automatically adapts to different screen sizes, ensuring a great user experience across all devices.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-4')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-4'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Can I customize BottleCRM for my specific business needs?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-4' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-4'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Absolutely! BottleCRM is open-source, so you have complete access to the source code. You can modify the interface, add custom fields, integrate with third-party services, create custom reports, and tailor it to your exact business requirements.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-5')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-5'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Does BottleCRM integrate with other tools and services?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-5' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-5'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM includes email integration and can be extended to integrate with various third-party services like payment processors, marketing tools, accounting software, and communication platforms. Custom integrations can be developed as needed.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('technical-6')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'technical-6'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">How do I migrate data from my existing CRM?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'technical-6' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'technical-6'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM supports data import through CSV files and API integrations. For complex migrations from existing CRM platforms, our Enterprise Setup service includes professional data migration assistance to help you transition smoothly.</p>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Support & Community Questions -->
    <div id="support" class="mb-16">
      <div class="text-center mb-12">
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 mb-4">
          <HeadphonesIcon class="w-5 h-5 mr-2" />
          Support & Community
        </div>
        <h2 class="text-3xl font-extrabold text-gray-900">Support & Community</h2>
      </div>

      <div class="max-w-4xl mx-auto space-y-4">
        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('support-0')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'support-0'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What kind of support is available for the free version?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'support-0' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'support-0'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Free users have access to community support through our GitHub repository, documentation, and community forums. You can report bugs, request features, and get help from other users and contributors.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('support-1')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'support-1'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">How quickly can I get help with paid support services?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'support-1' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'support-1'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Paid support customers receive priority assistance with response times of 24-48 hours for Professional Support and 12-24 hours for Enterprise Setup. Emergency support is available for critical issues.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('support-2')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'support-2'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Do you provide training for my team?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'support-2' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'support-2'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! Our Enterprise Setup service includes 2 hours of team training sessions. We also offer additional training packages and can create custom training materials for your specific use case and business processes.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('support-3')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'support-3'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Is there documentation available?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'support-3' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'support-3'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! We provide comprehensive documentation including installation guides, user manuals, API documentation, customization tutorials, and best practices. Documentation is continuously updated with new features and improvements.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('support-4')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'support-4'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Can I contribute to BottleCRM development?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'support-4' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'support-4'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Absolutely! BottleCRM is open-source and we welcome contributions. You can submit bug reports, feature requests, code improvements, documentation updates, and translations. Check our GitHub repository for contribution guidelines.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('support-5')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'support-5'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">How often is BottleCRM updated?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'support-5' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'support-5'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">We regularly release updates with bug fixes, security patches, and new features. Major updates are released quarterly, while minor updates and patches are released as needed. All updates are free for all users.</p>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Business & Legal Questions -->
    <div id="business" class="mb-16">
      <div class="text-center mb-12">
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 mb-4">
          <Briefcase class="w-5 h-5 mr-2" />
          Business & Legal
        </div>
        <h2 class="text-3xl font-extrabold text-gray-900">Business & Legal</h2>
      </div>

      <div class="max-w-4xl mx-auto space-y-4">
        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('business-0')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'business-0'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What license does BottleCRM use?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'business-0' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'business-0'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM is released under the MIT License, which is one of the most permissive open-source licenses. This means you can use, modify, distribute, and even sell BottleCRM without any licensing fees or restrictions.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('business-1')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'business-1'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Who owns the data in my BottleCRM installation?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'business-1' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'business-1'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">You own 100% of your data! Since BottleCRM is self-hosted, all your customer data, contacts, sales information, and business intelligence remain on your servers under your complete control. There's no vendor lock-in or data hostage situations.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('business-2')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'business-2'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Is BottleCRM secure for business use?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'business-2' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'business-2'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Yes! BottleCRM follows security best practices including data encryption, secure authentication, SQL injection protection, and CSRF protection. Since you control the hosting environment, you can implement additional security measures as needed for your compliance requirements.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('business-3')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'business-3'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Can BottleCRM handle GDPR compliance?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'business-3' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'business-3'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM provides the technical foundation for GDPR compliance including data export, data deletion, and audit trails. Since you control the data and hosting, you can implement the necessary policies and procedures to meet your specific compliance requirements.</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('business-4')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'business-4'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">Is BottleCRM suitable for regulated industries?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'business-4' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'business-4'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">BottleCRM can be adapted for regulated industries since you have complete control over the hosting environment and data handling. However, you're responsible for ensuring your implementation meets industry-specific compliance requirements (HIPAA, SOX, etc.).</p>
              </div>
            </div>
          {/if}
        </div>

        <div class="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          <button 
            onclick={() => toggleFaq('business-5')}
            class="w-full px-6 py-6 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
            aria-expanded={activeFaq === 'business-5'}
          >
            <div class="flex justify-between items-start">
              <h3 class="text-lg font-semibold text-gray-900 pr-4 leading-relaxed">What happens if BottleCRM development stops?</h3>
              <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 flex-shrink-0 mt-1 {activeFaq === 'business-5' ? 'rotate-180' : ''}" />
            </div>
          </button>
          
          {#if activeFaq === 'business-5'}
            <div transition:fade="{{ duration: 200 }}" class="px-6 pb-6 border-t border-gray-100">
              <div class="pt-4">
                <p class="text-gray-700 leading-relaxed">Since BottleCRM is open-source, you'll always have access to the complete source code. Even if we stop development, you can continue using, maintaining, and developing the software independently or with the help of the community.</p>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Quick Links Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Still Have Questions?
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Can't find what you're looking for? Here are some helpful resources and ways to get in touch.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-3 max-w-4xl mx-auto">
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 text-center">
        <div class="rounded-lg bg-blue-100 p-3 inline-block mb-4">
          <Download class="h-8 w-8 text-blue-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">Get Started</h3>
        <p class="text-gray-600 mb-4">Download and try BottleCRM for free right now.</p>
        <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" 
           class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
          Download Free
          <ExternalLink class="ml-2 w-4 h-4" />
        </a>
      </div>

      <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 text-center">
        <div class="rounded-lg bg-green-100 p-3 inline-block mb-4">
          <Github class="h-8 w-8 text-green-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">GitHub Support</h3>
        <p class="text-gray-600 mb-4">Report issues and get community help.</p>
        <a href="https://github.com/MicroPyramid/Django-CRM/issues" target="_blank" rel="noopener noreferrer"
           class="inline-flex items-center text-green-600 hover:text-green-700 font-semibold">
          Open Issue
          <ExternalLink class="ml-2 w-4 h-4" />
        </a>
      </div>

      <div class="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-6 text-center">
        <div class="rounded-lg bg-orange-100 p-3 inline-block mb-4">
          <MessageCircle class="h-8 w-8 text-orange-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">Contact Support</h3>
        <p class="text-gray-600 mb-4">Get professional help and paid support.</p>
        <a href="/contact" class="inline-flex items-center text-orange-600 hover:text-orange-700 font-semibold">
          Contact Us
          <ExternalLink class="ml-2 w-4 h-4" />
        </a>
      </div>
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Start Your Free CRM?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Now that you know everything about BottleCRM, why not give it a try? It's completely free, and you can have it running in minutes.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Zap class="w-6 h-6 mr-3" />
        Try Free Demo
      </a>
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Download class="w-6 h-6 mr-3" />
        Download Source
      </a>
    </div>
    
    <p class="mt-8 text-blue-200">
      🚀 No credit card • No setup fees • No user limits • No vendor lock-in
    </p>
  </div>
</section>