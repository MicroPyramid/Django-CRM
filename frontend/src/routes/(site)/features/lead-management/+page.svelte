<script>
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { 
    Users, 
    Target,
    TrendingUp,
    Filter,
    Zap,
    Check,
    Clock,
    Star,
    ArrowRight,
    BarChart3,
    UserPlus,
    Mail,
    Phone,
    Calendar,
    Tag,
    Search,
    FileText,
    Settings,
    Database,
    Workflow,
    Bell,
    MessageSquare,
    PieChart,
    Activity,
    Award,
    Shield,
    Code,
    GitBranch,
    ChevronRight,
    Download,
    Upload,
    RefreshCw,
    MapPin,
    Building,
    DollarSign,
    Percent,
    Timer,
    Eye,
    Edit,
    Trash2,
    MoreHorizontal
  } from '@lucide/svelte';

  let mounted = false;
  
  onMount(() => {
    mounted = true;
  });

  // JSON-LD schema for SoftwareApplication
  const schema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "BottleCRM Lead Management",
    "url": "https://bottlecrm.io/features/lead-management",
    "applicationCategory": "CRM Application",
    "operatingSystem": "All",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock"
    },
    "description": "Free, open-source CRM lead management software for startups and small businesses. Capture, score, nurture, and convert leads with automated workflows.",
    "publisher": {
      "@type": "Organization",
      "name": "BottleCRM"
    }
  };
</script>

