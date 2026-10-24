<script>
  /**
   * A webhook key, shown in the one response that carries it (a create or a
   * replace) and gone on the next load: reads only carry `key_hint`.
   *
   * @type {{ title: string, url?: string, secret: string, replaced?: boolean }}
   */
  import CopyValue from './CopyValue.svelte';

  let { title, url = '', secret, replaced = false } = $props();
</script>

<div
  class="v2-card"
  style="padding:15px 16px;margin-bottom:18px;border-color:color-mix(in srgb, var(--v2-moss) 40%, var(--v2-line))"
>
  <div style="font-weight:650;font-size:13px">{title}</div>
  <p class="v2-sub" style="font-size:12px;margin:4px 0 12px;line-height:1.5">
    This is the only time the key is shown. Paste it into the tool that sends your leads; if it is
    lost, replace it.
    {#if replaced}
      The old key keeps working for 7 days, so there is time to update the sender.
    {/if}
  </p>
  <div style="display:flex;flex-direction:column;gap:12px">
    {#if url}
      <CopyValue label="Webhook URL" value={url} id="once-url" />
    {/if}
    <CopyValue label="Key" value={secret} id="once-key" />
  </div>
</div>
