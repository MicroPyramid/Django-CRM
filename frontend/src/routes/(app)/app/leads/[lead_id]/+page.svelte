<script>
  import { fly } from 'svelte/transition';
  import { enhance } from '$app/forms';
  import { invalidateAll, goto } from '$app/navigation';
  import { 
    UserCircle, 
    Edit3, 
    CheckCircle, 
    Mail, 
    Phone, 
    Building, 
    MapPin, 
    Star, 
    MessageSquare, 
    ChevronRight, 
    Calendar, 
    TrendingUp,
    DollarSign,
    Briefcase,
    Globe,
    User,
    Clock,
    Target,
    Users,
    Plus,
    X,
    Loader2,
    ExternalLink,
    MapPin as Location,
    Award,
    Activity,
    Send,
    Copy,
    MoreVertical
  } from '@lucide/svelte';

  export let data;
  export let form;
  const { lead } = data;

  let newComment = '';
  let isSubmittingComment = false;
  let isConverting = false;

  // Toast state variables
  let showToast = false;
  let toastMessage = '';
  let toastType = 'success';

  // Confirmation modal state
  let showConfirmModal = false;

  // Function to get the full name of a lead
  /**
   * @param {any} lead
   */
  function getFullName(lead) {
    return `${lead.firstName} ${lead.lastName}`.trim();
  }

  // Function to format date
  /**
   * @param {string | Date | null | undefined} dateString
   */
  function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // Function to format date (short)
  /**
   * @param {string | Date | null | undefined} dateString
   */
  function formatDateShort(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }

  // Function to map lead status to colors
  /**
   * @param {string} status
   */
  function getStatusColor(status) {
    switch (status) {
      case 'NEW':
        return 'bg-blue-50 text-blue-700 border-blue-200 ring-blue-600/20';
      case 'PENDING':
        return 'bg-amber-50 text-amber-700 border-amber-200 ring-amber-600/20';
      case 'CONTACTED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 ring-emerald-600/20';
      case 'QUALIFIED':
        return 'bg-purple-50 text-purple-700 border-purple-200 ring-purple-600/20';
      case 'UNQUALIFIED':
        return 'bg-red-50 text-red-700 border-red-200 ring-red-600/20';
      case 'CONVERTED':
        return 'bg-gray-50 text-gray-700 border-gray-200 ring-gray-600/20';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200 ring-gray-600/20';
    }
  }

  // Function to get lead source display name
  /**
   * @param {string | null | undefined} source
   */
  function getLeadSourceDisplay(source) {
    if (!source) return 'Unknown';
    return source.replace('_', ' ').toLowerCase().replace(/\b\w/g, (/** @type {string} */ l) => l.toUpperCase());
  }

  // Function to get initials for avatar
  /**
   * @param {any} lead
   */
  function getInitials(lead) {
    const first = lead.firstName?.[0] || '';
    const last = lead.lastName?.[0] || '';
    return (first + last).toUpperCase();
  }

  // Function to copy email to clipboard
  async function copyEmail() {
    if (lead.email) {
      await navigator.clipboard.writeText(lead.email);
      toastMessage = 'Email copied to clipboard';
      toastType = 'success';
      showToast = true;
    }
  }

  // Function to copy phone to clipboard
  async function copyPhone() {
    if (lead.phone) {
      await navigator.clipboard.writeText(lead.phone);
      toastMessage = 'Phone number copied to clipboard';
      toastType = 'success';
      showToast = true;
    }
  }

  // Function to show confirmation modal
  function showConvertConfirmation() {
    showConfirmModal = true;
  }

  // Function to hide confirmation modal
  function hideConvertConfirmation() {
    showConfirmModal = false;
  }

  // Function to handle confirmed conversion
  function confirmConversion() {
    showConfirmModal = false;
    // Submit the form programmatically
    const form = document.getElementById('convertForm');
    if (form) {
      // Use dispatchEvent as a cross-browser solution
      const event = new Event('submit', { cancelable: true, bubbles: true });
      form.dispatchEvent(event);
    }
  }
  
  const enhanceConvertForm = () => {
    isConverting = true;
    return async (/** @type {{ update: any }} */ { update }) => {
      await update({ reset: false });
      // Note: If conversion is successful, the server will redirect automatically
      // This will only execute if there's an error
      isConverting = false;
    };
  };

  const enhanceCommentForm = () => {
    isSubmittingComment = true;
    return async (/** @type {{ update: any }} */ { update }) => {
      await update({ reset: false });
      // Reset the loading state after update
      isSubmittingComment = false;
    };
  };

  function closeToast() {
    showToast = false;
  }

  $: if (form?.status === 'success') {
    toastMessage = form.message || 'Action completed successfully!';
    toastType = 'success';
    showToast = true;
    invalidateAll();
    isConverting = false;
    isSubmittingComment = false;
    if (form.commentAdded) {
      newComment = '';
    }
    // Handle redirect for lead conversion
    if (form.redirectTo) {
      setTimeout(() => {
        goto(form.redirectTo);
      }, 1500); // Wait 1.5 seconds to show the success message before redirecting
    }
  } else if (form?.status === 'error') {
    toastMessage = form.message || 'An error occurred.';
    toastType = 'error';
    showToast = true;
    isConverting = false;
    isSubmittingComment = false;
  } else {
    // Reset loading states if no form response
    isConverting = false;
    isSubmittingComment = false;
  }
