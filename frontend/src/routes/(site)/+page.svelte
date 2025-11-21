<!-- home page -->
<script>
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import banner_img from '$lib/assets/images/banner.png';
  import { 
    Users, 
    BarChart3, 
    CheckSquare, 
    TrendingUp, 
    FileText, 
    Smartphone,
    Zap,
    Check,
    X,
    ChevronRight,
    ChevronDown,
    GitFork,
    MessageCircle,
    Github
  } from '@lucide/svelte';
  import { Download } from '@lucide/svelte';
  
  /** @type {number|null} */
  let activeFaq = null;
  let mounted = false;

  /**
   * @param {number} index
   */
  function toggleFaq(index) {
    activeFaq = activeFaq === index ? null : index;
  }
  
  onMount(() => {
    mounted = true;
  });

  // JSON-LD schema for SEO
  const schema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "BottleCRM",
    "description": "Free, open-source CRM software for startups and small businesses. Self-hosted, unlimited users, no subscription fees.",
    "url": "https://bottlecrm.io",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "reviewCount": "150"
    }
  };
</script>

<svelte:head>
  <title>BottleCRM: Free Open Source CRM for Startups & Small Business</title>
  <meta name="description" content="BottleCRM is a free, open-source CRM for startups and small businesses. Self-host, manage contacts, sales, and tasks. No subscription fees. Download now!" />
  <meta name="keywords" content="free crm, open source crm, crm software, startup crm, small business crm, self hosted crm, customer relationship management" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="https://bottlecrm.io/" />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/" />
  <meta property="og:title" content="BottleCRM: Free Open Source CRM for Startups & Small Business" />
  <meta property="og:description" content="Free, open-source CRM for startups and small businesses. Self-host, unlimited users, no subscription fees." />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:url" content="https://bottlecrm.io/" />
  <meta name="twitter:title" content="BottleCRM: Free Open Source CRM for Startups & Small Business" />
  <meta name="twitter:description" content="Free, open-source CRM for startups and small businesses. Self-host, unlimited users, no subscription fees." />
  <meta name="twitter:image" content="https://bottlecrm.io/twitter-image.png" />

  <!-- Structured Data for SEO -->
  <script type="application/ld+json">
    {@html JSON.stringify(schema)}
  </script>
</svelte:head>

