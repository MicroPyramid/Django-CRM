<!-- account management page -->
<script>
  import { fade, fly } from 'svelte/transition';
  import { 
    Users, 
    UserCheck,
    Database,
    Search,
    Filter,
    Tag,
    MapPin,
    Building,
    Phone,
    Mail,
    Calendar,
    Clock,
    TrendingUp,
    BarChart3,
    Shield,
    Upload,
    Download,
    RefreshCw,
    Check,
    Star,
    Target,
    Zap,
    Settings,
    Archive,
    UserPlus,
    Eye,
    Edit,
    Trash2,
    Copy,
    FileText,
    Globe,
    Lock,
    Smartphone,
    ChevronRight,
    MessageSquare,
    DollarSign,
    Award,
    Activity,
    Layers,
    GitBranch
  } from '@lucide/svelte';
</script>

<svelte:head>
  <title>Free Account Management CRM | Unlimited Contacts & Customer Database</title>
  <meta name="description" content="Manage unlimited customer accounts and contacts with BottleCRM. Free, open-source CRM for businesses to centralize data, track interactions, and grow relationships." />
  <meta name="keywords" content="free crm, account management, contact management, customer database, open source crm, unlimited contacts, client management software, business crm" />
  
  <!-- Open Graph -->
  <meta property="og:title" content="Free Account Management CRM | Unlimited Contacts & Customer Database" />
  <meta property="og:description" content="BottleCRM offers free, unlimited account and contact management. Centralize customer data, track interactions, and grow your business relationships." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/features/account-management" />

  <!-- Schema.org Structured Data -->
  <script type="application/ld+json">
    {`
      {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "BottleCRM",
        "applicationCategory": "Customer Relationship Management",
        "operatingSystem": "Web",
        "offers": {
          "@type": "Offer",
          "price": "0",
          "priceCurrency": "USD"
        },
        "description": "BottleCRM is a free, open-source CRM application for unlimited account and contact management. Centralize customer data, track interactions, and manage your business relationships efficiently.",
        "url": "https://bottlecrm.io/features/account-management",
        "publisher": {
          "@type": "Organization",
          "name": "BottleCRM"
        }
      }
    `}
  </script>
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
  
  <div class="max-w-7xl mx-auto py-20 px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Users class="w-4 h-4 mr-2" />
        <span class="text-sm font-medium">Account Management • 100% Free • Unlimited Contacts</span>
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
        Master Customer <span class="text-yellow-300">Account Management</span> with BottleCRM
      </h1>
      
      <p class="text-xl md:text-2xl mb-8 text-blue-100 leading-relaxed">
        Centralize customer information, track every interaction, and build stronger relationships with our comprehensive, free account management system. Everything you need to manage unlimited contacts and accounts.
      </p>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-4">
        <a href="/login" class="inline-flex items-center justify-center px-6 py-4 border border-transparent text-base font-semibold rounded-lg text-blue-700 bg-white hover:bg-gray-100 shadow-lg transition-all duration-200 hover:scale-105">
          <Zap class="w-5 h-5 mr-2" />
          Start Managing Accounts Free
        </a>
        <a href="#features" class="inline-flex items-center justify-center px-6 py-4 border-2 border-white text-base font-semibold rounded-lg text-white hover:bg-white/10 transition-all duration-200">
          Explore Account Features
        </a>
      </div>
    </div>
  </div>
</section>

