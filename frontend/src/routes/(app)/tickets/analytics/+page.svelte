<script>
  import { resolve } from '$app/paths';
  /**
   * Service health. Four questions, in the order a support lead asks them:
   * is the queue growing, are we answering in time, who is carrying it, and
   * what is it made of.
   *
   * No chart library. Every mark here is a div sized by a percentage, which
   * keeps the page honest about how little it is actually drawing, and a
   * fourteen-bar series does not need an axis, a legend and 90kb of SVG.
   *
   * WHAT THIS PAGE DOES NOT DO
   * It never averages across priorities. "SLA attainment: 92%" folds four
   * different promises into one number that describes none of them; an urgent
   * incident answered in ninety minutes and a low-priority question answered
   * in ninety minutes are not the same event. Attainment is reported per
   * priority, against that priority's own target, or not at all.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SectionTabs from '$lib/v2/components/SectionTabs.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import Avatar from '$lib/v2/components/Avatar.svelte';
  import { count, shortDate } from '$lib/v2/format.js';
  import { Clock } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let canView = $derived(data.can_view);
  let totals = $derived(data.totals);
  // Floor at 1 so an empty or all-zero window scales cleanly to flat bars
  // rather than dividing by a zero (or -Infinity) peak.
  let peak = $derived(Math.max(1, ...data.volume.map((d) => Math.max(d.opened, d.closed))));

  /**
   * Minutes → "41m" / "2h 20m" / "1d 3h" / "1d". A number of minutes is not a
   * duration, and neither is "1d 0h". A zero remainder is dropped rather than
   * printed, at every scale.
   */
  function duration(mins) {
    if (mins == null) return '—';
    if (mins < 60) return `${mins}m`;
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    if (h < 24) return m ? `${h}h ${m}m` : `${h}h`;
    const d = Math.floor(h / 24);
    return h % 24 ? `${d}d ${h % 24}h` : `${d}d`;
  }

  // Attainment among *decided* cases (met vs missed). A priority with no
  // decided cases yet (all in-flight, or none at all) has no percentage to
  // report, so it returns null and the row shows "—" rather than "NaN%".
  const attainment = (r) => {
    const decided = r.met + r.missed;
    return decided ? Math.round((r.met / decided) * 100) : null;
  };
  const barColor = (pct) =>
    pct == null
      ? 'var(--v2-line)'
      : pct >= 95
        ? 'var(--v2-moss)'
        : pct >= 85
          ? 'var(--v2-clay)'
          : 'var(--v2-rust)';

  /** Net change over the window. Opened minus closed is the backlog's direction. */
  let net = $derived(totals.opened - totals.closed);
</script>

