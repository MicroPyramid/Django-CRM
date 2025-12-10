<script>
  import '../../../app.css';

  import imgGoogle from '$lib/assets/images/google.svg';
  import imgLogo from '$lib/assets/images/logo.png';
  import { ArrowRight, Users, Target, BarChart3, Building2, CheckCircle2 } from '@lucide/svelte';

  let { data } = $props();

  let isLoading = $state(false);
  let mousePosition = $state({ x: 50, y: 50 });

  const features = [
    {
      icon: Users,
      title: 'Contact Management',
      description: 'Organize and track all your customer relationships'
    },
    {
      icon: Target,
      title: 'Sales Pipeline',
      description: 'Visualize deals and track progress through stages'
    },
    {
      icon: BarChart3,
      title: 'Analytics & Reports',
      description: 'Get insights with powerful dashboards'
    },
    {
      icon: Building2,
      title: 'Multi-Organization',
      description: 'Manage multiple businesses from one account'
    }
  ];

  const stats = [
    { value: '10K+', label: 'Active Users' },
    { value: '500K+', label: 'Contacts Managed' },
    { value: '99.9%', label: 'Uptime' }
  ];

  function handleGoogleLogin() {
    isLoading = true;
  }

  function handleMouseMove(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    mousePosition = {
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100
    };
  }
</script>

<svelte:head>
  <title>Sign In | BottleCRM - Modern CRM for Growing Teams</title>
  <meta
    name="description"
    content="Sign in to BottleCRM - the open-source CRM solution for startups and growing businesses. Manage contacts, track deals, and grow your business."
  />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link
    href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Outfit:wght@300;400;500;600;700&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<div
  class="login-page"
  role="presentation"
  onmousemove={handleMouseMove}
  style="--mouse-x: {mousePosition.x}%; --mouse-y: {mousePosition.y}%;"
