<script>
	import '../../../app.css';
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';

    import imgGoogle from '$lib/assets/images/google.svg';
    import imgLogo from '$lib/assets/images/logo.png';
    import { 
        Users, 
        BarChart3, 
        CheckSquare, 
        TrendingUp,
        Zap,
        Check,
        Shield,
        Github,
        Star
    } from '@lucide/svelte';
    
    export let data;

    let mounted = false;
    let isLoading = false;

    const features = [
        { icon: Users, text: "Unlimited Contacts" },
        { icon: BarChart3, text: "Sales Pipeline" },
        { icon: CheckSquare, text: "Task Management" },
        { icon: TrendingUp, text: "Analytics & Reports" }
    ];

    const benefits = [
        "100% Free Forever",
        "No Credit Card Required", 
        "Complete Data Ownership",
        "Self-Hostable Solution"
    ];

    onMount(() => {
        mounted = true;
    });

    function handleGoogleLogin() {
        isLoading = true;
        // The actual navigation will happen via the href
        setTimeout(() => {
            isLoading = false;
        }, 3000);
    }
</script>

<svelte:head>
    <title>Login | BottleCRM - Free Open-Source CRM for Startups</title>
    <meta name="description" content="Sign in to BottleCRM - the completely free, open-source CRM solution for startups and small businesses. No subscription fees, unlimited users." />
</svelte:head>

