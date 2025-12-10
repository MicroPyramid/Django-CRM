<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import {
    Building2,
    Globe,
    Banknote,
    Sparkles,
    Check,
    MapPin,
    Hash,
    FileText,
    Loader2
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { CURRENCY_CODES } from '$lib/constants/filters.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const settings = $derived(data.settings || {});
  let isLoading = $state(false);

  // Currency options for select
  const currencyOptions = CURRENCY_CODES.filter((c) => c.value);

  // Country options with flag emojis
  const countryOptions = [
    { value: '', label: 'Select Country', flag: '' },
    { value: 'US', label: 'United States', flag: '🇺🇸' },
    { value: 'GB', label: 'United Kingdom', flag: '🇬🇧' },
    { value: 'CA', label: 'Canada', flag: '🇨🇦' },
    { value: 'AU', label: 'Australia', flag: '🇦🇺' },
    { value: 'DE', label: 'Germany', flag: '🇩🇪' },
    { value: 'FR', label: 'France', flag: '🇫🇷' },
    { value: 'IN', label: 'India', flag: '🇮🇳' },
    { value: 'JP', label: 'Japan', flag: '🇯🇵' },
    { value: 'SG', label: 'Singapore', flag: '🇸🇬' },
    { value: 'AE', label: 'United Arab Emirates', flag: '🇦🇪' },
    { value: 'BR', label: 'Brazil', flag: '🇧🇷' },
    { value: 'MX', label: 'Mexico', flag: '🇲🇽' },
    { value: 'CH', label: 'Switzerland', flag: '🇨🇭' },
    { value: 'NL', label: 'Netherlands', flag: '🇳🇱' },
    { value: 'ES', label: 'Spain', flag: '🇪🇸' },
    { value: 'IT', label: 'Italy', flag: '🇮🇹' }
  ];

  // Form state
  let formName = $state('');
  let formDomain = $state('');
  let formDescription = $state('');
  let formCurrency = $state('USD');
  let formCountry = $state('');

  // Update form state when settings change
  $effect(() => {
    formName = settings.name || '';
    formDomain = settings.domain || '';
    formDescription = settings.description || '';
    formCurrency = settings.default_currency || 'USD';
    formCountry = settings.default_country || '';
  });

  // Handle form result
  $effect(() => {
    if (form?.success) {
      toast.success('Organization settings updated');
      invalidateAll();
    } else if (form?.error) {
      toast.error(form.error);
    }
  });

  // Get current country flag
  const currentCountryFlag = $derived(
    countryOptions.find(c => c.value === formCountry)?.flag || ''
  );

  // Get currency symbol
  const currencySymbol = $derived(() => {
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: formCurrency
      }).format(0).replace(/[\d.,\s]/g, '');
    } catch {
      return '$';
    }
  });

  // Generate initials from org name
  const orgInitials = $derived(
    formName
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2) || 'OR'
  );
</script>

<svelte:head>
  <title>Organization Settings - BottleCRM</title>
</svelte:head>

