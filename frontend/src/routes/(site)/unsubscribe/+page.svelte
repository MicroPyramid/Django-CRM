<script>
  import { enhance } from '$app/forms';
  import { onMount } from 'svelte';
  
  /** @type {import('./$types').PageData} */
  export let data;
  
  let unsubscribeForm;
  /** @type {string} */
  let message = '';
  let showMessage = false;
  let isSuccess = false;
</script>

<svelte:head>
  <title>Unsubscribe - BottleCRM Newsletter</title>
  <meta name="description" content="Unsubscribe from BottleCRM newsletter updates and communications." />
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
  <div class="sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900 mb-2">Newsletter Unsubscribe</h1>
        <p class="text-sm text-gray-600">We're sorry to see you go!</p>
      </div>

      {#if data.error}
        <div class="mb-6 p-4 rounded-lg bg-red-50 border border-red-200">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">Error</h3>
              <p class="mt-1 text-sm text-red-700">{data.error}</p>
            </div>
          </div>
        </div>
      {:else if data.subscriber}
        <div class="mb-6">
          <p class="text-sm text-gray-600 mb-4">
            You are about to unsubscribe the email address:
          </p>
          <p class="text-lg font-medium text-gray-900 mb-6 p-3 bg-gray-50 rounded-lg">
            {data.subscriber.email}
          </p>
          
          {#if showMessage}
            <div class="mb-4 p-3 rounded-lg {isSuccess ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}">
              <p class="text-sm {isSuccess ? 'text-green-800' : 'text-red-800'}">{message}</p>
            </div>
          {/if}
          
          <form 
            method="POST" 
            action="?/unsubscribe"
            use:enhance={({ submitter }) => {
              if (submitter) /** @type {HTMLButtonElement} */ (submitter).disabled = true;
              return async ({ result, update }) => {
                if (result.type === 'success') {
                  message = /** @type {string} */ (result.data?.message) || 'Successfully unsubscribed!';
                  showMessage = true;
                  isSuccess = true;
                } else if (result.type === 'failure') {
                  message = /** @type {string} */ (result.data?.message) || 'Failed to unsubscribe. Please try again.';
                  showMessage = true;
                  isSuccess = false;
                  if (submitter) /** @type {HTMLButtonElement} */ (submitter).disabled = false;
                }
                await update();
              };
            }}
            bind:this={unsubscribeForm}
          >
            <input type="hidden" name="token" value={data.subscriber.token} />
            
            <div class="space-y-4">
              <button 
                type="submit"
                class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              >
                Confirm Unsubscribe
              </button>
              
              <div class="text-center">
                <a 
                  href="/"
                  class="text-sm text-blue-600 hover:text-blue-500"
                >
                  Cancel and go back to homepage
                </a>
              </div>
            </div>
          </form>
        </div>
        
        <div class="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 class="text-sm font-medium text-blue-900 mb-2">Before you go...</h3>
          <p class="text-sm text-blue-800 mb-3">
            Consider adjusting your email preferences instead of unsubscribing completely. You might be interested in:
          </p>
          <ul class="text-sm text-blue-700 space-y-1">
            <li>• Product updates and new features</li>
            <li>• CRM best practices and tips</li>
            <li>• Weekly industry insights</li>
          </ul>
        </div>
      {/if}
    </div>
  </div>
</div>
