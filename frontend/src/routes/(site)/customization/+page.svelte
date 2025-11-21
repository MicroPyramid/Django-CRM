<script>
  import { onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import { 
    Palette,
    Code,
    Wrench,
    Zap,
    Check,
    X,
    Download,
    Github,
    MessageCircle,
    Settings,
    Brush,
    Database,
    Plug,
    Users,
    Shield,
    Smartphone,
    Cloud,
    ChevronDown,
    ChevronRight,
    Star,
    Lightbulb,
    Cog,
    Layout,
    FileCode,
    ArrowRight
  } from '@lucide/svelte';

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
</script>

<svelte:head>
  <title>BottleCRM Customization: Free Open Source CRM & Custom Development</title>
  <meta name="description" content="Customize BottleCRM, the free open-source CRM, to fit your business. DIY tools & expert services for branding, integrations, and workflow automation. Unlimited possibilities." />
  <meta name="keywords" content="free crm, open source crm, crm customization, custom crm development, crm integration, svelte crm, crm workflow, crm api, bottlecrm, business crm, crm software" />
  <link rel="canonical" href="https://bottlecrm.io/customization" />
  <meta name="robots" content="index, follow" />

  <!-- Open Graph -->
  <meta property="og:title" content="BottleCRM Customization: Free Open Source CRM & Custom Development" />
  <meta property="og:description" content="Customize BottleCRM to fit your business. Free CRM with unlimited customization, DIY guides, and professional services." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/customization" />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="BottleCRM Customization: Free Open Source CRM & Custom Development" />
  <meta name="twitter:description" content="Customize BottleCRM to fit your business. Free CRM with unlimited customization, DIY guides, and professional services." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Structured Data: SoftwareApplication & Service -->
  <script type="application/ld+json">
    {JSON.stringify({
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
      "license": "https://opensource.org/licenses/MIT",
      "url": "https://bottlecrm.io",
      "description": "BottleCRM is a free, open-source CRM application with unlimited customization, DIY tools, and professional development services.",
      "publisher": {
        "@type": "Organization",
        "name": "BottleCRM"
      }
    })}
  </script>
  <script type="application/ld+json">
    {JSON.stringify({
      "@context": "https://schema.org",
      "@type": "Service",
      "name": "BottleCRM Customization Services",
      "description": "Professional and DIY CRM customization for BottleCRM: branding, integrations, workflow automation, and more.",
      "provider": {
        "@type": "Organization",
        "name": "BottleCRM"
      },
      "areaServed": "Worldwide",
      "offers": [
        {
          "@type": "Offer",
          "name": "Professional Customization",
          "price": "497",
          "priceCurrency": "USD"
        },
        {
          "@type": "Offer",
          "name": "Enterprise Customization",
          "price": "1497",
          "priceCurrency": "USD"
        }
      ]
    })}
  </script>
</svelte:head>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-purple-600 via-indigo-700 to-blue-800 text-white py-20 relative overflow-hidden">
  <div class="absolute inset-0 bg-black/10"></div>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
    <div class="text-center max-w-4xl mx-auto">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Lightbulb class="w-4 h-4 mr-2" />
        <span class="text-sm font-medium">100% Customizable • Open Source Freedom</span>
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold mb-6 leading-tight">
        Make BottleCRM <span class="text-yellow-300">Uniquely Yours</span>
      </h1>
      
      <p class="text-xl md:text-2xl text-blue-100 mb-8 leading-relaxed">
        Transform your free CRM into the perfect solution for your business. From simple branding changes to complex integrations - customize everything with complete source code access or professional development services.
      </p>
      
      <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6 mb-12">
        <a href="#customization-types" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-purple-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
          <Code class="w-6 h-6 mr-3" />
          Explore Customization Options
        </a>
        <a href="/contact" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
          <MessageCircle class="w-6 h-6 mr-3" />
          Get Professional Help
        </a>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto">
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <div class="text-2xl font-bold text-yellow-300">100%</div>
          <div class="text-sm text-blue-200">Source Code Access</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <div class="text-2xl font-bold text-yellow-300">∞</div>
          <div class="text-sm text-blue-200">Customization Possibilities</div>
        </div>
        <div class="bg-white/10 backdrop-blur-sm rounded-lg p-4">
          <div class="text-2xl font-bold text-yellow-300">MIT</div>
          <div class="text-sm text-blue-200">Open Source License</div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Customization Types Section -->
<section id="customization-types" class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Four Levels of Customization
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        From simple visual changes to complex enterprise modifications - choose the level of customization that fits your needs and technical expertise.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-2">
      <!-- Visual Customization -->
      <div class="bg-white rounded-2xl shadow-xl p-8 transition-all duration-300 hover:shadow-2xl border border-gray-100">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center">
            <div class="rounded-xl bg-gradient-to-r from-purple-100 to-indigo-100 p-4 mr-4">
              <Palette class="h-8 w-8 text-purple-600" />
            </div>
            <div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Visual Customization</h3>
              <div class="flex items-center space-x-4 text-sm">
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">Beginner</span>
                <span class="text-gray-600">2-8 hours</span>
                <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full font-medium">DIY Friendly</span>
              </div>
            </div>
          </div>
        </div>
        
        <p class="text-gray-600 mb-6 leading-relaxed">Transform the look and feel of your CRM to match your brand identity perfectly.</p>
        
        <ul class="space-y-3 mb-6">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom color schemes and themes</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Logo and branding integration</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom CSS styling</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Layout modifications</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Font and typography changes</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Dashboard widget customization</span>
          </li>
        </ul>
        
        <div class="flex space-x-3">
          <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg text-purple-600 bg-purple-50 hover:bg-purple-100 transition-colors">
            <Download class="w-4 h-4 mr-2" />
            DIY Guide
          </a>
          <a href="/contact" class="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg text-white bg-purple-600 hover:bg-purple-700 transition-colors">
            <Wrench class="w-4 h-4 mr-2" />
            Get Professional Help
          </a>
        </div>
      </div>

      <!-- Functional Customization -->
      <div class="bg-white rounded-2xl shadow-xl p-8 transition-all duration-300 hover:shadow-2xl border border-gray-100">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center">
            <div class="rounded-xl bg-gradient-to-r from-purple-100 to-indigo-100 p-4 mr-4">
              <Cog class="h-8 w-8 text-purple-600" />
            </div>
            <div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Functional Customization</h3>
              <div class="flex items-center space-x-4 text-sm">
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">Intermediate</span>
                <span class="text-gray-600">8-24 hours</span>
                <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full font-medium">DIY Friendly</span>
              </div>
            </div>
          </div>
        </div>
        
        <p class="text-gray-600 mb-6 leading-relaxed">Add new features and modify existing workflows to match your business processes.</p>
        
        <ul class="space-y-3 mb-6">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom fields and data types</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Workflow automation rules</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom reporting dashboards</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Email template modifications</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">User role and permission customization</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Pipeline stage customization</span>
          </li>
        </ul>
        
        <div class="flex space-x-3">
          <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg text-purple-600 bg-purple-50 hover:bg-purple-100 transition-colors">
            <Download class="w-4 h-4 mr-2" />
            DIY Guide
          </a>
          <a href="/contact" class="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg text-white bg-purple-600 hover:bg-purple-700 transition-colors">
            <Wrench class="w-4 h-4 mr-2" />
            Get Professional Help
          </a>
        </div>
      </div>

      <!-- Integration & API Development -->
      <div class="bg-white rounded-2xl shadow-xl p-8 transition-all duration-300 hover:shadow-2xl border border-gray-100">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center">
            <div class="rounded-xl bg-gradient-to-r from-purple-100 to-indigo-100 p-4 mr-4">
              <Plug class="h-8 w-8 text-purple-600" />
            </div>
            <div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Integration & API Development</h3>
              <div class="flex items-center space-x-4 text-sm">
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">Advanced</span>
                <span class="text-gray-600">24-80 hours</span>
                <span class="px-3 py-1 bg-orange-100 text-orange-800 rounded-full font-medium">Professional Recommended</span>
              </div>
            </div>
          </div>
        </div>
        
        <p class="text-gray-600 mb-6 leading-relaxed">Connect BottleCRM with your existing tools and develop custom integrations.</p>
        
        <ul class="space-y-3 mb-6">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Third-party API integrations</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom webhook implementations</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Payment gateway integration</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Email service provider setup</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Social media platform connections</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom import/export tools</span>
          </li>
        </ul>
        
        <div class="flex space-x-3">
          <a href="/contact" class="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg text-white bg-purple-600 hover:bg-purple-700 transition-colors">
            <Wrench class="w-4 h-4 mr-2" />
            Get Professional Help
          </a>
        </div>
      </div>

      <!-- Enterprise Customization -->
      <div class="bg-white rounded-2xl shadow-xl p-8 transition-all duration-300 hover:shadow-2xl border border-gray-100">
        <div class="flex items-start justify-between mb-6">
          <div class="flex items-center">
            <div class="rounded-xl bg-gradient-to-r from-purple-100 to-indigo-100 p-4 mr-4">
              <Shield class="h-8 w-8 text-purple-600" />
            </div>
            <div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Enterprise Customization</h3>
              <div class="flex items-center space-x-4 text-sm">
                <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">Expert</span>
                <span class="text-gray-600">80+ hours</span>
                <span class="px-3 py-1 bg-orange-100 text-orange-800 rounded-full font-medium">Professional Recommended</span>
              </div>
            </div>
          </div>
        </div>
        
        <p class="text-gray-600 mb-6 leading-relaxed">Advanced modifications for large teams and complex business requirements.</p>
        
        <ul class="space-y-3 mb-6">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom module development</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Advanced security implementations</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Multi-tenant architecture</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom authentication systems</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Performance optimization</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Scalability enhancements</span>
          </li>
        </ul>
        
        <div class="flex space-x-3">
          <a href="/contact" class="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-semibold rounded-lg text-white bg-purple-600 hover:bg-purple-700 transition-colors">
            <Wrench class="w-4 h-4 mr-2" />
            Get Professional Help
          </a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Showcase Examples Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Real Customization Examples
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        See how businesses across different industries have customized BottleCRM to fit their unique requirements.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
      <!-- Real Estate CRM -->
      <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 text-center">
        <div class="text-4xl mb-4">🏠</div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">Real Estate CRM</h3>
        <p class="text-gray-600 mb-4">Custom property management fields, automated follow-up sequences, and integration with MLS systems.</p>
        <div class="flex flex-wrap gap-2 justify-center">
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-blue-700 border border-blue-200">Property Fields</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-blue-700 border border-blue-200">MLS Integration</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-blue-700 border border-blue-200">Auto Follow-ups</span>
        </div>
      </div>

      <!-- E-commerce Integration -->
      <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 text-center">
        <div class="text-4xl mb-4">🛒</div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">E-commerce Integration</h3>
        <p class="text-gray-600 mb-4">Shopify integration, automated order tracking, customer lifetime value calculations, and purchase history.</p>
        <div class="flex flex-wrap gap-2 justify-center">
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-green-700 border border-green-200">Shopify API</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-green-700 border border-green-200">Order Tracking</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-green-700 border border-green-200">LTV Analytics</span>
        </div>
      </div>

      <!-- Healthcare Practice -->
      <div class="bg-gradient-to-br from-red-50 to-rose-50 rounded-2xl p-8 text-center">
        <div class="text-4xl mb-4">🏥</div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">Healthcare Practice</h3>
        <p class="text-gray-600 mb-4">Patient management, appointment scheduling, HIPAA compliance features, and insurance tracking.</p>
        <div class="flex flex-wrap gap-2 justify-center">
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-red-700 border border-red-200">Patient Records</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-red-700 border border-red-200">HIPAA Compliant</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-red-700 border border-red-200">Appointment System</span>
        </div>
      </div>

      <!-- SaaS Startup CRM -->
      <div class="bg-gradient-to-br from-purple-50 to-violet-50 rounded-2xl p-8 text-center">
        <div class="text-4xl mb-4">💻</div>
        <h3 class="text-xl font-bold text-gray-900 mb-3">SaaS Startup CRM</h3>
        <p class="text-gray-600 mb-4">Trial tracking, usage analytics, churn prediction, and automated upgrade campaigns.</p>
        <div class="flex flex-wrap gap-2 justify-center">
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-purple-700 border border-purple-200">Trial Management</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-purple-700 border border-purple-200">Usage Analytics</span>
          <span class="px-3 py-1 bg-white rounded-full text-xs font-medium text-purple-700 border border-purple-200">Churn Prevention</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Services Pricing Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Customization Service Options
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Choose your path: customize it yourself with our free resources, or let our experts handle it for you.
      </p>
    </div>

    <div class="grid gap-8 lg:grid-cols-3">
      <!-- DIY Customization Kit -->
      <div class="bg-white rounded-2xl shadow-xl p-8 relative transition-all duration-300 hover:scale-105">
        <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span class="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold text-gray-700 bg-gray-100 border border-gray-200">
            Perfect for Developers
          </span>
        </div>
        
        <div class="text-center mb-8 pt-4">
          <div class="mb-4">
            <Code class="w-12 h-12 text-purple-600 mx-auto" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">DIY Customization Kit</h3>
          <p class="text-gray-600 mb-4">Everything you need to customize BottleCRM yourself with comprehensive guides and resources.</p>
          
          <div class="mb-6">
            <span class="text-5xl font-extrabold text-gray-900">Free</span>
            <span class="text-xl text-gray-500">/Forever</span>
          </div>
          
          <a href="https://github.com/MicroPyramid/Django-CRM" 
             target="_blank" rel="noopener noreferrer"
             class="w-full inline-flex items-center justify-center px-6 py-3 text-lg font-semibold rounded-lg text-purple-600 bg-purple-50 hover:bg-purple-100 transition-all duration-200">
            Download Free
          </a>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Complete source code access</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Detailed customization documentation</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Video tutorials and guides</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Community forum support</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Example customization templates</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Development environment setup guide</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Basic theming tools</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">CSS framework documentation</span>
          </li>
        </ul>
      </div>

      <!-- Professional Customization -->
      <div class="bg-white rounded-2xl shadow-xl p-8 relative transition-all duration-300 hover:scale-105 ring-4 ring-purple-500 ring-opacity-50">
        <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span class="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold text-white bg-gradient-to-r from-purple-500 to-indigo-600">
            <Star class="w-4 h-4 mr-1" />
            Most Popular
          </span>
        </div>
        
        <div class="text-center mb-8 pt-4">
          <div class="mb-4">
            <Brush class="w-12 h-12 text-purple-600 mx-auto" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">Professional Customization</h3>
          <p class="text-gray-600 mb-4">Expert customization services for businesses that want professional results without the learning curve.</p>
          
          <div class="mb-6">
            <span class="text-5xl font-extrabold text-gray-900">$497</span>
            <span class="text-xl text-gray-500">/per project</span>
          </div>
          
          <a href="/contact" 
             class="w-full inline-flex items-center justify-center px-6 py-3 text-lg font-semibold rounded-lg text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 transition-all duration-200">
            Get Professional Help
          </a>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Everything in DIY Kit</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom theme development</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Logo and branding integration</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Up to 5 custom fields</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Basic workflow automation</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Email template customization</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Mobile responsive optimization</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">2 rounds of revisions</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">1-week delivery</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">30-day support included</span>
          </li>
        </ul>
      </div>

      <!-- Enterprise Customization -->
      <div class="bg-white rounded-2xl shadow-xl p-8 relative transition-all duration-300 hover:scale-105">
        <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span class="inline-flex items-center px-4 py-2 rounded-full text-sm font-bold text-gray-700 bg-gray-100 border border-gray-200">
            Full Service
          </span>
        </div>
        
        <div class="text-center mb-8 pt-4">
          <div class="mb-4">
            <Shield class="w-12 h-12 text-purple-600 mx-auto" />
          </div>
          <h3 class="text-2xl font-bold text-gray-900 mb-2">Enterprise Customization</h3>
          <p class="text-gray-600 mb-4">Complete custom development for complex business requirements and enterprise-level implementations.</p>
          
          <div class="mb-6">
            <span class="text-5xl font-extrabold text-gray-900">$1,497</span>
            <span class="text-xl text-gray-500">/per project</span>
          </div>
          
          <a href="/contact" 
             class="w-full inline-flex items-center justify-center px-6 py-3 text-lg font-semibold rounded-lg text-purple-600 bg-purple-50 hover:bg-purple-100 transition-all duration-200">
            Contact Enterprise Team
          </a>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Everything in Professional</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Unlimited custom fields and modules</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Advanced workflow automation</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Third-party integrations (up to 3)</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Custom reporting dashboards</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Advanced user role management</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Performance optimization</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">Security enhancements</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">3-week delivery</span>
          </li>
          <li class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
            <span class="text-gray-700">90-day priority support</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</section>

<!-- Technical Requirements Section -->
<section class="py-20 bg-white">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Technical Requirements for DIY Customization
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        Planning to customize BottleCRM yourself? Here are the technical skills and technologies you'll need to know.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-3">
      <!-- Frontend Development -->
      <div class="bg-gradient-to-br from-gray-50 to-blue-50 rounded-2xl p-8 border border-gray-200 transition-all duration-300 hover:shadow-lg">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <Layout class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">Frontend Development</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Svelte 5.x</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">SvelteKit 2.21+</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">JavaScript/TypeScript</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">TailwindCSS 4.1+</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">HTML5/CSS3</span>
          </li>
        </ul>
      </div>

      <!-- Backend Development -->
      <div class="bg-gradient-to-br from-gray-50 to-blue-50 rounded-2xl p-8 border border-gray-200 transition-all duration-300 hover:shadow-lg">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <Database class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">Backend Development</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Node.js</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Prisma ORM</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Database Design</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">API Development</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Authentication</span>
          </li>
        </ul>
      </div>

      <!-- DevOps & Deployment -->
      <div class="bg-gradient-to-br from-gray-50 to-blue-50 rounded-2xl p-8 border border-gray-200 transition-all duration-300 hover:shadow-lg">
        <div class="flex items-center mb-6">
          <div class="rounded-lg bg-blue-100 p-3 mr-4">
            <Cloud class="h-6 w-6 text-blue-600" />
          </div>
          <h3 class="text-xl font-bold text-gray-900">DevOps & Deployment</h3>
        </div>
        
        <ul class="space-y-3">
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Docker</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Linux/Ubuntu</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Cloud Platforms</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">SSL Configuration</span>
          </li>
          <li class="flex items-center">
            <div class="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
            <span class="text-gray-700 font-medium">Domain Setup</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="mt-12 text-center">
      <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 border border-blue-200">
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Don't have the technical skills?</h3>
        <p class="text-lg text-gray-600 mb-6">
          No problem! Our professional customization services handle all the technical complexity for you.
        </p>
        <a href="/contact" class="inline-flex items-center justify-center px-6 py-3 text-lg font-semibold rounded-lg text-white bg-purple-600 hover:bg-purple-700 transition-colors">
          <MessageCircle class="w-5 h-5 mr-2" />
          Get Professional Help
        </a>
      </div>
    </div>
  </div>
</section>

<!-- FAQ Section -->
<section class="py-20 bg-gray-50">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-16">
      <h2 class="text-4xl font-extrabold text-gray-900 mb-6">
        Customization Questions & Answers
      </h2>
      <p class="text-xl text-gray-600">
        Everything you need to know about customizing BottleCRM for your business.
      </p>
    </div>

    <div class="space-y-4">
      <!-- FAQ 1 -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(0)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
          aria-expanded={activeFaq === 0}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can I customize BottleCRM without coding knowledge?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 0 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 0}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes! Basic visual customizations like colors, logos, and simple layout changes can be done through configuration files. For more advanced customizations, you can use our Professional Customization service or learn from our detailed tutorials.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 2 -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(1)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
          aria-expanded={activeFaq === 1}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Will my customizations be lost when BottleCRM updates?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 1 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 1}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Not if done properly! We provide guidelines for creating update-safe customizations. Our professional service includes future-proofing your customizations to survive software updates.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 3 -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(2)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
          aria-expanded={activeFaq === 2}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">How long does professional customization take?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 2 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 2}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Simple customizations (branding, basic fields) take 1-2 weeks. Complex integrations and custom modules can take 3-6 weeks. We provide detailed timelines before starting any project.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 4 -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(3)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
          aria-expanded={activeFaq === 3}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can you integrate BottleCRM with our existing tools?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 3 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 3}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Absolutely! We've integrated BottleCRM with hundreds of tools including Shopify, WordPress, QuickBooks, Mailchimp, Slack, and many others. If it has an API, we can likely integrate it.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 5 -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(4)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
          aria-expanded={activeFaq === 4}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Do you provide training after customization?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 4 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 4}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Yes! All our customization services include comprehensive training for your team, documentation of changes made, and ongoing support to ensure you get the most out of your customized CRM.</p>
          </div>
        {/if}
      </div>

      <!-- FAQ 6 -->
      <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <button 
          onclick={() => toggleFaq(5)}
          class="w-full px-6 py-5 text-left focus:outline-none focus:bg-gray-50 hover:bg-gray-50 transition-colors duration-200"
          aria-expanded={activeFaq === 5}
        >
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900 pr-4">Can I start with DIY and upgrade to professional service later?</h3>
            <ChevronDown class="w-5 h-5 text-gray-500 transform transition-transform duration-200 {activeFaq === 5 ? 'rotate-180' : ''}" />
          </div>
        </button>
        
        {#if activeFaq === 5}
          <div transition:fade="{{ duration: 200 }}" class="px-6 pb-5">
            <p class="text-gray-700 leading-relaxed">Definitely! Many clients start with basic customizations and later hire us for more complex features. We can work with existing customizations and enhance them further.</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
</section>

<!-- Call to Action -->
<section class="bg-gradient-to-r from-purple-700 via-purple-800 to-indigo-900 text-white py-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-4xl md:text-5xl font-extrabold mb-6">
      Ready to Create Your Perfect CRM?
    </h2>
    <p class="text-xl md:text-2xl mb-8 text-purple-100 max-w-3xl mx-auto">
      Whether you're a developer ready to dive into the code or a business owner who needs professional help, 
      we have the perfect solution for your customization needs.
    </p>
    
    <div class="flex flex-col sm:flex-row sm:justify-center space-y-4 sm:space-y-0 sm:space-x-6">
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener noreferrer" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-purple-700 bg-white hover:bg-gray-100 shadow-2xl transition-all duration-200 hover:scale-105">
        <Github class="w-6 h-6 mr-3" />
        Start DIY Customization
      </a>
      <a href="/contact" class="inline-flex items-center justify-center px-8 py-4 text-lg font-bold rounded-xl text-white border-2 border-white hover:bg-white/10 transition-all duration-200">
        <Wrench class="w-6 h-6 mr-3" />
        Get Professional Service
      </a>
    </div>
    
    <p class="mt-8 text-purple-200">
      🚀 Free source code • Professional services • 30-day money-back guarantee
    </p>
  </div>
</section>