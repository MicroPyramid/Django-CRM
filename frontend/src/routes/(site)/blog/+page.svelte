<script>
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  
  export let data;
  
  // Destructure the data with proper type checking
  const posts = data.posts || [];
  const pagination = data.pagination || { 
    page: 1, 
    totalPages: 1,
    hasNextPage: false,
    hasPreviousPage: false
  };
  
  /**
   * Format date for display
   * @param {string|Date} dateString - The date to format
   * @returns {string} The formatted date string
   */
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
  
  /**
   * Limit text to a certain number of words
   * @param {string} text - The text to limit
   * @param {number} limit - The word limit
   * @returns {string} The limited text
   */
  function limitWords(text, limit = 30) {
    if (!text) return '';
    const words = text.split(' ');
    if (words.length <= limit) return text;
    
    return words.slice(0, limit).join(' ') + '...';
  }
  
  /**
   * Change page function for pagination
   * @param {number} newPage - The new page number
   */
  function changePage(newPage) {
    if (newPage < 1 || newPage > pagination.totalPages) return;
    
    const params = new URLSearchParams($page.url.searchParams);
    params.set('page', newPage.toString());
    goto(`?${params.toString()}`);
  }
</script>

<svelte:head>
  <title>Blog | BottleCRM</title>
  <meta name="description" content="Latest articles and updates from BottleCRM" />
</svelte:head>

<section class="bg-gradient-to-b from-blue-50 to-white py-16">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center">
      <h1 class="text-4xl font-extrabold text-gray-900 sm:text-5xl sm:tracking-tight lg:text-6xl">
        Our Blog
      </h1>
      <p class="max-w-xl mt-5 mx-auto text-xl text-gray-500">
        The latest news, articles, and resources from BottleCRM
      </p>
    </div>
  </div>
</section>

<section class="py-12 bg-white">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    {#if posts && posts.length > 0}
      <div class="space-y-10 divide-y divide-gray-200">
        {#each posts as post}
          <article class="pt-10 first:pt-0">
            <div class="flex flex-col lg:flex-row">
              <div class="flex-1">
                <div class="flex items-center gap-3 text-sm text-gray-500 mb-2">
                  <time datetime={post.createdAt.toISOString()}>{formatDate(post.createdAt)}</time>
                  <span class="inline-block h-1 w-1 rounded-full bg-gray-300"></span>
                </div>
                
                <a href="/blog/{post.slug}" class="block group">
                  <h2 class="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors mb-3">
                    {post.title}
                  </h2>
                </a>
                
                {#if post.excerpt}
                  <p class="text-gray-600 text-base leading-relaxed mb-4">
                    {limitWords(post.excerpt, 40)}
                  </p>
                {/if}
                
                <div class="mt-4">
                  <a href="/blog/{post.slug}" class="text-blue-600 hover:text-blue-800 font-medium flex items-center">
                    Read article
                    <svg class="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                    </svg>
                  </a>
                </div>
              </div>
              
              
            </div>
          </article>
        {/each}
      </div>
      
      <!-- Pagination controls -->
      {#if pagination.totalPages > 1}
        <div class="mt-12 flex flex-col items-center justify-between space-y-4 border-t border-gray-200 pt-6 sm:flex-row sm:space-y-0">
          <div class="text-sm text-gray-700">
            Showing <span class="font-medium">{(pagination.page - 1) * pagination.pageSize + 1}</span> to 
            <span class="font-medium">{Math.min(pagination.page * pagination.pageSize, pagination.totalPosts)}</span> of 
            <span class="font-medium">{pagination.totalPosts}</span> blog posts
          </div>
          <div class="flex space-x-2">
            <button 
              onclick={() => changePage(1)}
              class="px-3 py-1 rounded-md text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!pagination.hasPreviousPage}
            >
              First
            </button>
            <button 
              onclick={() => changePage(pagination.page - 1)}
              class="px-3 py-1 rounded-md text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!pagination.hasPreviousPage}
            >
              Previous
            </button>
            <span class="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md">
              {pagination.page} / {pagination.totalPages}
            </span>
            <button 
              onclick={() => changePage(pagination.page + 1)}
              class="px-3 py-1 rounded-md text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!pagination.hasNextPage}
            >
              Next
            </button>
            <button 
              onclick={() => changePage(pagination.totalPages)}
              class="px-3 py-1 rounded-md text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!pagination.hasNextPage}
            >
              Last
            </button>
          </div>
        </div>
      {/if}
    {:else}
      <div class="text-center py-16">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1M19 20a2 2 0 002-2V8a2 2 0 00-2-2h-5M8 12h8m-8 4h6" />
        </svg>
        <h3 class="mt-2 text-lg font-medium text-gray-900">No blog posts yet</h3>
        <p class="mt-1 text-base text-gray-500">Check back soon for new content!</p>
      </div>
    {/if}
  </div>
</section>
