<script>
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { 
    BarChart3, 
    TrendingUp, 
    DollarSign,
    Clock,
    Users,
    Target,
    Zap,
    Check,
    ChevronRight,
    ArrowRight,
    Filter,
    Calendar,
    Bell,
    RefreshCw,
    PieChart,
    Settings,
    Eye,
    Edit,
    Trash2,
    Plus,
    Move,
    Star,
    AlertCircle,
    CheckCircle,
    X,
    MessageSquare,
    FileText,
    Phone,
    Mail,
    GitBranch,
    Code
  } from '@lucide/svelte';

  let mounted = false;
  /** @type {any} */
  let selectedDeal = null;
  let showDealModal = false;

  onMount(() => {
    mounted = true;
  });

  /**
   * Opens the deal details modal
   * @param {any} deal - The deal object to display
   */
  function openDealDetails(deal) {
    selectedDeal = deal;
    showDealModal = true;
  }

  function closeDealModal() {
    showDealModal = false;
    selectedDeal = null;
  }

  /**
   * Formats a number as currency
   * @param {number} value - The value to format
   * @returns {string} The formatted currency string
   */
  function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }

  // JSON-LD schema for SaaS CRM SoftwareApplication
  const schema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "BottleCRM",
    "image": "https://bottlecrm.io/logo.png",
    "url": "https://bottlecrm.io/features/sales-pipeline",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "All",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "description": "Free open-source CRM with visual sales pipeline management, deal tracking, sales forecasting, and workflow automation.",
    "publisher": {
      "@type": "Organization",
      "name": "BottleCRM"
    }
  };
</script>