</script>

<!-- Confirmation Modal -->
{#if showConfirmModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" transition:fly={{ duration: 200 }}>
    <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-xl max-w-md w-full p-6" transition:fly={{ y: 20, duration: 300 }}>
      <div class="flex items-center gap-4 mb-4">
        <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-xl flex items-center justify-center">
          <CheckCircle class="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">Convert Lead</h3>
          <p class="text-sm text-gray-600 dark:text-gray-400">This action cannot be undone</p>
        </div>
      </div>
      
      <p class="text-sm text-gray-700 dark:text-gray-300 mb-6">
        Are you sure you want to convert <strong>{getFullName(lead)}</strong> into an account and contact? 
        This will create new records and mark the lead as converted.
      </p>
      
      <div class="flex gap-3 justify-end">
        <button 
          onclick={hideConvertConfirmation}
          class="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        >
          Cancel
        </button>
        <button 
          onclick={confirmConversion}
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors"
        >
          <CheckCircle class="w-4 h-4" />
          Yes, Convert Lead
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Toast -->
{#if showToast}
  <div class="fixed top-4 right-4 z-50 max-w-md" transition:fly={{ y: -20, duration: 300 }}>
    <div class="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg p-4 flex items-center gap-3">
      <div class="flex-shrink-0">
        {#if toastType === 'success'}
          <div class="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
            <CheckCircle class="w-4 h-4 text-green-600 dark:text-green-400" />
          </div>
        {:else}
          <div class="w-6 h-6 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
            <X class="w-4 h-4 text-red-600 dark:text-red-400" />
          </div>
        {/if}
      </div>
      <p class="text-sm text-gray-900 dark:text-gray-100 font-medium flex-1">{toastMessage}</p>
      <button 
        onclick={closeToast}
        class="flex-shrink-0 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
      >
        <X class="w-4 h-4 text-gray-400 dark:text-gray-500" />
      </button>
    </div>
  </div>
{/if}

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <main class="container mx-auto px-4 py-8 max-w-7xl">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-8">
      <ol class="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
        <li><a href="/app/leads" class="hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium">Leads</a></li>
        <li><ChevronRight class="h-4 w-4 text-gray-400 dark:text-gray-500" /></li>
        <li class="font-medium text-gray-900 dark:text-gray-100 truncate max-w-xs">{getFullName(lead)}</li>
      </ol>
    </nav>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-8">
        <!-- Header Card -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div class="p-8">
            <div class="flex flex-col sm:flex-row items-start gap-6">
              <div class="flex-shrink-0">
                <div class="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 rounded-2xl flex items-center justify-center shadow-lg">
                  <span class="text-white font-bold text-xl">{getInitials(lead)}</span>
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-3">{getFullName(lead)}</h1>
                <div class="flex flex-wrap items-center gap-3 mb-4">
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border {getStatusColor(lead.status)} ring-1 ring-inset">
                    {lead.status}
                  </span>
                  {#if lead.company}
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 px-3 py-1 rounded-full">
                      <Building class="w-4 h-4" />
                      <span class="font-medium">{lead.company}</span>
                    </div>
                  {/if}
                  {#if lead.title}
                    <div class="flex items-center gap-2 text-gray-600 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 px-3 py-1 rounded-full">
                      <Briefcase class="w-4 h-4" />
                      <span>{lead.title}</span>
                    </div>
                  {/if}
                </div>
                
                <!-- Contact Information Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                  {#if lead.email}
                    <div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-xl group hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                      <div class="w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-xl flex items-center justify-center">
                        <Mail class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Email</p>
                        <a href="mailto:{lead.email}" class="text-sm text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors font-medium truncate block">
                          {lead.email}
                        </a>
                      </div>
                      <button onclick={copyEmail} class="opacity-0 group-hover:opacity-100 p-1 hover:bg-white dark:hover:bg-gray-500 rounded-lg transition-all">
                        <Copy class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                      </button>
                    </div>
                  {/if}
                  
                  {#if lead.phone}
                    <div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-xl group hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                      <div class="w-10 h-10 bg-green-100 dark:bg-green-900 rounded-xl flex items-center justify-center">
                        <Phone class="w-5 h-5 text-green-600 dark:text-green-400" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Phone</p>
                        <a href="tel:{lead.phone}" class="text-sm text-gray-900 dark:text-gray-100 hover:text-green-600 dark:hover:text-green-400 transition-colors font-medium">
                          {lead.phone}
                        </a>
                      </div>
                      <button onclick={copyPhone} class="opacity-0 group-hover:opacity-100 p-1 hover:bg-white dark:hover:bg-gray-500 rounded-lg transition-all">
                        <Copy class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                      </button>
                    </div>
                  {/if}
                </div>

                <!-- Quick Actions -->
                <div class="flex flex-wrap gap-3">
                  {#if lead.email}
                    <a 
                      href="mailto:{lead.email}"
                      class="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-sm font-medium rounded-xl hover:bg-blue-100 dark:hover:bg-blue-800 transition-colors"
                    >
                      <Send class="w-4 h-4" />
                      Send Email
                    </a>
                  {/if}
                  {#if lead.phone}
                    <a 
                      href="tel:{lead.phone}"
                      class="inline-flex items-center gap-2 px-4 py-2 bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 text-sm font-medium rounded-xl hover:bg-green-100 dark:hover:bg-green-800 transition-colors"
                    >
                      <Phone class="w-4 h-4" />
                      Call
                    </a>
                  {/if}
                </div>
              </div>
              
              <!-- Action Buttons -->
              <div class="flex flex-col gap-3">
                {#if lead.status !== 'CONVERTED'}
                  <form id="convertForm" method="POST" action="?/convert" use:enhance={enhanceConvertForm}>
                    <!-- Hidden form - will be submitted via JavaScript -->
                  </form>
                  <button 
                    type="button"
                    onclick={showConvertConfirmation} 
                    disabled={isConverting}
                    class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-700 dark:to-blue-800 text-white text-sm font-semibold rounded-xl hover:from-blue-700 hover:to-blue-800 dark:hover:from-blue-800 dark:hover:to-blue-900 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                  >
                    {#if isConverting}
                      <Loader2 class="w-4 h-4 animate-spin" />
                      Converting...
                    {:else}
                      <CheckCircle class="w-4 h-4" />
                      Convert Lead
                    {/if}
                  </button>
                {/if}
                <a 
                  href="/app/leads/{lead.id}/edit"
                  class="inline-flex items-center gap-2 px-6 py-3 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm font-semibold rounded-xl hover:bg-gray-50 dark:hover:bg-gray-600 hover:border-gray-400 dark:hover:border-gray-500 transition-all shadow-sm"
                >
                  <Edit3 class="w-4 h-4" />
                  Edit Lead
                </a>
              </div>
            </div>
          </div>
        </div>

        <!-- Lead Details Card -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div class="p-8">
            <h2 class="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6 flex items-center gap-3">
              <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <Activity class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              Lead Information
            </h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <!-- Lead Source -->
              {#if lead.leadSource}
                <div class="space-y-2">
                  <div class="flex items-center gap-2">
                    <Target class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Lead Source</span>
                  </div>
                  <p class="text-sm text-gray-900 dark:text-gray-100 font-medium bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded-lg">
                    {getLeadSourceDisplay(lead.leadSource)}
                  </p>
                </div>
              {/if}

              <!-- Industry -->
              {#if lead.industry}
                <div class="space-y-2">
                  <div class="flex items-center gap-2">
                    <Briefcase class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Industry</span>
                  </div>
                  <p class="text-sm text-gray-900 dark:text-gray-100 font-medium bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded-lg capitalize">
                    {lead.industry}
                  </p>
                </div>
              {/if}

              <!-- Rating -->
              {#if lead.rating}
                <div class="space-y-2">
                  <div class="flex items-center gap-2">
                    <Award class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                    <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Rating</span>
                  </div>
                  <div class="flex items-center gap-2 bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded-lg">
                    {#each Array(parseInt(lead.rating) || 0) as _, i}
                      <Star class="w-4 h-4 text-yellow-400 fill-current" />
                    {/each}
                    {#each Array(5 - (parseInt(lead.rating) || 0)) as _, i}
                      <Star class="w-4 h-4 text-gray-300 dark:text-gray-600 fill-current" />
                    {/each}
                    <span class="text-sm font-medium text-gray-700 dark:text-gray-300 ml-1">{lead.rating}/5</span>
                  </div>
                </div>
              {/if}

              <!-- Lead Owner -->
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <User class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Lead Owner</span>
                </div>
                <p class="text-sm text-gray-900 dark:text-gray-100 font-medium bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded-lg">
                  {lead.owner?.name || 'Unassigned'}
                </p>
              </div>

              <!-- Created Date -->
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <Calendar class="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <span class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Created</span>
                </div>
                <p class="text-sm text-gray-900 dark:text-gray-100 font-medium bg-gray-50 dark:bg-gray-700 px-3 py-2 rounded-lg">
                  {formatDateShort(lead.createdAt)}
                </p>
              </div>
            </div>

            <!-- Description -->
            {#if lead.description}
              <div class="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <div class="flex items-center gap-2 mb-3">
                  <MessageSquare class="w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <span class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Description</span>
                </div>
                <div class="bg-gray-50 dark:bg-gray-700 p-4 rounded-xl">
                  <div class="prose prose-sm max-w-none text-gray-700 dark:text-gray-300">
                    {@html lead.description}
                  </div>
                </div>
              </div>
            {/if}

            <!-- Conversion Information -->
            {#if lead.isConverted}
              <div class="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <div class="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-xl p-4">
                  <div class="flex items-center gap-3 mb-2">
                    <div class="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                      <CheckCircle class="w-5 h-5 text-green-600 dark:text-green-400" />
                    </div>
                    <h3 class="text-sm font-semibold text-green-800 dark:text-green-300">Lead Converted</h3>
                  </div>
                  {#if lead.convertedAt}
                    <p class="text-sm text-green-700 dark:text-green-400">
                      Converted on {formatDate(lead.convertedAt)}
                    </p>
                  {/if}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-8">
        <!-- Activity Feed -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
              <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                <MessageSquare class="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              Activity & Notes
            </h2>
          </div>
          
          <div class="p-6">
            <!-- Add Note Form -->
            <form method="POST" action="?/addComment" use:enhance={enhanceCommentForm} class="mb-6">
              <div class="space-y-4">
                <textarea 
                  name="comment" 
                  bind:value={newComment} 
                  placeholder="Add a note or log activity..." 
                  rows="4"
                  class="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none"
                ></textarea>
                <div class="flex justify-end">
                  <button 
                    type="submit" 
                    disabled={!newComment.trim() || isSubmittingComment}
                    class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 dark:hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                  >
                    {#if isSubmittingComment}
                      <Loader2 class="w-4 h-4 animate-spin" />
                      Adding...
                    {:else}
                      <Plus class="w-4 h-4" />
                      Add Note
                    {/if}
                  </button>
                </div>
              </div>
            </form>
            
            <!-- Activity List -->
            <div class="space-y-4">
              {#if lead.comments && lead.comments.length > 0}
                {#each lead.comments as comment, i (comment.id || i)}
                  <div class="flex gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-xl" in:fly={{ y: 10, delay: i * 60, duration: 200 }}>
                    <div class="flex-shrink-0">
                      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-gray-200 to-gray-300 dark:from-gray-600 dark:to-gray-700 flex items-center justify-center">
                        <User class="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      </div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-3 mb-2">
                        <p class="text-sm font-semibold text-gray-900 dark:text-gray-100">{comment.author?.name || 'Unknown User'}</p>
                        <p class="text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-600 px-2 py-1 rounded-md">{formatDate(comment.createdAt)}</p>
                      </div>
                      <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">{comment.body}</p>
                    </div>
                  </div>
                {/each}
              {:else}
                <div class="text-center py-12">
                  <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-2xl flex items-center justify-center">
                    <MessageSquare class="w-8 h-8 text-gray-400 dark:text-gray-500" />
                  </div>
                  <p class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">No activity yet</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400">Be the first to add a note or log an interaction.</p>
                </div>
              {/if}
            </div>
          </div>
        </div>

        <!-- Related Contact (if converted) -->
        {#if lead.convertedContactId && lead.contact}
          <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 class="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
                <div class="w-8 h-8 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
                  <Users class="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                Related Contact
              </h2>
            </div>
            
            <div class="p-6">
              <div class="space-y-4">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 dark:from-green-600 dark:to-green-700 rounded-xl flex items-center justify-center">
                    <User class="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p class="font-semibold text-gray-900 dark:text-gray-100">{lead.contact.firstName} {lead.contact.lastName}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">Contact</p>
                  </div>
                </div>
                
                {#if lead.contact.email}
                  <div class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
                    <Mail class="w-4 h-4" />
                    <span>{lead.contact.email}</span>
                  </div>
                {/if}
                
                {#if lead.contact.phone}
                  <div class="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-300">
                    <Phone class="w-4 h-4" />
                    <span>{lead.contact.phone}</span>
                  </div>
                {/if}
                
                <a 
                  href="/app/contacts/{lead.contact.id}"
                  class="inline-flex items-center justify-center w-full px-4 py-3 bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 text-sm font-semibold rounded-xl hover:bg-green-100 dark:hover:bg-green-800 transition-colors"
                >
                  <ExternalLink class="w-4 h-4 mr-2" />
                  View Contact
                </a>
              </div>
            </div>
          </div>
        {/if}

        <!-- Quick Stats -->
        <div class="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 class="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
              <div class="w-8 h-8 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
                <TrendingUp class="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              Quick Stats
            </h2>
          </div>
          
          <div class="p-6 space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600 dark:text-gray-300">Comments</span>
              <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">{lead.comments?.length || 0}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-600 dark:text-gray-300">Days Since Created</span>
              <span class="text-sm font-semibold text-gray-900 dark:text-gray-100">
                {Math.floor((new Date().getTime() - new Date(lead.createdAt).getTime()) / (1000 * 60 * 60 * 24))}
              </span>
            </div>
            {#if lead.convertedAt}
              <div class="flex justify-between items-center">
                <span class="text-sm text-gray-600 dark:text-gray-300">Days to Convert</span>
                <span class="text-sm font-semibold text-green-600 dark:text-green-400">
                  {Math.floor((new Date(lead.convertedAt).getTime() - new Date(lead.createdAt).getTime()) / (1000 * 60 * 60 * 24))}
                </span>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </main>
</div>
