<script>
  import '../../../../app.css';
  import imgLogo from '$lib/assets/images/logo.png';

  let { data } = $props();
</script>

<svelte:head>
  <title>Verify Sign-in | BottleCRM</title>
  <meta name="referrer" content="no-referrer" />
</svelte:head>

<div class="verify-page">
  <div class="verify-wrapper">
    <a href="/" class="logo">
      <img src={imgLogo} alt="" class="logo-icon" />
      <span class="logo-text">BottleCRM</span>
    </a>

    <div class="verify-card">
      {#if data.error}
        <h1 class="verify-title">Link expired or invalid</h1>
        <p class="verify-message">{data.error}</p>
        <a href="/login" class="back-link">Back to login</a>
      {:else}
        <h1 class="verify-title">Signing you in...</h1>
        <div class="spinner-large"></div>
      {/if}
    </div>
  </div>
</div>

<style>
  .verify-page {
    min-height: 100vh;
    min-height: 100dvh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f8fa;
    padding: 2rem;
  }

  .verify-wrapper {
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    margin-bottom: 2rem;
  }

  .logo-icon {
    width: 40px;
    height: 40px;
    object-fit: contain;
  }

  .logo-text {
    font-size: 1.5rem;
    font-weight: 700;
    color: #33475b;
    letter-spacing: -0.02em;
  }

  .verify-card {
    width: 100%;
    background: #fff;
    border-radius: 8px;
    padding: 2.5rem 2rem;
    text-align: center;
    box-shadow:
      0 1px 3px rgba(0, 0, 0, 0.08),
      0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .verify-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #33475b;
    margin: 0 0 1rem;
  }

  .verify-message {
    font-size: 0.9375rem;
    color: #516f90;
    margin: 0 0 1.5rem;
    line-height: 1.5;
  }

  .back-link {
    display: inline-block;
    color: #ff7a59;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9375rem;
  }

  .back-link:hover {
    text-decoration: underline;
  }

  .spinner-large {
    width: 32px;
    height: 32px;
    border: 3px solid #e0e0e0;
    border-top-color: #ff7a59;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    margin: 1rem auto 0;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  :global(.dark) .verify-page {
    background: #1a1a1a;
  }

  :global(.dark) .verify-card {
    background: #2d2d2d;
    box-shadow:
      0 1px 3px rgba(0, 0, 0, 0.2),
      0 4px 12px rgba(0, 0, 0, 0.15);
  }

  :global(.dark) .logo-text {
    color: #fff;
  }

  :global(.dark) .verify-title {
    color: #fff;
  }

  :global(.dark) .verify-message {
    color: #999;
  }
</style>
