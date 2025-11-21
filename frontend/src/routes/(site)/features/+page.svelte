<script>
  import { fade, fly } from 'svelte/transition';
  import { 
    Users, 
    BarChart3, 
    CheckSquare, 
    TrendingUp, 
    FileText, 
    Smartphone,
    Shield,
    Zap,
    Check,
    Clock,
    Settings,
    Globe,
    MessageSquare,
    Calendar,
    Mail,
    Phone,
    Target,
    PieChart,
    Lock,
    Code,
    Cloud,
    Server,
    GitBranch,
    Palette,
    Search,
    UserCheck,
    DollarSign,
    Database,
    MapPin
  } from '@lucide/svelte';
</script>

<svelte:head>
  <title>BottleCRM Features: Free & Open Source CRM Software</title>
  <meta name="description" content="Explore BottleCRM's powerful features: contact management, sales pipeline, task automation, analytics & more. A free, open-source CRM for growing businesses." />
  <meta name="keywords" content="bottlecrm features, free crm features, open source crm, crm software features, contact management, sales pipeline, task automation, crm analytics, business management software" />
  
  <!-- Open Graph -->
  <meta property="og:title" content="BottleCRM Features: Free & Open Source CRM Software" />
  <meta property="og:description" content="Discover BottleCRM's comprehensive features: contact management, sales automation, analytics & more. Enterprise-grade, free, and open-source." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/features" />
  <meta property="og:image" content="https://bottlecrm.io/logo_social.png" />

  <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebPage",
      "name": "BottleCRM Features",
      "description": "Explore BottleCRM's powerful features: contact management, sales pipeline, task automation, analytics & more. A free, open-source CRM for growing businesses.",
      "url": "https://bottlecrm.io/features",
      "isPartOf": {
        "@type": "WebSite",
        "name": "BottleCRM",
        "url": "https://bottlecrm.io"
      },
      "mainEntity": {
        "@type": "SoftwareApplication",
        "name": "BottleCRM",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web (Cross-platform)",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD"
        },
        "description": "BottleCRM is a free and open-source Customer Relationship Management (CRM) software offering enterprise-grade features like contact management, sales pipeline, task automation, analytics, and invoicing.",
        "url": "https://bottlecrm.io",
        "softwareVersion": "1.0", // Update as versions change
        "keywords": "crm, free crm, open source crm, contact management, sales pipeline, business software",
        "featureList": [
          "Advanced Contact Management",
          "Sales Pipeline Management (Coming Soon)",
          "Task & Activity Management",
          "Communication Center (Coming Soon)",
          "Real-time Analytics Dashboard (Coming Soon)",
          "Advanced Reporting System (Coming Soon)",
          "Invoice & Billing Management (Coming Soon)",
          "Customer Support Center (Coming Soon)",
          "Marketing Campaign Management (Coming Soon)",
          "Mobile-First Design",
          "Data Security & Privacy",
          "API & Integrations (Coming Soon)",
          "Self-Hosting & Deployment",
          "Complete Customization",
          "Multi-language Support (Coming Soon)"
        ],
        "provider": {
          "@type": "Organization",
          "name": "BottleCRM",
          "url": "https://bottlecrm.io",
          "logo": "https://bottlecrm.io/logo.png" // Add a relevant logo URL
        }
      },
      "publisher": {
        "@type": "Organization",
        "name": "BottleCRM",
        "url": "https://bottlecrm.io",
        "logo": {
          "@type": "ImageObject",
          "url": "https://bottlecrm.io/logo.png" // Add a relevant logo URL
        }
      }
    }
  </script>
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
  
  <div class="max-w-7xl mx-auto py-20 px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Zap class="w-4 h-4 mr-2" />
        <span class="text-sm font-medium">Enterprise Features • Zero Cost • Open Source</span>
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
        Enterprise CRM Features at <span class="text-yellow-300">Zero Cost</span>
      </h1>
      
      <p class="text-xl md:text-2xl mb-8 text-blue-100 leading-relaxed">
        Discover powerful features that rival premium CRM solutions. From contact management to advanced analytics, everything you need without subscription fees or vendor lock-in.
      </p>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
        <a href="/login" class="inline-flex items-center justify-center px-6 py-4 border border-transparent text-base font-semibold rounded-lg text-blue-700 bg-white hover:bg-gray-100 shadow-lg transition-all duration-200 hover:scale-105">
          <Check class="w-5 h-5 mr-2" />
          Try All Features Free
        </a>
        <a href="#features" class="inline-flex items-center justify-center px-6 py-4 border-2 border-white text-base font-semibold rounded-lg text-white hover:bg-white/10 transition-all duration-200">
          Explore Features Below
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Features Overview -->
<section class="py-20 bg-gray-50" id="features">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Professional CRM Feature Set
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        BottleCRM provides enterprise-grade functionality typically found in premium CRM solutions. All features are included in our free, open-source platform with no hidden costs or limitations.
      </p>
    </div>

    <!-- Core CRM Features -->
    <div class="mb-20">
      <div class="text-center mb-12">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">Core CRM Features</h3>
        <p class="text-lg text-gray-600">Essential customer relationship management tools</p>
      </div>

      <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
        <!-- Advanced Contact Management -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Users class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Advanced Contact Management</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Centralize all customer information in one place with our comprehensive contact management system. Store detailed customer profiles, track interaction history, manage contact segmentation, and build 360-degree customer views.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Unlimited contact storage</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom fields and tags</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Contact segmentation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Interaction timeline</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Duplicate detection</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Import/Export tools</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Advanced search & filtering</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Contact scoring</span>
            </div>
          </div>
        </div>

        <!-- Sales Pipeline Management -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <BarChart3 class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Sales Pipeline Management</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Visualize and manage your entire sales process with intuitive pipeline management. Track deals from initial contact to closing, forecast revenue, and optimize conversion rates with automated workflows.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Drag-and-drop pipeline</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom deal stages</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Revenue forecasting</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Deal probability tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Sales velocity metrics</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Win/loss analysis</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Activity reminders</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Team collaboration</span>
            </div>
          </div>
        </div>

        <!-- Task & Activity Management -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <CheckSquare class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Task & Activity Management</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Never miss a follow-up with comprehensive task management. Schedule activities, set reminders, assign tasks to team members, and track completion rates to ensure maximum productivity.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Task scheduling & reminders</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Activity logging</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Team task assignment</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Priority management</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Calendar integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Recurring tasks</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Task templates</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Progress tracking</span>
            </div>
          </div>
        </div>

        <!-- Communication Center -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <MessageSquare class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Communication Center</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Manage all customer communications from one central hub. Track emails, phone calls, meetings, and notes. Maintain complete conversation history and ensure no communication falls through the cracks.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Call logging</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Meeting notes</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Communication timeline</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email templates</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Auto-response setup</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Message scheduling</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Team communication</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Analytics & Reporting -->
    <div class="mb-20">
      <div class="text-center mb-12">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">Analytics & Reporting</h3>
        <p class="text-lg text-gray-600">Business intelligence and performance insights</p>
      </div>

      <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
        <!-- Real-time Analytics Dashboard -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <TrendingUp class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Real-time Analytics Dashboard</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Get instant insights into your business performance with customizable dashboards. Monitor key metrics, track trends, and make data-driven decisions to accelerate growth.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Customizable dashboards</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Real-time data updates</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Key performance indicators</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Visual chart library</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Goal tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Comparative analysis</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Export capabilities</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Mobile dashboard access</span>
            </div>
          </div>
        </div>

        <!-- Advanced Reporting System -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <PieChart class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Advanced Reporting System</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Generate comprehensive reports on sales performance, customer behavior, and business metrics. Create custom reports, schedule automated delivery, and share insights with stakeholders.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom report builder</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated report scheduling</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Multiple export formats</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Interactive charts</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Data filtering options</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Report templates</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Team sharing</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Historical comparisons</span>
            </div>
          </div>
        </div>

        <!-- Sales Performance Analytics -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Target class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Sales Performance Analytics</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Track and analyze sales team performance with detailed metrics. Monitor individual and team achievements, identify top performers, and optimize sales strategies.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Individual performance tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Team leaderboards</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Conversion rate analysis</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Activity reports</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Revenue attribution</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Performance benchmarking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Commission calculations</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Sales coaching insights</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Business Management -->
    <div class="mb-20">
      <div class="text-center mb-12">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">Business Management</h3>
        <p class="text-lg text-gray-600">Comprehensive business process automation</p>
      </div>

      <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
        <!-- Invoice & Billing Management -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <FileText class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Invoice & Billing Management</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Streamline your billing process with integrated invoicing. Create professional invoices, track payments, manage recurring billing, and integrate with payment gateways.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Professional invoice templates</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated invoice generation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Payment tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Recurring billing setup</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Payment gateway integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Tax calculations</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Late payment reminders</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Financial reporting</span>
            </div>
          </div>
        </div>

        <!-- Customer Support Center -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <UserCheck class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Customer Support Center</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Provide exceptional customer support with integrated ticketing system. Track support requests, manage resolution workflows, and maintain customer satisfaction.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Ticket management system</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Support workflow automation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Customer satisfaction surveys</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Knowledge base integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Multi-channel support</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>SLA tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Escalation rules</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Support analytics</span>
            </div>
          </div>
        </div>

        <!-- Marketing Campaign Management -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Mail class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Marketing Campaign Management</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Plan, execute, and track marketing campaigns with integrated tools. Manage email campaigns, track ROI, and nurture leads through automated marketing workflows.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email campaign builder</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Marketing automation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Lead nurturing workflows</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Campaign performance tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>A/B testing</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Landing page integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Social media management</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>ROI measurement</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Technical Features -->
    <div class="mb-20">
      <div class="text-center mb-12">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">Technical Features</h3>
        <p class="text-lg text-gray-600">Modern technology and infrastructure capabilities</p>
      </div>

      <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
        <!-- Mobile-First Design -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Smartphone class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Mobile-First Design</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Access your CRM from anywhere with our responsive, mobile-optimized interface. Work offline, sync data automatically, and manage your business on-the-go.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Responsive web design</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Offline data access</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automatic synchronization</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Touch-optimized interface</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Mobile notifications</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Cross-device compatibility</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Progressive web app</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Fast loading times</span>
            </div>
          </div>
        </div>

        <!-- Data Security & Privacy -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Shield class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Data Security & Privacy</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Protect your business data with enterprise-grade security features. Enjoy encrypted data storage, user access controls, and complete data ownership through self-hosting.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>End-to-end encryption</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Role-based access control</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Data backup & recovery</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Audit trail logging</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>GDPR compliance tools</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Two-factor authentication</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>IP restrictions</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Security monitoring</span>
            </div>
          </div>
        </div>

        <!-- API & Integrations -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Code class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">API & Integrations</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Connect BottleCRM with your existing tools through our comprehensive API. Build custom integrations, automate workflows, and create a unified business ecosystem.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>RESTful API access</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Webhook support</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Third-party integrations</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom field mapping</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Data import/export</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Zapier integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>OAuth authentication</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>API documentation</span>
            </div>
          </div>
        </div>

        <!-- Self-Hosting & Deployment -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Server class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Self-Hosting & Deployment</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Deploy BottleCRM on your own infrastructure for complete control. Choose from various hosting options, scale as needed, and maintain full data sovereignty.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Docker containerization</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Cloud deployment guides</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Database flexibility</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Scalable architecture</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Load balancing support</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated backups</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Environment configuration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Performance monitoring</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Customization & Flexibility -->
    <div class="mb-20">
      <div class="text-center mb-12">
        <h3 class="text-3xl font-bold text-gray-900 mb-4">Customization & Flexibility</h3>
        <p class="text-lg text-gray-600">Adapt BottleCRM to your unique business needs</p>
      </div>

      <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
        <!-- Complete Customization -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Settings class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Complete Customization</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Tailor BottleCRM to your exact business needs with extensive customization options. Modify workflows, create custom fields, and adapt the interface to match your processes.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom field creation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Workflow customization</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>UI theme customization</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Form builder</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom data validation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Business rule engine</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Layout customization</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Brand integration</span>
            </div>
          </div>
        </div>

        <!-- Multi-language Support -->
        <div class="bg-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Globe class="h-8 w-8 text-blue-600" />
          </div>
          
          <h4 class="text-2xl font-bold text-gray-900 mb-4">Multi-language Support</h4>
          <p class="text-gray-600 mb-6 leading-relaxed">Use BottleCRM in your preferred language with comprehensive internationalization support. Easily add new languages and adapt to local business requirements.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Multiple language support</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>RTL text support</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Currency localization</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Date/time formatting</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Number formatting</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Timezone handling</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Cultural adaptations</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Translation management</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Technology Stack -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Built with Modern Technology
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        BottleCRM is built using cutting-edge technologies to ensure performance, security, and maintainability.
      </p>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
      <div class="text-center p-6 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
        <Code class="w-12 h-12 text-blue-600 mx-auto mb-4" />
        <h4 class="font-bold text-gray-900 mb-2">SvelteKit 2.21+</h4>
        <p class="text-sm text-gray-600">Modern web framework</p>
      </div>
      <div class="text-center p-6 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
        <Database class="w-12 h-12 text-green-600 mx-auto mb-4" />
        <h4 class="font-bold text-gray-900 mb-2">Prisma ORM</h4>
        <p class="text-sm text-gray-600">Database management</p>
      </div>
      <div class="text-center p-6 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
        <Palette class="w-12 h-12 text-purple-600 mx-auto mb-4" />
        <h4 class="font-bold text-gray-900 mb-2">TailwindCSS 4.1+</h4>
        <p class="text-sm text-gray-600">Modern styling</p>
      </div>
      <div class="text-center p-6 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
        <GitBranch class="w-12 h-12 text-orange-600 mx-auto mb-4" />
        <h4 class="font-bold text-gray-900 mb-2">Open Source</h4>
        <p class="text-sm text-gray-600">MIT License</p>
      </div>
    </div>
  </div>