<!-- Hero Section with enhanced content -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white relative overflow-hidden">
  <!-- Animated background elements -->
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
  
  <div class="max-w-7xl mx-auto py-20 px-4 sm:px-6 lg:px-8 flex flex-col lg:flex-row items-center relative z-10">
    <div class="lg:w-1/2 mb-10 lg:mb-0">
      <div>
        <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
          <span class="text-sm font-medium">🚀 Free Forever • No Credit Card Required</span>
        </div>
        
        <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
          The Free <span class="text-yellow-300">CRM Software</span> That Startups Actually Need
        </h1>
        <p class="text-xl md:text-2xl mb-8 text-blue-100 leading-relaxed">
          Stop paying $50-300/month for CRM subscriptions. BottleCRM is a 100% free, open-source, and self-hostable customer relationship management solution built specifically for startups and growing businesses.
        </p>
        
        <!-- Value proposition bullets -->
        <ul class="mb-8 space-y-3 text-lg">
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span class="break-words">No monthly fees - Save thousands per year</span>
          </li>
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span class="break-words">Complete data ownership - Host on your servers</span>
          </li>
          <li class="flex items-center">
            <Check class="w-6 h-6 text-green-400 mr-3 flex-shrink-0" />
            <span class="break-words">Unlimited users and customization</span>
          </li>
        </ul>
        
        <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <a href="/login" class="inline-flex items-center justify-center px-6 py-4 border border-transparent text-base font-semibold rounded-lg text-blue-700 bg-white hover:bg-gray-100 shadow-lg transition-all duration-200 hover:scale-105 whitespace-nowrap">
            <Zap class="w-5 h-5 mr-2" />
            Start Free Demo
          </a>
          <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-4 border-2 border-white text-base font-semibold rounded-lg text-white hover:bg-white/10 transition-all duration-200 whitespace-nowrap">
            <Github class="w-5 h-5 mr-2" />
            View Source
          </a>
        </div>
      </div>
    </div>
    
    <div class="lg:w-1/2 flex justify-center lg:justify-end">
      <div class="w-full max-w-lg">
        <div class="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl overflow-hidden border border-white/20">
          <div class="h-80 bg-gradient-to-br from-gray-100 to-gray-200 relative">
            <img src="{banner_img}" alt="BottleCRM Dashboard Preview - Free CRM Software Interface" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          </div>
          <div class="p-6 bg-white/5">
            <div class="space-y-3">
              <div class="w-full bg-gradient-to-r from-blue-400 to-purple-500 h-3 rounded-full"></div>
              <div class="w-4/5 bg-gradient-to-r from-blue-300 to-indigo-400 h-3 rounded-full"></div>
              <div class="w-3/5 bg-gradient-to-r from-indigo-300 to-blue-400 h-3 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Features Section with enhanced content -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Enterprise-Grade CRM Features <span class="text-blue-600">Without Enterprise Costs</span>
      </h2>
      <p class="mt-4 max-w-3xl text-xl text-gray-600 mx-auto leading-relaxed">
        Everything your startup or small business needs to manage customer relationships, automate sales processes, and drive sustainable growth. All features included, no premium tiers.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
      <!-- Smart Contact Management System -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <Users class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Smart Contact Management System</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Centralize customer data with our intuitive contact management system. Track customer interactions, manage qualified leads, and build stronger customer relationships. Perfect for startups, small businesses, and growing enterprises looking for efficient CRM software.</p>
        
        <ul class="space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            360° Customer View
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Lead Scoring
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Contact Segmentation
          </li>
        </ul>
      </div>

      <!-- Visual Sales Pipeline Management -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <BarChart3 class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Visual Sales Pipeline Management</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Streamline your sales process with our drag-and-drop sales pipeline. Track deals from lead qualification to closing, forecast revenue accurately, and implement powerful sales automation workflows to boost your conversion rates.</p>
        
        <ul class="space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Deal Tracking
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Sales Forecasting
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Automation Workflows
          </li>
        </ul>
      </div>

      <!-- Advanced Task & Project Management -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <CheckSquare class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Advanced Task & Project Management</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Never miss a follow-up with integrated task management and project tracking. Set reminders, assign tasks to team members, track project milestones, and ensure maximum productivity across your sales and marketing teams.</p>
        
        <ul class="space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Task Automation
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Team Collaboration
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Deadline Tracking
          </li>
        </ul>
      </div>

      <!-- Real-time Analytics & Reporting -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <TrendingUp class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Real-time Analytics & Reporting</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Make data-driven decisions with comprehensive CRM analytics and business intelligence. Track sales performance, monitor marketing campaign effectiveness, and generate detailed reports to optimize your customer acquisition strategies.</p>
        
        <ul class="space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Custom Dashboards
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Performance Metrics
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            ROI Tracking
          </li>
        </ul>
      </div>

      <!-- Automated Invoice & Billing Management -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
            Coming Soon
          </span>
        </div>
        
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <FileText class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Automated Invoice & Billing Management</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Streamline your billing process with integrated invoicing software. Create professional invoices, track payments, manage recurring billing, and integrate with popular payment gateways. Perfect for service-based businesses and SaaS startups.</p>
        
        <ul class="space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Payment Tracking
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Recurring Billing
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Payment Integration
          </li>
        </ul>
      </div>

      <!-- Mobile CRM & Cloud Access -->
      <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
        <div class="absolute top-4 right-4">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
            Available Now
          </span>
        </div>
        
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <Smartphone class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Mobile CRM & Cloud Access</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Access your CRM data anywhere with our native mobile app and responsive web interface. Work offline, sync data automatically, and manage your business on-the-go. Perfect for sales teams, remote workers, and field service management.</p>
        
        <ul class="space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Native Mobile App
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2" />
            Cross-platform Support
          </li>
        </ul>
        
        <div class="mt-4 pt-4 border-t border-gray-200">
          <a href="https://play.google.com/store/apps/details?id=io.bottlecrm" target="_blank" rel="noopener noreferrer" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold text-sm">
            <Download class="w-4 h-4 mr-1" />
            Download Mobile App
            <ChevronRight class="w-4 h-4 ml-1" />
          </a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Mobile App Section -->
