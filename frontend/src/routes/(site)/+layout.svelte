<script>
  import { page } from '$app/state';
  import { onMount } from 'svelte';
  import '../../app.css';
  import logo from '$lib/assets/images/logo.png';
  import { 
    Menu, 
    X, 
    ArrowRight, 
    CheckSquare, 
    DollarSign, 
    Video, 
    Edit, 
    MessageCircle, 
    Github,
    Twitter,
    Linkedin
  } from '@lucide/svelte';
  let isMenuOpen = false;
  let scrollY = 0;
  
  // Toggle mobile menu
  function toggleMenu() {
    isMenuOpen = !isMenuOpen;
  }
  
  // Close mobile menu when route changes
  $: if (page.url.pathname) {
    isMenuOpen = false;
  }
  
  // Handle scroll for navbar transparency
  $: navbarClass = scrollY > 10 
    ? 'bg-white/95 backdrop-blur-lg shadow-lg border-b border-gray-200/50' 
    : 'bg-white/80 backdrop-blur-sm shadow-md';
  
  onMount(() => {
    const handleScroll = () => scrollY = window.scrollY;
    window.addEventListener('scroll', handleScroll);
    
    // Close mobile menu when clicking outside
    /**
     * @param {Event} event
     */
    const handleClickOutside = (event) => {
      const nav = document.querySelector('nav');
      if (isMenuOpen && nav && !nav.contains(/** @type {Node} */ (event.target))) {
        isMenuOpen = false;
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      document.removeEventListener('click', handleClickOutside);
    };
  });
</script>

<svelte:window bind:scrollY />

<svelte:head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
  <meta name="theme-color" content="#2563EB" />
  <meta name="msapplication-TileColor" content="#2563EB" />
  
  <!-- Enhanced SEO Meta Tags -->
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />
  <meta name="language" content="English" />
  <meta name="author" content="MicroPyramid" />
  <link rel="canonical" href="https://bottlecrm.io{page.url.pathname}" />
  
  <!-- Enhanced Open Graph -->
  <meta property="og:site_name" content="BottleCRM" />
  <meta property="og:locale" content="en_US" />
  
  <!-- Enhanced Twitter Cards -->
  <meta name="twitter:site" content="@micropyramid" />
  <meta name="twitter:creator" content="@micropyramid" />
  
  <!-- Preconnect to external domains -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://github.com" />
</svelte:head>

<div class="min-h-screen flex flex-col bg-gray-50 overflow-x-hidden">
  <!-- Enhanced Navigation -->
  <nav class="fixed top-0 w-full z-50 transition-all duration-300 {navbarClass}">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <!-- Logo Section -->
        <div class="flex items-center flex-shrink-0">
          <a href="/" class="flex items-center group" aria-label="BottleCRM Homepage">
            <div class="relative">
              <img src={logo} alt="BottleCRM Logo" class="h-7 w-7 sm:h-8 sm:w-8 group-hover:opacity-90 transition-opacity duration-200" />
              <div class="absolute -top-1 -right-1 w-2.5 h-2.5 sm:w-3 sm:h-3 bg-green-500 rounded-full animate-pulse"></div>
            </div>
            <span class="ml-2 text-lg sm:text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors duration-200">BottleCRM</span>
            <span class="hidden xs:block ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">FREE</span>
          </a>
        </div>
        
        <!-- Desktop Navigation - Hidden on smaller screens -->
        <div class="hidden xl:flex items-center space-x-1">
          <a href="/features" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Features</a>
          <a href="/pricing" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Pricing</a>
          <a href="https://www.youtube.com/@bottlecrm" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Live Demo</a>
          <a href="/blog" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Blog</a>
          <a href="/contact" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Support</a>
          
          <!-- GitHub Star Button -->
          <a href="https://github.com/MicroPyramid/opensource-startup-crm" target="_blank" rel="noopener noreferrer" 
             class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors duration-200"
             aria-label="Star BottleCRM on GitHub">
            <Github class="w-4 h-4 mr-1" />
          </a>
          
          <div class="h-6 w-px bg-gray-300 mx-2"></div>
          
          <a href="/login" class="px-4 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Login</a>
          <a href="/login" class="inline-flex items-center px-4 lg:px-6 py-2.5 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200">
            Start Free
            <ArrowRight class="ml-2 w-4 h-4" />
          </a>
        </div>
        
        <!-- Tablet Navigation - Shows limited items -->
        <div class="hidden lg:flex xl:hidden items-center space-x-2">
          <a href="https://www.youtube.com/@bottlecrm" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Demo</a>
          <a href="/login" class="px-3 py-2 rounded-lg text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200">Login</a>
          <a href="/signup" class="px-4 py-2 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors duration-200">Sign Up</a>
          
          <button onclick={toggleMenu} 
                  class="ml-2 inline-flex items-center justify-center p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-200"
                  aria-label="Toggle navigation menu">
            {#if isMenuOpen}
              <X class="h-5 w-5" />
            {:else}
              <Menu class="h-5 w-5" />
            {/if}
          </button>
        </div>
        
        <!-- Mobile Navigation Controls -->
        <div class="lg:hidden flex items-center space-x-2">
          <!-- Mobile Quick Actions -->
          <div class="hidden sm:flex items-center space-x-2">
            <a href="/login" class="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200">Login</a>
            <a href="/signup" class="px-3 py-2 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors duration-200">
              Sign Up
            </a>
          </div>
          
          <!-- Hamburger Menu Button -->
          <button onclick={toggleMenu} 
                  class="inline-flex items-center justify-center p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 active:bg-gray-200 transition-all duration-200"
                  aria-label="Toggle navigation menu"
                  aria-expanded={isMenuOpen}>
            {#if isMenuOpen}
              <X class="h-6 w-6" />
            {:else}
              <Menu class="h-6 w-6" />
            {/if}
          </button>
        </div>
      </div>
    </div>

    <!-- Enhanced Mobile & Tablet Menu -->
    {#if isMenuOpen}
      <div class="xl:hidden bg-white/98 backdrop-blur-xl border-t border-gray-200/60 shadow-2xl animate-in slide-in-from-top-5 duration-200">
        <div class="px-4 pt-4 pb-6 space-y-2 max-h-[calc(100vh-4rem)] overflow-y-auto">
          <!-- Navigation Links -->
          <div class="space-y-1">
            <a href="/features" class="flex items-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200">
              <CheckSquare class="w-5 h-5 mr-3 text-blue-500" />
              Features
            </a>
            <a href="/pricing" class="flex items-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200">
              <DollarSign class="w-5 h-5 mr-3 text-green-500" />
              <span class="flex-1">Pricing</span>
              <span class="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full font-medium">Free</span>
            </a>
            <a href="https://www.youtube.com/@bottlecrm" class="flex items-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200">
              <Video class="w-5 h-5 mr-3 text-purple-500" />
              Live Demo
            </a>
            <a href="/blog" class="flex items-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200">
              <Edit class="w-5 h-5 mr-3 text-red-500" />
              Blog
            </a>
            <a href="/contact" class="flex items-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 hover:text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200">
              <MessageCircle class="w-5 h-5 mr-3 text-indigo-500" />
              Support
            </a>
          </div>

          <!-- GitHub Link -->
          <div class="pt-2">
            <a href="https://github.com/MicroPyramid/svelte-crm" target="_blank" rel="noopener noreferrer" 
               class="flex items-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 active:bg-gray-100 transition-all duration-200">
              <Github class="w-5 h-5 mr-3" />
              <span class="flex-1">GitHub Repository</span>
              <span class="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full font-medium">★ 1K+</span>
            </a>
          </div>
          
          <!-- Mobile Auth Buttons -->
          <div class="pt-4 border-t border-gray-200 space-y-3 sm:hidden">
            <a href="/login" class="block w-full text-center px-4 py-3 rounded-xl text-base font-medium text-gray-700 border-2 border-gray-300 hover:bg-gray-50 active:bg-gray-100 transition-all duration-200">
              Sign In
            </a>
            <a href="/signup" class="block w-full text-center px-4 py-3 rounded-xl text-base font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 active:from-blue-800 active:to-blue-900 shadow-lg transition-all duration-200">
              Start Free Trial
            </a>
          </div>
        </div>
      </div>
    {/if}
  </nav>

  <!-- Page content with top padding for fixed nav -->
  <main class="flex-grow pt-16">
    <slot />
  </main>

  <!-- Enhanced Footer with better SEO -->
  <footer class="bg-gray-900 text-gray-300">
    <div class="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
        <!-- Company Info -->
        <div class="lg:col-span-2">
          <div class="flex items-center mb-4">
            <img src={logo} alt="BottleCRM Logo" class="h-8 w-8 mr-3" />
            <span class="text-xl font-bold text-white">BottleCRM</span>
          </div>
          <p class="text-gray-400 mb-6 leading-relaxed">The only CRM you'll ever need - completely free, open-source, and designed for startups. Build better customer relationships without breaking the bank.</p>
          
          <!-- Social Links -->
          <div class="flex space-x-4">
            <a href="https://github.com/MicroPyramid/opensource-startup-crm" target="_blank" rel="noopener noreferrer" 
               class="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200" aria-label="GitHub">
              <Github class="h-5 w-5" />
            </a>
            <a href="https://x.com/micropyramid" target="_blank" rel="noopener noreferrer" 
               class="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200" aria-label="Twitter">
              <Twitter class="h-5 w-5" />
            </a>
            <a href="https://linkedin.com/company/micropyramid" target="_blank" rel="noopener noreferrer" 
               class="p-2 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors duration-200" aria-label="LinkedIn">
              <Linkedin class="h-5 w-5" />
            </a>
          </div>
        </div>

        <!-- Enhanced footer columns with SEO-friendly content -->
        <div>
          <h3 class="text-lg font-semibold text-white mb-4">CRM Solutions</h3>
          <ul class="space-y-3 text-sm">
            <li><a href="/features/contact-management" class="hover:text-white transition-colors duration-200">Contact Management</a></li>
            <li><a href="/features/lead-management" class="hover:text-white transition-colors duration-200">Lead Management</a></li>
            <li><a href="/features/account-management" class="hover:text-white transition-colors duration-200">Account Management</a></li>
            <li><a href="/features/sales-pipeline" class="hover:text-white transition-colors duration-200">Sales Pipeline</a></li>
            <li>
              <a href="/features/analytics" class="hover:text-white transition-colors duration-200 inline-flex items-center">
                Analytics & Reports
                <span class="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-4">Resources</h3>
          <ul class="space-y-3 text-sm">
            <li><a href="/blog" class="hover:text-white transition-colors duration-200">CRM Blog</a></li>
            <li>
              <a href="/documentation" class="hover:text-white transition-colors duration-200 inline-flex items-center">
                Documentation
                <span class="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
              </a>
            </li>
            <li>
              <a href="/tutorials" class="hover:text-white transition-colors duration-200 inline-flex items-center">
                Video Tutorials
                <span class="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
              </a>
            </li>
            <li>
              <a href="/api-docs" class="hover:text-white transition-colors duration-200 inline-flex items-center">
                API Documentation
                <span class="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
              </a>
            </li>
            <li>
              <a href="/case-studies" class="hover:text-white transition-colors duration-200 inline-flex items-center">
                Case Studies
                <span class="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-white mb-4">Support</h3>
          <ul class="space-y-3 text-sm">
            <li><a href="/contact" class="hover:text-white transition-colors duration-200">Contact Support</a></li>
            <li><a href="/faq" class="hover:text-white transition-colors duration-200">FAQ</a></li>
            <li>
              <a href="/hosting-services" class="hover:text-white transition-colors duration-200 inline-flex items-center">
                Hosting Services
                <span class="ml-2 text-[10px] bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded-full font-medium">Coming Soon</span>
              </a>
            </li>
            <li><a href="/customization" class="hover:text-white transition-colors duration-200">Custom Development</a></li>
            <li><a href="/migration" class="hover:text-white transition-colors duration-200">CRM Migration</a></li>
          </ul>
        </div>
      </div>

      <!-- Bottom footer -->
      <div class="mt-12 pt-8 border-t border-gray-800">
        <div class="flex flex-col lg:flex-row justify-between items-center space-y-4 lg:space-y-0">
          <div class="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-6">
            <p class="text-sm text-gray-400">© {new Date().getFullYear()} BottleCRM by <a href="https://micropyramid.com" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300">MicroPyramid</a>. Open Source & Free Forever.</p>
            <div class="flex space-x-4 text-sm">
              <a href="/privacy-policy" class="text-gray-400 hover:text-white transition-colors duration-200">Privacy</a>
              <a href="/terms-of-service" class="text-gray-400 hover:text-white transition-colors duration-200">Terms</a>
              <a href="/sitemap.xml" class="text-gray-400 hover:text-white transition-colors duration-200">Sitemap</a>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  </footer>
</div>