<PageHeader title="Service analytics">
  {#snippet sub()}
    {#if canView}
      Last <span class="v2-num">{totals.window_days}</span> days
      {#if totals.business_hours_applied}
        · measured in business hours ({totals.calendar_name})
      {/if}
    {:else}
      Service health
    {/if}
  {/snippet}
</PageHeader>

<SectionTabs set="tickets" />

{#if !canView}
  <div class="v2-pad" style="padding-top:40px">
    <!-- Centred, not left-hugging: this is all a non-admin sees on this page,
         so a capped card pinned to the left leaves the rest of a wide screen
         empty. margin-inline centres the column. -->
    <div class="v2-card" style="padding:20px 22px;max-width:520px;margin-inline:auto">
      <strong>This dashboard is for administrators.</strong>
      <p>
        Opened and closed volume, first-response attainment and the queue breakdown are
        whole-organisation figures, so they are limited to admins. Your own tickets are on the <a
          href={resolve('/tickets')}>Tickets</a
        > tab.
      </p>
    </div>
  </div>
{:else}
  <div class="v2-pad" style="padding-top:16px;flex:none">
    <div class="v2-stats">
      <StatCard label="Opened" value={count(totals.opened)} tone="ink" />
      <StatCard label="Closed" value={count(totals.closed)} tone="moss" />
      <StatCard
        label="Backlog"
        value={count(totals.open_now)}
        tone={net > 0 ? 'clay' : 'slate'}
        detail={net > 0
          ? `Grew by ${net} over the window`
          : net < 0
            ? `Shrank by ${Math.abs(net)} over the window`
            : 'Level over the window'}
      />
      <StatCard
        label="Median resolution"
        value={`${totals.median_resolution_hours}h`}
        tone="slate"
        detail="Median, not mean. One three-week ticket should not move it"
      />
    </div>
  </div>

  <div class="v2-scroll">
    <div class="v2-pad" style="padding-bottom:32px">
      <!-- Volume -->
      <div class="v2-card" style="padding:16px 18px 14px;margin-bottom:18px">
        <div style="display:flex;align-items:baseline;gap:14px;margin-bottom:14px">
          <div class="v2-label">Opened and closed, per day</div>
          <span class="v2-sub" style="font-size:11.5px;margin-left:auto">
            <i class="v2-swatch v2-swatch-in"></i>opened
            <i class="v2-swatch" style="margin-left:10px"></i>closed
          </span>
        </div>
        <div class="v2-cols">
          {#each data.volume as d (d.date)}
            <div class="v2-col" title="{shortDate(d.date)}, {d.opened} opened, {d.closed} closed">
              <i class="in" style="height:{(d.opened / peak) * 100}%"></i>
              <i class="out" style="height:{(d.closed / peak) * 100}%"></i>
            </div>
          {/each}
        </div>
        <div class="v2-cols-axis">
          {#each data.volume as d, i (d.date)}
            <!-- Every other label. Fourteen dates at 10px overlap; seven do not. -->
            <span>{i % 2 === 0 ? shortDate(d.date) : ''}</span>
          {/each}
        </div>
      </div>

      <div class="v2-split" style="margin-bottom:18px">
        <!-- First response -->
        <div class="v2-card" style="padding:16px 18px">
          <div class="v2-label" style="margin-bottom:4px">First response, against target</div>
          <p class="v2-sub" style="font-size:11.5px;margin:0 0 14px">
            Each priority carries its own target from the escalation policy, so each one is scored
            against its own promise.
          </p>
          {#each data.firstResponse as r (r.priority)}
            {@const pct = attainment(r)}
            <div style="margin-bottom:14px">
              <div
                style="display:flex;align-items:baseline;gap:8px;font-size:12.5px;margin-bottom:5px"
              >
                <b style="font-weight:600">{r.priority}</b>
                <span class="v2-sub" style="font-size:11.5px">
                  target {duration(r.target_minutes)} · median {duration(r.median_minutes)}
                </span>
                <span
                  class="v2-num"
                  style="margin-left:auto;font-weight:650;color:{pct == null
                    ? 'var(--v2-slate)'
                    : barColor(pct)}"
                >
                  {pct == null ? '—' : `${pct}%`}
                </span>
              </div>
              <div class="v2-bar">
                <i style="width:{pct ?? 0}%;background:{barColor(pct)}"></i>
              </div>
              <div class="v2-bar-legend">
                <span><span class="v2-num">{r.met}</span> in time</span>
                <span>
                  {#if r.missed}
                    <span class="v2-num" style="color:var(--v2-rust)">{r.missed}</span> late
                  {:else}
                    none late
                  {/if}
                </span>
              </div>
            </div>
          {/each}
        </div>

        <!-- Mix -->
        <div class="v2-card" style="padding:16px 18px">
          <div class="v2-label" style="margin-bottom:4px">What the queue is made of</div>
          <p class="v2-sub" style="font-size:11.5px;margin:0 0 14px">
            Incidents and problems are work; questions are usually a gap in the knowledge base.
          </p>
          {#each data.byType as t (t.case_type)}
            {@const share = Math.round(
              (t.count / data.byType.reduce((a, x) => a + x.count, 0)) * 100
            )}
            <div style="margin-bottom:13px">
              <div style="display:flex;align-items:baseline;font-size:12.5px;margin-bottom:5px">
                <span>{t.case_type}</span>
                <span class="v2-sub v2-num" style="margin-left:auto;font-size:12px">
                  {t.count} · {share}%
                </span>
              </div>
              <div class="v2-bar"><i style="width:{share}%"></i></div>
            </div>
          {/each}

          {#if data.byType.find((t) => t.case_type === 'Question')}
            <p class="v2-sub" style="font-size:11.5px;margin:16px 0 0">
              <a href={resolve('/solutions')} style="color:inherit">
                {data.byType.find((t) => t.case_type === 'Question').count} questions in this window
              </a>. The ones that repeat belong in the knowledge base.
            </p>
          {/if}
        </div>
      </div>

      <!-- Per agent -->
      <div class="v2-label" style="margin-bottom:10px">Who is carrying it</div>
      <div class="v2-table-wrap">
        <table class="v2-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th class="v2-r">Open now</th>
              <th class="v2-r">Closed this week</th>
              <th class="v2-r">Median first response</th>
              <th class="v2-r">Missed target</th>
            </tr>
          </thead>
          <tbody>
            {#each data.byAgent as a (a.id ?? a.name)}
              <tr>
                <td>
                  <span style="display:flex;gap:8px;align-items:center">
                    {#if a.id}
                      <Avatar name={a.name} size={24} />
                    {:else}
                      <!-- Unassigned is not a person and does not get a face. -->
                      <span
                        style="width:24px;height:24px;border-radius:50%;border:1px dashed var(--v2-line);flex:none"
                      ></span>
                    {/if}
                    <span class="v2-table-primary">{a.name}</span>
                  </span>
                </td>
                <td class="v2-r v2-num">{a.open}</td>
                <td class="v2-r v2-num">{a.closed_this_week}</td>
                <td class="v2-r v2-num">{duration(a.median_first_response_minutes)}</td>
                <td
                  class="v2-r v2-num"
                  style={a.breached ? 'color:var(--v2-rust);font-weight:600' : ''}
                >
                  {a.breached || '—'}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!--
      The clock these figures are measured on. Without it "answered in 4h" is
      ambiguous: a ticket opened at 17:20 on Friday and answered at 09:10 on
      Monday is either fifteen hours late or fifty minutes early, and only the
      calendar says which.
    -->
      <div style="display:flex;gap:9px;align-items:flex-start;margin-top:16px">
        <Clock size={15} style="color:var(--v2-slate);flex:none;margin-top:2px" />
        <p class="v2-sub" style="font-size:12px;margin:0">
          {#if totals.business_hours_applied}
            Elapsed time is counted inside {totals.calendar_name}, so evenings, weekends and
            holidays do not count against a target.
            <a href={resolve('/settings/business-hours')} style="color:inherit"
              >Change the calendar</a
            >.
          {:else}
            Elapsed time is counted around the clock, no business-hours calendar is set, so evenings
            and weekends count against a target.
            <a href={resolve('/settings/business-hours')} style="color:inherit">Set up a calendar</a
            >.
          {/if}
        </p>
      </div>
    </div>
  </div>
{/if}
