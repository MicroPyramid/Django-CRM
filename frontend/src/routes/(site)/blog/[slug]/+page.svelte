<script>
  import { marked } from 'marked';
  
  export let data;

  const { post } = data;

  // Combine all content blocks into a single rendered string
  let renderedContent = post.contentBlocks?.map(block => marked(block.content)).join('') || '';
</script>

<svelte:head>
  <title>{post.title} | BottleCRM Blog</title>
  <meta name="description" content={post.excerpt || `Read ${post.title} on the BottleCRM blog`} />
</svelte:head>

<article class="bg-white">
  <!-- Hero section -->
  <div class="py-16 bg-gradient-to-b from-blue-50 to-white">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Breadcrumb navigation -->
      <nav class="mb-6">
        <ol class="flex items-center space-x-2 text-sm text-gray-600">
          <li>
            <a href="/blog" class="hover:text-blue-600">Blog</a>
          </li>
          <li>
            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
            </svg>
          </li>
          <li>
            <span class="text-gray-900 font-medium truncate" aria-current="page">{post.title}</span>
          </li>
        </ol>
      </nav>
      
      <div class="text-center">
        <h1 class="text-3xl font-extrabold text-gray-900 sm:text-4xl md:text-5xl">
          {post.title}
        </h1>
      </div>

    </div>
  </div>
  
  <!-- Blog content -->
  <div class="py-12">
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="prose prose-blue prose-lg mx-auto">
        {@html renderedContent}
      </div>
    </div>
  </div>
</article>

<div class="bg-white py-8">
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center">
      <a href="/blog" class="inline-flex items-center text-blue-600 hover:underline">
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
        </svg>
        Back to all blog posts
      </a>
    </div>
  </div>
</div>

<style>
  /* Add additional styling for the prose content if needed */
  :global(.prose img) {
    border-radius: 0.375rem;
    margin: 2rem auto;
  }
  
  :global(.prose a) {
    color: #2563eb;
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  
  :global(.prose a:hover) {
    color: #1e40af;
  }
  
  :global(.prose blockquote) {
    border-left-color: #93c5fd;
    background-color: #f0f9ff;
    padding: 1rem;
    border-radius: 0.25rem;
  }
</style>
