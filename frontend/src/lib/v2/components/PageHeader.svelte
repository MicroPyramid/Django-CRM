<script>
  /**
   * @type {{
   *   title: string,
   *   record?: boolean,
   *   center?: boolean,
   *   width?: string,
   *   leading?: import('svelte').Snippet,
   *   sub?: import('svelte').Snippet,
   *   crumb?: import('svelte').Snippet,
   *   actions?: import('svelte').Snippet
   * }}
   *
   * `center` narrows the header to a form column so it sits above a centred
   * `.v2-form` (or other centred body) rather than spanning the full width.
   * `width` overrides that column's outer width for pages whose body is wider
   * than the standard 560px form, pass the body's own max-width.
   *
   * `leading` renders before the title block. An avatar or record mark. It is
   * centred against the text so it sits beside the name, not the crumb.
   */
  let { title, record = false, center = false, width, leading, sub, crumb, actions } = $props();
</script>

<header
  class="v2-header"
  class:is-centered={center}
  style={center && width ? `--v2-header-col:${width}` : null}
>
  {#if leading}<div style="align-self:center;flex:none">{@render leading()}</div>{/if}
  <div style="min-width:0">
    {#if crumb}<div class="v2-crumb">{@render crumb()}</div>{/if}
    <h1 class={record ? 'v2-record-title' : 'v2-page-title'}>{title}</h1>
    {#if sub}<div class="v2-sub" style="margin-top:5px">{@render sub()}</div>{/if}
  </div>
  {#if actions}<div class="v2-actions">{@render actions()}</div>{/if}
</header>
