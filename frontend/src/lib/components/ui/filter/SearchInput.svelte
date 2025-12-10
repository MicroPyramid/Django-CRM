<script>
  import { Search, X, Command } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   value?: string,
   *   placeholder?: string,
   *   label?: string,
   *   showLabel?: boolean,
   *   showShortcut?: boolean,
   *   class?: string,
   *   onchange?: (value: string) => void,
   *   [key: string]: any
   * }}
   */
  let {
    value = $bindable(''),
    placeholder = 'Search...',
    label = 'Search',
    showLabel = true,
    showShortcut = false,
    class: className,
    onchange,
    ...restProps
  } = $props();

  /** @type {HTMLInputElement | undefined} */
  let inputEl = $state();
  let inputValue = $state(value);
  let isFocused = $state(false);

  // Sync external value changes to internal state only when not focused
  $effect(() => {
    if (!isFocused && value !== inputValue) {
      inputValue = value;
    }
  });

  /**
   * @param {Event} e
   */
  function handleInput(e) {
    const target = /** @type {HTMLInputElement} */ (e.target);
    inputValue = target.value;
  }

  function handleFocus() {
    isFocused = true;
  }

  function handleBlur() {
    isFocused = false;
    if (inputValue !== value) {
      value = inputValue;
      onchange?.(inputValue);
    }
  }

  /**
   * @param {KeyboardEvent} e
   */
  function handleKeydown(e) {
    if (e.key === 'Enter') {
      inputEl?.blur();
    }
    if (e.key === 'Escape') {
      handleClear();
      inputEl?.blur();
    }
  }

  function handleClear() {
    inputValue = '';
    value = '';
    onchange?.('');
  }
</script>

<div class={cn('flex flex-col gap-1.5', className)} {...restProps}>
  {#if showLabel && label}
    <label
      for="search-input"
      class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70"
    >
      {label}
    </label>
  {/if}

  <div class="search-input-wrapper group relative">
    <!-- Search icon with pulse on focus -->
    <div
      class={cn(
        'absolute left-3 top-1/2 -translate-y-1/2',
        'transition-all duration-300 ease-out',
        isFocused ? 'text-primary scale-110' : 'text-muted-foreground'
      )}
    >
      <Search class="h-4 w-4" />
    </div>

    <!-- Input field -->
    <input
      id="search-input"
      bind:this={inputEl}
      type="text"
      value={inputValue}
      oninput={handleInput}
      onfocus={handleFocus}
      onblur={handleBlur}
      onkeydown={handleKeydown}
      {placeholder}
      class={cn(
        'search-input',
        'flex h-9 w-full rounded-lg',
        'bg-background/60 backdrop-blur-sm',
        'border border-input/60',
        'pl-9 pr-9 text-sm',
        'placeholder:text-muted-foreground/50',
        'transition-all duration-200 ease-out',
        'outline-none',
        'hover:border-input hover:bg-background/80',
        'focus:border-primary/50 focus:bg-background',
        'focus:ring-2 focus:ring-primary/20',
        'dark:bg-white/[0.03] dark:border-white/[0.08]',
        'dark:hover:bg-white/[0.05] dark:hover:border-white/[0.12]',
        'dark:focus:bg-white/[0.06] dark:focus:border-primary/40',
        'dark:focus:ring-primary/30',
        inputValue && 'pr-16'
      )}
    />

    <!-- Right side: shortcut hint or clear button -->
    <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
      {#if inputValue}
        <!-- Clear button -->
        <button
          type="button"
          onclick={handleClear}
          class={cn(
            'flex h-6 w-6 items-center justify-center rounded-md',
            'text-muted-foreground/70',
            'transition-all duration-150',
            'hover:bg-muted hover:text-foreground',
            'active:scale-95'
          )}
        >
          <X class="h-3.5 w-3.5" />
        </button>
      {:else if showShortcut}
        <!-- Keyboard shortcut hint -->
        <div
          class={cn(
            'hidden items-center gap-0.5 sm:flex',
            'rounded-md border border-border/60 bg-muted/50 px-1.5 py-0.5',
            'text-[10px] font-medium text-muted-foreground/60',
            'dark:border-white/[0.06] dark:bg-white/[0.03]'
          )}
        >
          <Command class="h-2.5 w-2.5" />
          <span>K</span>
        </div>
      {/if}
    </div>

    <!-- Focus glow effect (dark mode) -->
    <div
      class={cn(
        'pointer-events-none absolute inset-0 -z-10 rounded-lg',
        'opacity-0 transition-opacity duration-300',
        'dark:bg-[radial-gradient(ellipse_at_center,var(--primary)_0%,transparent_70%)]',
        'dark:blur-xl',
        isFocused && 'dark:opacity-[0.15]'
      )}
    ></div>
  </div>
</div>

<style>
  .search-input-wrapper {
    --glow-color: var(--primary);
  }

  .search-input::placeholder {
    transition: color 0.2s ease;
  }

  .search-input:focus::placeholder {
    color: transparent;
  }

  /* Subtle inner shadow for depth */
  .search-input {
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  }

  :global(.dark) .search-input {
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .search-input:focus {
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.02),
      0 0 0 3px var(--ring);
  }

  :global(.dark) .search-input:focus {
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.1),
      0 0 0 3px var(--ring),
      0 0 20px -4px var(--glow-color);
  }
</style>