>
  <!-- Animated background layers -->
  <div class="bg-layer bg-base"></div>
  <div class="bg-layer bg-gradient"></div>
  <div class="bg-layer bg-grid"></div>
  <div class="bg-layer bg-noise"></div>

  <!-- Floating geometric shapes -->
  <div class="geo-shapes">
    <div class="geo-diamond geo-1"></div>
    <div class="geo-diamond geo-2"></div>
    <div class="geo-line geo-line-1"></div>
    <div class="geo-circle geo-circle-1"></div>
  </div>

  <!-- Main content -->
  <div class="content-wrapper">
    <!-- Left side - Branding & Features (desktop) -->
    <div class="left-panel">
      <!-- Logo -->
      <header class="login-header">
        <div class="logo-group">
          <div class="logo-mark">
            <img src={imgLogo} alt="" class="logo-img" />
          </div>
          <div class="logo-text">
            <span class="logo-name">BottleCRM</span>
          </div>
        </div>
      </header>

      <!-- Headline -->
      <div class="hero-section">
        <h1 class="hero-title">
          <span class="title-line">The CRM that grows</span>
          <span class="title-line title-accent">with your business</span>
        </h1>
        <p class="hero-subtitle">
          Powerful, intuitive, and completely open-source. Manage your customer relationships
          without limits.
        </p>
      </div>

      <!-- Features grid -->
      <div class="features-grid">
        {#each features as feature}
          <div class="feature-card">
            <div class="feature-icon">
              <feature.icon size={20} />
            </div>
            <div class="feature-content">
              <h3 class="feature-title">{feature.title}</h3>
              <p class="feature-desc">{feature.description}</p>
            </div>
          </div>
        {/each}
      </div>

      <!-- Stats -->
      <div class="stats-row">
        {#each stats as stat}
          <div class="stat-item">
            <span class="stat-value">{stat.value}</span>
            <span class="stat-label">{stat.label}</span>
          </div>
        {/each}
      </div>
    </div>

    <!-- Right side - Login Card -->
    <div class="right-panel">
      <div class="login-card">
        <div class="card-glow"></div>
        <div class="card-inner">
          <!-- Mobile logo -->
          <div class="mobile-logo">
            <img src={imgLogo} alt="" class="logo-img" />
            <span class="logo-name">BottleCRM</span>
          </div>

          <div class="card-header">
            <h2 class="card-title">Welcome back</h2>
            <p class="card-subtitle">Sign in to continue to your dashboard</p>
          </div>

          <!-- Login button -->
          <div class="login-action">
            <a
              href={data['google_url']}
              onclick={handleGoogleLogin}
              class="google-btn"
              class:loading={isLoading}
            >
              <span class="btn-bg"></span>
              <span class="btn-content">
                {#if isLoading}
                  <span class="loader"></span>
                  <span class="btn-text">Signing in...</span>
                {:else}
                  <img src={imgGoogle} alt="" class="google-icon" />
                  <span class="btn-text">Continue with Google</span>
                  <ArrowRight class="btn-arrow" size={18} />
                {/if}
              </span>
            </a>
          </div>

          <!-- What you get (mobile) -->
          <div class="mobile-features">
            <p class="mobile-features-label">What you get</p>
            <div class="mobile-features-grid">
              {#each ['Unlimited contacts', 'Sales pipeline', 'Task management', 'Team collaboration'] as item}
                <div class="mobile-feature-item">
                  <CheckCircle2 size={16} class="check-icon" />
                  <span>{item}</span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Footer info -->
          <div class="card-footer">
            <p class="footer-note">
              Don't have an account? <span>Sign in with Google to get started</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Links -->
      <div class="footer-links">
        <a href="https://github.com/MicroPyramid/Django-CRM" target="_blank" rel="noopener">
          GitHub
        </a>
        <span class="footer-dot"></span>
        <a href="https://bottlecrm.io/docs">Docs</a>
        <span class="footer-dot"></span>
        <a href="https://bottlecrm.io/privacy-policy">Privacy</a>
      </div>
    </div>
  </div>
</div>

<style>
  /* ═══════════════════════════════════════════════════════════════
     GEOMETRIC NOIR - Premium Login Experience
     ═══════════════════════════════════════════════════════════════ */

  .login-page {
    --font-display: 'Cormorant Garamond', Georgia, serif;
    --font-ui: 'Outfit', 'Plus Jakarta Sans', system-ui, sans-serif;

    /* Color palette */
    --noir-950: #08090a;
    --noir-900: #0f1114;
    --noir-850: #141619;
    --noir-800: #1a1d21;
    --noir-700: #252931;
    --noir-600: #353b47;
    --noir-500: #4a5568;
    --noir-400: #718096;
    --noir-300: #a0aec0;
    --noir-200: #cbd5e0;
    --noir-100: #edf2f7;

    /* Accent */
    --gold-500: #d4a574;
    --gold-400: #e5b886;
    --cyan-500: #22d3ee;
    --cyan-400: #67e8f9;

    --ease-expo: cubic-bezier(0.16, 1, 0.3, 1);
    --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .login-page {
    position: relative;
    min-height: 100vh;
    min-height: 100dvh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    font-family: var(--font-ui);
    color: var(--noir-100);
  }

  /* ═══════════════════════════════════════════════════════════════
     BACKGROUND
     ═══════════════════════════════════════════════════════════════ */

  .bg-layer {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .bg-base {
    background: var(--noir-950);
  }

  .bg-gradient {
    background:
      radial-gradient(
        ellipse 80% 60% at var(--mouse-x) var(--mouse-y),
        rgba(212, 165, 116, 0.06) 0%,
        transparent 50%
      ),
      radial-gradient(ellipse 100% 80% at 10% 90%, rgba(34, 211, 238, 0.03) 0%, transparent 40%);
    transition: background 0.3s ease;
  }

  .bg-grid {
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
    background-size: 60px 60px;
    mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black, transparent);
  }

  .bg-noise {
    opacity: 0.02;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  }

  /* ═══════════════════════════════════════════════════════════════
     GEOMETRIC SHAPES
     ═══════════════════════════════════════════════════════════════ */

  .geo-shapes {
    position: absolute;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
  }

  .geo-diamond {
    position: absolute;
    border: 1px solid rgba(212, 165, 116, 0.1);
    transform: rotate(45deg);
    animation: float 20s ease-in-out infinite;
  }

  .geo-1 {
    top: 15%;
    left: 8%;
    width: 100px;
    height: 100px;
  }

  .geo-2 {
    bottom: 20%;
    right: 10%;
    width: 140px;
    height: 140px;
    border-color: rgba(34, 211, 238, 0.08);
    animation-delay: -10s;
  }

  .geo-line {
    position: absolute;
    height: 1px;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, transparent, rgba(212, 165, 116, 0.15), transparent);
  }

  .geo-line-1 {
    top: 30%;
    transform: rotate(-3deg);
  }

  .geo-circle {
    position: absolute;
    border-radius: 50%;
    border: 1px solid rgba(212, 165, 116, 0.08);
    animation: spin 80s linear infinite;
  }

  .geo-circle-1 {
    top: 10%;
    right: 15%;
    width: 250px;
    height: 250px;
  }

  @keyframes float {
    0%,
    100% {
      transform: rotate(45deg) translateY(0);
    }
    50% {
      transform: rotate(45deg) translateY(-15px);
    }
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  /* ═══════════════════════════════════════════════════════════════
     LAYOUT
     ═══════════════════════════════════════════════════════════════ */

  .content-wrapper {
    position: relative;
    z-index: 10;
    display: flex;
    width: 100%;
    max-width: 1200px;
    min-height: 100vh;
    min-height: 100dvh;
    padding: 2rem;
    gap: 4rem;
  }

  .left-panel {
    flex: 1;
    display: none;
    flex-direction: column;
    justify-content: center;
    padding: 2rem 0;
    animation: fadeInLeft 0.8s var(--ease-expo) both;
  }

  .right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    max-width: 440px;
    margin: 0 auto;
    animation: fadeInUp 0.8s var(--ease-expo) 0.1s both;
  }

  @keyframes fadeInLeft {
    from {
      opacity: 0;
      transform: translateX(-30px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes fadeInUp {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* ═══════════════════════════════════════════════════════════════
     LEFT PANEL - BRANDING
     ═══════════════════════════════════════════════════════════════ */

  .login-header {
    margin-bottom: 3rem;
  }

  .logo-group {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .logo-mark {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: linear-gradient(135deg, var(--noir-800), var(--noir-850));
    border: 1px solid var(--noir-700);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .logo-img {
    width: 24px;
    height: 24px;
    object-fit: contain;
  }

  .logo-name {
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--noir-100);
  }

  .hero-section {
    margin-bottom: 2.5rem;
  }

  .hero-title {
    font-family: var(--font-display);
    font-size: 2.75rem;
    font-weight: 500;
    line-height: 1.15;
    margin: 0 0 1rem;
  }

  .title-line {
    display: block;
    color: var(--noir-100);
  }

  .title-accent {
    background: linear-gradient(135deg, var(--gold-400), var(--gold-500));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-subtitle {
    font-size: 1.05rem;
    color: var(--noir-400);
    line-height: 1.6;
    margin: 0;
    max-width: 400px;
  }

  /* Features */
  .features-grid {
    display: grid;
    gap: 0.875rem;
    margin-bottom: 2.5rem;
  }

  .feature-card {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    border-radius: 12px;
    background: var(--noir-850);
    border: 1px solid var(--noir-800);
    transition: all 0.3s var(--ease-expo);
  }

  .feature-card:hover {
    border-color: var(--noir-700);
    background: var(--noir-800);
  }

  .feature-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(212, 165, 116, 0.1);
    color: var(--gold-400);
    flex-shrink: 0;
  }

  .feature-content {
    flex: 1;
    min-width: 0;
  }

  .feature-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--noir-100);
    margin: 0 0 0.25rem;
  }

  .feature-desc {
    font-size: 0.85rem;
    color: var(--noir-500);
    margin: 0;
  }

  /* Stats */
  .stats-row {
    display: flex;
    gap: 2.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--noir-800);
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--noir-100);
  }

  .stat-label {
    font-size: 0.8rem;
    color: var(--noir-500);
  }

  /* ═══════════════════════════════════════════════════════════════
     RIGHT PANEL - LOGIN CARD
     ═══════════════════════════════════════════════════════════════ */

  .login-card {
    position: relative;
    width: 100%;
    border-radius: 20px;
    padding: 1px;
    background: linear-gradient(
      135deg,
      rgba(212, 165, 116, 0.25),
      rgba(212, 165, 116, 0.05) 40%,
      rgba(34, 211, 238, 0.05) 60%,
      rgba(34, 211, 238, 0.15)
    );
  }

  .card-glow {
    position: absolute;
    inset: -1px;
    border-radius: 20px;
    background: radial-gradient(
      ellipse 60% 40% at 50% 0%,
      rgba(212, 165, 116, 0.15),
      transparent 60%
    );
    filter: blur(20px);
    pointer-events: none;
  }

  .card-inner {
    position: relative;
    background: linear-gradient(180deg, var(--noir-850) 0%, var(--noir-900) 100%);
    border-radius: 19px;
    padding: 2.5rem;
  }

  .mobile-logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.625rem;
    margin-bottom: 2rem;
  }

  .mobile-logo .logo-img {
    width: 28px;
    height: 28px;
  }

  .mobile-logo .logo-name {
    font-size: 1.375rem;
  }

  .card-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .card-title {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 500;
    color: var(--noir-100);
    margin: 0 0 0.5rem;
  }

  .card-subtitle {
    font-size: 0.95rem;
    color: var(--noir-400);
    margin: 0;
  }

  /* Google button */
  .login-action {
    margin-bottom: 1.5rem;
  }

  .google-btn {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 52px;
    border-radius: 12px;
    text-decoration: none;
    overflow: hidden;
    transition: transform 0.2s var(--ease-expo);
  }

  .google-btn:hover {
    transform: translateY(-2px);
  }

  .google-btn:active {
    transform: translateY(0);
  }

  .google-btn.loading {
    pointer-events: none;
  }

  .btn-bg {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--noir-100), var(--noir-200));
    transition: opacity 0.3s ease;
  }

  .google-btn:hover .btn-bg {
    opacity: 0.95;
  }

  .btn-content {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    color: var(--noir-900);
    font-weight: 600;
    font-size: 0.95rem;
  }

  .google-icon {
    width: 20px;
    height: 20px;
  }

  .btn-text {
    letter-spacing: -0.01em;
  }

  :global(.btn-arrow) {
    opacity: 0.5;
    transition: all 0.3s var(--ease-expo);
  }

  .google-btn:hover :global(.btn-arrow) {
    opacity: 1;
    transform: translateX(3px);
  }

  .loader {
    width: 20px;
    height: 20px;
    border: 2px solid var(--noir-300);
    border-top-color: var(--noir-900);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  /* Mobile features */
  .mobile-features {
    padding-top: 1.5rem;
    border-top: 1px solid var(--noir-800);
    margin-bottom: 1.5rem;
  }

  .mobile-features-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--noir-500);
    margin: 0 0 1rem;
  }

  .mobile-features-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .mobile-feature-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: var(--noir-300);
  }

  :global(.check-icon) {
    color: var(--cyan-400);
    flex-shrink: 0;
  }

  .card-footer {
    text-align: center;
  }

  .footer-note {
    font-size: 0.85rem;
    color: var(--noir-500);
    margin: 0;
  }

  .footer-note span {
    color: var(--noir-300);
  }

  /* Footer links */
  .footer-links {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    margin-top: 2rem;
  }

  .footer-links a {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--noir-500);
    text-decoration: none;
    transition: color 0.2s ease;
  }

  .footer-links a:hover {
    color: var(--gold-400);
  }

  .footer-dot {
    width: 3px;
    height: 3px;
    border-radius: 50%;
    background: var(--noir-700);
  }

  /* ═══════════════════════════════════════════════════════════════
     RESPONSIVE
     ═══════════════════════════════════════════════════════════════ */

  @media (min-width: 1024px) {
    .left-panel {
      display: flex;
    }

    .mobile-logo {
      display: none;
    }

    .mobile-features {
      display: none;
    }

    .right-panel {
      flex: none;
      width: 420px;
      margin: 0;
    }
  }

  @media (max-width: 480px) {
    .content-wrapper {
      padding: 1.5rem;
    }

    .card-inner {
      padding: 2rem 1.5rem;
    }

    .geo-shapes {
      opacity: 0.4;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
</style>