<svelte:head>
  <title>Free CRM Lead Management Software | BottleCRM</title>
  <meta name="description" content="Free, open-source CRM lead management software for startups & small businesses. Capture, score, nurture & convert leads with automated workflows." />
  <meta name="keywords" content="lead management software, free crm, lead generation, lead nurturing, open source crm, sales crm, lead scoring, crm for startups, crm for small business" />
  <link rel="canonical" href="https://bottlecrm.io/features/lead-management" />
  <meta name="robots" content="index, follow" />

  <!-- Open Graph -->
  <meta property="og:title" content="Free CRM Lead Management Software | BottleCRM" />
  <meta property="og:description" content="Free, open-source CRM lead management software for startups & small businesses. Capture, score, nurture & convert leads with automated workflows." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/features/lead-management" />
  <meta property="og:image" content="https://bottlecrm.io/og-lead-management.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Free CRM Lead Management Software | BottleCRM" />
  <meta name="twitter:description" content="Free, open-source CRM lead management software for startups & small businesses. Capture, score, nurture & convert leads with automated workflows." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-lead-management.png" />

  <script type="application/ld+json">{JSON.stringify(schema)}</script>
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
  
  <div class="max-w-7xl mx-auto py-20 px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Target class="w-4 h-4 mr-2" />
        <span class="text-sm font-medium">Convert More Leads • Accelerate Growth • 100% Free</span>
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
        Transform Prospects into <span class="text-yellow-300">Paying Customers</span>
      </h1>
      
      <p class="text-xl md:text-2xl mb-8 text-blue-100 leading-relaxed">
        Capture, score, nurture, and convert leads with BottleCRM's comprehensive lead management system. Stop losing potential customers and start maximizing your sales pipeline.
      </p>
      
      <!-- Key Benefits -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-6">
          <Target class="w-10 h-10 text-yellow-300 mx-auto mb-3" />
          <div class="text-lg font-semibold mb-2">Smart Lead Scoring</div>
          <div class="text-sm text-blue-100">Automatically identify your hottest prospects</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-6">
          <Workflow class="w-10 h-10 text-yellow-300 mx-auto mb-3" />
          <div class="text-lg font-semibold mb-2">Automated Nurturing</div>
          <div class="text-sm text-blue-100">Guide leads through personalized journeys</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-xl p-6">
          <TrendingUp class="w-10 h-10 text-yellow-300 mx-auto mb-3" />
          <div class="text-lg font-semibold mb-2">Higher Conversions</div>
          <div class="text-sm text-blue-100">Increase lead-to-customer conversion rates</div>
        </div>
      </div>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
        <a href="/login" class="inline-flex items-center justify-center px-6 py-4 border border-transparent text-base font-semibold rounded-lg text-blue-700 bg-white hover:bg-gray-100 shadow-lg transition-all duration-200 hover:scale-105">
          <Zap class="w-5 h-5 mr-2" />
          Start Managing Leads Free
        </a>
        <a href="#features" class="inline-flex items-center justify-center px-6 py-4 border-2 border-white text-base font-semibold rounded-lg text-white hover:bg-white/10 transition-all duration-200">
          Explore Lead Features
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Lead Management Process -->
<section class="py-20 bg-gray-50" id="features">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Complete Lead Management Process
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        From initial capture to final conversion, BottleCRM streamlines every step of your lead management process.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-4">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="relative bg-white rounded-2xl shadow-lg p-8 text-center group hover:shadow-2xl transition-all duration-300">
          
          <!-- Step Number -->
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
              1
            </div>
          </div>
          
          <!-- Process Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Download class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Process Content -->
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lead Capture</h3>
          <p class="text-gray-600 mb-6">Capture leads from websites, forms, emails, and social media automatically</p>
          
          <!-- Process Details -->
          <ul class="text-left space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Website form integration</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email parsing & extraction</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Social media monitoring</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Manual lead entry</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>API integrations</span>
            </li>
          </ul>
          
          <!-- Arrow -->
          <div class="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2">
            <ArrowRight class="w-6 h-6 text-blue-400" />
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 150 }}"
             class="relative bg-white rounded-2xl shadow-lg p-8 text-center group hover:shadow-2xl transition-all duration-300">
          
          <!-- Step Number -->
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
              2
            </div>
          </div>
          
          <!-- Process Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Target class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Process Content -->
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lead Qualification</h3>
          <p class="text-gray-600 mb-6">Score and qualify leads based on fit and interest levels</p>
          
          <!-- Process Details -->
          <ul class="text-left space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated lead scoring</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>BANT qualification</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Behavioral analysis</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Demographic matching</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Engagement tracking</span>
            </li>
          </ul>
          
          <!-- Arrow -->
          <div class="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2">
            <ArrowRight class="w-6 h-6 text-blue-400" />
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="relative bg-white rounded-2xl shadow-lg p-8 text-center group hover:shadow-2xl transition-all duration-300">
          
          <!-- Step Number -->
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
              3
            </div>
          </div>
          
          <!-- Process Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Mail class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Process Content -->
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lead Nurturing</h3>
          <p class="text-gray-600 mb-6">Engage leads with personalized content and follow-up sequences</p>
          
          <!-- Process Details -->
          <ul class="text-left space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email campaigns</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Content personalization</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated follow-ups</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Multi-channel outreach</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Engagement monitoring</span>
            </li>
          </ul>
          
          <!-- Arrow -->
          <div class="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2">
            <ArrowRight class="w-6 h-6 text-blue-400" />
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 450 }}"
             class="relative bg-white rounded-2xl shadow-lg p-8 text-center group hover:shadow-2xl transition-all duration-300">
          
          <!-- Step Number -->
          <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
            <div class="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
              4
            </div>
          </div>
          
          <!-- Process Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <TrendingUp class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Process Content -->
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lead Conversion</h3>
          <p class="text-gray-600 mb-6">Convert qualified leads into sales opportunities and customers</p>
          
          <!-- Process Details -->
          <ul class="text-left space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Opportunity creation</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Sales handoff process</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Conversion tracking</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>ROI measurement</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Performance analytics</span>
            </li>
          </ul>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Core Lead Management Features -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Powerful Lead Management Features
      </h2>
      <p class="text-xl text-gray-600">
        Everything you need to capture, manage, and convert leads into customers.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-2">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-gray-50 rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          
          <!-- Status Badge -->
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <!-- Feature Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <UserPlus class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Feature Content -->
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Smart Lead Capture & Import</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Capture leads from multiple sources including web forms, email campaigns, social media, and manual entry. Automatically parse contact information and prevent duplicates.</p>
          
          <!-- Feature List -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Multi-channel lead capture</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Web form integration</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email signature parsing</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Social media lead import</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Bulk CSV import/export</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Duplicate detection & merging</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>API-based lead creation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Real-time lead notifications</span>
            </div>
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 100 }}"
             class="bg-gray-50 rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          
          <!-- Status Badge -->
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <!-- Feature Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Target class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Feature Content -->
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Lead Scoring & Qualification</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Automatically score leads based on behavior, demographics, and engagement. Identify hot prospects and prioritize follow-up activities for maximum conversion.</p>
          
          <!-- Feature List -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Customizable scoring rules</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Behavioral tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Demographic scoring</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Engagement metrics</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Lead temperature indicators</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Qualification frameworks</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated lead routing</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Score history tracking</span>
            </div>
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 200 }}"
             class="bg-gray-50 rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          
          <!-- Status Badge -->
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-green-100 text-green-800 border-green-200">
              <Check class="w-3 h-3 mr-1" />
              Available Now
            </span>
          </div>
          
          <!-- Feature Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Filter class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Feature Content -->
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Advanced Lead Segmentation</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Organize leads into meaningful segments based on industry, size, behavior, or custom criteria. Create targeted campaigns and personalized follow-up strategies.</p>
          
          <!-- Feature List -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Dynamic segmentation rules</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Industry-based grouping</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Company size filtering</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Geographic segmentation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Behavior-based segments</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom field filtering</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Segment performance tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated segment updates</span>
            </div>
          </div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-gray-50 rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group relative overflow-hidden">
          
          <!-- Status Badge -->
          <div class="absolute top-4 right-4">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border bg-yellow-100 text-yellow-800 border-yellow-200">
              <Clock class="w-3 h-3 mr-1" />
              Coming Soon
            </span>
          </div>
          
          <!-- Feature Icon -->
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Workflow class="h-8 w-8 text-blue-600" />
          </div>
          
          <!-- Feature Content -->
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Lead Nurturing Workflows</h3>
          <p class="text-gray-600 mb-6 leading-relaxed">Create automated nurturing sequences to guide leads through your sales funnel. Send personalized emails, schedule follow-ups, and track engagement.</p>
          
          <!-- Feature List -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Drag-and-drop workflow builder</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email sequence automation</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Trigger-based actions</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Personalization tokens</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>A/B testing capabilities</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Multi-channel nurturing</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Engagement tracking</span>
            </div>
            <div class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Conversion optimization</span>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Lead Analytics & Metrics -->
