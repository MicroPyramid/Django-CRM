<script>
  import { resolve } from '$app/paths';
  import { asInternalPath } from '$lib/utils/paths.js';
  /**
   * The signature element. One per record, at the top, always a verb.
   * This is the one place ember earns its keep on a record page: it is
   * literally "the thing that needs you".
   *
   * Give it an `href` and the action becomes a link. Without one it stays a
   * button, which on the fixture pages goes nowhere. Fine while a page is a
   * sandbox, not fine once the record it names is real and one click away.
   *
   * @type {{ label?: string, text: string, action?: string, href?: string|null, secondary?: string, tone?: 'ember'|'rust' }}
   */
  let {
    label = 'Next action',
    text,
    action = null,
    href = null,
    secondary = null,
    tone = 'ember'
  } = $props();

  let accent = $derived(tone === 'rust' ? 'var(--v2-rust)' : 'var(--v2-ember)');
</script>

<div
  class="v2-next"
  style={tone === 'rust'
    ? 'background:color-mix(in srgb, var(--v2-rust) 9%, transparent);border-color:color-mix(in srgb, var(--v2-rust) 28%, transparent)'
    : ''}
>
  <div class="v2-next-body">
    <div class="v2-label" style="color:{accent}">{label}</div>
    <div class="v2-next-text">{text}</div>
  </div>
  {#if action && href}
    <a
      class="v2-btn v2-btn-primary"
      href={resolve(asInternalPath(href))}
      style={tone === 'rust' ? `background:${accent};border-color:${accent}` : ''}
    >
      {action}
    </a>
  {:else if action}
    <button
      class="v2-btn v2-btn-primary"
      style={tone === 'rust' ? `background:${accent};border-color:${accent}` : ''}
    >
      {action}
    </button>
  {/if}
  {#if secondary}
    <button class="v2-btn">{secondary}</button>
  {/if}
</div>