</section>

<!-- Feature Comparison -->
<section class="py-20 bg-gradient-to-r from-gray-50 to-blue-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Compare Feature Availability
      </h2>
      <p class="text-xl text-gray-600">
        See what's available now and what's coming soon in BottleCRM development roadmap.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-2">
      <!-- Available Now -->
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-green-100 p-3 mr-4">
            <Check class="w-8 h-8 text-green-600" />
          </div>
          <div>
            <h3 class="text-2xl font-bold text-gray-900">Available Now</h3>
            <p class="text-gray-600">Ready to use features</p>
          </div>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <Check class="w-5 h-5 text-green-500 mr-3" />
            <span>Advanced Contact Management</span>
          </li>
          <li class="flex items-center">
            <Check class="w-5 h-5 text-green-500 mr-3" />
            <span>Task & Activity Management</span>
          </li>
          <li class="flex items-center">
            <Check class="w-5 h-5 text-green-500 mr-3" />
            <span>Mobile-First Design</span>
          </li>
          <li class="flex items-center">
            <Check class="w-5 h-5 text-green-500 mr-3" />
            <span>Data Security & Privacy</span>
          </li>
          <li class="flex items-center">
            <Check class="w-5 h-5 text-green-500 mr-3" />
            <span>Self-Hosting & Deployment</span>
          </li>
          <li class="flex items-center">
            <Check class="w-5 h-5 text-green-500 mr-3" />
            <span>Complete Customization</span>
          </li>
        </ul>
      </div>

      <!-- Coming Soon -->
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-yellow-100 p-3 mr-4">
            <Clock class="w-8 h-8 text-yellow-600" />
          </div>
          <div>
            <h3 class="text-2xl font-bold text-gray-900">Coming Soon</h3>
            <p class="text-gray-600">In active development</p>
          </div>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <Clock class="w-5 h-5 text-yellow-500 mr-3" />
            <span>Sales Pipeline Management</span>
          </li>
          <li class="flex items-center">
            <Clock class="w-5 h-5 text-yellow-500 mr-3" />
            <span>Real-time Analytics Dashboard</span>
          </li>
          <li class="flex items-center">
            <Clock class="w-5 h-5 text-yellow-500 mr-3" />
            <span>Invoice & Billing Management</span>
          </li>
          <li class="flex items-center">
            <Clock class="w-5 h-5 text-yellow-500 mr-3" />
            <span>Communication Center</span>
          </li>
          <li class="flex items-center">
            <Clock class="w-5 h-5 text-yellow-500 mr-3" />
            <span>API & Integrations</span>
          </li>
          <li class="flex items-center">
            <Clock class="w-5 h-5 text-yellow-500 mr-3" />
            <span>Multi-language Support</span>
          </li>
        </ul>
      </div>
    </div>
    
    <div class="text-center mt-12">
      <p class="text-lg text-gray-600 mb-6">
        Want to contribute to feature development or request a specific feature?
      </p>
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
        <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 shadow-lg transition-all duration-200">
          <GitBranch class="w-5 h-5 mr-2" />
          Contribute on GitHub
        </a>
        <a href="/contact" class="inline-flex items-center justify-center px-6 py-3 border border-gray-300 text-base font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 shadow-lg transition-all duration-200">
          <MessageSquare class="w-5 h-5 mr-2" />
          Request Feature
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Value Proposition Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Why Choose BottleCRM?
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Unlike traditional CRM solutions, BottleCRM offers enterprise-grade features without the enterprise price tag.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-3">
      <!-- Cost-Effective -->
      <div class="text-center p-8 bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl">
        <div class="rounded-xl bg-green-100 p-4 inline-block mb-6">
          <DollarSign class="h-8 w-8 text-green-600" />
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Cost-Effective Solution</h3>
        <p class="text-gray-600 mb-6">
          Save thousands on CRM costs while getting professional features. No per-user fees, no monthly subscriptions, no surprise charges.
        </p>
        <ul class="text-left space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>$0 monthly fees</span>
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>Unlimited users</span>
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>No feature restrictions</span>
          </li>
        </ul>
      </div>

      <!-- Data Ownership -->
      <div class="text-center p-8 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl">
        <div class="rounded-xl bg-blue-100 p-4 inline-block mb-6">
          <Lock class="h-8 w-8 text-blue-600" />
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Complete Data Control</h3>
        <p class="text-gray-600 mb-6">
          Your data stays yours. Self-host on your infrastructure with full control over security, privacy, and compliance.
        </p>
        <ul class="text-left space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>Self-hosted deployment</span>
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>No vendor lock-in</span>
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>GDPR compliance ready</span>
          </li>
        </ul>
      </div>

      <!-- Customization Freedom -->
      <div class="text-center p-8 bg-gradient-to-br from-purple-50 to-pink-50 rounded-2xl">
        <div class="rounded-xl bg-purple-100 p-4 inline-block mb-6">
          <Code class="h-8 w-8 text-purple-600" />
        </div>
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Unlimited Customization</h3>
        <p class="text-gray-600 mb-6">
          Modify and extend BottleCRM to fit your exact needs. Open-source means no limitations on customization.
        </p>
        <ul class="text-left space-y-2">
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>Full source code access</span>
                   </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>Custom integrations</span>
          </li>
          <li class="flex items-center text-sm text-gray-700">
            <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
            <span>Community support</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Experience Professional CRM Features?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Join businesses that have chosen BottleCRM for enterprise-grade features without enterprise costs.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Zap class="w-6 h-6 mr-3" />
        Start Using All Features Free
      </a>
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Code class="w-6 h-6 mr-3" />
        View Source Code
      </a>
    </div>
    
    <p class="mt-8 text-blue-200 text-lg">
      🚀 No subscription fees • Enterprise features included • Deploy anywhere
    </p>
  </div>
</section>