<section class="py-20 bg-gradient-to-r from-gray-50 to-blue-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Track What Matters Most
      </h2>
      <p class="text-xl text-gray-600">
        Monitor key lead metrics and optimize your conversion funnel with actionable insights.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center hover:shadow-2xl transition-all duration-300">
          
          <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Percent class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-3">Lead Conversion Rate</h3>
          <p class="text-gray-600 mb-4 text-sm">Track the percentage of leads that convert to customers</p>
          
          <div class="text-3xl font-extrabold text-blue-600 mb-2">15-25%</div>
          <div class="text-sm text-gray-500">Industry average: 2-5%</div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 100 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center hover:shadow-2xl transition-all duration-300">
          
          <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Timer class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-3">Lead Response Time</h3>
          <p class="text-gray-600 mb-4 text-sm">Monitor how quickly your team responds to new leads</p>
          
          <div class="text-3xl font-extrabold text-blue-600 mb-2"> 5 minutes</div>
          <div class="text-sm text-gray-500">Best practice: Under 1 hour</div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 200 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center hover:shadow-2xl transition-all duration-300">
          
          <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <DollarSign class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-3">Lead Source ROI</h3>
          <p class="text-gray-600 mb-4 text-sm">Identify which channels generate the highest quality leads</p>
          
          <div class="text-3xl font-extrabold text-blue-600 mb-2">Per channel</div>
          <div class="text-sm text-gray-500">Optimize based on performance</div>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-white rounded-2xl shadow-lg p-8 text-center hover:shadow-2xl transition-all duration-300">
          
          <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Activity class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-3">Sales Cycle Length</h3>
          <p class="text-gray-600 mb-4 text-sm">Average time from lead to customer conversion</p>
          
          <div class="text-3xl font-extrabold text-blue-600 mb-2">30-60 days</div>
          <div class="text-sm text-gray-500">Varies by industry</div>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Lead Management Tools -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Complete Lead Management Toolkit
      </h2>
      <p class="text-xl text-gray-600">
        All the tools you need to manage leads effectively, integrated into one platform.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 0 }}"
             class="bg-gray-50 rounded-2xl p-8 text-center hover:bg-gray-100 transition-all duration-300 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <BarChart3 class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lead Dashboard</h3>
          <p class="text-gray-600 mb-6">Comprehensive overview of all lead activities and metrics</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Real-time lead count</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Conversion metrics</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Source analysis</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Team performance</span>
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 100 }}"
             class="bg-gray-50 rounded-2xl p-8 text-center hover:bg-gray-100 transition-all duration-300 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <Database class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Lead Database</h3>
          <p class="text-gray-600 mb-6">Centralized storage for all lead information and history</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Contact details</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Interaction history</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Document storage</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom fields</span>
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 200 }}"
             class="bg-gray-50 rounded-2xl p-8 text-center hover:bg-gray-100 transition-all duration-300 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <MessageSquare class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Communication Hub</h3>
          <p class="text-gray-600 mb-6">Manage all lead communications from one central location</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Email integration</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Call logging</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Meeting notes</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Message templates</span>
            </li>
          </ul>
        </div>

        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}"
             class="bg-gray-50 rounded-2xl p-8 text-center hover:bg-gray-100 transition-all duration-300 group">
          
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
            <FileText class="h-8 w-8 text-blue-600" />
          </div>
          
          <h3 class="text-xl font-bold text-gray-900 mb-4">Reporting Engine</h3>
          <p class="text-gray-600 mb-6">Generate detailed reports on lead performance and trends</p>
          
          <ul class="space-y-2">
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Custom reports</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Automated delivery</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Performance analytics</span>
            </li>
            <li class="flex items-center text-sm text-gray-700">
              <Check class="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
              <span>Export options</span>
            </li>
          </ul>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Benefits Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="lg:flex lg:items-center lg:justify-between lg:space-x-12">
      <div class="lg:w-1/2">
        <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-8">
          Why Choose BottleCRM for Lead Management?
        </h2>
        
        <div class="space-y-8">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-blue-100 p-3">
                <DollarSign class="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div class="ml-4">
              <h3 class="text-xl font-bold text-gray-900 mb-2">100% Free Forever</h3>
              <p class="text-gray-600">No per-lead fees, no monthly subscriptions. Use all lead management features completely free.</p>
            </div>
          </div>
          
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-green-100 p-3">
                <Shield class="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div class="ml-4">
              <h3 class="text-xl font-bold text-gray-900 mb-2">Complete Data Ownership</h3>
              <p class="text-gray-600">Self-host your lead data for complete privacy and control. No vendor lock-in.</p>
            </div>
          </div>
          
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-purple-100 p-3">
                <Settings class="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div class="ml-4">
              <h3 class="text-xl font-bold text-gray-900 mb-2">Fully Customizable</h3>
              <p class="text-gray-600">Adapt lead scoring, workflows, and processes to match your unique business needs.</p>
            </div>
          </div>
          
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <div class="rounded-lg bg-orange-100 p-3">
                <Code class="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <div class="ml-4">
              <h3 class="text-xl font-bold text-gray-900 mb-2">Open Source</h3>
              <p class="text-gray-600">Built on open-source technologies with active community support and development.</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="mt-12 lg:mt-0 lg:w-1/2">
        <div class="bg-white rounded-2xl shadow-2xl p-8">
          <h3 class="text-2xl font-bold text-gray-900 mb-6 text-center">Lead Management ROI Calculator</h3>
          
          <div class="space-y-6">
            <div class="bg-gray-50 rounded-xl p-6">
              <div class="text-center">
                <div class="text-3xl font-extrabold text-blue-600 mb-2">5x</div>
                <div class="text-sm text-gray-600">Faster Lead Response Time</div>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-green-50 rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-green-600 mb-1">+25%</div>
                <div class="text-xs text-gray-600">Conversion Rate</div>
              </div>
              <div class="bg-blue-50 rounded-xl p-4 text-center">
                <div class="text-2xl font-bold text-blue-600 mb-1">-40%</div>
                <div class="text-xs text-gray-600">Sales Cycle</div>
              </div>
            </div>
            
            <div class="text-center pt-4 border-t border-gray-200">
              <div class="text-lg font-semibold text-gray-700 mb-2">Potential Annual Savings</div>
              <div class="text-3xl font-extrabold text-green-600">$12,000+</div>
              <div class="text-sm text-gray-500">vs. paid lead management tools</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- FAQ Section -->