<section class="py-20 bg-gradient-to-br from-indigo-600 via-purple-700 to-blue-800 text-white relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center mb-16">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Smartphone class="w-5 h-5 mr-2" />
        <span class="text-sm font-medium">📱 Now Available on Mobile</span>
      </div>
      
      <h2 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">
        Take Your CRM <span class="text-yellow-300">On The Go</span>
      </h2>
      <p class="text-xl md:text-2xl mb-8 text-blue-100 leading-relaxed max-w-4xl mx-auto">
        Introducing the BottleCRM mobile app - manage your customers, leads, and sales pipeline from anywhere. 
        Built with Flutter for seamless cross-platform performance.
      </p>
    </div>

    <div class="grid lg:grid-cols-2 gap-12 items-center">
      <!-- Left side - App features -->
      <div>
        <h3 class="text-3xl font-bold mb-8">Mobile CRM Features</h3>
        
        <div class="space-y-6">
          <div class="flex items-start space-x-4">
            <div class="bg-white/20 rounded-lg p-3 flex-shrink-0">
              <Users class="w-6 h-6" />
            </div>
            <div>
              <h4 class="text-xl font-semibold mb-2">Manage Contacts & Leads</h4>
              <p class="text-blue-100">Access your complete customer database, add new leads, and update contact information on the go.</p>
            </div>
          </div>
          
          <div class="flex items-start space-x-4">
            <div class="bg-white/20 rounded-lg p-3 flex-shrink-0">
              <BarChart3 class="w-6 h-6" />
            </div>
            <div>
              <h4 class="text-xl font-semibold mb-2">Track Sales Pipeline</h4>
              <p class="text-blue-100">Monitor deal progress, update opportunity stages, and never miss a follow-up while on the field.</p>
            </div>
          </div>
          
          <div class="flex items-start space-x-4">
            <div class="bg-white/20 rounded-lg p-3 flex-shrink-0">
              <CheckSquare class="w-6 h-6" />
            </div>
            <div>
              <h4 class="text-xl font-semibold mb-2">Task Management</h4>
              <p class="text-blue-100">Create tasks, set reminders, and manage your daily schedule with integrated task management.</p>
            </div>
          </div>
          
          
        </div>
        
        <div class="mt-10 flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <a href="https://play.google.com/store/apps/details?id=io.bottlecrm" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-4 bg-white text-gray-900 font-semibold rounded-lg hover:bg-gray-100 transition-all duration-200 hover:scale-105 shadow-lg">
            <Download class="w-5 h-5 mr-2" />
            Download on Google Play
          </a>
          <a href="https://github.com/MicroPyramid/flutter-crm" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-4 border-2 border-white text-white font-semibold rounded-lg hover:bg-white/10 transition-all duration-200">
            <Github class="w-5 h-5 mr-2" />
            View Mobile Source
          </a>
        </div>
      </div>
      
      <!-- Right side - App showcase -->
      <div class="flex justify-center lg:justify-end">
        <div class="relative">
          <!-- Phone mockup -->
          <div class="bg-gray-900 rounded-[3rem] p-4 shadow-2xl">
            <div class="bg-white rounded-[2.5rem] overflow-hidden w-80 h-[640px] relative">
              <!-- Status bar -->
              <div class="bg-gray-100 h-8 flex items-center justify-between px-6 text-xs text-gray-600">
                <span>9:41</span>
                <div class="flex space-x-1">
                  <div class="w-4 h-2 bg-gray-400 rounded-sm"></div>
                  <div class="w-4 h-2 bg-gray-400 rounded-sm"></div>
                  <div class="w-4 h-2 bg-gray-400 rounded-sm"></div>
                </div>
              </div>
              
              <!-- App content -->
              <div class="p-6 bg-gradient-to-br from-blue-50 to-indigo-100 h-full">
                <div class="text-center mb-8">
                  <div class="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl mx-auto mb-4 flex items-center justify-center">
                    <span class="text-white font-bold text-xl">B</span>
                  </div>
                  <h3 class="text-xl font-bold text-gray-900">BottleCRM</h3>
                  <p class="text-gray-600 text-sm">Mobile CRM App</p>
                </div>
                
                <!-- Mock UI elements -->
                <div class="space-y-4">
                  <div class="bg-white rounded-lg p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-2">
                      <div class="w-24 h-3 bg-blue-200 rounded"></div>
                      <div class="w-16 h-3 bg-green-200 rounded"></div>
                    </div>
                    <div class="w-32 h-2 bg-gray-200 rounded mb-2"></div>
                    <div class="w-20 h-2 bg-gray-200 rounded"></div>
                  </div>
                  
                  <div class="bg-white rounded-lg p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-2">
                      <div class="w-28 h-3 bg-purple-200 rounded"></div>
                      <div class="w-12 h-3 bg-yellow-200 rounded"></div>
                    </div>
                    <div class="w-36 h-2 bg-gray-200 rounded mb-2"></div>
                    <div class="w-24 h-2 bg-gray-200 rounded"></div>
                  </div>
                  
                  <div class="bg-white rounded-lg p-4 shadow-sm">
                    <div class="flex items-center justify-between mb-2">
                      <div class="w-20 h-3 bg-indigo-200 rounded"></div>
                      <div class="w-18 h-3 bg-red-200 rounded"></div>
                    </div>
                    <div class="w-40 h-2 bg-gray-200 rounded mb-2"></div>
                    <div class="w-16 h-2 bg-gray-200 rounded"></div>
                  </div>
                </div>
                
                <!-- Bottom navigation mockup -->
                <div class="absolute bottom-8 left-6 right-6">
                  <div class="bg-white rounded-full p-2 shadow-lg flex justify-around">
                    <div class="w-8 h-8 bg-blue-100 rounded-full"></div>
                    <div class="w-8 h-8 bg-gray-100 rounded-full"></div>
                    <div class="w-8 h-8 bg-gray-100 rounded-full"></div>
                    <div class="w-8 h-8 bg-gray-100 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Floating elements -->
          <div class="absolute -top-4 -right-4 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-semibold animate-bounce">
            Free Download
          </div>
          <div class="absolute -bottom-4 -left-4 bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
            Open Source
          </div>
        </div>
      </div>
    </div>
    
    <!-- Stats row -->
    <div class="mt-16 text-center">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl mx-auto">
        <div>
          <div class="text-3xl font-bold text-yellow-300 mb-2">Flutter</div>
          <div class="text-blue-100">Cross-platform mobile framework</div>
        </div>
        <div>
          <div class="text-3xl font-bold text-yellow-300 mb-2">Free</div>
          <div class="text-blue-100">No app store fees or subscriptions</div>
        </div>
        <div>
          <div class="text-3xl font-bold text-yellow-300 mb-2">Open Source</div>
          <div class="text-blue-100">Fully customizable mobile CRM</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Comparison Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Why Choose BottleCRM Over <span class="text-red-600">Expensive CRM Solutions?</span>
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Compare BottleCRM with typical commercial CRM solutions and see how much you can save while getting powerful features.
      </p>
    </div>

    <div class="overflow-x-auto -mx-4 sm:mx-0">
      <div class="min-w-full inline-block align-middle">
        <table class="min-w-full bg-white rounded-xl shadow-lg overflow-hidden">
          <thead class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
            <tr>
              <th class="px-3 sm:px-6 py-4 text-left text-xs sm:text-sm font-semibold whitespace-nowrap">CRM Category</th>
              <th class="px-3 sm:px-6 py-4 text-center text-xs sm:text-sm font-semibold whitespace-nowrap">Typical Pricing</th>
              <th class="px-3 sm:px-6 py-4 text-center text-xs sm:text-sm font-semibold whitespace-nowrap">Open Source</th>
              <th class="px-3 sm:px-6 py-4 text-center text-xs sm:text-sm font-semibold whitespace-nowrap">Self-Hosted</th>
              <th class="px-3 sm:px-6 py-4 text-center text-xs sm:text-sm font-semibold whitespace-nowrap">Customizable</th>
              <th class="px-3 sm:px-6 py-4 text-center text-xs sm:text-sm font-semibold whitespace-nowrap">User Limit</th>
            </tr>
          </thead>
          <tbody>
            <tr class="border-b border-gray-200 bg-blue-50 border-l-4 border-l-blue-500">
              <td class="px-3 sm:px-6 py-4 font-semibold text-blue-700 whitespace-nowrap">
                <div class="flex flex-col sm:flex-row sm:items-center">
                  <span>BottleCRM</span>
                  <span class="mt-1 sm:mt-0 sm:ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full whitespace-nowrap">Recommended</span>
                </div>
              </td>
              <td class="px-3 sm:px-6 py-4 text-center font-medium text-green-600 text-xs sm:text-sm">Free</td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <Check class="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <Check class="w-4 h-4 sm:w-5 sm:h-5 text-green-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Yes</td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Unlimited</td>
            </tr>
            <tr class="border-b border-gray-200 hover:bg-gray-50">
              <td class="px-3 sm:px-6 py-4 font-semibold text-gray-900 whitespace-nowrap">
                <span>Enterprise CRM Solutions</span>
              </td>
              <td class="px-3 sm:px-6 py-4 text-center font-medium text-gray-700 text-xs sm:text-sm">$25-300+/user/month</td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <X class="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <X class="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Yes</td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Per seat pricing</td>
            </tr>
            <tr class="border-b border-gray-200 hover:bg-gray-50">
              <td class="px-3 sm:px-6 py-4 font-semibold text-gray-900 whitespace-nowrap">
                <span>Popular Cloud CRMs</span>
              </td>
              <td class="px-3 sm:px-6 py-4 text-center font-medium text-gray-700 text-xs sm:text-sm">$50-3200+/month</td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <X class="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <X class="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Limited</td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Contact-based pricing</td>
            </tr>
            <tr class="border-b border-gray-200 hover:bg-gray-50">
              <td class="px-3 sm:px-6 py-4 font-semibold text-gray-900 whitespace-nowrap">
                <span>Traditional CRM Platforms</span>
              </td>
              <td class="px-3 sm:px-6 py-4 text-center font-medium text-gray-700 text-xs sm:text-sm">$15-99+/user/month</td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <X class="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center">
                <X class="w-4 h-4 sm:w-5 sm:h-5 text-red-500 mx-auto" />
              </td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Limited</td>
              <td class="px-3 sm:px-6 py-4 text-center text-gray-700 text-xs sm:text-sm">Per seat pricing</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mt-8 text-center">
      <p class="text-lg text-gray-600 mb-4">
        <strong class="text-green-600">Potential Annual Savings with BottleCRM:</strong> 
        $3,000 - $36,000+ per year for a typical team
      </p>
      <a href="/pricing" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold">
        See detailed cost comparison
        <ChevronRight class="ml-2 w-4 h-4" />
      </a>
    </div>
  </div>
