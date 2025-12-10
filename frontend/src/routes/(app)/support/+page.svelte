<script>
  import {
    Github,
    Mail,
    Bug,
    Lightbulb,
    Shield,
    Wrench,
    Heart,
    Users,
    ExternalLink,
    Sparkles,
    ArrowRight,
    Zap,
    Code2,
    MessageSquareHeart
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();
</script>

<svelte:head>
  <title>Support - BottleCRM</title>
</svelte:head>

<div class="support-page">
  <!-- Hero Section with Gradient Mesh -->
  <header class="hero noise-overlay">
    <div class="hero-glow"></div>
    <div class="hero-content">
      <div class="hero-badge animate-in-up">
        <Sparkles class="h-3.5 w-3.5" />
        <span>Open Source • Forever Free</span>
      </div>
      <h1 class="hero-title animate-in-up stagger-1">
        Help & <span class="text-gradient">Support</span>
      </h1>
      <p class="hero-description animate-in-up stagger-2">
        Join thousands of businesses using BottleCRM to manage customer relationships without the enterprise price tag.
      </p>
    </div>
  </header>

  <!-- Mission Card - Featured -->
  <section class="content-area">
    <div class="mission-card glass-card animate-in-up stagger-3">
      <div class="mission-icon-wrap">
        <Heart class="h-7 w-7" />
      </div>
      <div class="mission-content">
        <h2>Our Mission</h2>
        <p>
          BottleCRM addresses the high subscription costs of commercial CRM alternatives by providing a
          <strong>completely free, open-source, and highly customizable</strong> solution. Clone it, self-host it,
          and make it yours — forever free.
        </p>
      </div>
      <div class="mission-pattern"></div>
    </div>

    <!-- Bento Grid -->
    <div class="bento-grid">
      <!-- Community Support - Large Card -->
      <article class="bento-card bento-featured hover-lift animate-in-up stagger-4">
        <div class="card-header">
          <div class="icon-box icon-github">
            <Github class="h-6 w-6" />
          </div>
          <div class="card-badge">Community</div>
        </div>
        <h3>Join the Community</h3>
        <p>
          Collaborate with developers worldwide. Get free support, share ideas, and help shape the future of open-source CRM.
        </p>
        <div class="card-stats">
          <div class="stat">
            <Code2 class="h-4 w-4" />
            <span>Open Source</span>
          </div>
          <div class="stat">
            <Users class="h-4 w-4" />
            <span>Active Community</span>
          </div>
        </div>
        <Button
          class="card-action"
          onclick={() => window.open('https://github.com/MicroPyramid/Django-CRM', '_blank')}
        >
          <Github class="h-4 w-4" />
          Visit GitHub
          <ArrowRight class="h-4 w-4 ml-auto transition-transform group-hover:translate-x-1" />
        </Button>
      </article>

      <!-- Professional Support -->
      <article class="bento-card hover-lift animate-in-up stagger-5">
        <div class="card-header">
          <div class="icon-box icon-pro">
            <Zap class="h-5 w-5" />
          </div>
        </div>
        <h3>Professional Support</h3>
        <p>
          Priority support, hosting assistance, and custom development services from the core team.
        </p>
        <Button
          variant="outline"
          class="card-action-outline"
          onclick={() => (window.location.href = 'mailto:ashwin@micropyramid.com')}
        >
          <Mail class="h-4 w-4" />
          Contact Team
        </Button>
      </article>

      <!-- Feature Requests -->
      <article class="bento-card hover-lift animate-in-up stagger-5">
        <div class="card-header">
          <div class="icon-box icon-idea">
            <Lightbulb class="h-5 w-5" />
          </div>
        </div>
        <h3>Feature Requests</h3>
        <p>
          Have an idea? Share your requests and help shape the future of BottleCRM.
        </p>
        <Button
          variant="outline"
          class="card-action-outline"
          onclick={() =>
            window.open(
              'https://github.com/MicroPyramid/Django-CRM/issues/new?template=feature_request.md',
              '_blank'
            )}
        >
          <Lightbulb class="h-4 w-4" />
          Request Feature
          <ExternalLink class="h-3 w-3" />
        </Button>
      </article>

      <!-- Bug Reports -->
      <article class="bento-card hover-lift animate-in-up stagger-6">
        <div class="card-header">
          <div class="icon-box icon-bug">
            <Bug class="h-5 w-5" />
          </div>
        </div>
        <h3>Bug Reports</h3>
        <p>
          Found an issue? Your feedback helps make the platform more stable for everyone.
        </p>
        <Button
          variant="outline"
          class="card-action-outline"
          onclick={() =>
            window.open(
              'https://github.com/MicroPyramid/Django-CRM/issues/new?template=bug_report.md',
              '_blank'
            )}
        >
          <Bug class="h-4 w-4" />
          Report Bug
          <ExternalLink class="h-3 w-3" />
        </Button>
      </article>

      <!-- Security - Emphasized -->
      <article class="bento-card bento-security hover-lift animate-in-up stagger-6">
        <div class="security-glow"></div>
        <div class="card-header">
          <div class="icon-box icon-security">
            <Shield class="h-5 w-5" />
          </div>
          <div class="card-badge badge-security">Critical</div>
        </div>
        <h3>Security Issues</h3>
        <p>
          <strong>Security is our priority.</strong> Report vulnerabilities privately.
          Never create public issues for security concerns.
        </p>
        <Button
          variant="destructive"
          class="card-action-security"
          onclick={() =>
            (window.location.href =
              'mailto:ashwin@micropyramid.com?subject=Security%20Issue%20-%20BottleCRM')}
        >
          <Shield class="h-4 w-4" />
          Report Privately
        </Button>
      </article>
    </div>

    <!-- Custom Development Banner -->
    <div class="custom-dev-banner animate-in-up stagger-6">
      <div class="banner-content">
        <div class="banner-icon">
          <Wrench class="h-8 w-8" />
        </div>
        <div class="banner-text">
          <h3>Need Custom CRM Development?</h3>
          <p>
            Tailored solutions including hosting, custom features, integrations, and ongoing support
            for your specific business needs.
          </p>
        </div>
        <Button
          size="lg"
          class="banner-cta"
          onclick={() =>
            (window.location.href =
              'mailto:ashwin@micropyramid.com?subject=Custom%20CRM%20Development%20Inquiry')}
        >
          <MessageSquareHeart class="h-4 w-4" />
          Get Custom Quote
          <ArrowRight class="h-4 w-4" />
        </Button>
      </div>
      <div class="banner-pattern"></div>
    </div>

    <!-- Version -->
    <footer class="version-footer">
      <span>BottleCRM</span>
      <span class="version-divider">•</span>
      <span>v1.0.0</span>
    </footer>
  </section>
</div>

<style>
  /* ═══════════════════════════════════════════════════════════════════════════
     SUPPORT PAGE - Premium Knowledge Hub Aesthetic
     ═══════════════════════════════════════════════════════════════════════════ */

  .support-page {
    min-height: 100vh;
    background: var(--background);
  }

  /* ─────────────────────────────────────────────────────────────────────────
     HERO SECTION
     ───────────────────────────────────────────────────────────────────────── */

  .hero {
    position: relative;
    padding: 3rem 1.5rem 2.5rem;
    overflow: hidden;
    background:
      radial-gradient(ellipse 80% 50% at 50% -20%, var(--accent-primary-subtle), transparent),
      radial-gradient(ellipse 60% 40% at 80% 0%, var(--accent-secondary-subtle), transparent),
      var(--background);
  }

  :global(.dark) .hero {
    background:
      radial-gradient(ellipse 80% 50% at 50% -20%, rgba(34, 211, 238, 0.08), transparent),
      radial-gradient(ellipse 60% 40% at 80% 0%, rgba(251, 191, 36, 0.05), transparent),
      var(--background);
  }

  .hero-glow {
    position: absolute;
    top: -50%;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 400px;
    background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%);
    opacity: 0.04;
    filter: blur(60px);
    pointer-events: none;
  }

  :global(.dark) .hero-glow {
    opacity: 0.08;
  }

  .hero-content {
    position: relative;
    max-width: 680px;
    margin: 0 auto;
    text-align: center;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.875rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--accent-primary);
    background: var(--accent-primary-subtle);
    border: 1px solid color-mix(in oklch, var(--accent-primary) 20%, transparent);
    border-radius: var(--radius-full);
    margin-bottom: 1rem;
  }

  .hero-title {
    font-family: var(--font-sans);
    font-size: clamp(2rem, 5vw, 2.75rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    color: var(--text-primary);
    margin-bottom: 0.75rem;
  }

  .hero-description {
    font-size: 1rem;
    line-height: 1.6;
    color: var(--text-secondary);
    max-width: 520px;
    margin: 0 auto;
  }

  /* ─────────────────────────────────────────────────────────────────────────
     CONTENT AREA
     ───────────────────────────────────────────────────────────────────────── */

  .content-area {
    padding: 0 1.5rem 3rem;
    max-width: 1000px;
    margin: 0 auto;
  }

  /* ─────────────────────────────────────────────────────────────────────────
     MISSION CARD
     ───────────────────────────────────────────────────────────────────────── */

  .mission-card {
    position: relative;
    display: flex;
    align-items: flex-start;
    gap: 1.25rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    border-radius: var(--radius-xl);
    overflow: hidden;
    background: var(--card);
    border: 1px solid var(--border);
  }

  .mission-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, var(--accent-primary-subtle) 0%, transparent 50%);
    pointer-events: none;
  }

  :global(.dark) .mission-card::before {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.05) 0%, transparent 50%);
  }

  .mission-icon-wrap {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    flex-shrink: 0;
    border-radius: var(--radius-lg);
    background: linear-gradient(135deg, var(--accent-primary) 0%, color-mix(in oklch, var(--accent-primary) 80%, var(--accent-secondary)) 100%);
    color: white;
    box-shadow: 0 4px 12px -2px color-mix(in oklch, var(--accent-primary) 30%, transparent);
  }

  :global(.dark) .mission-icon-wrap {
    box-shadow: 0 4px 20px -2px color-mix(in oklch, var(--accent-primary) 40%, transparent);
  }

  .mission-content {
    position: relative;
    flex: 1;
  }

  .mission-content h2 {
    font-family: var(--font-sans);
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }

  .mission-content p {
    font-size: 0.9375rem;
    line-height: 1.65;
    color: var(--text-secondary);
  }

  .mission-content strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  .mission-pattern {
    position: absolute;
    top: 0;
    right: 0;
    width: 200px;
    height: 100%;
    background:
      radial-gradient(circle at 100% 0%, var(--accent-secondary-subtle) 0%, transparent 50%);
    pointer-events: none;
    opacity: 0.6;
  }

  /* ─────────────────────────────────────────────────────────────────────────
     BENTO GRID
     ───────────────────────────────────────────────────────────────────────── */

  .bento-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  @media (max-width: 680px) {
    .bento-grid {
      grid-template-columns: 1fr;
    }

    .bento-featured {
      grid-column: 1;
    }
  }

  .bento-card {
    position: relative;
    padding: 1.25rem;
    border-radius: var(--radius-lg);
    background: var(--card);
    border: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    transition: all var(--duration-normal) var(--ease-out);
  }

  .bento-card:hover {
    border-color: var(--border-strong);
  }

  :global(.dark) .bento-card:hover {
    border-color: color-mix(in oklch, var(--accent-primary) 40%, var(--border));
  }

  .bento-featured {
    grid-column: span 2;
    padding: 1.5rem;
    background: linear-gradient(145deg, var(--card) 0%, color-mix(in oklch, var(--card) 95%, var(--accent-primary)) 100%);
  }

  @media (max-width: 680px) {
    .bento-featured {
      grid-column: span 1;
    }
  }

  .bento-security {
    grid-column: span 2;
    background: color-mix(in oklch, var(--status-danger-bg) 50%, var(--card));
    border-color: color-mix(in oklch, var(--status-danger) 20%, var(--border));
  }

  :global(.dark) .bento-security {
    background: color-mix(in oklch, var(--status-danger-bg) 100%, var(--card));
  }

  .security-glow {
    position: absolute;
    top: -20px;
    right: -20px;
    width: 120px;
    height: 120px;
    background: radial-gradient(circle, var(--status-danger) 0%, transparent 70%);
    opacity: 0.06;
    filter: blur(30px);
    pointer-events: none;
  }

  @media (max-width: 680px) {
    .bento-security {
      grid-column: span 1;
    }
  }

  /* Card Header */
  .card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.875rem;
  }

  .icon-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-md);
    transition: all var(--duration-normal) var(--ease-out);
  }

  .icon-github {
    background: var(--bg-emphasis);
    color: var(--text-primary);
  }

  :global(.dark) .icon-github {
    background: color-mix(in oklch, var(--text-primary) 15%, transparent);
  }

  .icon-pro {
    background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
    color: white;
  }

  .icon-idea {
    background: linear-gradient(135deg, var(--accent-secondary) 0%, #fcd34d 100%);
    color: #78350f;
  }

  .icon-bug {
    background: linear-gradient(135deg, #f97316 0%, #fb923c 100%);
    color: white;
  }

  .icon-security {
    background: linear-gradient(135deg, var(--status-danger) 0%, #f87171 100%);
    color: white;
  }

  .card-badge {
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-full);
    background: var(--accent-primary-subtle);
    color: var(--accent-primary);
    margin-left: auto;
  }

  .badge-security {
    background: var(--status-danger-bg);
    color: var(--status-danger);
  }

  /* Card Content */
  .bento-card h3 {
    font-family: var(--font-sans);
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.375rem;
  }

  .bento-card p {
    font-size: 0.875rem;
    line-height: 1.55;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    flex: 1;
  }

  .bento-card strong {
    color: var(--text-primary);
    font-weight: 600;
  }

  .card-stats {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-tertiary);
  }

  /* Card Actions */
  .bento-card :global(.card-action) {
    width: 100%;
    justify-content: flex-start;
    gap: 0.5rem;
  }

  .bento-card :global(.card-action-outline) {
    width: 100%;
    justify-content: flex-start;
    gap: 0.5rem;
  }

  .bento-card :global(.card-action-security) {
    width: 100%;
    justify-content: flex-start;
    gap: 0.5rem;
  }

  /* ─────────────────────────────────────────────────────────────────────────
     CUSTOM DEVELOPMENT BANNER
     ───────────────────────────────────────────────────────────────────────── */

  .custom-dev-banner {
    position: relative;
    padding: 1.5rem;
    border-radius: var(--radius-xl);
    overflow: hidden;
    background: linear-gradient(135deg,
      color-mix(in oklch, var(--accent-primary) 12%, var(--card)) 0%,
      color-mix(in oklch, var(--accent-secondary) 8%, var(--card)) 100%
    );
    border: 1px solid color-mix(in oklch, var(--accent-primary) 20%, var(--border));
  }

  :global(.dark) .custom-dev-banner {
    background: linear-gradient(135deg,
      color-mix(in oklch, var(--accent-primary) 8%, var(--card)) 0%,
      color-mix(in oklch, var(--accent-secondary) 5%, var(--card)) 100%
    );
    border-color: color-mix(in oklch, var(--accent-primary) 30%, var(--border));
  }

  .banner-content {
    position: relative;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    flex-wrap: wrap;
  }

  .banner-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    border-radius: var(--radius-lg);
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
    color: white;
    flex-shrink: 0;
  }

  :global(.dark) .banner-icon {
    box-shadow: 0 4px 20px -4px color-mix(in oklch, var(--accent-primary) 50%, transparent);
  }

  .banner-text {
    flex: 1;
    min-width: 200px;
  }

  .banner-text h3 {
    font-family: var(--font-sans);
    font-size: 1.0625rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .banner-text p {
    font-size: 0.875rem;
    line-height: 1.5;
    color: var(--text-secondary);
  }

  .custom-dev-banner :global(.banner-cta) {
    gap: 0.5rem;
    flex-shrink: 0;
    box-shadow: 0 4px 12px -2px color-mix(in oklch, var(--accent-primary) 30%, transparent);
  }

  :global(.dark) .custom-dev-banner :global(.banner-cta) {
    box-shadow: 0 4px 20px -4px color-mix(in oklch, var(--accent-primary) 40%, transparent);
  }

  .banner-pattern {
    position: absolute;
    top: 0;
    right: 0;
    width: 300px;
    height: 100%;
    background:
      radial-gradient(circle at 100% 50%, var(--accent-secondary-subtle) 0%, transparent 50%);
    pointer-events: none;
    opacity: 0.5;
  }

  /* ─────────────────────────────────────────────────────────────────────────
     VERSION FOOTER
     ───────────────────────────────────────────────────────────────────────── */

  .version-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding-top: 2rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-tertiary);
  }

  .version-divider {
    opacity: 0.4;
  }
</style>
