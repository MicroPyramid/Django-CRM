<script>
  /**
   * Help.
   *
   * ── WHAT THIS PAGE IS NOT ────────────────────────────────────────────────
   * v1's support page is 647 lines of mission statement, pricing rationale and
   * "join thousands of businesses": marketing copy shown to people who have
   * ALREADY BOUGHT and are, by the fact of being here, stuck. Somebody who
   * opens Help is not deciding whether to adopt the product; they are trying
   * to get out of a hole, and every paragraph between them and the way out is
   * a paragraph that makes them angrier.
   *
   * So the ordering is: things you can fix yourself, then how to reach a
   * person, then what that person will need from you. Sales copy belongs on
   * the marketing site, which is a different repo.
   *
   * ── THE LAST SECTION IS THE POINT ────────────────────────────────────────
   * "What to include" exists because the first reply to almost every support
   * email is a request for the same four facts. Printing them on the page,
   * and only the ones the browser already knows, turns a two-day round trip
   * into one message. Nothing here is fetched, and nothing identifying is
   * displayed: no org id, no token, no email, no user id. A support page that
   * renders an identifier is a support page that puts it in screenshots.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import {
    BookOpen,
    LifeBuoy,
    Bug,
    Mail,
    Activity,
    ArrowUpRight,
    ClipboardList
  } from '@lucide/svelte';

  const SELF_SERVE = [
    {
      href: '/solutions',
      icon: BookOpen,
      title: 'Knowledge base',
      body: 'The answers your team has already written down, including the ones customers can read.'
    },
    {
      href: '/tickets',
      icon: LifeBuoy,
      title: 'Your tickets',
      body: 'Everything open, and who it is waiting on. Most "no one replied" turns out to be a ticket assigned to nobody.'
    },
    {
      href: '/settings',
      icon: ClipboardList,
      title: 'Settings',
      body: 'Routing, escalation, business hours and inbound email. Each page reports what its rules are actually doing, not just what they are set to.'
    }
  ];

  const CONTACT = [
    {
      href: 'https://github.com/django-crm/Django-CRM/issues',
      icon: Bug,
      title: 'Report a bug',
      body: 'Public issue tracker. Fastest route for anything reproducible.',
      external: true
    },
    {
      href: 'mailto:support@bottlecrm.example',
      icon: Mail,
      title: 'Email support',
      body: 'For anything involving your data, billing or an account you cannot get into.'
    },
    {
      href: 'https://status.bottlecrm.example',
      icon: Activity,
      title: 'Service status',
      body: 'Check here first if something that worked this morning stopped working this afternoon.',
      external: true
    }
  ];

  /**
   * The four facts a first reply always asks for. Browser and screen come from
   * the client; the other two are things only the person writing can supply,
   * and they are phrased as prompts rather than pre-filled. This page is not
   * going to quietly ship an org identifier into an email body.
   */
  let browser = $state('—');
  let screen = $state('—');
  $effect(() => {
    const ua = navigator.userAgent;
    const m = ua.match(/(Firefox|Edg|Chrome|Safari)\/([\d.]+)/);
    browser = m ? `${m[1] === 'Edg' ? 'Edge' : m[1]} ${m[2].split('.')[0]}` : 'Unknown browser';
    screen = `${window.innerWidth}×${window.innerHeight}`;
  });
</script>

<PageHeader title="Help" center width="840px">
  {#snippet sub()}
    Fix it yourself, or reach someone who can
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <!-- Centred column, not left-hugging: on a wide screen the header and body
       share one 840px column down the middle (same pattern as the form pages).
       max-width caps it; margin-inline centres it. -->
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px;max-width:840px;margin-inline:auto">
    <div class="v2-label" style="margin-bottom:10px">Start here</div>
    <div class="cards">
      {#each SELF_SERVE as c (c.href)}
        <a class="v2-card card" href={c.href}>
          <c.icon size={17} />
          <div>
            <b>{c.title}</b>
            <p>{c.body}</p>
          </div>
        </a>
      {/each}
    </div>

    <div class="v2-label" style="margin:26px 0 10px">If that did not do it</div>
    <div class="cards">
      {#each CONTACT as c (c.href)}
        <a
          class="v2-card card"
          href={c.href}
          rel={c.external ? 'noreferrer noopener' : undefined}
          target={c.external ? '_blank' : undefined}
        >
          <c.icon size={17} />
          <div>
            <b>
              {c.title}{#if c.external}<ArrowUpRight size={12} class="ext" />{/if}
            </b>
            <p>{c.body}</p>
          </div>
        </a>
      {/each}
    </div>

    <div class="v2-label" style="margin:26px 0 10px">What to include when you write</div>
    <div class="v2-card" style="padding:16px 18px">
      <p class="lead">
        Four things turn a two-day exchange into one message. The first two are already known.
      </p>
      <dl class="facts">
        <dt>Browser</dt>
        <dd class="v2-num">{browser}</dd>
        <dt>Window size</dt>
        <dd class="v2-num">{screen}</dd>
        <dt>What you expected</dt>
        <dd>The thing you were trying to do, in one sentence.</dd>
        <dt>What happened instead</dt>
        <dd>
          The exact wording of any error. "It didn't work" and "Something went wrong" are the same
          message to us.
        </dd>
      </dl>
      <p class="fine">
        Please do not paste screenshots containing an invoice link, an API token or a survey URL.
        Each of those is a working credential for whoever ends up holding it.
      </p>
    </div>
  </div>
</div>

<style>
  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 12px;
  }
  .card {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding: 15px 16px;
    color: inherit;
    text-decoration: none;
    transition: border-color 0.12s;
  }
  .card:hover {
    border-color: var(--v2-slate);
  }
  .card :global(svg) {
    flex: none;
    margin-top: 1px;
    color: var(--v2-slate);
  }
  .card b {
    display: flex;
    align-items: center;
    gap: 3px;
    font-size: 13.5px;
    font-weight: 600;
  }
  .card :global(.ext) {
    opacity: 0.5;
  }
  .card p {
    margin: 4px 0 0;
    font-size: 12px;
    color: var(--v2-slate);
    line-height: 1.5;
  }

  .lead {
    margin: 0 0 12px;
    font-size: 12.5px;
    color: var(--v2-slate);
  }
  .facts {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 8px 18px;
    margin: 0;
    font-size: 12.5px;
    line-height: 1.5;
  }
  .facts dt {
    color: var(--v2-slate);
    white-space: nowrap;
  }
  .facts dd {
    margin: 0;
  }
  .fine {
    margin: 14px 0 0;
    padding-top: 12px;
    border-top: 1px solid var(--v2-line);
    font-size: 11.5px;
    color: var(--v2-slate);
    line-height: 1.55;
  }
  @media (max-width: 520px) {
    .facts {
      grid-template-columns: 1fr;
      gap: 2px 0;
    }
    .facts dd {
      margin-bottom: 8px;
    }
  }
</style>
