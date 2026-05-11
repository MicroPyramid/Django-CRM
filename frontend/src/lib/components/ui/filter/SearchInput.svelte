<script>
  import { Search, X } from '@lucide/svelte';

  /**
   * @type {{
   *   value?: string,
   *   placeholder?: string,
   *   class?: string,
   *   onchange?: (value: string) => void,
   *   [key: string]: any
   * }}
   */
  let {
    value = $bindable(''),
    placeholder = 'Search...',
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

<div class="relative inline-flex items-center {className || ''}" {...restProps}>
  <Search class="pointer-events-none absolute left-2.5 size-3.5 text-[color:var(--text-subtle)]" />
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
    class="h-7 w-full rounded-[var(--r-sm)] border border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] py-0 pl-8 pr-7 text-[13.5px] text-[color:var(--text)] placeholder:text-[color:var(--text-subtle)] outline-none transition-colors focus:border-[color:var(--violet)]/50 focus:ring-1 focus:ring-[color:var(--violet)]/30"
  />
  {#if inputValue}
    <button
      type="button"
      onclick={handleClear}
      class="absolute right-1.5 flex size-4 items-center justify-center rounded-sm text-[color:var(--text-subtle)] hover:bg-[color:var(--bg-hover)] hover:text-[color:var(--text-muted)]"
      aria-label="Clear search"
    >
      <X class="size-3" />
    </button>
  {/if}
</div>