<!-- Core Features Section -->
<section class="py-20 bg-gray-50" id="features">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Complete Account Management Solution
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Everything you need to manage customer accounts, contacts, and relationships in one comprehensive, free platform.
      </p>
    </div>

    <div class="space-y-16">
      <!-- Feature 1: Centralized Contact Database -->
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-8">
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Database class="h-10 w-10 text-blue-600" />
          </div>
          
          <h3 class="text-3xl font-bold text-gray-900 mb-4">Centralized Contact Database</h3>
          <p class="text-xl text-gray-600 mb-6 leading-relaxed max-w-3xl mx-auto">Store unlimited contacts with comprehensive profile information. Never lose track of important customer details with our centralized contact management system.</p>
          <p class="text-gray-700 mb-8 leading-relaxed max-w-4xl mx-auto">Our contact database serves as the foundation of your CRM, allowing you to store detailed information about every customer, prospect, and business contact. With unlimited storage capacity and rich data fields, you can maintain comprehensive records that grow with your business.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Unlimited contact storage</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Rich profile information</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Contact relationship mapping</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Duplicate detection & merging</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Historical data preservation</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Cross-reference capabilities</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Feature 2: Advanced Contact Search & Filtering -->
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-8">
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Search class="h-10 w-10 text-blue-600" />
          </div>
          
          <h3 class="text-3xl font-bold text-gray-900 mb-4">Advanced Contact Search & Filtering</h3>
          <p class="text-xl text-gray-600 mb-6 leading-relaxed max-w-3xl mx-auto">Find any contact instantly with powerful search capabilities and advanced filtering options. Organize and segment your contacts for targeted communication.</p>
          <p class="text-gray-700 mb-8 leading-relaxed max-w-4xl mx-auto">Our intelligent search system allows you to quickly locate contacts using any piece of information - name, company, email, phone, or custom fields. Advanced filters help you create targeted lists for marketing campaigns and sales outreach.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Global search functionality</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Multi-criteria filtering</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Saved search queries</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Real-time search results</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Custom search operators</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Bulk action capabilities</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Feature 3: Contact Segmentation & Tagging -->
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-8">
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Tag class="h-10 w-10 text-blue-600" />
          </div>
          
          <h3 class="text-3xl font-bold text-gray-900 mb-4">Contact Segmentation & Tagging</h3>
          <p class="text-xl text-gray-600 mb-6 leading-relaxed max-w-3xl mx-auto">Organize contacts into meaningful groups with custom tags and segments. Create targeted lists for personalized marketing and sales activities.</p>
          <p class="text-gray-700 mb-8 leading-relaxed max-w-4xl mx-auto">Effective contact segmentation is crucial for personalized communication. Our tagging and segmentation tools allow you to group contacts based on any criteria, from demographics to purchase behavior, enabling more targeted and effective outreach.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Custom tag creation</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Automated segmentation rules</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Behavioral segmentation</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Demographic grouping</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Interest-based categories</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Dynamic list updates</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Feature 4: Contact Interaction Timeline -->
      <div class="max-w-5xl mx-auto">
        <div class="text-center mb-8">
          <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6">
            <Clock class="h-10 w-10 text-blue-600" />
          </div>
          
          <h3 class="text-3xl font-bold text-gray-900 mb-4">Contact Interaction Timeline</h3>
          <p class="text-xl text-gray-600 mb-6 leading-relaxed max-w-3xl mx-auto">Track every interaction with your contacts in a visual timeline. Maintain complete communication history and never miss important context.</p>
          <p class="text-gray-700 mb-8 leading-relaxed max-w-4xl mx-auto">Understanding the complete history of your relationship with each contact is essential for effective customer management. Our timeline feature captures every email, call, meeting, and interaction, providing valuable context for future communications.</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl mx-auto">
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Complete interaction history</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Visual timeline view</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Multi-channel tracking</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Automated activity logging</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Context preservation</span>
            </div>
            <div class="flex items-center bg-white rounded-lg p-4 shadow-sm border border-gray-100">
              <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
              <span class="text-gray-700 text-sm font-medium">Team collaboration notes</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Account Management Capabilities -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Comprehensive Account Management Capabilities
      </h2>
      <p class="text-xl text-gray-600">
        Handle every aspect of customer account management with these powerful features.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
      <!-- Capability 1: Company & Organization Management -->
      <div class="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <Building class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Company & Organization Management</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Manage company accounts with multiple contacts, organizational hierarchies, and account-level information tracking.</p>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Multi-contact accounts</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Organizational charts</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Account hierarchies</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Company profile management</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Revenue tracking per account</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Account status management</span>
          </li>
        </ul>
      </div>

      <!-- Capability 2: Contact Information Management -->
      <div class="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <UserCheck class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Contact Information Management</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Store comprehensive contact details including personal information, communication preferences, and custom data fields.</p>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Personal & professional details</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Multiple contact methods</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Communication preferences</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Custom field support</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Photo & document storage</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Social media integration</span>
          </li>
        </ul>
      </div>

      <!-- Capability 3: Geographic & Location Tracking -->
      <div class="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <MapPin class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Geographic & Location Tracking</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Track contact locations, territories, and geographic information for better sales territory management and local marketing.</p>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Address management</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Territory assignment</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Geographic analytics</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Location-based filtering</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Regional reporting</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Map visualization</span>
          </li>
        </ul>
      </div>

      <!-- Capability 4: Contact Communication Hub -->
      <div class="bg-gradient-to-br from-gray-50 to-white rounded-2xl shadow-lg p-8 transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl border border-gray-100 group">
        <div class="rounded-xl bg-gradient-to-r from-blue-100 to-indigo-100 p-4 inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
          <MessageSquare class="h-8 w-8 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Contact Communication Hub</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Centralize all communication channels including email, phone, social media, and in-person meetings with full tracking.</p>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Email integration</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Call logging</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Meeting scheduling</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Social media tracking</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Communication templates</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Response tracking</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- Data Management Section -->
