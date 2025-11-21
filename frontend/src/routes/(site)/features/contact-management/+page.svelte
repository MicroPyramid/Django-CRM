<!-- contact management page -->
<script>
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { 
    Users, 
    Search, 
    Filter, 
    Download, 
    Upload,
    Mail, 
    Phone, 
    MapPin, 
    Building2,
    Tag,
    Calendar,
    Eye,
    Edit,
    Trash2,
    Plus,
    ChevronDown,
    Check,
    X,
    Star,
    TrendingUp,
    Smartphone,
    BarChart3,
    MessageCircle,
    Github,
    Zap,
    Shield,
    Database,
    Infinity,
    DollarSign,
    UserPlus,
    Target,
    Activity,
    Clock,
    Globe,
    Settings
  } from '@lucide/svelte';

  let mounted = false;
  /** @type {number|null} */
  let activeFaq = null;
  let selectedContact = null;

  /**
   * @param {number} index
   */
  function toggleFaq(index) {
    activeFaq = activeFaq === index ? null : index;
  }

  /**
   * Selects a contact for display
   * @param {any} contact - The contact object to select
   */
  function selectContact(contact) {
    selectedContact = contact;
  }

  onMount(() => {
    mounted = true;
  });
</script>

<svelte:head>
  <title>Free Contact Management Software | Unlimited CRM - BottleCRM</title>
  <meta name="description" content="Manage unlimited contacts for free with BottleCRM. Advanced search, custom fields, mobile access. No per-contact fees. 100% data ownership." />
  <meta name="keywords" content="free crm, contact management, unlimited contacts, open source crm, customer database, contact manager, crm software, bottlecrm" />
  <link rel="canonical" href="https://bottlecrm.io/features/contact-management" />

  <!-- Open Graph -->
  <meta property="og:title" content="Free Contact Management Software | Unlimited CRM - BottleCRM" />
  <meta property="og:description" content="Manage unlimited contacts for free with BottleCRM. Advanced search, custom fields, mobile access. No per-contact fees. 100% data ownership." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/features/contact-management" />
  <meta property="og:image" content="https://bottlecrm.io/og-image-contact-management.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Free Contact Management Software | Unlimited CRM - BottleCRM" />
  <meta name="twitter:description" content="Manage unlimited contacts for free with BottleCRM. Advanced search, custom fields, mobile access. No per-contact fees. 100% data ownership." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image-contact-management.png" />

  <!-- Structured Data (JSON-LD) -->
  {@html `
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "BottleCRM",
        "url": "https://bottlecrm.io/features/contact-management",
        "image": "https://bottlecrm.io/og-image-contact-management.png",
        "description": "Free contact management software with unlimited contacts, advanced search, custom fields, and mobile access. No per-contact fees.",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "All",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD"
        },
        "publisher": {
          "@type": "Organization",
          "name": "BottleCRM"
        }
      }
    </script>
  `}
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="lg:flex lg:items-center lg:space-x-12">
      <div class="lg:w-1/2 mb-12 lg:mb-0">
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-green-500 text-white text-sm font-semibold mb-6">
          <Users class="w-4 h-4 mr-2" />
          Unlimited Contacts • Always Free
        </div>
        
        <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">
          Contact Management That <span class="text-green-300">Doesn't Cost Per Contact</span>
        </h1>
        
        <p class="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
          Stop paying $2-10 per contact. BottleCRM gives you unlimited contact storage, advanced search, custom fields, and mobile access - all completely free. Build stronger customer relationships without breaking the bank.
        </p>
        
        <ul class="mb-8 space-y-3 text-lg">
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span>Unlimited contacts and custom fields</span>
          </li>
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span>Advanced search and smart filtering</span>
          </li>
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span>Complete interaction history and timeline</span>
          </li>
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span>Mobile-optimized with offline access</span>
          </li>
        </ul>
        
        <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
            <UserPlus class="w-6 h-6 mr-3" />
            Start Managing Contacts
          </a>
          <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
            <Github class="w-6 h-6 mr-3" />
            View Source Code
          </a>
        </div>
      </div>
      
      <div class="lg:w-1/2">
        <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
          <h3 class="text-2xl font-bold mb-6 text-center">💰 Industry Cost Comparison*</h3>
          
          <div class="space-y-4">
            <div class="bg-white/20 rounded-lg p-4">
              <div class="flex justify-between items-center mb-2">
                <span class="font-semibold">1,000 contacts in Enterprise CRM:</span>
                <span class="text-2xl font-bold text-red-300">$25,000+/year</span>
              </div>
              <div class="flex justify-between items-center mb-2">
                <span class="font-semibold">1,000 contacts in Popular CRM:</span>
                <span class="text-2xl font-bold text-red-300">$3,000-8,000/year</span>
              </div>
              <div class="flex justify-between items-center mb-4">
                <span class="font-semibold">1,000 contacts in Standard CRM:</span>
                <span class="text-2xl font-bold text-red-300">$1,500-3,000/year</span>
              </div>
              <div class="border-t border-white/30 pt-4">
                <div class="flex justify-between items-center">
                  <span class="font-bold text-lg">Unlimited contacts in BottleCRM:</span>
                  <span class="text-3xl font-bold text-green-300">$0</span>
                </div>
              </div>
            </div>
            
            <div class="text-center text-green-300 font-bold text-xl">
              Save $1,500 - $25,000+ per year!
            </div>
            
            <div class="text-center text-xs text-blue-200 mt-4">
              *Based on industry-standard per-contact pricing models as of 2024
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Features Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Professional Contact Management Features
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Everything you need to organize, track, and nurture your customer relationships. All features included for free, no premium tiers or hidden costs.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative">
          
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
              Save $2-10 per contact vs competitors
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Users class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">
            Unlimited Contact Storage
          </h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Store unlimited contacts with complete profile information, interaction history, and custom fields. No per-contact pricing or storage limits.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Unlimited contacts
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Custom fields
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Rich profiles
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              No storage limits
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 100 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative">
          
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
              Enterprise-grade search for free
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Search class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">
            Advanced Search & Filtering
          </h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Find contacts instantly with powerful search capabilities, smart filters, and custom tags. Search by name, company, tags, location, or any custom field.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Instant search
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Smart filters
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Custom tags
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Bulk operations
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 200 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative">
          
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
              360° customer view
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Activity class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">
            Contact Interaction Timeline
          </h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Track every interaction with your contacts including emails, calls, meetings, and notes. Build stronger relationships with complete interaction history.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Complete timeline
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Interaction tracking
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Meeting history
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Notes & tasks
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative opacity-75">
          
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300 grayscale">
            <Target class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">
            Smart Contact Segmentation
            <span class="text-sm font-normal text-orange-600 ml-2">• Coming Soon</span>
          </h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Organize contacts into dynamic segments based on behavior, demographics, or custom criteria. Target your outreach and marketing efforts effectively.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Dynamic segments
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Behavioral targeting
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Custom criteria
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Automated grouping
            </li>
          </ul>

          <div class="mt-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
            <p class="text-sm text-orange-700 font-medium">This feature is in development and will be available soon!</p>
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 400 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative opacity-75">
          
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300 grayscale">
            <Database class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">
            Bulk Import & Export
            <span class="text-sm font-normal text-orange-600 ml-2">• Coming Soon</span>
          </h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Easily import contacts from CSV, Excel, or other CRM systems. Export your data anytime with no vendor lock-in. Your data stays yours.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              CSV/Excel import
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              CRM migration
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Data export
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              No vendor lock-in
            </li>
          </ul>

          <div class="mt-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
            <p class="text-sm text-orange-700 font-medium">This feature is in development and will be available soon!</p>
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 500 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative opacity-75">
          
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 border border-orange-200">
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300 grayscale">
            <Smartphone class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">
            Mobile-First Contact Access
            <span class="text-sm font-normal text-orange-600 ml-2">• Coming Soon</span>
          </h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Access and manage contacts on any device with our responsive interface. Work offline and sync automatically when connected.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Mobile optimized
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Offline access
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Auto sync
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Cross-platform
            </li>
          </ul>

          <div class="mt-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
            <p class="text-sm text-orange-700 font-medium">This feature is in development and will be available soon!</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Interactive Demo Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        See Contact Management in Action
      </h2>
      <p class="text-xl text-gray-600">
        Experience the intuitive interface and powerful features of BottleCRM's contact management system.
      </p>
    </div>

    <div class="bg-gray-50 rounded-2xl p-8">
      <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div class="flex items-center space-x-4">
          <div class="relative">
            <Search class="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            <label for="contact-search-demo" class="sr-only">Search contacts</label>
            <input id="contact-search-demo" type="text" placeholder="Search contacts..." class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 w-64" />
          </div>
          <button class="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
            <Filter class="w-4 h-4 mr-2" />
            Filter
          </button>
        </div>
        <button class="flex items-center px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <Plus class="w-4 h-4 mr-2" />
          Add Contact
        </button>
      </div>

      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div class="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer border-l-4 border-green-500">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h4 class="text-lg font-bold text-gray-900">Sarah Johnson</h4>
              <p class="text-gray-600 flex items-center mt-1">
                <Building2 class="w-4 h-4 mr-1" />
                TechStart Inc.
              </p>
            </div>
            <span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
              Qualified
            </span>
          </div>
          
          <div class="space-y-2 text-sm text-gray-600">
            <p class="flex items-center">
              <Mail class="w-4 h-4 mr-2" />
              sarah@techstart.com
            </p>
            <p class="flex items-center">
              <Phone class="w-4 h-4 mr-2" />
              +1 (555) 123-4567
            </p>
            <p class="flex items-center">
              <MapPin class="w-4 h-4 mr-2" />
              San Francisco, CA
            </p>
            <p class="flex items-center">
              <Clock class="w-4 h-4 mr-2" />
              Last contact: 2 days ago
            </p>
          </div>
          
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">Hot Lead</span>
            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">Enterprise</span>
          </div>
          
          <div class="mt-4 flex space-x-2">
            <button class="flex-1 flex items-center justify-center px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 text-sm">
              <Eye class="w-4 h-4 mr-1" />
              View
            </button>
            <button class="flex-1 flex items-center justify-center px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 text-sm">
              <Edit class="w-4 h-4 mr-1" />
              Edit
            </button>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer border-l-4 border-yellow-500">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h4 class="text-lg font-bold text-gray-900">Michael Chen</h4>
              <p class="text-gray-600 flex items-center mt-1">
                <Building2 class="w-4 h-4 mr-1" />
                Growth Co.
              </p>
            </div>
            <span class="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
              Negotiation
            </span>
          </div>
          
          <div class="space-y-2 text-sm text-gray-600">
            <p class="flex items-center">
              <Mail class="w-4 h-4 mr-2" />
              m.chen@growthco.com
            </p>
            <p class="flex items-center">
              <Phone class="w-4 h-4 mr-2" />
              +1 (555) 987-6543
            </p>
            <p class="flex items-center">
              <MapPin class="w-4 h-4 mr-2" />
              New York, NY
            </p>
            <p class="flex items-center">
              <Clock class="w-4 h-4 mr-2" />
              Last contact: 1 week ago
            </p>
          </div>
          
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">Proposal Sent</span>
            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">Decision Maker</span>
          </div>
          
          <div class="mt-4 flex space-x-2">
            <button class="flex-1 flex items-center justify-center px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 text-sm">
              <Eye class="w-4 h-4 mr-1" />
              View
            </button>
            <button class="flex-1 flex items-center justify-center px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 text-sm">
              <Edit class="w-4 h-4 mr-1" />
              Edit
            </button>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer border-l-4 border-blue-500">
          <div class="flex items-start justify-between mb-4">
            <div class="flex-1">
              <h4 class="text-lg font-bold text-gray-900">Emma Rodriguez</h4>
              <p class="text-gray-600 flex items-center mt-1">
                <Building2 class="w-4 h-4 mr-1" />
                Scale Solutions
              </p>
            </div>
            <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
              New
            </span>
          </div>
          
          <div class="space-y-2 text-sm text-gray-600">
            <p class="flex items-center">
              <Mail class="w-4 h-4 mr-2" />
              emma@scalesolutions.com
            </p>
            <p class="flex items-center">
              <Phone class="w-4 h-4 mr-2" />
              +1 (555) 456-7890
            </p>
            <p class="flex items-center">
              <MapPin class="w-4 h-4 mr-2" />
              Austin, TX
            </p>
            <p class="flex items-center">
              <Clock class="w-4 h-4 mr-2" />
              Last contact: 3 days ago
            </p>
          </div>
          
          <div class="mt-4 flex flex-wrap gap-2">
            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">New Contact</span>
            <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full">SMB</span>
          </div>
          
          <div class="mt-4 flex space-x-2">
            <button class="flex-1 flex items-center justify-center px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 text-sm">
              <Eye class="w-4 h-4 mr-1" />
              View
            </button>
            <button class="flex-1 flex items-center justify-center px-3 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 text-sm">
              <Edit class="w-4 h-4 mr-1" />
              Edit
            </button>
          </div>
        </div>
      </div>
      
      <div class="mt-8 text-center">
        <p class="text-gray-600 mb-4">This is just a preview. The actual BottleCRM interface includes advanced filtering, bulk operations, custom fields, and much more.</p>
        <a href="/login" class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold">
          <Zap class="w-5 h-5 mr-2" />
          Try the Full Interface
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Coming Soon Features Section -->
<section class="py-20 bg-gradient-to-r from-orange-50 to-amber-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        🚀 Coming Soon Features
      </h2>
      <p class="text-xl text-gray-600">
        We're continuously improving BottleCRM with new contact management features based on user feedback.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-3">
      <div class="bg-white rounded-2xl shadow-lg p-8 border border-orange-200">
        <div class="rounded-xl bg-gradient-to-r from-orange-100 to-amber-100 p-4 inline-block mb-6">
          <Target class="h-8 w-8 text-orange-600" />
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Smart Contact Segmentation</h3>
        <p class="text-gray-600 mb-4">Automatically segment contacts based on behavior, engagement, and custom criteria for targeted campaigns.</p>
        <div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
          Q2 2024
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-lg p-8 border border-orange-200">
        <div class="rounded-xl bg-gradient-to-r from-orange-100 to-amber-100 p-4 inline-block mb-6">
          <Database class="h-8 w-8 text-orange-600" />
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Bulk Import & Export</h3>
        <p class="text-gray-600 mb-4">Import thousands of contacts from CSV/Excel files and export your data in multiple formats with advanced mapping.</p>
        <div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
          Q2 2024
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-lg p-8 border border-orange-200">
        <div class="rounded-xl bg-gradient-to-r from-orange-100 to-amber-100 p-4 inline-block mb-6">
          <Smartphone class="h-8 w-8 text-orange-600" />
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Mobile-First Contact Access</h3>
        <p class="text-gray-600 mb-4">Native mobile app with offline sync, push notifications, and optimized contact management on the go.</p>
        <div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
          Q3 2024
        </div>
      </div>
    </div>

    <div class="mt-12 text-center bg-white rounded-2xl p-8 shadow-lg">
      <h3 class="text-2xl font-bold text-gray-900 mb-4">Want to influence our roadmap?</h3>
      <p class="text-gray-600 mb-6">Join our community and help us prioritize which features to build next. Your feedback shapes BottleCRM's future!</p>
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
        <a href="https://github.com/MicroPyramid/Django-CRM/discussions" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-semibold">
          <MessageCircle class="w-5 h-5 mr-2" />
          Join Discussions
        </a>
        <a href="https://github.com/MicroPyramid/Django-CRM/issues" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-semibold">
          <Github class="w-5 h-5 mr-2" />
          Request Features
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Workflow Section -->
<section class="py-20 bg-gradient-to-r from-blue-50 to-indigo-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Simple Contact Management Workflow
      </h2>
      <p class="text-xl text-gray-600">
        Get started with professional contact management in just 4 easy steps.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center relative">
          
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
              1
            </div>
          </div>
          
          <div class="mt-4 mb-6">
            <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block">
              <Upload class="h-8 w-8 text-blue-600" />
            </div>
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Import Your Contacts</h3>
          <p class="text-gray-600 mb-6">Upload from CSV, Excel, or migrate from your existing CRM</p>
          
          <ul class="space-y-2 text-sm text-gray-700">
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Drag & drop files
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Map fields automatically
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Validate data
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 150 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center relative">
          
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
              2
            </div>
          </div>
          
          <div class="mt-4 mb-6">
            <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block">
              <Tag class="h-8 w-8 text-blue-600" />
            </div>
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Organize & Segment</h3>
          <p class="text-gray-600 mb-6">Create tags, segments, and custom fields for better organization</p>
          
          <ul class="space-y-2 text-sm text-gray-700">
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Create custom tags
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Set up segments
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Add custom fields
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center relative">
          
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
              3
            </div>
          </div>
          
          <div class="mt-4 mb-6">
            <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block">
              <MessageCircle class="h-8 w-8 text-blue-600" />
            </div>
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Track Interactions</h3>
          <p class="text-gray-600 mb-6">Log emails, calls, meetings, and notes for each contact</p>
          
          <ul class="space-y-2 text-sm text-gray-700">
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Log communications
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Schedule follow-ups
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Add notes
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 450 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center relative">
          
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold">
              4
            </div>
          </div>
          
          <div class="mt-4 mb-6">
            <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block">
              <BarChart3 class="h-8 w-8 text-blue-600" />
            </div>
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Analyze & Optimize</h3>
          <p class="text-gray-600 mb-6">Use insights to improve relationships and conversion rates</p>
          
          <ul class="space-y-2 text-sm text-gray-700">
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              View analytics
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Track engagement
            </li>
            <li class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-2" />
              Optimize outreach
            </li>
          </ul>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Comparison Table -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Contact Management Feature Comparison
      </h2>
      <p class="text-xl text-gray-600">
        See how BottleCRM's contact management compares to typical CRM pricing models.
      </p>
    </div>

    <div class="overflow-x-auto">
      <table class="w-full bg-white rounded-xl shadow-lg overflow-hidden">
        <thead class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
          <tr>
            <th class="px-6 py-4 text-left text-sm font-semibold">Platform Type</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">Contact Limit</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">Typical Pricing</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">Custom Fields</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">Data Export</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">Mobile App</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">API Access</th>
            <th class="px-6 py-4 text-center text-sm font-semibold">Self-Hosted</th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-b border-gray-200 bg-green-50 border-l-4 border-l-green-500">
            <td class="px-6 py-4 font-semibold text-green-700">
              <div class="flex items-center">
                BottleCRM
                <span class="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Free & Open Source</span>
              </div>
            </td>
            <td class="px-6 py-4 text-center font-bold text-green-600">Unlimited</td>
            <td class="px-6 py-4 text-center font-bold text-green-600">$0</td>
            <td class="px-6 py-4 text-center text-gray-700">Unlimited</td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
          </tr>
          <tr class="border-b border-gray-200 hover:bg-gray-50">
            <td class="px-6 py-4 font-semibold text-gray-900">
              <div class="flex items-center">
                Enterprise CRM Platforms
              </div>
            </td>
            <td class="px-6 py-4 text-center text-gray-700">Plan-dependent</td>
            <td class="px-6 py-4 text-center text-gray-700">$25-300+/user</td>
            <td class="px-6 py-4 text-center text-gray-700">Limited by tier</td>
            <td class="px-6 py-4 text-center">
              <span class="text-gray-700 text-sm">Often restricted</span>
            </td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <span class="text-gray-700 text-sm">Premium tiers</span>
            </td>
            <td class="px-6 py-4 text-center">
              <X class="w-5 h-5 text-red-500 mx-auto" />
            </td>
          </tr>
          <tr class="border-b border-gray-200 hover:bg-gray-50">
            <td class="px-6 py-4 font-semibold text-gray-900">
              <div class="flex items-center">
                Popular Cloud CRMs
              </div>
            </td>
            <td class="px-6 py-4 text-center text-gray-700">Limited on free plans</td>
            <td class="px-6 py-4 text-center text-gray-700">$15-100+/month</td>
            <td class="px-6 py-4 text-center text-gray-700">Tier-restricted</td>
            <td class="px-6 py-4 text-center">
              <span class="text-gray-700 text-sm">Basic exports</span>
            </td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <span class="text-gray-700 text-sm">Paid features</span>
            </td>
            <td class="px-6 py-4 text-center">
              <X class="w-5 h-5 text-red-500 mx-auto" />
            </td>
          </tr>
          <tr class="border-b border-gray-200 hover:bg-gray-50">
            <td class="px-6 py-4 font-semibold text-gray-900">
              <div class="flex items-center">
                Mid-Market CRM Solutions
              </div>
            </td>
            <td class="px-6 py-4 text-center text-gray-700">Per-user limitations</td>
            <td class="px-6 py-4 text-center text-gray-700">$15-99/user</td>
            <td class="px-6 py-4 text-center text-gray-700">Limited</td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <Check class="w-5 h-5 text-green-500 mx-auto" />
            </td>
            <td class="px-6 py-4 text-center">
              <span class="text-gray-700 text-sm">Higher tiers</span>
            </td>
            <td class="px-6 py-4 text-center">
              <X class="w-5 h-5 text-red-500 mx-auto" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="mt-8 text-center">
      <p class="text-sm text-gray-600">
        *Pricing and features based on publicly available information as of 2024. Individual platform offerings may vary.
      </p>
    </div>
  </div>
