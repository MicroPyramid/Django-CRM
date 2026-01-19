<script>
  import '../../../app.css';

  import imgGoogle from '$lib/assets/images/google.svg';
  import imgLogo from '$lib/assets/images/logo.png';
  import { ArrowRight } from '@lucide/svelte';

  let { data } = $props();

  let isLoading = $state(false);

  function handleGoogleLogin() {
    isLoading = true;
  }
</script>

<svelte:head>
  <title>Log in | BottleCRM</title>
  <meta
    name="description"
    content="Log in to BottleCRM to manage your contacts, deals, and grow your business."
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
      <h1 class="login-title">Log in to your account</h1>

      <!-- Google Sign In -->
      <a
        href={data['google_url']}
        onclick={handleGoogleLogin}
        class="google-btn"
        class:loading={isLoading}
      >
        {#if isLoading}
          <span class="spinner"></span>
          <span>Signing in...</span>
        {:else}
          <img src={imgGoogle} alt="" class="google-icon" />
          <span>Sign in with Google</span>
        {/if}
      </a>

      <!-- Divider -->
      <div class="divider">
        <span>or</span>
      </div>

      <!-- SSO Notice -->
      <p class="sso-notice">
        We use Google Sign-In for secure, passwordless authentication.
        Your data is protected with enterprise-grade security.
      </p>
    </div>

    <!-- Help Links -->
    <div class="help-section">
      <p class="help-text">
        Don't have an account? <a href={data['google_url']} class="help-link">Sign up for free</a>
      </p>
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

  /* SSO Notice */
  .sso-notice {
    font-size: 0.875rem;
    color: #516f90;
    text-align: center;
    line-height: 1.5;
    margin: 0;
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

  .help-link {
    color: #ff7a59;
    text-decoration: none;
    font-weight: 500;
  }

  .help-link:hover {
    text-decoration: underline;
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

  :global(.dark) .sso-notice {
    color: #999;
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