<section class="py-20 bg-gradient-to-r from-gray-50 to-blue-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Advanced Data Management
      </h2>
      <p class="text-xl text-gray-600">
        Secure, reliable, and efficient data handling for all your account management needs.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-3">
      <!-- Data Feature 1: Data Import & Export -->
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl">
        <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-6 inline-block mb-6">
          <Upload class="h-10 w-10 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Data Import & Export</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Easily migrate your existing contact data or export for backup and analysis purposes.</p>
        
        <ul class="space-y-2 text-left">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">CSV/Excel import</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Multiple data formats</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Field mapping tools</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Bulk data validation</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Export scheduling</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3" />
            <span class="text-gray-700">Data transformation</span>
          </li>
        </ul>
      </div>

      <!-- Data Feature 2: Data Security & Privacy -->
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl">
        <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-6 inline-block mb-6">
          <Shield class="h-10 w-10 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Data Security & Privacy</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Protect sensitive contact information with enterprise-grade security and privacy controls.</p>
        
        <ul class="space-y-2 text-left">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Data encryption</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Access control</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Audit trails</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">GDPR compliance</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Data retention policies</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Privacy settings</span>
          </li>
        </ul>
      </div>

      <!-- Data Feature 3: Real-time Data Sync -->
      <div class="bg-white rounded-2xl shadow-xl p-8 text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl">
        <div class="rounded-full bg-gradient-to-r from-blue-100 to-indigo-100 p-6 inline-block mb-6">
          <RefreshCw class="h-10 w-10 text-blue-600" />
        </div>
        
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Real-time Data Sync</h3>
        <p class="text-gray-600 mb-6 leading-relaxed">Keep contact information synchronized across all devices and team members in real-time.</p>
        
        <ul class="space-y-2 text-left">
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Automatic synchronization</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Conflict resolution</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Offline data access</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Multi-device support</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Team collaboration</span>
          </li>
          <li class="flex items-center">
            <Check class="w-4 h-4 text-green-500 mr-3 flex-shrink-0" />
            <span class="text-gray-700">Version control</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- Benefits by User Type -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Benefits for Every Team
      </h2>
      <p class="text-xl text-gray-600">
        See how different teams can leverage BottleCRM's account management features.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
      <!-- Sales Teams -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <Target class="h-8 w-8 text-blue-600" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900">Sales Teams</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Complete prospect information at your fingertips</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Track sales interactions and follow-ups</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Identify warm leads and opportunities</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Maintain consistent communication history</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Coordinate team efforts on large accounts</span>
          </li>
        </ul>
      </div>

      <!-- Marketing Teams -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <Award class="h-8 w-8 text-blue-600" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900">Marketing Teams</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Create targeted marketing segments</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Track campaign engagement and responses</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Personalize marketing communications</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Measure marketing ROI by contact</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Generate qualified leads for sales</span>
          </li>
        </ul>
      </div>

      <!-- Customer Support -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <UserCheck class="h-8 w-8 text-blue-600" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900">Customer Support</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Access complete customer history instantly</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Provide personalized support experiences</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Track support interactions and resolutions</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Identify recurring issues by account</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Maintain customer satisfaction records</span>
          </li>
        </ul>
      </div>

      <!-- Business Owners -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <TrendingUp class="h-8 w-8 text-blue-600" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900">Business Owners</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Get complete view of customer relationships</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Track business growth and customer acquisition</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Identify most valuable accounts and contacts</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Make data-driven business decisions</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5" />
            <span class="text-gray-700">Ensure no customer falls through cracks</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- Implementation Guide -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Implementation Roadmap
      </h2>
      <p class="text-xl text-gray-600">
        Get started with BottleCRM account management in three simple steps.
      </p>
    </div>

    <div class="space-y-8">
      <!-- Step 1 -->
      <div class="lg:flex lg:items-center lg:space-x-8">
        <div class="flex-shrink-0 mb-6 lg:mb-0">
          <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            1
          </div>
        </div>
        
        <div class="bg-white rounded-2xl shadow-lg p-8 flex-1">
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Data Migration & Setup</h3>
          <p class="text-gray-600 mb-6">Import existing contact data and configure account structure</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Import contact databases</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Set up custom fields</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Configure user permissions</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Establish data validation rules</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2 -->
      <div class="lg:flex lg:items-center lg:space-x-8">
        <div class="flex-shrink-0 mb-6 lg:mb-0">
          <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            2
          </div>
        </div>
        
        <div class="bg-white rounded-2xl shadow-lg p-8 flex-1">
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Team Training & Onboarding</h3>
          <p class="text-gray-600 mb-6">Train your team on account management best practices</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">User training sessions</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Workflow establishment</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Data entry standards</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Regular usage monitoring</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="lg:flex lg:items-center lg:space-x-8">
        <div class="flex-shrink-0 mb-6 lg:mb-0">
          <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
            3
          </div>
        </div>
        
        <div class="bg-white rounded-2xl shadow-lg p-8 flex-1">
          <h3 class="text-2xl font-bold text-gray-900 mb-4">Process Optimization</h3>
          <p class="text-gray-600 mb-6">Fine-tune your account management processes for maximum efficiency</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Performance monitoring</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Process refinement</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Advanced feature adoption</span>
            </div>
            <div class="flex items-center">
              <Check class="w-4 h-4 text-green-500 mr-3" />
              <span class="text-gray-700">Continuous improvement</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Feature Comparison -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 sm:text-5xl mb-6">
        Why Choose BottleCRM for Account Management?
      </h2>
      <p class="text-xl text-gray-600">
        Compare our account management features with traditional CRM solutions.
      </p>
    </div>

    <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
            <tr>
              <th class="px-6 py-4 text-left text-sm font-semibold">Feature</th>
              <th class="px-6 py-4 text-center text-sm font-semibold">BottleCRM</th>
              <th class="px-6 py-4 text-center text-sm font-semibold">Enterprise CRM A</th>
              <th class="px-6 py-4 text-center text-sm font-semibold">Popular CRM B</th>
              <th class="px-6 py-4 text-center text-sm font-semibold">Commercial CRM C</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium text-gray-900">Unlimited Contacts</td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
              <td class="px-6 py-4 text-center text-gray-500">Paid plans only</td>
              <td class="px-6 py-4 text-center text-gray-500">Limited in free</td>
              <td class="px-6 py-4 text-center text-gray-500">Paid only</td>
            </tr>
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium text-gray-900">Custom Fields</td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
            </tr>
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium text-gray-900">Self-Hosting Option</td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
              <td class="px-6 py-4 text-center text-gray-500">Limited</td>
              <td class="px-6 py-4 text-center text-gray-500">Not available</td>
              <td class="px-6 py-4 text-center text-gray-500">Enterprise only</td>
            </tr>
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium text-gray-900">Monthly Cost Range</td>
              <td class="px-6 py-4 text-center font-bold text-green-600">$0</td>
              <td class="px-6 py-4 text-center text-gray-700">$25-300/user*</td>
              <td class="px-6 py-4 text-center text-gray-700">$50-3200/month*</td>
              <td class="px-6 py-4 text-center text-gray-700">$15-99/user*</td>
            </tr>
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 font-medium text-gray-900">Open Source</td>
              <td class="px-6 py-4 text-center"><Check class="w-5 h-5 text-green-500 mx-auto" /></td>
              <td class="px-6 py-4 text-center text-gray-500">Proprietary</td>
              <td class="px-6 py-4 text-center text-gray-500">Proprietary</td>
              <td class="px-6 py-4 text-center text-gray-500">Proprietary</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <div class="text-center mt-8">
      <p class="text-lg text-gray-600 mb-4">
        <strong class="text-green-600">Potential Annual Savings:</strong> $3,000 - $36,000 per year for a 10-person team*
      </p>
      <p class="text-sm text-gray-500 italic">
        * Pricing estimates based on publicly available information and market research. Actual pricing may vary. 
        Comparison is for illustrative purposes only and does not represent specific vendor quotes.
      </p>
    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-700 via-blue-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Transform Your Account Management?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
      Start managing unlimited contacts and accounts today with BottleCRM's comprehensive, free account management system.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="/login" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-blue-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Zap class="w-6 h-6 mr-3" />
        Start Managing Accounts Free
      </a>
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <GitBranch class="w-6 h-6 mr-3" />
        View Source Code
      </a>
    </div>
    
    <p class="mt-8 text-blue-200 text-lg">
      🚀 No credit card required • Unlimited contacts • Self-host anywhere • Full customization
    </p>
  </div>
</section>