<section class="py-20 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Lead Management FAQs
      </h2>
      <p class="text-xl text-gray-600">
        Common questions about BottleCRM's lead management capabilities.
      </p>
    </div>

    <div class="space-y-6">
      <div class="bg-gray-50 rounded-xl p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">How does lead scoring work in BottleCRM?</h3>
        <p class="text-gray-600">BottleCRM's lead scoring system automatically evaluates leads based on demographic information, behavioral data, and engagement levels. You can customize scoring rules to match your ideal customer profile and business priorities.</p>
      </div>
      
      <div class="bg-gray-50 rounded-xl p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">Can I import leads from other systems?</h3>
        <p class="text-gray-600">Yes, BottleCRM supports bulk lead import from CSV files, API integrations, and direct migration from other CRM systems. Our duplicate detection ensures clean data integration.</p>
      </div>
      
      <div class="bg-gray-50 rounded-xl p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">How are lead nurturing workflows automated?</h3>
        <p class="text-gray-600">Create automated sequences based on triggers like lead source, behavior, or time delays. Send personalized emails, assign tasks, and move leads through your sales funnel automatically.</p>
      </div>
      
      <div class="bg-gray-50 rounded-xl p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-3">What lead analytics are available?</h3>
        <p class="text-gray-600">Track conversion rates, lead sources, response times, and pipeline velocity. Generate custom reports to identify your best-performing lead channels and optimize your strategy.</p>
      </div>
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Transform Your Lead Management?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Stop losing leads and start converting more prospects into customers. Try BottleCRM's lead management features today.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Target class="w-6 h-6 mr-3" />
        Start Managing Leads Free
      </a>
      <a href="/features" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Eye class="w-6 h-6 mr-3" />
        View All CRM Features
      </a>
    </div>
    
    <p class="mt-8 text-blue-200 text-lg">
      🚀 No credit card • Unlimited leads • Self-host anywhere • Open source
    </p>
  </div>
</section>