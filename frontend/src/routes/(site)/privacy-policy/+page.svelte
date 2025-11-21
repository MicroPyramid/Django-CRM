<!-- Privacy Policy page -->
<script>
  import { 
    Shield, 
    Server, 
    Eye, 
    Lock, 
    Database, 
    Users, 
    Mail, 
    FileText,
    Calendar,
    CheckCircle,
    Globe,
    ArrowLeft
  } from '@lucide/svelte';

  let lastUpdated = "June 2025";
  const schema = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "Privacy Policy | BottleCRM",
    "description": "Read the privacy policy for BottleCRM, the free and open-source CRM. Learn how your data is protected, your privacy rights, and how self-hosting ensures full control.",
    "url": "https://bottlecrm.io/privacy-policy",
    "dateModified": "2025-06-01",
    "publisher": {
      "@type": "Organization",
      "name": "BottleCRM",
      "url": "https://bottlecrm.io",
      "logo": {
        "@type": "ImageObject",
        "url": "https://bottlecrm.io/logo.png"
      }
    }
  };
</script>

<svelte:head>
  <title>Privacy Policy | BottleCRM - Free Open Source CRM for Data Privacy</title>
  <meta name="description" content="Read the privacy policy for BottleCRM, the free and open-source CRM. Learn how your data is protected, your privacy rights, and how self-hosting ensures full control." />
  <meta name="keywords" content="privacy policy, free crm, open source crm, data privacy, GDPR, self-hosted CRM, data security, BottleCRM" />
  <link rel="canonical" href="https://bottlecrm.io/privacy-policy" />
  <meta name="robots" content="index, follow" />

  <!-- Open Graph -->
  <meta property="og:title" content="Privacy Policy | BottleCRM - Free Open Source CRM for Data Privacy" />
  <meta property="og:description" content="Read how BottleCRM protects your data and privacy. Free, open-source, and self-hosted CRM for businesses." />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="https://bottlecrm.io/privacy-policy" />
  <meta property="og:site_name" content="BottleCRM" />
  <meta property="og:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Privacy Policy | BottleCRM - Free Open Source CRM" />
  <meta name="twitter:description" content="BottleCRM is a free, open-source CRM. Read our privacy policy to learn how your data is protected and your privacy rights are respected." />
  <meta name="twitter:image" content="https://bottlecrm.io/og-image.png" />

  <!-- Schema.org JSON-LD -->
  <script type="application/ld+json">
    {JSON.stringify(schema)}
  </script>
</svelte:head>

<!-- Breadcrumb Navigation -->
<nav class="bg-gray-50 py-4">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="flex items-center space-x-2 text-sm">
      <a href="/" class="flex items-center text-blue-600 hover:text-blue-700 transition-colors">
        <ArrowLeft class="w-4 h-4 mr-1" />
        Home
      </a>
      <span class="text-gray-400">/</span>
      <span class="text-gray-600">Privacy Policy</span>
    </div>
  </div>
</nav>

<!-- Hero Section -->
<section class="bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 text-white py-16">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
        <Shield class="w-5 h-5 mr-2" />
        <span class="text-sm font-medium">Your Privacy, Our Priority</span>
      </div>
      
      <h1 class="text-4xl md:text-6xl font-extrabold mb-6">
        Privacy Policy
      </h1>
      <p class="text-xl md:text-2xl text-blue-100 max-w-3xl mx-auto">
        At BottleCRM, we believe in complete transparency about how we handle your data. 
        As a self-hostable, open-source CRM, your privacy and data ownership are fundamental rights.
      </p>
      
      <div class="mt-8 flex flex-col sm:flex-row justify-center items-center space-y-2 sm:space-y-0 sm:space-x-6 text-blue-100">
        <div class="flex items-center">
          <Calendar class="w-5 h-5 mr-2" />
          <span>Last Updated: {lastUpdated}</span>
        </div>
        <div class="flex items-center">
          <CheckCircle class="w-5 h-5 mr-2" />
          <span>GDPR Compliant</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Privacy Principles -->
