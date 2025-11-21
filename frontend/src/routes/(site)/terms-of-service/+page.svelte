<!-- Terms of Service page -->
<script>
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { 
    FileText, 
    Shield, 
    Users, 
    Code, 
    HeartHandshake,
    AlertTriangle,
    CheckCircle,
    ArrowLeft,
    ExternalLink,
    Calendar
  } from '@lucide/svelte';

  let mounted = false;
  const lastUpdated = "December 2024";

  onMount(() => {
    mounted = true;
  });
</script>

<svelte:head>
  <title>Terms of Service | Free Open Source CRM - BottleCRM</title>
  <meta name="description" content="Read the Terms of Service for BottleCRM, a free and open source CRM software for startups and small businesses. MIT licensed. No hidden fees." />
  <meta name="keywords" content="free crm, open source crm, crm software, mit license, bottlecrm, terms of service, startup crm, small business crm" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="https://bottlecrm.io/terms-of-service" />

  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/terms-of-service" />
  <meta property="og:title" content="Terms of Service | Free Open Source CRM - BottleCRM" />
  <meta property="og:description" content="Terms of Service for BottleCRM, a free and open source CRM software for startups and small businesses. MIT licensed." />
  <meta property="og:site_name" content="BottleCRM" />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:url" content="https://bottlecrm.io/terms-of-service" />
  <meta name="twitter:title" content="Terms of Service | Free Open Source CRM - BottleCRM" />
  <meta name="twitter:description" content="Terms of Service for BottleCRM, a free and open source CRM software for startups and small businesses. MIT licensed." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Structured Data -->
  {@html `
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Terms of Service - BottleCRM",
        "description": "Terms of Service for BottleCRM, a free and open source CRM software for startups and small businesses. MIT licensed.",
        "url": "https://bottlecrm.io/terms-of-service",
        "lastReviewed": "2024-12-01",
        "about": {
          "@type": "SoftwareApplication",
          "name": "BottleCRM",
          "applicationCategory": "Customer Relationship Management",
          "operatingSystem": "All",
          "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
          }
        }
      }
    </script>
  `}
</svelte:head>

