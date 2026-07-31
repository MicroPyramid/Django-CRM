<script>
  /**
   * The reference sheet. If a colour or a size is not on this page, it should
   * not be in the product.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import NextAction from '$lib/v2/components/NextAction.svelte';
  import StageMeter from '$lib/v2/components/StageMeter.svelte';
  import {
    STAGES,
    STAGE_LABEL,
    STAGE_TONE,
    AGING_TONE,
    AGING_LABEL,
    LEAD_STATUS_TONE,
    PRIORITY_TONE,
    CASE_STATUS_TONE,
    INVOICE_STATUS_TONE,
    invoiceStatusLabel
  } from '$lib/v2/enums.js';

  const PALETTE = [
    {
      name: 'Ember',
      hex: '#EA580C',
      v: '--v2-ember',
      job: 'Primary action, due-now. Never a heading, never an icon tint.'
    },
    {
      name: 'Ink',
      hex: '#1C1917',
      v: '--v2-ink',
      job: 'All primary text and the bulk-action bar.'
    },
    {
      name: 'Slate',
      hex: '#78716C',
      v: '--v2-slate',
      job: 'Labels, secondary text, on-pace aging fill.'
    },
    {
      name: 'Paper',
      hex: '#FAFAF9',
      v: '--v2-paper',
      job: 'App canvas. Cards sit on it in pure white.'
    },
    {
      name: 'Clay',
      hex: '#B45309',
      v: '--v2-clay',
      job: 'aging_status yellow — past expected_days.'
    },
    {
      name: 'Rust',
      hex: '#9A3412',
      v: '--v2-rust',
      job: 'aging_status red, overdue follow-ups, destructive.'
    },
    {
      name: 'Moss',
      hex: '#3F6212',
      v: '--v2-moss',
      job: 'Won, completed, positive delta. Used sparingly.'
    }
  ];

  const ENUM_MAPS = [
    {
      title: 'Opportunity.stage',
      source: 'STAGES',
      rows: STAGES.map((s) => [STAGE_LABEL[s], STAGE_TONE[s], s])
    },
    {
      title: 'Opportunity.aging_status',
      source: 'get_aging_status()',
      rows: ['green', 'yellow', 'red'].map((s) => [AGING_LABEL[s], AGING_TONE[s], `'${s}'`])
    },
    {
      title: 'Lead.status',
      source: 'LEAD_STATUS',
      rows: Object.keys(LEAD_STATUS_TONE).map((s) => [s, LEAD_STATUS_TONE[s], s])
    },
    {
      title: 'Case.priority',
      source: 'PRIORITY_CHOICE',
      rows: Object.keys(PRIORITY_TONE).map((s) => [s, PRIORITY_TONE[s], s])
    },
    {
      title: 'Case.status',
      source: 'STATUS_CHOICE',
      rows: Object.keys(CASE_STATUS_TONE).map((s) => [s, CASE_STATUS_TONE[s], s])
    },
    {
      title: 'Invoice.status',
      source: 'INVOICE_STATUS',
      rows: Object.keys(INVOICE_STATUS_TONE).map((s) => [
        invoiceStatusLabel(s),
        INVOICE_STATUS_TONE[s],
        s
      ])
    }
  ];
</script>

<PageHeader title="Design system">
  {#snippet sub()}
    Seven colours, one type scale. Every status enum in the product maps onto this page.
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:40px;max-width:1000px">
    <h2 class="v2-section" style="margin-bottom:12px">Palette — each colour has one job</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px">
      {#each PALETTE as c (c.name)}
        <div class="v2-card" style="overflow:hidden">
          <div style="height:46px;background:var({c.v})"></div>
          <div style="padding:9px 11px">
            <div style="font-weight:650;font-size:12.5px">{c.name}</div>
            <div class="v2-num v2-muted" style="font-size:10px">{c.hex}</div>
            <div class="v2-sub" style="font-size:11px;margin-top:5px;line-height:1.45">{c.job}</div>
          </div>
        </div>
      {/each}
    </div>

    <div class="v2-card" style="padding:14px 16px;margin-top:14px">
      <div class="v2-label" style="margin-bottom:7px">The one rule</div>
      <p style="margin:0;font-size:13.5px;line-height:1.6">
        In v1, orange appeared on headings, icons, active chrome and buttons at once, so it carried
        no information. Here it marks one thing: <b
          >something you can act on, or something that needs you</b
        >. That is why the active nav item is weight and ink rather than orange, why no status pill
        is ever ember, and why there is exactly one ember button per view.
      </p>
    </div>

    <h2 class="v2-section" style="margin:30px 0 12px">Type scale</h2>
    <div class="v2-card" style="padding:4px 16px">
      {#each [['Page & record title', 'v2-page-title', '21.9px / 640 / −0.023em', 'Today'], ['Section', 'v2-section', '15.4px / 640 / −0.015em', 'Overdue'], ['Body', '', '14.4px — the base every size derives from', 'Sent the security addendum'], ['Secondary', 'v2-sub', '13.4px · slate', 'Northwind Trading']] as [name, cls, spec, sample] (name)}
        <div
          style="display:flex;align-items:baseline;gap:18px;padding:13px 0;border-bottom:1px solid var(--v2-line-soft)"
        >
          <span class={cls}>{sample}</span>
          <span class="v2-num v2-muted" style="margin-left:auto;font-size:10.5px;white-space:nowrap"
            >{spec}</span
          >
        </div>
      {/each}
      <div
        style="display:flex;align-items:baseline;gap:18px;padding:13px 0;border-bottom:1px solid var(--v2-line-soft)"
      >
        <span class="v2-label">Past expected stage</span>
        <span class="v2-num v2-muted" style="margin-left:auto;font-size:10.5px"
          >10px sans / .09em / upper</span
        >
      </div>
      <div style="display:flex;align-items:baseline;gap:18px;padding:13px 0">
        <span class="v2-num" style="font-weight:600">$84,000 · 31d · 214</span>
        <span class="v2-num v2-muted" style="margin-left:auto;font-size:10.5px">mono · tabular</span
        >
      </div>
    </div>
    <p class="v2-sub" style="margin-top:10px;font-size:12.5px;line-height:1.6;max-width:70ch">
      Numerals are the only thing set in monospace, and every one of them is tabular. Columns of
      money and days line up without extra CSS, and a changing figure never reflows the row it sits
      in. Labels, section headings and table headers are quiet sans — mono there would compete with
      the figures it is meant to caption.
    </p>

    <h2 class="v2-section" style="margin:30px 0 12px">Components</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="v2-card" style="padding:14px">
        <div class="v2-label" style="margin-bottom:10px">Buttons</div>
        <div style="display:flex;gap:7px;flex-wrap:wrap">
          <button class="v2-btn v2-btn-primary">Log a call</button>
          <button class="v2-btn">Edit</button>
          <button class="v2-btn v2-btn-quiet">Snooze</button>
          <button class="v2-btn v2-btn-sm">Small</button>
        </div>
        <p class="v2-sub" style="font-size:11.5px;margin-top:10px;line-height:1.5">
          One ember button per view. It names the outcome — “Log a call”, never “Submit”.
        </p>
      </div>

      <div class="v2-card" style="padding:14px">
        <div class="v2-label" style="margin-bottom:10px">Status pills</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap">
          <Pill tone="rust">Urgent</Pill>
          <Pill tone="clay">Past expected</Pill>
          <Pill tone="moss">Paid</Pill>
          <Pill tone="ink">Negotiation</Pill>
          <Pill tone="slate" dot>On pace</Pill>
        </div>
        <p class="v2-sub" style="font-size:11.5px;margin-top:10px;line-height:1.5">
          Tinted background, never solid — solid reads as a button. Ember is not an available tone.
        </p>
      </div>

      <div class="v2-card" style="padding:14px;grid-column:1 / -1">
        <div class="v2-label" style="margin-bottom:10px">Next-action strip</div>
        <NextAction
          text="Call Kavi about the legal review — nobody has since 16 July."
          action="Log a call"
        />
        <p class="v2-sub" style="font-size:11.5px;margin-top:10px;line-height:1.5">
          The signature element and the one place ember belongs on a record. One per record, at the
          top, always a verb. Turns rust when the thing it names is already overdue.
        </p>
      </div>

      <div class="v2-card" style="padding:14px">
        <div class="v2-label" style="margin-bottom:10px">Stage meter</div>
        <StageMeter stage="PROPOSAL" />
        <p class="v2-sub" style="font-size:11.5px;margin-top:10px;line-height:1.5">
          Four segments for the four open stages. A closed deal leaves the meter and becomes a pill
          — a won deal is not “100% through a funnel”, it is done.
        </p>
      </div>

      <div class="v2-card" style="padding:14px">
        <div class="v2-label" style="margin-bottom:10px">Filter chips</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
          <span class="v2-view">My open deals</span>
          <span class="v2-chip"
            ><b>Owner</b> Priya <button type="button" aria-label="Remove">×</button></span
          >
          <span class="v2-chip v2-chip-add">+ Filter</span>
        </div>
        <p class="v2-sub" style="font-size:11.5px;margin-top:10px;line-height:1.5">
          One system. A saved view, then a removable chip per filter. v1 had three overlapping
          systems and you could not tell what was applied.
        </p>
      </div>
    </div>

    <h2 class="v2-section" style="margin:30px 0 12px">Every status enum, mapped</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px 30px">
      {#each ENUM_MAPS as m (m.title)}
        <div>
          <div class="v2-label" style="margin-bottom:8px">
            {m.title} · <span style="text-transform:none;letter-spacing:0">{m.source}</span>
          </div>
          {#each m.rows as [label, tone, wire] (wire)}
            <div
              style="display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid var(--v2-line-soft)"
            >
              <Pill {tone}>{label}</Pill>
              <code class="v2-num v2-muted" style="font-size:10.5px;margin-left:auto">{wire}</code>
            </div>
          {/each}
        </div>
      {/each}
    </div>
  </div>
</div>