<section class="py-16 bg-gray-50">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-12">
      <h2 class="text-3xl font-extrabold text-gray-900 sm:text-4xl mb-4">
        Our Privacy Principles
      </h2>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto">
        BottleCRM is built on the foundation of user privacy and data ownership.
      </p>
    </div>

    <div class="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
      <div class="bg-white rounded-xl shadow-lg p-6 text-center hover:shadow-xl transition-all duration-300">
        <div class="rounded-full bg-blue-100 p-3 inline-block mb-4">
          <Shield class="h-6 w-6 text-blue-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Data Ownership</h3>
        <p class="text-gray-600 text-sm">When you self-host BottleCRM, you maintain complete ownership and control of your data.</p>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 text-center hover:shadow-xl transition-all duration-300">
        <div class="rounded-full bg-blue-100 p-3 inline-block mb-4">
          <Server class="h-6 w-6 text-blue-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Self-Hosting Privacy</h3>
        <p class="text-gray-600 text-sm">Host on your own servers for maximum privacy and compliance with data protection regulations.</p>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 text-center hover:shadow-xl transition-all duration-300">
        <div class="rounded-full bg-blue-100 p-3 inline-block mb-4">
          <Lock class="h-6 w-6 text-blue-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">No Data Mining</h3>
        <p class="text-gray-600 text-sm">We don't collect, analyze, or monetize your business data. Your information stays private.</p>
      </div>

      <div class="bg-white rounded-xl shadow-lg p-6 text-center hover:shadow-xl transition-all duration-300">
        <div class="rounded-full bg-blue-100 p-3 inline-block mb-4">
          <Eye class="h-6 w-6 text-blue-600" />
        </div>
        <h3 class="text-lg font-bold text-gray-900 mb-2">Transparency</h3>
        <p class="text-gray-600 text-sm">Open-source code means you can inspect exactly how your data is handled and stored.</p>
      </div>
    </div>
  </div>
</section>

