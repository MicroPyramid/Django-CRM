<script>
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { 
    Download,
    ArrowRight,
    CheckCircle,
    Clock,
    Database,
    Shield,
    Zap,
    Users,
    DollarSign,
    AlertCircle,
    FileText,
    Settings,
    Cloud,
    CheckSquare,
    MessageCircle,
    Github,
    ExternalLink,
    TrendingUp,
    Lock,
    Unlock,
    ChevronDown,
    Mail,
    Calendar
  } from '@lucide/svelte';

  /** @type {number|null} */
  let activeFaq = null;
  let mounted = false;
  let emailForUpdates = '';
  let subscribed = false;

  /**
   * @param {number} index
   */
  function toggleFaq(index) {
    activeFaq = activeFaq === index ? null : index;
  }

  async function subscribeForUpdates() {
    // Simulate subscription - replace with actual implementation
    if (emailForUpdates) {
      subscribed = true;
    }
  }

  onMount(() => {
    mounted = true;
  });
</script>

<svelte:head>
  <title>Migrate to BottleCRM – Free CRM Migration Tools & Service</title>
  <meta name="description" content="Migrate from Salesforce, HubSpot, Pipedrive, and more to BottleCRM. Free CRM migration tools, expert support, and zero subscription fees. Own your CRM data." />
  <meta name="keywords" content="crm migration, migrate crm, crm data migration, free crm migration, open source crm, salesforce migration, hubspot migration, pipedrive migration, crm import, crm export, crm migration service" />
  <link rel="canonical" href="https://bottlecrm.io/migration" />

  <!-- Open Graph -->
  <meta property="og:title" content="Migrate to BottleCRM – Free CRM Migration Tools & Service" />
  <meta property="og:description" content="Switch from Salesforce, HubSpot, Pipedrive, and more to BottleCRM. Free migration tools, expert support, and zero subscription fees." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/migration" />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Migrate to BottleCRM – Free CRM Migration Tools & Service" />
  <meta name="twitter:description" content="Migrate from Salesforce, HubSpot, Pipedrive, and more to BottleCRM. Free CRM migration tools, expert support, and zero subscription fees." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Structured Data (JSON-LD) -->
  {@html `
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "CRM Migration to BottleCRM",
        "description": "Professional CRM migration services and free tools to move from Salesforce, HubSpot, Pipedrive, and other platforms to BottleCRM. Preserve your data and eliminate subscription costs.",
        "provider": {
          "@type": "Organization",
          "name": "BottleCRM",
          "url": "https://bottlecrm.io"
        },
        "areaServed": "Worldwide",
        "serviceType": "CRM Data Migration",
        "url": "https://bottlecrm.io/migration"
      }
    </script>
  `}
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <div class="max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Clock class="w-4 h-4 mr-2" />
        Migration Tools Coming Soon • CSV Import Available Now
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold mb-6">
        Break Free from CRM Subscriptions. <span class="text-yellow-300">Own Your Data.</span>
      </h1>
      
      <p class="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
        Migrate from expensive subscription-based CRM platforms to BottleCRM. 
        Keep all your data, gain complete control, and eliminate monthly fees forever.
      </p>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6 mb-12">
        <a href="#preparation" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
          <CheckCircle class="w-6 h-6 mr-3" />
          Start Migration Prep
        </a>
        <a href="#notify" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
          <Mail class="w-6 h-6 mr-3" />
          Get Notified When Ready
        </a>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <div class="text-2xl font-bold text-yellow-300">$0</div>
          <div class="text-sm text-blue-200">Migration Cost (DIY)</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <div class="text-2xl font-bold text-yellow-300">100%</div>
          <div class="text-sm text-blue-200">Data Preserved</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <div class="text-2xl font-bold text-yellow-300">1-4</div>
          <div class="text-sm text-blue-200">Weeks Timeline</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Migration Sources Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Migrate From Any CRM Platform
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        We're building migration tools for all major CRM platforms. See what you can expect when migrating from popular systems.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      <!-- Enterprise CRM Platform A -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="text-center mb-6">
          <div class="text-4xl mb-4">🏢</div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">Enterprise CRM Platform</h3>
          <div class="flex justify-center space-x-4 text-sm">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded">Complex</span>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded">2-4 weeks</span>
          </div>
        </div>
        
        <div class="space-y-4">
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Data Types:</h4>
            <div class="flex flex-wrap gap-1">
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Contacts</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Leads</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Opportunities</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Accounts</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Tasks</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Notes</span>
            </div>
          </div>
          
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Challenges:</h4>
            <ul class="space-y-1">
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Custom fields mapping
              </li>
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Complex workflow recreation
              </li>
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                API rate limitations
              </li>
            </ul>
          </div>
          
          <div class="pt-4 border-t border-gray-200">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium text-gray-900">Typical Savings:</span>
              <span class="text-lg font-bold text-green-600">$3,000-36,000/year</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Marketing-Focused CRM -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="text-center mb-6">
          <div class="text-4xl mb-4">🧡</div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">Marketing-Focused CRM</h3>
          <div class="flex justify-center space-x-4 text-sm">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded">Moderate</span>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded">1-2 weeks</span>
          </div>
        </div>
        
        <div class="space-y-4">
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Data Types:</h4>
            <div class="flex flex-wrap gap-1">
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Contacts</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Companies</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Deals</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Tasks</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Email history</span>
            </div>
          </div>
          
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Challenges:</h4>
            <ul class="space-y-1">
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Marketing automation setup
              </li>
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Custom properties mapping
              </li>
            </ul>
          </div>
          
          <div class="pt-4 border-t border-gray-200">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium text-gray-900">Typical Savings:</span>
              <span class="text-lg font-bold text-green-600">$6,000-60,000/year</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sales Pipeline CRM -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="text-center mb-6">
          <div class="text-4xl mb-4">🟢</div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">Sales Pipeline CRM</h3>
          <div class="flex justify-center space-x-4 text-sm">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded">Simple</span>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded">1 week</span>
          </div>
        </div>
        
        <div class="space-y-4">
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Data Types:</h4>
            <div class="flex flex-wrap gap-1">
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Contacts</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Organizations</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Deals</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Activities</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Notes</span>
            </div>
          </div>
          
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Challenges:</h4>
            <ul class="space-y-1">
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Pipeline stage mapping
              </li>
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Activity type recreation
              </li>
            </ul>
          </div>
          
          <div class="pt-4 border-t border-gray-200">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium text-gray-900">Typical Savings:</span>
              <span class="text-lg font-bold text-green-600">$1,800-20,000/year</span>
            </div>
          </div>
        </div>
      </div>

      <!-- All-in-One CRM Suite -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="text-center mb-6">
          <div class="text-4xl mb-4">🔴</div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">All-in-One CRM Suite</h3>
          <div class="flex justify-center space-x-4 text-sm">
            <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded">Complex</span>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded">2-3 weeks</span>
          </div>
        </div>
        
        <div class="space-y-4">
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Data Types:</h4>
            <div class="flex flex-wrap gap-1">
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Leads</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Contacts</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Accounts</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Deals</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Tasks</span>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded">Events</span>
            </div>
          </div>
          
          <div>
            <h4 class="font-semibold text-gray-900 mb-2">Challenges:</h4>
            <ul class="space-y-1">
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Custom module recreation
              </li>
              <li class="text-sm text-gray-600 flex items-center">
                <AlertCircle class="w-3 h-3 text-orange-500 mr-2" />
                Workflow rule mapping
              </li>
            </ul>
          </div>
          
          <div class="pt-4 border-t border-gray-200">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium text-gray-900">Typical Savings:</span>
              <span class="text-lg font-bold text-green-600">$1,200-15,000/year</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Migration Preparation Section -->
