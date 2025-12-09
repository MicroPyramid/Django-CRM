<script>
  import { Search, X } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';

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
  }

  function handleClear() {
    inputValue = '';
    value = '';
    onchange?.('');
  }
</script>

<div class={cn('relative', className)} {...restProps}>
  <Search class="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
  <input
    bind:this={inputEl}
    type="text"
    value={inputValue}
    oninput={handleInput}
    onfocus={handleFocus}
    onblur={handleBlur}
    onkeydown={handleKeydown}
    {placeholder}
    class="border-input bg-background placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 flex h-9 w-full rounded-md border pr-9 pl-9 text-sm shadow-xs transition-colors outline-none focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50"
  />
  {#if inputValue}
    <button
      type="button"
      onclick={handleClear}
      class="text-muted-foreground hover:text-foreground absolute top-1/2 right-3 -translate-y-1/2"
    >
      <X class="h-4 w-4" />
    </button>
  {/if}
</div>