<!-- Main Container with Gradient Background -->
<div class="min-h-screen bg-gradient-to-br from-blue-600 via-indigo-700 to-purple-800 relative overflow-hidden">
    <!-- Animated Background Elements -->
    <div class="absolute inset-0 bg-black/10"></div>
    <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent"></div>
    
    <!-- Floating Background Shapes -->
    <div class="absolute top-10 left-10 w-72 h-72 bg-white/5 rounded-full blur-3xl animate-pulse"></div>
    <div class="absolute bottom-10 right-10 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
    
    <div class="relative z-10 flex items-center justify-center min-h-screen p-4">
        <div class="w-full max-w-6xl mx-auto">
            <div class="grid lg:grid-cols-2 gap-12 items-center">
                
                <!-- Left Side - Branding & Features -->
                <div class="hidden lg:block text-white">
                    {#if mounted}
                        <div in:fly="{{ x: -50, duration: 800, delay: 200 }}">
                            <div class="mb-8">
                                <div class="inline-flex items-center px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-6">
                                    <Star class="w-4 h-4 mr-2" />
                                    <span class="text-sm font-medium">Free & Open Source CRM</span>
                                </div>
                                
                                <h1 class="text-4xl xl:text-5xl font-extrabold mb-6 leading-tight">
                                    Welcome to <span class="text-yellow-300">BottleCRM</span>
                                </h1>
                                
                                <p class="text-xl text-blue-100 mb-8 leading-relaxed">
                                    The completely free, self-hostable CRM solution built specifically for startups and growing businesses.
                                </p>
                            </div>

                            <!-- Key Benefits -->
                            <div class="mb-8">
                                <h3 class="text-lg font-semibold mb-4">Why Choose BottleCRM?</h3>
                                <ul class="space-y-3">
                                    {#each benefits as benefit, i}
                                        <li class="flex items-center" in:fly="{{ x: -30, duration: 600, delay: 400 + (i * 100) }}">
                                            <Check class="w-5 h-5 text-green-400 mr-3 flex-shrink-0" />
                                            <span>{benefit}</span>
                                        </li>
                                    {/each}
                                </ul>
                            </div>

                            <!-- Feature Icons -->
                            <div class="grid grid-cols-2 gap-4">
                                {#each features as feature, i}
                                    <div class="flex items-center p-3 bg-white/10 backdrop-blur-sm rounded-xl border border-white/20"
                                         in:fly="{{ y: 30, duration: 600, delay: 600 + (i * 100) }}">
                                        <div class="rounded-lg bg-white/20 p-2 mr-3">
                                            {#snippet featureIcon(/** @type {any} */ icon)}
                                                {@const FeatureIcon = icon}
                                                <FeatureIcon class="w-5 h-5" />
                                            {/snippet}
                                            {@render featureIcon(feature.icon)}
                                        </div>
                                        <span class="text-sm font-medium">{feature.text}</span>
                                    </div>
                                {/each}
                            </div>

                            <!-- Stats -->
                            <div class="mt-8 pt-8 border-t border-white/20">
                                <div class="grid grid-cols-3 gap-4 text-center">
                                    <div>
                                        <div class="text-2xl font-bold text-yellow-300">100%</div>
                                        <div class="text-sm text-blue-200">Free</div>
                                    </div>
                                    <div>
                                        <div class="text-2xl font-bold text-yellow-300">∞</div>
                                        <div class="text-sm text-blue-200">Users</div>
                                    </div>
                                    <div>
                                        <div class="text-2xl font-bold text-yellow-300">MIT</div>
                                        <div class="text-sm text-blue-200">License</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {/if}
                </div>

                <!-- Right Side - Login Form -->
                <div class="flex justify-center lg:justify-end">
                    {#if mounted}
                        <div class="w-full max-w-md" in:fly="{{ y: 50, duration: 800, delay: 100 }}">
                            <!-- Login Card -->
                            <div class="bg-white/95 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border border-white/20 relative overflow-hidden">
                                
                                <!-- Card Background Pattern -->
                                <div class="absolute inset-0 bg-gradient-to-br from-gray-50/50 to-white/50"></div>
                                
                                <!-- Card Content -->
                                <div class="relative z-10">
                                    <!-- Logo and Header -->
                                    <div class="text-center mb-8">
                                        <div class="mb-6" in:fade="{{ duration: 600, delay: 300 }}">
                                            <img src="{imgLogo}" alt="BottleCRM Logo" class="mx-auto h-16 w-auto" />
                                        </div>
                                        
                                        <div in:fade="{{ duration: 600, delay: 400 }}">
                                            <h2 class="text-2xl font-bold text-gray-900 mb-2">Welcome Back</h2>
                                            <p class="text-gray-600 text-sm leading-relaxed">
                                                Sign in to your free BottleCRM account and start managing your customer relationships more effectively.
                                            </p>
                                        </div>
                                    </div>

                                    <!-- Benefits List for Mobile -->
                                    <div class="lg:hidden mb-6" in:fade="{{ duration: 600, delay: 500 }}">
                                        <div class="bg-blue-50 rounded-xl p-4 border border-blue-100">
                                            <div class="flex items-center mb-3">
                                                <Zap class="w-5 h-5 text-blue-600 mr-2" />
                                                <span class="font-semibold text-blue-900 text-sm">Free CRM Features</span>
                                            </div>
                                            <ul class="space-y-2 text-xs text-blue-700">
                                                <li class="flex items-center">
                                                    <Check class="w-3 h-3 mr-2 flex-shrink-0" />
                                                    <span>Unlimited contacts & users</span>
                                                </li>
                                                <li class="flex items-center">
                                                    <Check class="w-3 h-3 mr-2 flex-shrink-0" />
                                                    <span>Self-hosted solution</span>
                                                </li>
                                                <li class="flex items-center">
                                                    <Check class="w-3 h-3 mr-2 flex-shrink-0" />
                                                    <span>No subscription fees</span>
                                                </li>
                                            </ul>
                                        </div>
                                    </div>

                                    <!-- Google Sign In Button -->
                                    <div in:fade="{{ duration: 600, delay: 600 }}">
                                        <a href="{data['google_url']}"
                                           onclick={handleGoogleLogin}
                                           class="group w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-200 hover:border-blue-300 hover:bg-blue-50 text-gray-800 font-semibold py-4 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 focus:outline-none focus:ring-4 focus:ring-blue-200 relative overflow-hidden">
                                            
                                            <!-- Button Background Effect -->
                                            <div class="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/5 to-blue-500/0 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                                            
                                            <!-- Loading Spinner -->
                                            {#if isLoading}
                                                <div class="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
                                            {:else}
                                                <img src="{imgGoogle}" alt="Google" class="h-5 w-5 group-hover:scale-110 transition-transform duration-200" />
                                            {/if}
                                            
                                            <span class="relative z-10">
                                                {isLoading ? 'Connecting...' : 'Continue with Google'}
                                            </span>
                                        </a>
                                    </div>

                                    <!-- Security Notice -->
                                    <div class="mt-6 text-center" in:fade="{{ duration: 600, delay: 700 }}">
                                        <div class="flex items-center justify-center text-xs text-gray-500 mb-3">
                                            <Shield class="w-4 h-4 mr-1" />
                                            <span>Your data is secure and private</span>
                                        </div>
                                        
                                        <!-- Footer Links -->
                                        <div class="flex items-center justify-center space-x-4 text-xs">
                                            <a href="https://github.com/MicroPyramid/opensource-startup-crm" 
                                               target="_blank" 
                                               rel="noopener noreferrer"
                                               class="flex items-center text-gray-600 hover:text-blue-600 transition-colors duration-200">
                                                <Github class="w-3 h-3 mr-1" />
                                                <span>Open Source</span>
                                            </a>
                                            <span class="text-gray-300">•</span>
                                            <a href="/features" class="text-gray-600 hover:text-blue-600 transition-colors duration-200">
                                                Features
                                            </a>
                                            <span class="text-gray-300">•</span>
                                            <a href="/contact" class="text-gray-600 hover:text-blue-600 transition-colors duration-200">
                                                Support
                                            </a>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Below Card Notice -->
                            <div class="mt-6 text-center" in:fade="{{ duration: 600, delay: 800 }}">
                                <p class="text-blue-100 text-sm">
                                    New to BottleCRM? 
                                    <a href="/" class="text-yellow-300 hover:text-yellow-200 font-medium underline transition-colors duration-200">
                                        Learn more about our free CRM
                                    </a>
                                </p>
                            </div>
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            opacity: 0.5;
        }
        50% {
            transform: scale(1.05);
            opacity: 0.8;
        }
    }
    
    .animate-pulse {
        animation: pulse 4s ease-in-out infinite;
    }
</style>