</section>

<!-- FAQ Section for SEO -->
<section class="py-20 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Frequently Asked Questions
      </h2>
      <p class="text-xl text-gray-600">
        Everything you need to know about BottleCRM and free CRM software.
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
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Is BottleCRM really free to use?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 0 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 0}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes! BottleCRM is 100% free and open-source. You can download, install, customize, and use it without any subscription fees or hidden costs. We also offer optional paid support services for hosting and customization.</p>
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
            <h3 class="text-lg font-semibold text-gray-900 pr-4">How does BottleCRM compare to traditional CRM platforms?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 1 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 1}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM offers many of the same core features as enterprise CRM platforms but without the high monthly costs. While some commercial CRMs might have more advanced features, BottleCRM provides everything most startups and small businesses need to manage customer relationships effectively.</p>
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
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can I self-host BottleCRM on my own servers?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 2 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 2}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Absolutely! BottleCRM is designed to be self-hosted. You have complete control over your data and can deploy it on your own servers, cloud infrastructure, or local environment. This ensures data privacy and eliminates vendor lock-in.</p>
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
            <h3 class="text-lg font-semibold text-gray-900 pr-4">What technology stack does BottleCRM use?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 3 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 3}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM is built with modern web technologies: SvelteKit 2.21.x for the frontend, Prisma for database management, TailwindCSS for styling, and includes integration capabilities with various third-party services.</p>
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
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Do you provide support for BottleCRM implementation?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 4 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 4}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes! While the software is free, we offer paid professional services including hosting setup, custom development, data migration, training, and ongoing technical support to help you get the most out of BottleCRM.</p>
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
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Is BottleCRM suitable for my industry?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 5 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 5}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">BottleCRM is industry-agnostic and works well for most businesses including SaaS startups, consulting firms, e-commerce businesses, real estate agencies, and service-based companies. Its customizable nature allows adaptation to various industry-specific needs.</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</section>

