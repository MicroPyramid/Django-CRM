<script>
  import { resolve } from '$app/paths';
  import '../../../../app.css';
  import '$lib/v2/styles/v2.css';
  import imgLogo from '$lib/assets/images/logo.png';

  let { data } = $props();
</script>

<svelte:head>
  <title>Verifying · BottleCRM</title>
  <meta name="referrer" content="no-referrer" />
</svelte:head>

<div class="v2-root v2-auth">
  <div class="v2-auth-box">
    <a href={resolve('/')} class="v2-auth-brand">
      <img src={imgLogo} alt="" />
      <b>BottleCRM</b>
    </a>

    <div class="v2-auth-card" style="text-align:center">
      {#if data.error}
        <div class="v2-auth-head" style="margin-bottom:16px">
          <h1>Link expired or invalid</h1>
          <p>{data.error}</p>
        </div>
        <a href={resolve('/login')} class="v2-btn v2-btn-block">Back to sign in</a>
      {:else}
        <div
          class="v2-spin"
          style="width:26px;height:26px;margin:4px auto 15px;color:var(--v2-ember)"
        ></div>
        <div class="v2-auth-head" style="margin-bottom:0">
          <h1>Signing you in…</h1>
          <p>One moment while we verify your link.</p>
        </div>
      {/if}
    </div>
  </div>
</div>