</section>

<!-- FAQ Section -->
<section class="py-20 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Contact Management FAQ
      </h2>
      <p class="text-xl text-gray-600">
        Common questions about BottleCRM's contact management features.
      </p>
    </div>

    <div class="space-y-4">
      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(0)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 0}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">How many contacts can I store in BottleCRM?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 0 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 0}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Unlimited! Unlike other CRM systems that charge per contact or have storage limits, BottleCRM allows you to store as many contacts as you need without any additional costs.</p>
          </div>
        {/if}
      </div>

      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(1)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 1}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can I import contacts from my existing CRM or spreadsheet?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 1 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 1}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes, BottleCRM supports importing contacts from CSV files, Excel spreadsheets, and most popular CRM systems. Our import wizard helps you map fields and ensures data integrity during the migration process.</p>
          </div>
        {/if}
      </div>

      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(2)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 2}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Is my contact data secure and private?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 2 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 2}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Absolutely. Since BottleCRM is self-hosted, your contact data never leaves your servers. You have complete control over data security, privacy, and compliance with regulations like GDPR.</p>
          </div>
        {/if}
      </div>

      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(3)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 3}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can I customize contact fields for my business needs?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 3 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 3}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes, BottleCRM allows unlimited custom fields. Add industry-specific information, custom tags, dropdown selections, and any other data points relevant to your business without restrictions.</p>
          </div>
        {/if}
      </div>

      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(4)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 4}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Does BottleCRM work on mobile devices?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 4 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 4}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM is fully responsive and works perfectly on smartphones and tablets. You can access, search, and manage contacts on any device with a modern web browser.</p>
          </div>
        {/if}
      </div>

      <div class="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(5)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-100 hover:bg-gray-100 transition-colors duration-200"
          aria-expanded={activeFaq === 5}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">How does contact management in BottleCRM compare to paid alternatives?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 5 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 5}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM provides enterprise-grade contact management features for free, including unlimited contacts, custom fields, advanced search, and data export. Most commercial CRM systems charge $25-100+ per user per month for similar functionality, often with contact limits and feature restrictions.</p>
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
      Ready to Manage Unlimited Contacts for Free?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Stop paying per contact or hitting storage limits. Start building better customer relationships with BottleCRM's powerful, free contact management system.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6 mb-8">
      <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <UserPlus class="w-6 h-6 mr-3" />
        Start Managing Contacts
      </a>
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Github class="w-6 h-6 mr-3" />
        Download Source Code
      </a>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
      <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
        <div class="text-2xl font-bold text-green-300">∞</div>
        <div class="text-sm text-blue-200">Unlimited Contacts</div>
      </div>
      <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
        <div class="text-2xl font-bold text-green-300">$0</div>
        <div class="text-sm text-blue-200">Monthly Cost</div>
      </div>
      <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
        <div class="text-2xl font-bold text-green-300">100%</div>
        <div class="text-sm text-blue-200">Data Ownership</div>
      </div>
    </div>
    
    <p class="mt-8 text-blue-200">
      🚀 No setup fees • No user limits • No vendor lock-in • Free forever
    </p>
  </div>
</section>