<!-- Open Source Section -->
<section class="py-20 bg-gradient-to-r from-gray-50 to-blue-50"> 
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="lg:flex lg:items-center lg:justify-between lg:space-x-12">
      <div class="lg:w-1/2">
        <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-8">
          100% Free & Open Source CRM Software
        </h2>
        <p class="text-xl text-gray-700 mb-8 leading-relaxed"> 
          BottleCRM is completely free, open-source CRM software hosted on GitHub. Download, customize, self-host, and contribute to the project without any licensing restrictions. Perfect for startups seeking a cost-effective CRM alternative to expensive subscription-based solutions.
        </p>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
          <div class="bg-white p-6 rounded-xl shadow-lg">
            <h4 class="font-bold text-gray-900 mb-2">Zero Licensing Costs</h4>
            <p class="text-gray-600 text-sm">Download and use forever without any subscription fees or hidden costs</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-lg">
            <h4 class="font-bold text-gray-900 mb-2">Complete Customization</h4>
            <p class="text-gray-600 text-sm">Modify source code to match your exact business requirements</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-lg">
            <h4 class="font-bold text-gray-900 mb-2">Self-Hosting Options</h4>
            <p class="text-gray-600 text-sm">Host on your own servers for complete data control and privacy</p>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-lg">
            <h4 class="font-bold text-gray-900 mb-2">Active Community</h4>
            <p class="text-gray-600 text-sm">Benefit from community contributions and collaborative improvements</p>
          </div>
        </div>
        
        <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
          <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-lg transition-all duration-200 hover:scale-105 whitespace-nowrap">
            <Github class="w-5 h-5 mr-2" />
            ⭐ Star on GitHub
          </a>
          <a href="https://github.com/MicroPyramid/Django-CRM/fork" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 shadow-lg transition-all duration-200 whitespace-nowrap">
            <GitFork class="w-5 h-5 mr-2" />
            Fork & Customize
          </a>
        </div>
      </div>
      
      <div class="mt-12 lg:mt-0 lg:w-1/2">
        <div class="bg-white rounded-xl p-8 border border-gray-200 shadow-xl">
          <div class="flex items-center mb-6">
            <Github class="h-10 w-10 text-gray-700 mr-4" />
            <div>
              <h3 class="text-2xl font-bold text-gray-900">MicroPyramid/Django-CRM</h3>
              <p class="text-gray-700">Free Open Source CRM: SvelteKit + Prisma</p>
            </div>
          </div>
          
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-600">2+</div>
              <div class="text-sm text-gray-600">GitHub Stars</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-green-600">0+</div>
              <div class="text-sm text-gray-600">Forks</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-purple-600">MIT</div>
              <div class="text-sm text-gray-600">License</div>
            </div>
          </div>
          
          <div class="bg-gray-900 rounded-lg p-4 text-sm font-mono text-green-400 overflow-x-auto">
            <div class="mb-2 whitespace-nowrap"># Clone and install BottleCRM</div>
            <div class="text-gray-300 whitespace-nowrap">$ git clone https://github.com/MicroPyramid/Django-CRM.git</div>
            <div class="text-gray-300 whitespace-nowrap">$ cd Django-CRM</div>
            <div class="text-gray-300 whitespace-nowrap">$ pnpm install && pnpm run dev</div>
            <div class="mt-2 text-yellow-400 whitespace-nowrap"># 🎉 Your free CRM is ready!</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Enhanced CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20 relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center">
      <h2 class="text-4xl md:text-6xl font-extrabold mb-6">
        Ready to Stop Paying for CRM?
      </h2>
      <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-4xl mx-auto leading-relaxed">
        Join the growing community of startups and small businesses who are ditching expensive CRM subscriptions. 
        Start managing customer relationships more effectively today with BottleCRM - completely free, forever.
      </p>
      
      <!-- Savings calculator -->
      <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-8 max-w-2xl mx-auto mb-12">
        <h3 class="text-2xl font-bold mb-4">💰 Your Annual Savings Calculator</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div>
            <div class="text-3xl font-bold text-yellow-300">$3,000+</div>
            <div class="text-sm text-blue-100">5 Users vs Enterprise CRM</div>
          </div>
          <div>
            <div class="text-3xl font-bold text-yellow-300">$6,000+</div>
            <div class="text-sm text-blue-100">10 Users vs Cloud CRM</div>
          </div>
          <div>
            <div class="text-3xl font-bold text-yellow-300">$18,000+</div>
            <div class="text-sm text-blue-100">30 Users vs Commercial CRM</div>
          </div>
        </div>
      </div>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
        <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
          <Zap class="w-6 h-6 mr-3" />
          Start Your Free CRM Today
        </a>
        <a href="/contact" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
          <MessageCircle class="w-6 h-6 mr-3" />
          Get Professional Support
        </a>
      </div>
      
      <p class="mt-8 text-blue-200 text-lg">
        🚀 No credit card • No setup fees • No user limits • No vendor lock-in
      </p>
    </div>
  </div>
