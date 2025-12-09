<script>
  import '../../../../app.css';
  import imgLogo from '$lib/assets/images/logo.png';
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { Building2, ArrowLeft, Check, AlertCircle, Sparkles } from '@lucide/svelte';

  let { form } = $props();

  let isSubmitting = $state(false);

  // Handle form submission success - redirect after showing success message
  $effect(() => {
    if (form?.data) {
      const timer = setTimeout(() => {
        goto('/org');
      }, 1500);
      return () => clearTimeout(timer);
    }
  });
</script>

<svelte:head>
  <title>Create Organization | BottleCRM</title>
</svelte:head>

<div class="flex min-h-screen flex-col bg-slate-50">
  <!-- Header -->
  <header class="border-b border-slate-200 bg-white">
    <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
      <div class="flex items-center gap-3">
        <img src={imgLogo} alt="BottleCRM" class="h-8 w-auto" />
        <span class="text-lg font-semibold text-slate-900">BottleCRM</span>
      </div>
      <a
        href="/org"
        class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
      >
        <ArrowLeft class="h-4 w-4" />
        <span>Back</span>
      </a>
    </div>
  </header>

  <!-- Main Content -->
  <main class="flex flex-1 items-start justify-center px-6 py-12">
    <div class="w-full max-w-md">
      <!-- Page Header -->
      <div class="mb-8 text-center">
        <div
          class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-50"
        >
          <Sparkles class="h-6 w-6 text-blue-600" />
        </div>
        <h1 class="text-2xl font-bold text-slate-900">Create organization</h1>
        <p class="mt-2 text-slate-600">Set up a new workspace for your team</p>
      </div>

      <!-- Form Card -->
      <div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <form
          action="/org/new"
          method="POST"
          use:enhance={() => {
            isSubmitting = true;
            return async ({ update }) => {
              await update();
              isSubmitting = false;
            };
          }}
          class="space-y-5"
        >
          <!-- Organization Name Field -->
          <div class="space-y-2">
            <label for="org_name" class="block text-sm font-medium text-slate-700">
              Organization name
            </label>
            <input
              type="text"
              id="org_name"
              name="org_name"
              required
              disabled={isSubmitting || !!form?.data}
              class="w-full rounded-lg border border-slate-300 px-4 py-2.5 text-slate-900 placeholder-slate-400 transition-colors focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none disabled:bg-slate-50 disabled:text-slate-500"
              placeholder="e.g. Acme Inc."
            />
            <p class="text-xs text-slate-500">This will be your workspace name in BottleCRM</p>
          </div>

          <!-- Error Message -->
          {#if form?.error}
            <div class="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4">
              <AlertCircle class="h-5 w-5 shrink-0 text-red-500" />
              <div>
                <p class="text-sm font-medium text-red-800">Unable to create organization</p>
                <p class="mt-1 text-sm text-red-600">{form.error.name || 'Please try again'}</p>
              </div>
            </div>
          {/if}

          <!-- Success Message -->
          {#if form?.data}
            <div class="flex items-start gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
              <Check class="h-5 w-5 shrink-0 text-green-500" />
              <div>
                <p class="text-sm font-medium text-green-800">Organization created!</p>
                <p class="mt-1 text-sm text-green-600">Redirecting to your organizations...</p>
              </div>
            </div>
          {/if}

          <!-- Submit Button -->
          <button
            type="submit"
            disabled={isSubmitting || !!form?.data}
            class="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
          >
            {#if isSubmitting}
              <div
                class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
              ></div>
              <span>Creating...</span>
            {:else if form?.data}
              <Check class="h-4 w-4" />
              <span>Created!</span>
            {:else}
              <Building2 class="h-4 w-4" />
              <span>Create organization</span>
            {/if}
          </button>
        </form>
      </div>

      <!-- Help Text -->
      <p class="mt-6 text-center text-sm text-slate-500">
        You can invite team members after creating your organization
      </p>
    </div>
  </main>
</div>