<!-- Main Privacy Policy Content -->
<section class="py-16 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="prose prose-lg max-w-none">
      
      <!-- Information We Collect -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6 flex items-center">
          <Database class="w-8 h-8 mr-3 text-blue-600" />
          Information We Collect
        </h2>
        
        <div class="bg-blue-50 border-l-4 border-blue-500 p-6 mb-6">
          <div class="flex items-start">
            <Server class="w-6 h-6 text-blue-500 mr-3 mt-1 flex-shrink-0" />
            <div>
              <h4 class="font-semibold text-blue-900 mb-2">Self-Hosted Deployments</h4>
              <p class="text-blue-800">When you self-host BottleCRM, we do not collect any of your business data, customer information, or usage analytics. All data remains on your servers under your complete control.</p>
            </div>
          </div>
        </div>

        <h3 class="text-xl font-semibold text-gray-900 mb-4">Website Analytics (bottlecrm.io only)</h3>
        <ul class="space-y-2 text-gray-700 mb-6">
          <li class="flex items-start">
            <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
            <span>Basic website analytics (page views, visitor count, referral sources)</span>
          </li>
          <li class="flex items-start">
            <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
            <span>IP addresses (anonymized and not linked to personal identity)</span>
          </li>
          <li class="flex items-start">
            <CheckCircle class="w-5 h-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
            <span>Browser type and device information (for optimization purposes)</span>
          </li>
        </ul>

        <h3 class="text-xl font-semibold text-gray-900 mb-4">Information You Provide</h3>
        <ul class="space-y-2 text-gray-700 mb-6">
          <li class="flex items-start">
            <Mail class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
            <span>Contact information when you reach out for support or inquiries</span>
          </li>
          <li class="flex items-start">
            <FileText class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
            <span>Feedback and suggestions submitted through our channels</span>
          </li>
          <li class="flex items-start">
            <Users class="w-5 h-5 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
            <span>Professional service requests and consultation details</span>
          </li>
        </ul>
      </div>

      <!-- How We Use Information -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6">How We Use Your Information</h2>
        
        <div class="grid md:grid-cols-2 gap-6 mb-6">
          <div class="bg-green-50 p-6 rounded-xl border border-green-200">
            <h4 class="font-semibold text-green-900 mb-3">What We DO Use Information For:</h4>
            <ul class="space-y-2 text-green-800 text-sm">
              <li>• Responding to support requests and inquiries</li>
              <li>• Improving our website and documentation</li>
              <li>• Providing professional services when requested</li>
              <li>• Communicating important updates about BottleCRM</li>
            </ul>
          </div>
          
          <div class="bg-red-50 p-6 rounded-xl border border-red-200">
            <h4 class="font-semibold text-red-900 mb-3">What We DON'T Use Information For:</h4>
            <ul class="space-y-2 text-red-800 text-sm">
              <li>• Selling or sharing with third parties</li>
              <li>• Marketing campaigns or advertisements</li>
              <li>• Building user profiles or tracking</li>
              <li>• Any form of data monetization</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Data Storage & Security -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6 flex items-center">
          <Lock class="w-8 h-8 mr-3 text-blue-600" />
          Data Storage & Security
        </h2>
        
        <div class="bg-gray-50 p-6 rounded-xl mb-6">
          <h4 class="font-semibold text-gray-900 mb-3">Self-Hosted Security</h4>
          <p class="text-gray-700 mb-4">
            When you self-host BottleCRM, you are responsible for implementing appropriate security measures. 
            We provide documentation and best practices to help secure your installation.
          </p>
          <ul class="space-y-2 text-gray-700 text-sm">
            <li>• Use HTTPS/SSL encryption for web traffic</li>
            <li>• Implement proper database security and access controls</li>
            <li>• Regular security updates and patches</li>
            <li>• Backup and disaster recovery procedures</li>
          </ul>
        </div>

        <h4 class="font-semibold text-gray-900 mb-3">Website Security</h4>
        <p class="text-gray-700 mb-4">
          Our website (bottlecrm.io) is protected with industry-standard security measures including SSL encryption, 
          regular security audits, and secure hosting infrastructure.
        </p>
      </div>

      <!-- Your Rights -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Your Privacy Rights</h2>
        
        <div class="grid md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <h4 class="font-semibold text-gray-900">Data Subject Rights (GDPR)</h4>
            <ul class="space-y-2 text-gray-700 text-sm">
              <li class="flex items-start">
                <CheckCircle class="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Right to access your personal data</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Right to rectification (correction)</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Right to erasure ("right to be forgotten")</span>
              </li>
              <li class="flex items-start">
                <CheckCircle class="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Right to data portability</span>
              </li>
            </ul>
          </div>
          
          <div class="space-y-4">
            <h4 class="font-semibold text-gray-900">Self-Hosting Advantages</h4>
            <ul class="space-y-2 text-gray-700 text-sm">
              <li class="flex items-start">
                <Server class="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Complete control over data location</span>
              </li>
              <li class="flex items-start">
                <Lock class="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>No third-party data sharing</span>
              </li>
              <li class="flex items-start">
                <Globe class="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Compliance with local regulations</span>
              </li>
              <li class="flex items-start">
                <Database class="w-4 h-4 text-blue-500 mr-2 mt-0.5 flex-shrink-0" />
                <span>Custom data retention policies</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Third-Party Services -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Third-Party Services</h2>
        
        <div class="bg-yellow-50 border-l-4 border-yellow-500 p-6 mb-6">
          <h4 class="font-semibold text-yellow-900 mb-2">Website Analytics</h4>
          <p class="text-yellow-800">
            We use privacy-focused analytics tools to understand website usage. These tools are configured to respect user privacy and comply with data protection regulations.
          </p>
        </div>

        <h4 class="font-semibold text-gray-900 mb-3">Self-Hosted Integrations</h4>
        <p class="text-gray-700 mb-4">
          BottleCRM may support integrations with third-party services (email providers, payment processors, etc.). 
          When you configure these integrations in your self-hosted instance, you are responsible for reviewing 
          and accepting the privacy policies of those services.
        </p>
      </div>

      <!-- Contact & Updates -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Contact Information & Policy Updates</h2>
        
        <div class="bg-blue-50 p-6 rounded-xl">
          <h4 class="font-semibold text-blue-900 mb-3">Questions About This Policy?</h4>
          <p class="text-blue-800 mb-4">
            If you have any questions about this Privacy Policy or how we handle your data, please contact us:
          </p>
          <ul class="space-y-2 text-blue-800">
            <li class="flex items-center">
              <Mail class="w-5 h-5 mr-2" />
              <a href="mailto:privacy@bottlecrm.io" class="hover:underline">privacy@bottlecrm.io</a>
            </li>
            <li class="flex items-center">
              <Globe class="w-5 h-5 mr-2" />
              <a href="/contact" class="hover:underline">Contact Form</a>
            </li>
          </ul>
        </div>

        <div class="mt-6 p-6 bg-gray-50 rounded-xl">
          <h4 class="font-semibold text-gray-900 mb-3">Policy Updates</h4>
          <p class="text-gray-700">
            We may update this Privacy Policy from time to time to reflect changes in our practices or legal requirements. 
            When we make significant changes, we will notify users through our website and GitHub repository. 
            The "Last Updated" date at the top of this policy indicates when the most recent changes were made.
          </p>
        </div>
      </div>

      <!-- Open Source Transparency -->
      <div class="mb-12">
        <h2 class="text-3xl font-bold text-gray-900 mb-6">Open Source Transparency</h2>
        
        <div class="bg-green-50 border border-green-200 p-6 rounded-xl">
          <p class="text-green-800 mb-4">
            <strong>Complete Transparency:</strong> As an open-source project, you can inspect our entire codebase 
            to verify how data is handled, stored, and processed. This level of transparency is impossible with 
            proprietary CRM solutions.
          </p>
          <div class="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
            <a href="https://github.com/MicroPyramid/Django-CRM" 
               target="_blank" 
               rel="noopener noreferrer"
               class="inline-flex items-center text-green-700 hover:text-green-800 font-medium">
              <FileText class="w-5 h-5 mr-2" />
              View Source Code
            </a>
            <a href="https://github.com/MicroPyramid/Django-CRM/blob/main/SECURITY.md" 
               target="_blank" 
               rel="noopener noreferrer"
               class="inline-flex items-center text-green-700 hover:text-green-800 font-medium">
              <Shield class="w-5 h-5 mr-2" />
              Security Guidelines
            </a>
          </div>
        </div>
      </div>

    </div>
  </div>
</section>

<!-- CTA Section -->
<section class="bg-gradient-to-r from-blue-600 to-indigo-700 text-white py-16">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h2 class="text-3xl font-bold mb-6">
      Take Control of Your Data Privacy
    </h2>
    <p class="text-xl text-blue-100 mb-8">
      Ready to switch to a CRM solution that truly respects your privacy? 
      Self-host BottleCRM and maintain complete control over your business data.
    </p>
    <div class="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
      <a href="/login" 
         class="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-blue-700 bg-white hover:bg-gray-100 transition-colors">
        <Shield class="w-5 h-5 mr-2" />
        Start Private Demo
      </a>
      <a href="/contact" 
         class="inline-flex items-center justify-center px-6 py-3 border-2 border-white text-base font-medium rounded-lg text-white hover:bg-white/10 transition-colors">
        <Mail class="w-5 h-5 mr-2" />
        Privacy Questions?
      </a>
    </div>
  </div>
</section>