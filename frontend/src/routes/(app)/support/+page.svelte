<script>
    import { Github, Mail, Bug, Lightbulb, Shield, Wrench, Heart, Users } from '@lucide/svelte';
    
    /** @type {{ data: import('./$types').PageData }} */
    let { data } = $props();
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
        <!-- Header Section -->
        <div class="text-center mb-12">
            <h1 class="text-4xl font-bold mb-4 text-gray-900 dark:text-white">BottleCRM Support</h1>
            <p class="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                Empowering startups with free, open-source CRM solutions. 
                Say goodbye to expensive subscription fees.
            </p>
        </div>

        <!-- Mission Statement -->
        <div class="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800 rounded-xl p-8 mb-8">
            <div class="flex items-start gap-4">
                <div class="bg-blue-100 dark:bg-blue-800 p-3 rounded-lg flex-shrink-0">
                    <Heart class="w-6 h-6 text-blue-600 dark:text-blue-300" />
                </div>
                <div>
                    <h2 class="text-2xl font-semibold mb-3 text-gray-900 dark:text-white">Our Mission</h2>
                    <p class="text-gray-700 dark:text-gray-300 leading-relaxed">
                        BottleCRM addresses the high subscription costs of commercial CRM alternatives by providing 
                        a completely free, open-source, and highly customizable solution. Clone it, self-host it, 
                        and make it yours - forever free.
                    </p>
                </div>
            </div>
        </div>

        <!-- Support Grid -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
            <!-- Community Support -->
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 hover:shadow-lg dark:hover:shadow-xl dark:hover:shadow-gray-900/20 transition-shadow">
                <div class="flex items-center gap-3 mb-4">
                    <div class="bg-green-100 dark:bg-green-800 p-2 rounded-lg">
                        <Github class="w-5 h-5 text-green-600 dark:text-green-300" />
                    </div>
                    <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Community Support</h3>
                </div>
                <p class="text-gray-600 dark:text-gray-300 mb-4">
                    Join our open-source community for free support, discussions, and collaboration.
                </p>
                <a 
                    href="https://github.com/MicroPyramid/Django-CRM" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-2 text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 font-medium"
                >
                    <Github class="w-4 h-4" />
                    Visit GitHub Repository
                </a>
            </div>

            <!-- Paid Support -->
            <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 hover:shadow-lg dark:hover:shadow-xl dark:hover:shadow-gray-900/20 transition-shadow">
                <div class="flex items-center gap-3 mb-4">
                    <div class="bg-purple-100 dark:bg-purple-800 p-2 rounded-lg">
                        <Users class="w-5 h-5 text-purple-600 dark:text-purple-300" />
                    </div>
                    <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Professional Support</h3>
                </div>
                <p class="text-gray-600 dark:text-gray-300 mb-4">
                    Get priority support, hosting assistance, and custom development services.
                </p>
                <a 
                    href="mailto:ashwin@micropyramid.com" 
                    class="inline-flex items-center gap-2 text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium"
                >
                    <Mail class="w-4 h-4" />
                    Contact for Paid Support
                </a>
            </div>
        </div>

        <!-- Feature Requests & Bug Reports -->
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-6">
            <div class="flex items-center gap-3 mb-4">
                <div class="bg-blue-100 dark:bg-blue-800 p-2 rounded-lg">
                    <Lightbulb class="w-5 h-5 text-blue-600 dark:text-blue-300" />
                </div>
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Feature Requests & Ideas</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
                Have an idea to make BottleCRM better? We'd love to hear from you! Share your feature 
                requests and help shape the future of open-source CRM.
            </p>
            <a 
                href="https://github.com/MicroPyramid/Django-CRM/issues/new?template=feature_request.md" 
                target="_blank" 
                rel="noopener noreferrer"
                class="inline-flex items-center gap-2 bg-blue-600 dark:bg-blue-700 text-white px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
            >
                <Lightbulb class="w-4 h-4" />
                Request Feature
            </a>
        </div>

        <!-- Bug Reports -->
        <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-6 mb-6">
            <div class="flex items-center gap-3 mb-4">
                <div class="bg-orange-100 dark:bg-orange-800 p-2 rounded-lg">
                    <Bug class="w-5 h-5 text-orange-600 dark:text-orange-300" />
                </div>
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Bug Reports</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
                Found a bug? Help us improve BottleCRM by reporting issues. Your feedback helps 
                make the platform more stable for everyone.
            </p>
            <a 
                href="https://github.com/MicroPyramid/Django-CRM/issues/new?template=bug_report.md" 
                target="_blank" 
                rel="noopener noreferrer"
                class="inline-flex items-center gap-2 bg-orange-600 dark:bg-orange-700 text-white px-4 py-2 rounded-lg hover:bg-orange-700 dark:hover:bg-orange-600 transition-colors"
            >
                <Bug class="w-4 h-4" />
                Report Bug
            </a>
        </div>

        <!-- Security Issues -->
        <div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 mb-6">
            <div class="flex items-center gap-3 mb-4">
                <div class="bg-red-100 dark:bg-red-800 p-2 rounded-lg">
                    <Shield class="w-5 h-5 text-red-600 dark:text-red-300" />
                </div>
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Security Issues</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
                <strong>Security is our priority.</strong> If you discover any security vulnerabilities, 
                please report them privately. Do not create public GitHub issues for security concerns.
            </p>
            <a 
                href="mailto:ashwin@micropyramid.com?subject=Security%20Issue%20-%20BottleCRM" 
                class="inline-flex items-center gap-2 bg-red-600 dark:bg-red-700 text-white px-4 py-2 rounded-lg hover:bg-red-700 dark:hover:bg-red-600 transition-colors"
            >
                <Mail class="w-4 h-4" />
                Report Security Issue
            </a>
        </div>

        <!-- Custom Development -->
        <div class="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border border-indigo-200 dark:border-indigo-800 rounded-xl p-6">
            <div class="flex items-center gap-3 mb-4">
                <div class="bg-indigo-100 dark:bg-indigo-800 p-2 rounded-lg">
                    <Wrench class="w-5 h-5 text-indigo-600 dark:text-indigo-300" />
                </div>
                <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Custom CRM Development</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">
                Need BottleCRM tailored to your specific business needs? We offer professional 
                customization services including hosting, custom features, integrations, and ongoing support.
            </p>
            <div class="flex flex-col sm:flex-row gap-3">
                <a 
                    href="mailto:ashwin@micropyramid.com?subject=Custom%20CRM%20Development%20Inquiry" 
                    class="inline-flex items-center gap-2 bg-indigo-600 dark:bg-indigo-700 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
                >
                    <Mail class="w-4 h-4" />
                    Get Custom Quote
                </a>
                
            </div>
        </div>
    </div>
</div>