<section id="preparation" class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Prepare for Your Migration
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Get ready for a smooth migration with our comprehensive preparation guide. 
        Complete these steps before migration tools are released.
      </p>
    </div>

    <div class="space-y-8">
      <!-- Data Audit & Cleanup -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex flex-col lg:flex-row lg:items-center lg:space-x-8">
          <div class="lg:w-1/3 mb-6 lg:mb-0">
            <div class="flex items-center mb-4">
              <div class="rounded-xl bg-blue-100 p-3 mr-4">
                <Database class="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 class="text-xl font-bold text-gray-900">Data Audit & Cleanup</h3>
                <p class="text-sm text-blue-600 font-medium">Estimated time: 1-2 days</p>
              </div>
            </div>
            <p class="text-gray-600">Review and clean your existing CRM data before migration</p>
          </div>
          
          <div class="lg:w-2/3">
            <div class="grid gap-3 md:grid-cols-2">
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Remove duplicate contacts and leads</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Standardize data formats (phone, email, addresses)</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Archive outdated or irrelevant records</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Document custom fields and their purposes</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Export Data from Current CRM -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex flex-col lg:flex-row lg:items-center lg:space-x-8">
          <div class="lg:w-1/3 mb-6 lg:mb-0">
            <div class="flex items-center mb-4">
              <div class="rounded-xl bg-blue-100 p-3 mr-4">
                <Download class="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 class="text-xl font-bold text-gray-900">Export Data from Current CRM</h3>
                <p class="text-sm text-blue-600 font-medium">Estimated time: 2-4 hours</p>
              </div>
            </div>
            <p class="text-gray-600">Gather all necessary data from your existing system</p>
          </div>
          
          <div class="lg:w-2/3">
            <div class="grid gap-3 md:grid-cols-2">
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Export contacts with all custom fields</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Download deal/opportunity data</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Save task and activity history</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Backup email integration settings</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Plan Your BottleCRM Setup -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex flex-col lg:flex-row lg:items-center lg:space-x-8">
          <div class="lg:w-1/3 mb-6 lg:mb-0">
            <div class="flex items-center mb-4">
              <div class="rounded-xl bg-blue-100 p-3 mr-4">
                <Settings class="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 class="text-xl font-bold text-gray-900">Plan Your BottleCRM Setup</h3>
                <p class="text-sm text-blue-600 font-medium">Estimated time: 1 day</p>
              </div>
            </div>
            <p class="text-gray-600">Configure BottleCRM to match your business needs</p>
          </div>
          
          <div class="lg:w-2/3">
            <div class="grid gap-3 md:grid-cols-2">
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Define your sales pipeline stages</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Set up custom fields and properties</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Configure user roles and permissions</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Plan integration requirements</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Test with Sample Data -->
      <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex flex-col lg:flex-row lg:items-center lg:space-x-8">
          <div class="lg:w-1/3 mb-6 lg:mb-0">
            <div class="flex items-center mb-4">
              <div class="rounded-xl bg-blue-100 p-3 mr-4">
                <CheckSquare class="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 class="text-xl font-bold text-gray-900">Test with Sample Data</h3>
                <p class="text-sm text-blue-600 font-medium">Estimated time: 1-2 days</p>
              </div>
            </div>
            <p class="text-gray-600">Validate the migration process with a small data set</p>
          </div>
          
          <div class="lg:w-2/3">
            <div class="grid gap-3 md:grid-cols-2">
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Import a small batch of test data</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Verify data integrity and formatting</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Test critical workflows and processes</span>
              </div>
              <div class="flex items-start space-x-3 bg-white p-4 rounded-lg shadow-sm">
                <CheckCircle class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span class="text-gray-700 text-sm">Train team on new interface</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="mt-12 text-center">
      <div class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white rounded-2xl p-8 max-w-3xl mx-auto">
        <h3 class="text-2xl font-bold mb-4">Need Professional Help?</h3>
        <p class="text-blue-100 mb-6">
          Our migration experts can handle the entire process for you, including data cleanup, 
          custom field mapping, and workflow recreation.
        </p>
        <a href="/contact" class="inline-flex items-center justify-center px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-gray-100 transition-colors">
          <MessageCircle class="w-5 h-5 mr-2" />
          Get Professional Migration Service
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Benefits of Migration Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Why Choose BottleCRM?
      </h2>
      <p class="text-xl text-gray-600">
        Experience the freedom of open-source CRM with enterprise-level features.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      <div class="bg-white rounded-xl p-8 shadow-lg text-center">
        <div class="rounded-full bg-green-100 p-4 inline-block mb-6">
          <DollarSign class="w-8 h-8 text-green-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-4">Eliminate Subscription Costs</h3>
        <p class="text-gray-600 mb-4">Stop paying monthly fees. One-time setup, lifetime ownership.</p>
        <div class="text-2xl font-bold text-green-600">$0/month</div>
      </div>
      
      <div class="bg-white rounded-xl p-8 shadow-lg text-center">
        <div class="rounded-full bg-blue-100 p-4 inline-block mb-6">
          <Shield class="w-8 h-8 text-blue-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-4">Complete Data Control</h3>
        <p class="text-gray-600 mb-4">Self-host on your servers. No vendor lock-in or data hostage situations.</p>
        <div class="text-2xl font-bold text-blue-600">100% Yours</div>
      </div>
      
      <div class="bg-white rounded-xl p-8 shadow-lg text-center">
        <div class="rounded-full bg-indigo-100 p-4 inline-block mb-6">
          <Settings class="w-8 h-8 text-indigo-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-4">Unlimited Customization</h3>
        <p class="text-gray-600 mb-4">Modify source code to fit your exact business needs.</p>
        <div class="text-2xl font-bold text-indigo-600">∞ Flexible</div>
      </div>
      
      <div class="bg-white rounded-xl p-8 shadow-lg text-center">
        <div class="rounded-full bg-purple-100 p-4 inline-block mb-6">
          <Users class="w-8 h-8 text-purple-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-4">No User Limits</h3>
        <p class="text-gray-600 mb-4">Add unlimited users without additional per-seat costs.</p>
        <div class="text-2xl font-bold text-purple-600">∞ Users</div>
      </div>
      
      <div class="bg-white rounded-xl p-8 shadow-lg text-center">
        <div class="rounded-full bg-yellow-100 p-4 inline-block mb-6">
          <Unlock class="w-8 h-8 text-yellow-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-4">Open Source Freedom</h3>
        <p class="text-gray-600 mb-4">MIT license gives you complete freedom to use and modify.</p>
        <div class="text-2xl font-bold text-yellow-600">MIT License</div>
      </div>
      
      <div class="bg-white rounded-xl p-8 shadow-lg text-center">
        <div class="rounded-full bg-green-100 p-4 inline-block mb-6">
          <TrendingUp class="w-8 h-8 text-green-600" />
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-4">Future-Proof</h3>
        <p class="text-gray-600 mb-4">Never worry about price increases or feature limitations.</p>
        <div class="text-2xl font-bold text-green-600">Forever</div>
      </div>
    </div>
  </div>