</section>

<!-- Enhanced Stats Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
        <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
            Trusted by a Growing Global Community
        </h2>
        <p class="text-xl text-gray-600 max-w-3xl mx-auto">
            BottleCRM is empowering startups and small businesses worldwide to build better customer relationships without breaking the bank.
        </p>
    </div>
    
    <div class="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
        <div class="text-5xl font-extrabold text-blue-600 mb-2">100%</div>
        <div class="text-lg font-bold text-gray-700 mb-2">Free & Open Source</div>
        <div class="text-sm text-gray-500">No hidden costs, licensing fees, or subscription charges ever.</div>
      </div>
      
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
        <div class="text-5xl font-extrabold text-green-600 mb-2">New!</div>
        <div class="text-lg font-bold text-gray-700 mb-2">Fresh & Modern</div>
        <div class="text-sm text-gray-500">Built with the latest technologies and modern best practices.</div>
      </div>
      
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
        <div class="text-5xl font-extrabold text-purple-600 mb-2">MIT</div>
        <div class="text-lg font-bold text-gray-700 mb-2">Open License</div>
        <div class="text-sm text-gray-500">Complete freedom to use, modify, and distribute.</div>
      </div>
      
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transform transition-all duration-300 hover:scale-105 hover:shadow-2xl">
        <div class="text-5xl font-extrabold text-yellow-600 mb-2">24/7</div>
        <div class="text-lg font-bold text-gray-700 mb-2">Self-Hosted</div>
        <div class="text-sm text-gray-500">Run on your own servers with complete control over your data.</div>
      </div>
    </div>
    
    <!-- Trust badges -->
    <div class="mt-16 text-center">
      <p class="text-gray-600 mb-8 text-lg">Developed with modern, secure, high-performance technologies:</p>
      <div class="flex flex-wrap justify-center items-center gap-4">
        <div class="flex items-center space-x-2 bg-white px-4 py-2 rounded-lg shadow-md whitespace-nowrap">
          <span class="font-semibold text-gray-700">SvelteKit 2.21+</span>
        </div>
        <div class="flex items-center space-x-2 bg-white px-4 py-2 rounded-lg shadow-md whitespace-nowrap">
          <span class="font-semibold text-gray-700">Prisma ORM</span>
        </div>
        <div class="flex items-center space-x-2 bg-white px-4 py-2 rounded-lg shadow-md whitespace-nowrap">
          <span class="font-semibold text-gray-700">TailwindCSS 4.1+</span>
        </div>
      </div>
    </div>
  </div>
</section>