<!-- Header Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white py-16">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center">
      {#if mounted}
        <div in:fly="{{ y: -30, duration: 600 }}">
          <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
            <FileText class="w-5 h-5 mr-2" />
            <span class="text-sm font-medium">Legal Information</span>
          </div>
          
          <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight mb-6">
            Terms of Service
          </h1>
          <p class="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto leading-relaxed">
            Transparent terms for our free, open-source CRM software and optional professional services
          </p>
          
          <div class="flex items-center justify-center space-x-4 text-blue-200">
            <Calendar class="w-5 h-5" />
            <span>Last updated: {lastUpdated}</span>
          </div>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Navigation Back -->
<section class="bg-gray-50 py-4 border-b">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <a href="/" class="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium transition-colors duration-200">
      <ArrowLeft class="w-4 h-4 mr-2" />
      Back to Home
    </a>
  </div>
</section>

<!-- Table of Contents -->
<section class="py-12 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    {#if mounted}
      <div in:fly="{{ y: 30, duration: 600, delay: 200 }}">
        <h2 class="text-2xl font-bold text-gray-900 mb-8">Table of Contents</h2>
        <div class="bg-gray-50 rounded-xl p-6">
          <nav class="space-y-3">
            <a href="#acceptance" 
               class="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-200 group">
              <CheckCircle class="w-5 h-5 mr-3 text-gray-400 group-hover:text-blue-500" />
              <span class="font-medium">1. Acceptance of Terms</span>
            </a>
            <a href="#software-license" 
               class="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-200 group">
              <Code class="w-5 h-5 mr-3 text-gray-400 group-hover:text-blue-500" />
              <span class="font-medium">2. Software License & Open Source</span>
            </a>
            <a href="#free-services" 
               class="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-200 group">
              <Shield class="w-5 h-5 mr-3 text-gray-400 group-hover:text-blue-500" />
              <span class="font-medium">3. Free Software Services</span>
            </a>
            <a href="#paid-services" 
               class="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-200 group">
              <HeartHandshake class="w-5 h-5 mr-3 text-gray-400 group-hover:text-blue-500" />
              <span class="font-medium">4. Paid Professional Services</span>
            </a>
            <a href="#user-responsibilities" 
               class="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-200 group">
              <Users class="w-5 h-5 mr-3 text-gray-400 group-hover:text-blue-500" />
              <span class="font-medium">5. User Responsibilities</span>
            </a>
            <a href="#disclaimers" 
               class="flex items-center text-gray-700 hover:text-blue-600 transition-colors duration-200 group">
              <AlertTriangle class="w-5 h-5 mr-3 text-gray-400 group-hover:text-blue-500" />
              <span class="font-medium">6. Disclaimers & Limitations</span>
            </a>
          </nav>
        </div>
      </div>
    {/if}
  </div>
</section>

<!-- Main Content -->
<section class="py-16 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="prose prose-lg max-w-none">
      
      <!-- Introduction -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 300 }}" class="mb-16">
          <div class="bg-blue-50 border-l-4 border-blue-500 p-6 rounded-r-lg mb-8">
            <h2 class="text-2xl font-bold text-blue-900 mb-4">Welcome to BottleCRM</h2>
            <p class="text-blue-800 leading-relaxed">
              BottleCRM is a free, open-source Customer Relationship Management (CRM) software designed specifically for startups and small businesses. 
              These Terms of Service ("Terms") govern your use of the BottleCRM software and any related services we provide.
            </p>
          </div>
        </div>
      {/if}

      <!-- 1. Acceptance of Terms -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 400 }}" 
             id="acceptance" 
             class="mb-12 scroll-mt-8">
          
          <div class="flex items-center mb-6">
            <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
              <CheckCircle class="h-6 w-6 text-blue-600" />
            </div>
            <h2 class="text-3xl font-bold text-gray-900">1. Acceptance of Terms</h2>
          </div>

          <div class="bg-gray-50 rounded-xl p-6 mb-6">
            <p class="text-gray-700 leading-relaxed mb-4">By accessing, downloading, or using BottleCRM software, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our software or services.</p>
            <ul class="space-y-2 text-gray-700">
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>These terms apply to all users of BottleCRM software</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>By downloading or using our software, you accept these terms</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>If you disagree with any part, please do not use BottleCRM</span>
              </li>
            </ul>
          </div>
        </div>
      {/if}

      <!-- 2. Software License & Open Source -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 500 }}" 
             id="software-license" 
             class="mb-12 scroll-mt-8">
          
          <div class="flex items-center mb-6">
            <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
              <Code class="h-6 w-6 text-blue-600" />
            </div>
            <h2 class="text-3xl font-bold text-gray-900">2. Software License & Open Source</h2>
          </div>

          <div class="bg-gray-50 rounded-xl p-6 mb-6">
            <p class="text-gray-700 leading-relaxed mb-4">BottleCRM is distributed under the MIT License, which grants you extensive rights to use, modify, and distribute the software. You may freely download, install, customize, and self-host BottleCRM without any licensing fees or subscription charges.</p>
            
            <div class="bg-gray-900 rounded-lg p-4 mb-4">
              <h4 class="text-white font-bold mb-2">MIT License Summary</h4>
              <p class="text-gray-300 text-sm mb-3">
                Permission is hereby granted, free of charge, to any person obtaining a copy of this software...
              </p>
              <a href="https://github.com/MicroPyramid/Django-CRM/blob/main/LICENSE" 
                 target="_blank" 
                 rel="noopener noreferrer"
                 class="inline-flex items-center text-blue-400 hover:text-blue-300 text-sm">
                View Full License on GitHub
                <ExternalLink class="w-4 h-4 ml-1" />
              </a>
            </div>

            <h4 class="font-bold text-gray-900 mb-3">What you can do:</h4>
            <ul class="space-y-2 text-gray-700 mb-6">
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Use BottleCRM for personal or commercial purposes</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Modify and customize the source code</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Distribute copies of the original or modified software</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Self-host on your own servers or cloud infrastructure</span>
              </li>
            </ul>
          </div>
        </div>
      {/if}

      <!-- 3. Free Software Services -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 600 }}" 
             id="free-services" 
             class="mb-12 scroll-mt-8">
          
          <div class="flex items-center mb-6">
            <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
              <Shield class="h-6 w-6 text-blue-600" />
            </div>
            <h2 class="text-3xl font-bold text-gray-900">3. Free Software Services</h2>
          </div>

          <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-6">
            <p class="text-gray-700 leading-relaxed mb-4">The BottleCRM software is provided free of charge with no warranty or guarantee. We make no representations about the software's suitability for your specific business needs. Use at your own risk.</p>
            
            <h4 class="font-bold text-gray-900 mb-3">Important Disclaimers for Free Software:</h4>
            <ul class="space-y-2 text-gray-700">
              <li class="flex items-start">
                <AlertTriangle class="w-5 h-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>BottleCRM is provided "as is" without warranty of any kind</span>
              </li>
              <li class="flex items-start">
                <AlertTriangle class="w-5 h-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>No guarantee of fitness for any particular purpose</span>
              </li>
              <li class="flex items-start">
                <AlertTriangle class="w-5 h-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Users are responsible for their own data backup and security</span>
              </li>
              <li class="flex items-start">
                <AlertTriangle class="w-5 h-5 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Community support available through GitHub and forums</span>
              </li>
            </ul>
          </div>
        </div>
      {/if}

      <!-- 4. Paid Professional Services -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 700 }}" 
             id="paid-services" 
             class="mb-12 scroll-mt-8">
          
          <div class="flex items-center mb-6">
            <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
              <HeartHandshake class="h-6 w-6 text-blue-600" />
            </div>
            <h2 class="text-3xl font-bold text-gray-900">4. Paid Professional Services</h2>
          </div>

          <div class="bg-green-50 border border-green-200 rounded-xl p-6 mb-6">
            <p class="text-gray-700 leading-relaxed mb-4">We offer optional paid services including hosting setup, custom development, data migration, training, and technical support. These services are governed by separate service agreements and payment terms.</p>
            
            <h4 class="font-bold text-gray-900 mb-3">Available Paid Services:</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div class="bg-white p-4 rounded-lg border">
                <h5 class="font-semibold text-gray-900 mb-2">Hosting & Deployment</h5>
                <p class="text-sm text-gray-600">Professional setup on your preferred cloud platform</p>
              </div>
              <div class="bg-white p-4 rounded-lg border">
                <h5 class="font-semibold text-gray-900 mb-2">Custom Development</h5>
                <p class="text-sm text-gray-600">Tailored features and integrations for your business</p>
              </div>
              <div class="bg-white p-4 rounded-lg border">
                <h5 class="font-semibold text-gray-900 mb-2">Data Migration</h5>
                <p class="text-sm text-gray-600">Import data from your existing CRM or systems</p>
              </div>
              <div class="bg-white p-4 rounded-lg border">
                <h5 class="font-semibold text-gray-900 mb-2">Training & Support</h5>
                <p class="text-sm text-gray-600">Team training and ongoing technical support</p>
              </div>
            </div>
            
            <p class="text-sm text-gray-600">
              <strong>Note:</strong> Paid services are subject to separate service agreements and payment terms. 
              Contact us for pricing and availability.
            </p>
          </div>
        </div>
      {/if}

      <!-- 5. User Responsibilities -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 800 }}" 
             id="user-responsibilities" 
             class="mb-12 scroll-mt-8">
          
          <div class="flex items-center mb-6">
            <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
              <Users class="h-6 w-6 text-blue-600" />
            </div>
            <h2 class="text-3xl font-bold text-gray-900">5. User Responsibilities</h2>
          </div>

          <div class="bg-gray-50 rounded-xl p-6 mb-6">
            <p class="text-gray-700 leading-relaxed mb-4">You are responsible for your use of BottleCRM, including compliance with applicable laws, data protection regulations, and proper security practices when self-hosting the software.</p>
            
            <h4 class="font-bold text-gray-900 mb-3">Your Responsibilities Include:</h4>
            <ul class="space-y-3 text-gray-700">
              <li class="flex items-start">
                <Shield class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <strong>Data Protection:</strong> Comply with GDPR, CCPA, and other applicable data protection laws
                </div>
              </li>
              <li class="flex items-start">
                <Shield class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <strong>Security:</strong> Implement proper security measures when self-hosting
                </div>
              </li>
              <li class="flex items-start">
                <Shield class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <strong>Legal Compliance:</strong> Use BottleCRM in accordance with applicable laws
                </div>
              </li>
              <li class="flex items-start">
                <Shield class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <strong>Proper Use:</strong> Do not use the software for illegal or harmful activities
                </div>
              </li>
            </ul>
          </div>
        </div>
      {/if}

      <!-- 6. Disclaimers & Limitations -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 900 }}" 
             id="disclaimers" 
             class="mb-12 scroll-mt-8">
          
          <div class="flex items-center mb-6">
            <div class="rounded-lg bg-gradient-to-r from-blue-100 to-indigo-100 p-3 mr-4">
              <AlertTriangle class="h-6 w-6 text-blue-600" />
            </div>
            <h2 class="text-3xl font-bold text-gray-900">6. Disclaimers & Limitations</h2>
          </div>

          <div class="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
            <p class="text-gray-700 leading-relaxed mb-4">BottleCRM is provided "as is" without warranty of any kind. We shall not be liable for any damages arising from the use of our software or services, except as required by applicable law.</p>
            
            <h4 class="font-bold text-gray-900 mb-3">Limitation of Liability:</h4>
            <div class="bg-white p-4 rounded-lg border-l-4 border-red-500 mb-4">
              <p class="text-gray-700 text-sm leading-relaxed">
                IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
                WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
                OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
              </p>
            </div>
            
            <ul class="space-y-2 text-gray-700 text-sm">
              <li class="flex items-start">
                <AlertTriangle class="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>We are not responsible for data loss or business interruption</span>
              </li>
              <li class="flex items-start">
                <AlertTriangle class="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>No warranty regarding software performance or reliability</span>
              </li>
              <li class="flex items-start">
                <AlertTriangle class="w-4 h-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Users assume all risks associated with software use</span>
              </li>
            </ul>
          </div>
        </div>
      {/if}

      <!-- Additional Legal Sections -->
      {#if mounted}
        <div in:fly="{{ y: 30, duration: 600, delay: 800 }}" class="space-y-12">
          
          <!-- Contact Information -->
          <div id="contact" class="scroll-mt-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-6">7. Contact Information</h2>
            <div class="bg-blue-50 rounded-xl p-6">
              <p class="text-gray-700 mb-4">
                For questions about these Terms of Service, the BottleCRM software, or our paid services, please contact us:
              </p>
              <div class="space-y-3">
                <div class="flex items-center">
                  <ExternalLink class="w-5 h-5 text-blue-600 mr-3" />
                  <a href="https://github.com/MicroPyramid/Django-CRM" 
                     target="_blank" 
                     rel="noopener noreferrer"
                     class="text-blue-600 hover:text-blue-700">
                    GitHub Repository & Issues
                  </a>
                </div>
                <div class="flex items-center">
                  <ExternalLink class="w-5 h-5 text-blue-600 mr-3" />
                  <a href="/contact" class="text-blue-600 hover:text-blue-700">
                    Professional Services Contact
                  </a>
                </div>
              </div>
            </div>
          </div>

          <!-- Changes to Terms -->
          <div id="changes" class="scroll-mt-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-6">8. Changes to These Terms</h2>
            <div class="bg-gray-50 rounded-xl p-6">
              <p class="text-gray-700 mb-4">
                We may update these Terms of Service from time to time. Any changes will be posted on this page with an updated 
                "Last updated" date. Your continued use of BottleCRM after any changes constitutes acceptance of the new terms.
              </p>
              <p class="text-gray-700">
                For significant changes affecting paid services, we will provide reasonable notice to existing customers.
              </p>
            </div>
          </div>

          <!-- Governing Law -->
          <div id="governing-law" class="scroll-mt-8">
            <h2 class="text-3xl font-bold text-gray-900 mb-6">9. Governing Law</h2>
            <div class="bg-gray-50 rounded-xl p-6">
              <p class="text-gray-700">
                These Terms of Service are governed by and construed in accordance with applicable international open-source 
                software laws and the MIT License under which BottleCRM is distributed. Any disputes shall be resolved through 
                appropriate legal channels in the jurisdiction where the dispute arises.
              </p>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</section>

<!-- Footer CTA -->
<section class="py-16 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    {#if mounted}
      <div in:fade="{{ duration: 600, delay: 1000 }}">
        <h2 class="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p class="text-xl text-blue-100 mb-8">
          Now that you understand our terms, download BottleCRM and start managing your customer relationships for free.
        </p>
        <div class="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
          <a href="/login" 
             class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-blue-700 bg-white hover:bg-gray-100 transition-colors duration-200">
            Start Using BottleCRM
          </a>
          <a href="/" 
             class="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-base font-medium rounded-lg text-white hover:bg-white/10 transition-colors duration-200">
            Learn More
          </a>
        </div>
      </div>
    {/if}
  </div>
</section>