</section>

<!-- Notification Signup Section -->
<section id="notify" class="py-20 bg-gradient-to-r from-blue-600 via-indigo-700 to-purple-800 text-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl font-extrabold mb-6">
      Be First to Know When Migration Tools Launch
    </h2>
    <p class="text-xl text-blue-100 mb-8">
      Get notified the moment our automated migration tools are ready. 
      Plus receive migration guides, tips, and early access to new features.
    </p>
    
    {#if !subscribed}
      <div class="max-w-md mx-auto">
        <div class="flex flex-col sm:flex-row gap-4">
          <label for="email-updates" class="sr-only">Email address for updates</label>
          <input 
            id="email-updates"
            type="email" 
            bind:value={emailForUpdates}
            placeholder="Enter your email address"
            class="flex-1 px-4 py-3 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white"
          />
          <button 
            onclick={subscribeForUpdates}
            class="px-6 py-3 bg-white text-blue-600 font-semibold rounded-lg hover:bg-gray-100 transition-colors"
          >
            Notify Me
          </button>
        </div>
        <p class="text-sm text-blue-200 mt-4">
          No spam. Unsubscribe anytime. We respect your privacy.
        </p>
      </div>
    {:else}
      <div class="bg-green-500 rounded-lg p-6 max-w-md mx-auto">
        <CheckCircle class="w-8 h-8 mx-auto mb-4" />
        <h3 class="text-xl font-bold mb-2">You're all set!</h3>
        <p>We'll notify you when migration tools are ready.</p>
      </div>
    {/if}
    
    <div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
      <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
        <Calendar class="w-8 h-8 mx-auto mb-2" />
        <div class="font-semibold">Migration Guides</div>
        <div class="text-sm text-blue-200">Step-by-step instructions</div>
      </div>
      <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
        <Zap class="w-8 h-8 mx-auto mb-2" />
        <div class="font-semibold">Early Access</div>
        <div class="text-sm text-blue-200">Beta testing opportunities</div>
      </div>
      <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
        <MessageCircle class="w-8 h-8 mx-auto mb-2" />
        <div class="font-semibold">Expert Support</div>
        <div class="text-sm text-blue-200">Migration assistance</div>
      </div>
    </div>
  </div>
</section>

<!-- FAQ Section -->
<section class="py-20 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Migration Questions & Answers
      </h2>
      <p class="text-xl text-gray-600">
        Everything you need to know about migrating to BottleCRM.
      </p>
    </div>

    <div class="space-y-4">
      <!-- FAQ 1 -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(0)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 0}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">When will the migration tools be available?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 0 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 0}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">We're actively developing automated migration tools for popular CRM platforms. Follow our GitHub repository or subscribe to updates to be notified when they're ready. CSV/Excel imports are available now for immediate migration.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 2 -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(1)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 1}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Will I lose any data during migration?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 1 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 1}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM migration tools are designed to preserve all your important data. We recommend keeping backups of your original data and testing with sample data first. Our professional migration service includes data integrity verification.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 3 -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(2)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 2}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">How long does a typical migration take?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 2 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 2}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Migration time varies by source CRM and data complexity. Simple CSV imports take hours, while complex CRM migrations can take 1-4 weeks. Our professional migration service can accelerate this process significantly.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 4 -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(3)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 3}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can you help with custom field migration?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 3 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 3}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes! Our professional migration service includes custom field mapping, workflow recreation, and business process migration. We ensure your BottleCRM setup matches your current business needs.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 5 -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(4)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 4}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">What if my current CRM has complex workflows?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 4 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 4}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM supports custom workflows and automation. Our migration service includes analyzing your current workflows and recreating them in BottleCRM, often with improvements and optimizations.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 6 -->
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(5)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 5}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Is there a cost for migration assistance?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 5 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 5}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Basic migration guidance is free through our community. Professional migration services are available starting at $497, which includes data migration, custom field setup, and workflow configuration.</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</section>

<!-- Call to Action -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Own Your CRM Data?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Start preparing for your migration today. Download BottleCRM, explore the features, 
      and experience the freedom of open-source CRM.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Github class="w-6 h-6 mr-3" />
        Download BottleCRM
      </a>
      <a href="/contact" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <MessageCircle class="w-6 h-6 mr-3" />
        Get Migration Help
      </a>
    </div>
    
    <p class="mt-8 text-blue-200">
      🚀 CSV import available now • Automated tools coming soon • Professional migration services available
    </p>
  </div>
</section>