<style>
  /* Custom animations */
  @keyframes float {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(2deg); }
  }

  @keyframes pulse-ring {
    0% { transform: scale(0.95); opacity: 0.5; }
    50% { transform: scale(1.05); opacity: 0.3; }
    100% { transform: scale(0.95); opacity: 0.5; }
  }

  @keyframes shimmer-slide {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  .org-avatar {
    animation: float 6s ease-in-out infinite;
  }

  .pulse-ring {
    animation: pulse-ring 3s ease-in-out infinite;
  }

  .shimmer::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    animation: shimmer-slide 3s ease-in-out infinite;
  }

  /* Custom select styling */
  .custom-select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 12px center;
    padding-right: 40px;
  }

  /* Gradient border effect */
  .gradient-border {
    position: relative;
    background: var(--card);
    border-radius: var(--radius-xl);
  }

  .gradient-border::before {
    content: '';
    position: absolute;
    inset: 0;
    padding: 1px;
    border-radius: inherit;
    background: linear-gradient(135deg, var(--accent-primary), transparent 50%, var(--accent-secondary));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0.5;
    transition: opacity 0.3s ease;
  }

  .gradient-border:hover::before {
    opacity: 1;
  }

  /* Input focus glow */
  .input-glow:focus-within {
    box-shadow: 0 0 0 2px var(--accent-primary-subtle), 0 0 20px -5px var(--accent-primary);
  }

  /* Section reveal animation */
  .section-reveal {
    opacity: 0;
    transform: translateY(20px);
    animation: reveal 0.6s ease forwards;
  }

  @keyframes reveal {
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .delay-1 { animation-delay: 0.1s; }
  .delay-2 { animation-delay: 0.2s; }
</style>

<PageHeader title="Organization Settings" subtitle="Manage your organization preferences">
  {#snippet actions()}
    <Button type="submit" form="org-settings-form" disabled={isLoading} class="gap-2">
      {#if isLoading}
        <Loader2 class="h-4 w-4 animate-spin" />
        Saving...
      {:else}
        <Check class="h-4 w-4" />
        Save Changes
      {/if}
    </Button>
  {/snippet}
</PageHeader>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <form
    id="org-settings-form"
    method="POST"
    action="?/update"
    use:enhance={() => {
      isLoading = true;
      return async ({ update }) => {
        await update();
        isLoading = false;
      };
    }}
    class="mx-auto max-w-4xl space-y-8"
  >
    <!-- Hero Section: Organization Identity -->
    <section class="section-reveal">
      <div class="gradient-border overflow-hidden">
        <div class="relative p-8 md:p-10">
          <!-- Background decoration -->
          <div class="pointer-events-none absolute inset-0 overflow-hidden">
            <div class="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-gradient-to-br from-[var(--accent-primary)] to-transparent opacity-10 blur-3xl"></div>
            <div class="absolute -bottom-32 -left-32 h-80 w-80 rounded-full bg-gradient-to-tr from-[var(--accent-secondary)] to-transparent opacity-10 blur-3xl"></div>
          </div>

          <div class="relative flex flex-col gap-8 md:flex-row md:items-start">
            <!-- Organization Avatar -->
            <div class="flex flex-col items-center gap-4">
              <div class="relative">
                <!-- Animated ring -->
                <div class="pulse-ring absolute -inset-2 rounded-3xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] opacity-30"></div>

                <!-- Avatar container -->
                <div class="org-avatar relative flex h-28 w-28 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] shadow-2xl">
                  <span class="text-3xl font-bold text-white">{orgInitials}</span>
                </div>
              </div>
            </div>

            <!-- Organization Details -->
            <div class="flex-1 space-y-6">
              <div class="space-y-1">
                <div class="text-muted-foreground mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider">
                  <Building2 class="h-3.5 w-3.5" />
                  Organization Identity
                </div>
              </div>

              <div class="grid gap-5 md:grid-cols-2">
                <!-- Organization Name -->
                <div class="space-y-2">
                  <Label for="name" class="text-muted-foreground flex items-center gap-2 text-sm">
                    <Hash class="h-3.5 w-3.5" />
                    Organization Name
                  </Label>
                  <div class="input-glow rounded-lg transition-shadow duration-300">
                    <Input
                      id="name"
                      name="name"
                      type="text"
                      bind:value={formName}
                      placeholder="Acme Corporation"
                      class="h-11 border-[var(--border-default)] bg-[var(--bg-subtle)] text-base transition-colors focus:border-[var(--accent-primary)] focus:bg-transparent"
                    />
                  </div>
                </div>

                <!-- Domain -->
                <div class="space-y-2">
                  <Label for="domain" class="text-muted-foreground flex items-center gap-2 text-sm">
                    <Globe class="h-3.5 w-3.5" />
                    Company Domain
                  </Label>
                  <div class="input-glow rounded-lg transition-shadow duration-300">
                    <div class="relative flex items-center">
                      <div class="pointer-events-none absolute left-3 flex items-center">
                        <Globe class="text-muted-foreground h-4 w-4" />
                      </div>
                      <Input
                        id="domain"
                        name="domain"
                        type="text"
                        bind:value={formDomain}
                        placeholder="yourcompany.com"
                        class="h-11 border-[var(--border-default)] bg-[var(--bg-subtle)] pl-10 text-base transition-colors focus:border-[var(--accent-primary)] focus:bg-transparent"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <!-- Description -->
              <div class="space-y-2">
                <Label for="description" class="text-muted-foreground flex items-center gap-2 text-sm">
                  <FileText class="h-3.5 w-3.5" />
                  About Your Organization
                </Label>
                <div class="input-glow rounded-lg transition-shadow duration-300">
                  <textarea
                    id="description"
                    name="description"
                    rows="3"
                    bind:value={formDescription}
                    placeholder="Brief description of your organization, industry, and what you do..."
                    class="border-input bg-[var(--bg-subtle)] ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[100px] w-full resize-none rounded-lg border px-4 py-3 text-base transition-colors focus:border-[var(--accent-primary)] focus:bg-transparent focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Locale & Currency Section -->
    <section class="section-reveal delay-1">
      <div class="gradient-border overflow-hidden">
        <div class="relative p-8 md:p-10">
          <!-- Background decoration -->
          <div class="pointer-events-none absolute inset-0 overflow-hidden">
            <div class="absolute -left-20 top-10 h-48 w-48 rounded-full bg-gradient-to-br from-[var(--status-success)] to-transparent opacity-10 blur-3xl"></div>
          </div>

          <div class="relative space-y-8">
            <!-- Section Header -->
            <div class="flex items-center justify-between">
              <div class="space-y-1">
                <div class="text-muted-foreground mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-wider">
                  <Globe class="h-3.5 w-3.5" />
                  Regional Settings
                </div>
                <h3 class="text-lg font-semibold">Currency & Locale</h3>
                <p class="text-muted-foreground text-sm">Configure default currency and regional preferences</p>
              </div>
            </div>

            <div class="grid gap-6 lg:grid-cols-2">
              <!-- Currency Selection -->
              <div class="space-y-3">
                <Label for="default_currency" class="text-muted-foreground flex items-center gap-2 text-sm">
                  <Banknote class="h-3.5 w-3.5" />
                  Default Currency
                </Label>
                <div class="input-glow rounded-lg transition-shadow duration-300">
                  <div class="relative">
                    <select
                      id="default_currency"
                      name="default_currency"
                      bind:value={formCurrency}
                      class="custom-select border-input bg-[var(--bg-subtle)] h-12 w-full cursor-pointer rounded-lg border px-4 text-base transition-colors focus:border-[var(--accent-primary)] focus:bg-transparent focus:ring-2 focus:ring-[var(--accent-primary-subtle)] focus:outline-none"
                    >
                      {#each currencyOptions as currency}
                        <option value={currency.value}>{currency.label}</option>
                      {/each}
                    </select>
                  </div>
                </div>
                <p class="text-muted-foreground text-xs">
                  Applied to opportunities, invoices, and financial reports
                </p>
              </div>

              <!-- Country Selection -->
              <div class="space-y-3">
                <Label for="default_country" class="text-muted-foreground flex items-center gap-2 text-sm">
                  <MapPin class="h-3.5 w-3.5" />
                  Default Country
                </Label>
                <div class="input-glow rounded-lg transition-shadow duration-300">
                  <div class="relative">
                    <select
                      id="default_country"
                      name="default_country"
                      bind:value={formCountry}
                      class="custom-select border-input bg-[var(--bg-subtle)] h-12 w-full cursor-pointer rounded-lg border px-4 text-base transition-colors focus:border-[var(--accent-primary)] focus:bg-transparent focus:ring-2 focus:ring-[var(--accent-primary-subtle)] focus:outline-none"
                    >
                      {#each countryOptions as country}
                        <option value={country.value}>{country.flag} {country.label}</option>
                      {/each}
                    </select>
                  </div>
                </div>
                <p class="text-muted-foreground text-xs">
                  Used for addresses, date formats, and locale settings
                </p>
              </div>
            </div>

            <!-- Currency Preview -->
            {#if formCurrency}
              <div class="relative overflow-hidden rounded-xl bg-gradient-to-br from-[var(--bg-subtle)] to-[var(--bg-muted)] p-6">
                <div class="shimmer absolute inset-0"></div>
                <div class="relative">
                  <div class="mb-3 flex items-center gap-2">
                    <Sparkles class="h-4 w-4 text-[var(--accent-secondary)]" />
                    <span class="text-muted-foreground text-sm font-medium">Currency Preview</span>
                  </div>
                  <div class="flex items-baseline gap-3">
                    <span class="text-gradient text-4xl font-bold tracking-tight md:text-5xl">
                      {new Intl.NumberFormat('en-US', {
                        style: 'currency',
                        currency: formCurrency,
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                      }).format(125000)}
                    </span>
                    <span class="text-muted-foreground text-lg">
                      {currentCountryFlag}
                    </span>
                  </div>
                  <div class="text-muted-foreground mt-2 text-sm">
                    Sample: {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: formCurrency
                    }).format(12345.67)}
                  </div>
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </section>

    <!-- Quick Stats Footer -->
    <section class="section-reveal delay-2">
      <div class="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-subtle)] p-4">
        <div class="flex items-center gap-6">
          <div class="flex items-center gap-2">
            <div class="h-2 w-2 rounded-full bg-[var(--status-success)]"></div>
            <span class="text-muted-foreground text-sm">Settings synced</span>
          </div>
          <div class="text-muted-foreground text-sm">
            Last updated: {new Date().toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            })}
          </div>
        </div>
        <Button
          type="submit"
          disabled={isLoading}
          size="lg"
          class="gap-2 bg-gradient-to-r from-[var(--accent-primary)] to-[var(--stage-qualified)] text-white shadow-lg shadow-[var(--accent-primary)]/25 transition-all hover:shadow-xl hover:shadow-[var(--accent-primary)]/30"
        >
          {#if isLoading}
            <Loader2 class="h-4 w-4 animate-spin" />
            Saving...
          {:else}
            <Check class="h-4 w-4" />
            Save All Changes
          {/if}
        </Button>
      </div>
    </section>
  </form>
</div>
