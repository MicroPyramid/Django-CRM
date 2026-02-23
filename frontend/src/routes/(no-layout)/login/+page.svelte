<script>
  import '../../../app.css';
  import { enhance } from '$app/forms';

  import imgGoogle from '$lib/assets/images/google.svg';
  import imgLogo from '$lib/assets/images/logo.png';
  import { ArrowRight } from '@lucide/svelte';

  let { data } = $props();

  let isLoading = $state(false);
  let email = $state('');
  let magicLinkSent = $state(false);
  let isSendingLink = $state(false);
  let magicLinkError = $state('');

  function handleGoogleLogin() {
    isLoading = true;
  }

  function handleMagicLink() {
    isSendingLink = true;
    return async ({ result }) => {
      isSendingLink = false;
      if (result.type === 'success') {
        magicLinkSent = true;
      } else if (result.type === 'failure') {
        magicLinkError = result.data?.error || 'Something went wrong. Please try again.';
      }
    };
  }
</script>

<svelte:head>
  <title>Sign in | BottleCRM</title>
  <meta
    name="description"
    content="Sign in or sign up for BottleCRM to manage your contacts, deals, and grow your business."
  />
</svelte:head>

<div class="login-page">
  <!-- Main Container -->
  <div class="login-wrapper">
    <!-- Logo -->
    <a href="/" class="logo">
      <img src={imgLogo} alt="" class="logo-icon" />
      <span class="logo-text">BottleCRM</span>
    </a>

    <!-- Login Card -->
    <div class="login-card">
      <h1 class="login-title">Sign in to your account</h1>

      <!-- Google Sign In -->
      <a
        href={data['google_url']}
        onclick={handleGoogleLogin}
        class="google-btn"
        class:loading={isLoading}
      >
        {#if isLoading}
          <span class="spinner"></span>
          <span>Redirecting...</span>
        {:else}
          <img src={imgGoogle} alt="" class="google-icon" />
          <span>Continue with Google</span>
        {/if}
      </a>

      <!-- Divider -->
      <div class="divider">
        <span>or</span>
      </div>

      <!-- Magic Link -->
      {#if magicLinkSent}
        <div class="magic-link-success">
          <p>Check your email for a sign-in link.</p>
          <p class="magic-link-hint">The link expires in 10 minutes.</p>
        </div>
      {:else}
        <form method="POST" action="/login?/requestMagicLink" use:enhance={handleMagicLink} class="magic-link-form">
          <input
            type="email"
            name="email"
            placeholder="Enter your email address"
            class="email-input"
            required
            bind:value={email}
            disabled={isSendingLink}
          />
          <button type="submit" class="magic-link-btn" disabled={isSendingLink}>
            {#if isSendingLink}
              <span class="spinner"></span>
              <span>Sending...</span>
            {:else}
              <span>Continue with email</span>
              <ArrowRight size={16} />
            {/if}
          </button>
        </form>
      {/if}
    </div>

    <!-- Help Links -->
    <div class="help-section">
      <p class="help-text">New here? Just enter your email above to get started.</p>
    </div>

    <!-- Footer -->
    <footer class="login-footer">
      <a href="https://bottlecrm.io/privacy-policy">Privacy Policy</a>
      <span class="dot"></span>
      <a href="https://bottlecrm.io/terms">Terms of Service</a>
      <span class="dot"></span>
      <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener">GitHub</a>
    </footer>
  </div>
</div>

<style>
  .login-page {
    min-height: 100vh;
    min-height: 100dvh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f5f8fa;
    padding: 2rem;
  }

  .login-wrapper {
    width: 100%;
    max-width: 400px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* Logo */
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

  /* Login Card */
  .login-card {
    width: 100%;
    background: #fff;
    border-radius: 8px;
    padding: 2.5rem 2rem;
    box-shadow:
      0 1px 3px rgba(0, 0, 0, 0.08),
      0 4px 12px rgba(0, 0, 0, 0.05);
  }

  .login-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #33475b;
    text-align: center;
    margin: 0 0 1.5rem;
    letter-spacing: -0.01em;
  }

  /* Google Button */
  .google-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    width: 100%;
    height: 48px;
    background: #ff7a59;
    border: none;
    border-radius: 6px;
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .google-btn:hover {
    background: #ff5c35;
  }

  .google-btn:active {
    background: #e8532d;
  }

  .google-btn.loading {
    pointer-events: none;
    opacity: 0.85;
  }

  .google-icon {
    width: 20px;
    height: 20px;
    background: #fff;
    border-radius: 3px;
    padding: 2px;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Divider */
  .divider {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 1.5rem 0;
  }

  .divider::before,
  .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #cbd6e2;
  }

  .divider span {
    font-size: 0.8125rem;
    color: #7c98b6;
    text-transform: lowercase;
  }

  /* Magic Link Form */
  .magic-link-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .email-input {
    width: 100%;
    height: 48px;
    padding: 0 1rem;
    border: 1px solid #cbd6e2;
    border-radius: 6px;
    font-size: 1rem;
    color: #33475b;
    background: #fff;
    outline: none;
    transition: border-color 0.15s ease;
    box-sizing: border-box;
  }

  .email-input:focus {
    border-color: #ff7a59;
  }

  .email-input:disabled {
    opacity: 0.6;
  }

  .magic-link-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    height: 48px;
    background: #33475b;
    border: none;
    border-radius: 6px;
    color: #fff;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .magic-link-btn:hover {
    background: #2d3e50;
  }

  .magic-link-btn:disabled {
    opacity: 0.85;
    pointer-events: none;
  }

  .magic-link-success {
    text-align: center;
    padding: 1rem 0;
  }

  .magic-link-success p {
    color: #33475b;
    font-size: 1rem;
    font-weight: 500;
    margin: 0;
  }

  .magic-link-hint {
    color: #7c98b6 !important;
    font-size: 0.875rem !important;
    font-weight: 400 !important;
    margin-top: 0.5rem !important;
  }

  /* Help Section */
  .help-section {
    margin-top: 1.5rem;
    text-align: center;
  }

  .help-text {
    font-size: 0.9375rem;
    color: #516f90;
    margin: 0;
  }

  /* Footer */
  .login-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    margin-top: 2rem;
    flex-wrap: wrap;
  }

  .login-footer a {
    font-size: 0.8125rem;
    color: #7c98b6;
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .login-footer a:hover {
    color: #33475b;
  }

  .dot {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: #cbd6e2;
  }

  /* Responsive */
  @media (max-width: 480px) {
    .login-page {
      padding: 1.5rem;
      align-items: flex-start;
      padding-top: 3rem;
    }

    .login-card {
      padding: 2rem 1.5rem;
    }

    .login-title {
      font-size: 1.375rem;
    }
  }

  /* Dark mode support */
  :global(.dark) .login-page {
    background: #1a1a1a;
  }

  :global(.dark) .login-card {
    background: #2d2d2d;
    box-shadow:
      0 1px 3px rgba(0, 0, 0, 0.2),
      0 4px 12px rgba(0, 0, 0, 0.15);
  }

  :global(.dark) .logo-text {
    color: #fff;
  }

  :global(.dark) .login-title {
    color: #fff;
  }

  :global(.dark) .divider::before,
  :global(.dark) .divider::after {
    background: #404040;
  }

  :global(.dark) .divider span {
    color: #888;
  }

  :global(.dark) .email-input {
    background: #1a1a1a;
    border-color: #404040;
    color: #fff;
  }

  :global(.dark) .email-input:focus {
    border-color: #ff7a59;
  }

  :global(.dark) .magic-link-btn {
    background: #fff;
    color: #1a1a1a;
  }

  :global(.dark) .magic-link-btn:hover {
    background: #e0e0e0;
  }

  :global(.dark) .magic-link-success p {
    color: #fff;
  }

  :global(.dark) .help-text {
    color: #999;
  }

  :global(.dark) .login-footer a {
    color: #888;
  }

  :global(.dark) .login-footer a:hover {
    color: #fff;
  }

  :global(.dark) .dot {
    background: #404040;
  }
</style>