<svelte:head>
  <title>Free Sales Pipeline CRM | Visual Deal Tracking & Forecasting</title>
  <meta name="description" content="Free CRM with visual sales pipeline, deal tracking, sales forecasting & automation. Boost conversions with BottleCRM's open-source pipeline management." />
  <link rel="canonical" href="https://bottlecrm.io/features/sales-pipeline" />

  <!-- Open Graph -->
  <meta property="og:title" content="Free Sales Pipeline CRM | Visual Deal Tracking" />
  <meta property="og:description" content="Open-source CRM for sales pipeline management, deal tracking, and forecasting. Try BottleCRM free." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/features/sales-pipeline" />
  <meta property="og:image" content="https://bottlecrm.io/logo.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Free Sales Pipeline CRM | Visual Deal Tracking" />
  <meta name="twitter:description" content="Open-source CRM for sales pipeline management, deal tracking, and forecasting. Try BottleCRM free." />
  <meta name="twitter:image" content="https://bottlecrm.io/logo.png" />

  <!-- Schema.org JSON-LD -->
  {@html `<script type="application/ld+json">${JSON.stringify(schema)}</script>`}
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
  
  <div class="max-w-7xl mx-auto py-20 px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <BarChart3 class="w-4 h-4 mr-2" />
        <span class="text-sm font-medium">Coming Soon • Visual Sales Pipeline Management</span>
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
        Visualize Your Sales Process with <span class="text-yellow-300">Smart Pipeline Management</span>
      </h1>
      
      <p class="text-xl md:text-2xl mb-8 text-blue-100 leading-relaxed">
        Transform your sales workflow with BottleCRM's intuitive visual pipeline. Track deals from first contact to closed-won, forecast revenue accurately, and automate your sales process for maximum efficiency.
      </p>
      
      <!-- Value proposition points -->
      <ul class="mb-8 space-y-3 text-lg max-w-2xl mx-auto">
        <li class="flex items-center justify-center md:justify-start">
          <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
          <span>Drag-and-drop deal management</span>
        </li>
        <li class="flex items-center justify-center md:justify-start">
          <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
          <span>Automated sales forecasting</span>
        </li>
        <li class="flex items-center justify-center md:justify-start">
          <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
          <span>Real-time collaboration and insights</span>
        </li>
      </ul>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
        <a href="/login" class="inline-flex items-center justify-center px-6 py-4 border border-transparent text-base font-semibold rounded-lg text-blue-700 bg-white hover:bg-gray-100 shadow-lg transition-all duration-200 hover:scale-105">
          <Eye class="w-5 h-5 mr-2" />
          Preview Pipeline Demo
        </a>
        <a href="/features" class="inline-flex items-center justify-center px-6 py-4 border-2 border-white text-base font-semibold rounded-lg text-white hover:bg-white/10 transition-all duration-200">
          View All Features
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Sales Metrics Overview -->
<section class="py-16 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <h2 class="text-3xl font-extrabold text-gray-900 mb-4">
        Real-time Sales Performance Dashboard
      </h2>
      <p class="text-lg text-gray-600">
        Monitor key sales metrics and track your pipeline performance at a glance
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#if mounted}
        <div in:fly="{{ y: 20, duration: 500, delay: 0 }}"
             class="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-500">Total Pipeline Value</h3>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              +12.5%
            </span>
          </div>
          <p class="text-3xl font-bold text-gray-900">$1.31M</p>
        </div>
        
        <div in:fly="{{ y: 20, duration: 500, delay: 100 }}"
             class="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-500">Deals in Pipeline</h3>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              +8
            </span>
          </div>
          <p class="text-3xl font-bold text-gray-900">77</p>
        </div>
        
        <div in:fly="{{ y: 20, duration: 500, delay: 200 }}"
             class="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-500">Average Deal Size</h3>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              +5.2%
            </span>
          </div>
          <p class="text-3xl font-bold text-gray-900">$17,013</p>
        </div>
        
        <div in:fly="{{ y: 20, duration: 500, delay: 300 }}"
             class="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-500">Conversion Rate</h3>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              +2.1%
            </span>
          </div>
          <p class="text-3xl font-bold text-gray-900">23.5%</p>
        </div>
        
        <div in:fly="{{ y: 20, duration: 500, delay: 400 }}"
             class="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-500">Sales Cycle</h3>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              -3 days
            </span>
          </div>
          <p class="text-3xl font-bold text-gray-900">28 days</p>
        </div>
        
        <div in:fly="{{ y: 20, duration: 500, delay: 500 }}"
             class="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-all duration-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-500">Win Rate</h3>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              +4.8%
            </span>
          </div>
          <p class="text-3xl font-bold text-gray-900">65.2%</p>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Interactive Pipeline Demo -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Interactive Sales Pipeline Demo
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Experience how BottleCRM's visual pipeline makes deal management intuitive and efficient. Drag deals between stages and watch your sales process come to life.
      </p>
    </div>

    <!-- Pipeline Board -->
    <div class="bg-white rounded-2xl shadow-xl p-6 overflow-x-auto">
      <div class="flex space-x-6 min-w-max">
        <!-- Lead Stage -->
        <div class="flex-shrink-0 w-80">
          <div class="bg-gray-50 rounded-t-xl p-4 border-b-4 border-blue-500">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-bold text-gray-900 flex items-center">
                <div class="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                Lead
              </h3>
              <span class="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-sm font-medium">24</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">Initial prospects and incoming leads</p>
            <p class="text-lg font-bold text-gray-900">$120,000</p>
          </div>

          <div class="bg-gray-50 rounded-b-xl p-4 min-h-96 space-y-3">
            {#if mounted}
              <div in:fly="{{ y: 20, duration: 400, delay: 0 }}"
                   class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                   role="button"
                   tabindex="0">
                
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-semibold text-gray-900 group-hover:text-blue-600">TechStart Inc.</h4>
                  <button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity">
                    <Move class="w-4 h-4" />
                  </button>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Value:</span>
                    <span class="font-semibold text-gray-900">$15,000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Probability:</span>
                    <span class="font-semibold text-gray-900">20%</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Contact:</span>
                    <span class="font-medium text-gray-900">John Smith</span>
                  </div>
                </div>
                
                <div class="mt-3">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-300 bg-blue-500" style="width: 20%"></div>
                  </div>
                </div>
                
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span class="text-xs text-gray-500">2 hours ago</span>
                  <div class="flex space-x-1">
                    <button class="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                      <Mail class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-green-600 transition-colors">
                      <Phone class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-purple-600 transition-colors">
                      <MessageSquare class="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>

              <div in:fly="{{ y: 20, duration: 400, delay: 50 }}"
                   class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                   role="button"
                   tabindex="0">
                
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-semibold text-gray-900 group-hover:text-blue-600">Digital Solutions</h4>
                  <button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity">
                    <Move class="w-4 h-4" />
                  </button>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Value:</span>
                    <span class="font-semibold text-gray-900">$8,500</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Probability:</span>
                    <span class="font-semibold text-gray-900">15%</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Contact:</span>
                    <span class="font-medium text-gray-900">Sarah Johnson</span>
                  </div>
                </div>
                
                <div class="mt-3">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-300 bg-blue-500" style="width: 15%"></div>
                  </div>
                </div>
                
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span class="text-xs text-gray-500">1 day ago</span>
                  <div class="flex space-x-1">
                    <button class="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                      <Mail class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-green-600 transition-colors">
                      <Phone class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-purple-600 transition-colors">
                      <MessageSquare class="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            {/if}
            
            <button class="w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors group">
              <Plus class="w-5 h-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
              <span class="text-sm">Add Deal</span>
            </button>
          </div>
        </div>

        <!-- Qualified Stage -->
        <div class="flex-shrink-0 w-80">
          <div class="bg-gray-50 rounded-t-xl p-4 border-b-4 border-indigo-500">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-bold text-gray-900 flex items-center">
                <div class="w-3 h-3 rounded-full bg-indigo-500 mr-2"></div>
                Qualified
              </h3>
              <span class="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-sm font-medium">18</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">Leads that meet qualification criteria</p>
            <p class="text-lg font-bold text-gray-900">$180,000</p>
          </div>

          <div class="bg-gray-50 rounded-b-xl p-4 min-h-96 space-y-3">
            {#if mounted}
              <div in:fly="{{ y: 20, duration: 400, delay: 100 }}"
                   class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                   role="button"
                   tabindex="0">
                
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-semibold text-gray-900 group-hover:text-blue-600">Innovation Labs</h4>
                  <button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity">
                    <Move class="w-4 h-4" />
                  </button>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Value:</span>
                    <span class="font-semibold text-gray-900">$25,000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Probability:</span>
                    <span class="font-semibold text-gray-900">40%</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Contact:</span>
                    <span class="font-medium text-gray-900">Emily Davis</span>
                  </div>
                </div>
                
                <div class="mt-3">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-300 bg-indigo-500" style="width: 40%"></div>
                  </div>
                </div>
                
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span class="text-xs text-gray-500">30 min ago</span>
                  <div class="flex space-x-1">
                    <button class="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                      <Mail class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-green-600 transition-colors">
                      <Phone class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-purple-600 transition-colors">
                      <MessageSquare class="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            {/if}
            
            <button class="w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors group">
              <Plus class="w-5 h-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
              <span class="text-sm">Add Deal</span>
            </button>
          </div>
        </div>

        <!-- Proposal Stage -->
        <div class="flex-shrink-0 w-80">
          <div class="bg-gray-50 rounded-t-xl p-4 border-b-4 border-purple-500">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-bold text-gray-900 flex items-center">
                <div class="w-3 h-3 rounded-full bg-purple-500 mr-2"></div>
                Proposal
              </h3>
              <span class="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-sm font-medium">12</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">Proposals sent and under review</p>
            <p class="text-lg font-bold text-gray-900">$240,000</p>
          </div>

          <div class="bg-gray-50 rounded-b-xl p-4 min-h-96 space-y-3">
            {#if mounted}
              <div in:fly="{{ y: 20, duration: 400, delay: 200 }}"
                   class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                   role="button"
                   tabindex="0">
                
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-semibold text-gray-900 group-hover:text-blue-600">Enterprise Corp</h4>
                  <button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity">
                    <Move class="w-4 h-4" />
                  </button>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Value:</span>
                    <span class="font-semibold text-gray-900">$45,000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Probability:</span>
                    <span class="font-semibold text-gray-900">60%</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Contact:</span>
                    <span class="font-medium text-gray-900">Lisa Anderson</span>
                  </div>
                </div>
                
                <div class="mt-3">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-300 bg-purple-500" style="width: 60%"></div>
                  </div>
                </div>
                
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span class="text-xs text-gray-500">1 hour ago</span>
                  <div class="flex space-x-1">
                    <button class="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                      <Mail class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-green-600 transition-colors">
                      <Phone class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-purple-600 transition-colors">
                      <MessageSquare class="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            {/if}
            
            <button class="w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors group">
              <Plus class="w-5 h-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
              <span class="text-sm">Add Deal</span>
            </button>
          </div>
        </div>

        <!-- Negotiation Stage -->
        <div class="flex-shrink-0 w-80">
          <div class="bg-gray-50 rounded-t-xl p-4 border-b-4 border-orange-500">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-bold text-gray-900 flex items-center">
                <div class="w-3 h-3 rounded-full bg-orange-500 mr-2"></div>
                Negotiation
              </h3>
              <span class="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-sm font-medium">8</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">Active contract negotiations</p>
            <p class="text-lg font-bold text-gray-900">$320,000</p>
          </div>

          <div class="bg-gray-50 rounded-b-xl p-4 min-h-96 space-y-3">
            {#if mounted}
              <div in:fly="{{ y: 20, duration: 400, delay: 300 }}"
                   class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                   role="button"
                   tabindex="0">
                
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-semibold text-gray-900 group-hover:text-blue-600">Global Systems</h4>
                  <button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity">
                    <Move class="w-4 h-4" />
                  </button>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Value:</span>
                    <span class="font-semibold text-gray-900">$75,000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Probability:</span>
                    <span class="font-semibold text-gray-900">80%</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Contact:</span>
                    <span class="font-medium text-gray-900">Jennifer Lee</span>
                  </div>
                </div>
                
                <div class="mt-3">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-300 bg-orange-500" style="width: 80%"></div>
                  </div>
                </div>
                
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span class="text-xs text-gray-500">15 min ago</span>
                  <div class="flex space-x-1">
                    <button class="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                      <Mail class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-green-600 transition-colors">
                      <Phone class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-purple-600 transition-colors">
                      <MessageSquare class="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            {/if}
            
            <button class="w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors group">
              <Plus class="w-5 h-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
              <span class="text-sm">Add Deal</span>
            </button>
          </div>
        </div>

        <!-- Closed Won Stage -->
        <div class="flex-shrink-0 w-80">
          <div class="bg-gray-50 rounded-t-xl p-4 border-b-4 border-green-500">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-bold text-gray-900 flex items-center">
                <div class="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                Closed Won
              </h3>
              <span class="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-sm font-medium">15</span>
            </div>
            <p class="text-sm text-gray-600 mb-2">Successfully closed deals</p>
            <p class="text-lg font-bold text-gray-900">$450,000</p>
          </div>

          <div class="bg-gray-50 rounded-b-xl p-4 min-h-96 space-y-3">
            {#if mounted}
              <div in:fly="{{ y: 20, duration: 400, delay: 400 }}"
                   class="bg-white rounded-lg p-4 shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200 cursor-pointer group"
                   role="button"
                   tabindex="0">
                
                <div class="flex items-start justify-between mb-3">
                  <h4 class="font-semibold text-gray-900 group-hover:text-blue-600">Success Stories</h4>
                  <button class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-600 transition-opacity">
                    <Move class="w-4 h-4" />
                  </button>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Value:</span>
                    <span class="font-semibold text-gray-900">$60,000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Probability:</span>
                    <span class="font-semibold text-gray-900">100%</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-gray-600">Contact:</span>
                    <span class="font-medium text-gray-900">Robert Chen</span>
                  </div>
                </div>
                
                <div class="mt-3">
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-300 bg-green-500" style="width: 100%"></div>
                  </div>
                </div>
                
                <div class="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span class="text-xs text-gray-500">Today</span>
                  <div class="flex space-x-1">
                    <button class="p-1 text-gray-400 hover:text-blue-600 transition-colors">
                      <Mail class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-green-600 transition-colors">
                      <Phone class="w-3 h-3" />
                    </button>
                    <button class="p-1 text-gray-400 hover:text-purple-600 transition-colors">
                      <MessageSquare class="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            {/if}
            
            <button class="w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors group">
              <Plus class="w-5 h-5 mx-auto mb-1 group-hover:scale-110 transition-transform" />
              <span class="text-sm">Add Deal</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Pipeline Controls -->
    <div class="mt-8 flex flex-wrap items-center justify-between bg-white rounded-xl shadow-lg p-6">
      <div class="flex items-center space-x-4 mb-4 lg:mb-0">
        <button class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Filter class="w-4 h-4 mr-2" />
          Filter Deals
        </button>
        <button class="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
          <Calendar class="w-4 h-4 mr-2" />
          Date Range
        </button>
        <button class="inline-flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
          <RefreshCw class="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>
      
      <div class="flex items-center space-x-4">
        <span class="text-sm text-gray-600">Pipeline Value:</span>
        <span class="text-2xl font-bold text-gray-900">$1,310,000</span>
        <span class="text-sm text-green-600 font-medium">+12.5% this month</span>
      </div>
    </div>
  </div>
</section>

<!-- Pipeline Features -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Powerful Pipeline Features
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Everything you need to manage your sales pipeline effectively and close more deals faster.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Eye class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Visual Deal Tracking</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">See all your deals at a glance with our intuitive kanban-style pipeline view. Drag and drop deals between stages effortlessly.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Instant pipeline overview
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Drag-and-drop interface
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Real-time updates
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Color-coded stages
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 100 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <TrendingUp class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Sales Forecasting</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Predict future revenue with probability-based forecasting. Track sales velocity and identify bottlenecks in your process.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Revenue predictions
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Probability weighting
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Velocity tracking
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Trend analysis
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 200 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <FileText class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Deal Management</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Manage individual deals with detailed information, activity tracking, and automated reminders for follow-ups.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Deal details
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Activity timeline
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Automated reminders
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Contact integration
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <PieChart class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Pipeline Analytics</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Analyze your sales performance with detailed metrics, conversion rates, and stage-by-stage insights.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Conversion rates
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Stage analytics
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Performance metrics
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Historical data
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 400 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Zap class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Workflow Automation</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Automate routine tasks like follow-up emails, stage transitions, and notification alerts to boost productivity.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Automated workflows
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Smart notifications
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Task automation
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Email sequences
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 500 }}"
             class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Users class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Team Collaboration</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Share pipeline visibility with your team, assign deals, and collaborate on closing opportunities together.</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Team visibility
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Deal assignment
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Collaborative notes
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              Activity sharing
            </li>
          </ul>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Benefits Section -->
<section class="py-20 bg-gradient-to-r from-gray-50 to-blue-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="lg:flex lg:items-center lg:space-x-12">
      <div class="lg:w-1/2">
        <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-8">
          Why Visual Pipeline Management Matters
        </h2>
        <p class="text-xl text-gray-700 mb-8 leading-relaxed">
          Transform your sales process from chaotic spreadsheets to organized, visual workflow management. See immediate improvements in deal closure rates and sales team productivity.
        </p>
        
        <div class="space-y-6">
          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-green-100 p-3">
                <TrendingUp class="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div>
              <h4 class="text-lg font-semibold text-gray-900 mb-2">Increase Conversion Rates by 30%</h4>
              <p class="text-gray-600">Visual pipeline management helps identify bottlenecks and optimize your sales process for better conversion rates.</p>
            </div>
          </div>
          
          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-blue-100 p-3">
                <Clock class="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div>
              <h4 class="text-lg font-semibold text-gray-900 mb-2">Reduce Sales Cycle by 25%</h4>
              <p class="text-gray-600">Automated workflows and clear process visualization help sales teams move deals through stages faster.</p>
            </div>
          </div>
          
          <div class="flex items-start space-x-4">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-purple-100 p-3">
                <Target class="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div>
              <h4 class="text-lg font-semibold text-gray-900 mb-2">Improve Forecast Accuracy by 40%</h4>
              <p class="text-gray-600">Probability-based forecasting and historical data analysis provide more accurate revenue predictions.</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-12 lg:mt-0 lg:w-1/2">
        <div class="bg-white rounded-2xl shadow-2xl p-8">
          <h3 class="text-2xl font-bold text-gray-900 mb-6">Pipeline Performance Impact</h3>
          
          <div class="space-y-6">
            <div>
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">Deal Closure Rate</span>
                <span class="text-sm font-semibold text-green-600">+30%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div class="bg-gradient-to-r from-green-400 to-green-600 h-3 rounded-full" style="width: 85%"></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">Sales Team Productivity</span>
                <span class="text-sm font-semibold text-blue-600">+45%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div class="bg-gradient-to-r from-blue-400 to-blue-600 h-3 rounded-full" style="width: 90%"></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">Forecast Accuracy</span>
                <span class="text-sm font-semibold text-purple-600">+40%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div class="bg-gradient-to-r from-purple-400 to-purple-600 h-3 rounded-full" style="width: 88%"></div>
              </div>
            </div>
            
            <div>
              <div class="flex justify-between items-center mb-2">
                <span class="text-sm font-medium text-gray-700">Customer Follow-up</span>
                <span class="text-sm font-semibold text-orange-600">+60%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-3">
                <div class="bg-gradient-to-r from-orange-400 to-orange-600 h-3 rounded-full" style="width: 95%"></div>
              </div>
            </div>
          </div>
          
          <div class="mt-6 p-4 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-600 text-center">
              <strong class="text-gray-900">Average ROI:</strong> 320% within 6 months of implementation
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Coming Soon Notice -->
<section class="py-16 bg-yellow-50 border-y border-yellow-200">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <div class="inline-flex items-center px-4 py-2 rounded-full bg-yellow-200 text-yellow-800 mb-6">
      <AlertCircle class="w-5 h-5 mr-2" />
      <span class="font-semibold">Development Update</span>
    </div>
    
    <h2 class="text-3xl font-bold text-gray-900 mb-4">
      Sales Pipeline Features Coming Soon
    </h2>
    <p class="text-lg text-gray-700 mb-8 leading-relaxed">
      Our development team is actively working on the visual sales pipeline features. Want to contribute to the development or get early access? Join our open-source community and be part of building the future of free CRM software.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-lg transition-all duration-200">
        <GitBranch class="w-5 h-5 mr-2" />
        Contribute to Development
      </a>
      <a href="/contact" class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 shadow-lg transition-all duration-200">
        <Bell class="w-5 h-5 mr-2" />
        Get Notified When Ready
      </a>
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Transform Your Sales Process?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Start using BottleCRM today and experience the power of visual sales pipeline management. Join the community building the future of free CRM software.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Zap class="w-6 h-6 mr-3" />
        Start Free Demo
      </a>
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Code class="w-6 h-6 mr-3" />
        View Source Code
      </a>
    </div>
    
    <p class="mt-8 text-blue-200 text-lg">
      🚀 No credit card required • Open source • Self-host anywhere
    </p>
  </div>
</section>

<!-- Deal Modal (if needed for interactivity) -->
{#if showDealModal && selectedDeal}
  <div class="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
    <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
      <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onclick={closeDealModal}></div>
      
      <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
        <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
          <div class="sm:flex sm:items-start">
            <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4" id="modal-title">
                Deal Details: {selectedDeal.company}
              </h3>
              
              <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <div class="block text-sm font-medium text-gray-700">Deal Value</div>
                    <p class="text-lg font-semibold text-gray-900">{formatCurrency(selectedDeal.value)}</p>
                  </div>
                  <div>
                    <div class="block text-sm font-medium text-gray-700">Probability</div>
                    <p class="text-lg font-semibold text-gray-900">{selectedDeal.probability}%</p>
                  </div>
                </div>
                
                <div>
                  <div class="block text-sm font-medium text-gray-700">Primary Contact</div>
                  <p class="text-gray-900">{selectedDeal.contact}</p>
                </div>
                
                <div>
                  <div class="block text-sm font-medium text-gray-700">Last Activity</div>
                  <p class="text-gray-900">{selectedDeal.lastActivity}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
          <button type="button" onclick={closeDealModal} class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm">
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}