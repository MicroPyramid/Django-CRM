<script>
  import { CalendarDays, ChevronDown, X, Clock, ArrowRight } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import Calendar from '$lib/components/ui/calendar/Calendar.svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { today, getLocalTimeZone, parseDate } from '@internationalized/date';

  /**
   * @type {{
   *   startDate?: string,
   *   endDate?: string,
   *   label?: string,
   *   placeholder?: string,
   *   class?: string,
   *   onchange?: (startDate: string, endDate: string) => void,
   * }}
   */
  let {
    startDate = $bindable(''),
    endDate = $bindable(''),
    label: _label = '',
    placeholder = 'Select dates',
    class: className,
    onchange
  } = $props();

  let open = $state(false);
  let selectingEnd = $state(false);

  const todayDate = today(getLocalTimeZone());

  // Convert string dates to DateValue for calendar
  const startDateValue = $derived(startDate ? parseDate(startDate) : undefined);
  const endDateValue = $derived(endDate ? parseDate(endDate) : undefined);

  /** @type {{ label: string, shortLabel: string, getRange: () => { start: string, end: string } }[]} */
  const presets = [
    {
      label: 'Today',
      shortLabel: 'Today',
      getRange: () => {
        const d = todayDate.toString();
        return { start: d, end: d };
      }
    },
    {
      label: 'Last 7 days',
      shortLabel: '7d',
      getRange: () => ({
        start: todayDate.subtract({ days: 7 }).toString(),
        end: todayDate.toString()
      })
    },
    {
      label: 'Last 30 days',
      shortLabel: '30d',
      getRange: () => ({
        start: todayDate.subtract({ days: 30 }).toString(),
        end: todayDate.toString()
      })
    },
    {
      label: 'This month',
      shortLabel: 'Month',
      getRange: () => ({
        start: todayDate.set({ day: 1 }).toString(),
        end: todayDate.toString()
      })
    },
    {
      label: 'Last month',
      shortLabel: 'Prev',
      getRange: () => {
        const lastMonth = todayDate.subtract({ months: 1 });
        const lastDayOfLastMonth = lastMonth
          .set({ day: 1 })
          .add({ months: 1 })
          .subtract({ days: 1 });
        return {
          start: lastMonth.set({ day: 1 }).toString(),
          end: lastDayOfLastMonth.toString()
        };
      }
    },
    {
      label: 'Last 90 days',
      shortLabel: '90d',
      getRange: () => ({
        start: todayDate.subtract({ days: 90 }).toString(),
        end: todayDate.toString()
      })
    }
  ];

  const displayText = $derived.by(() => {
    if (!startDate && !endDate) return placeholder;
    if (startDate && endDate) {
      if (startDate === endDate) return formatDate(startDate);
      return `${formatDateShort(startDate)} - ${formatDateShort(endDate)}`;
    }
    if (startDate) return `From ${formatDateShort(startDate)}`;
    return `Until ${formatDateShort(endDate)}`;
  });

  /**
   * @param {string} dateStr
   */
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  /**
   * @param {string} dateStr
   */
  function formatDateShort(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  /**
   * @param {{ label: string, shortLabel: string, getRange: () => { start: string, end: string } }} preset
   */
  function handlePreset(preset) {
    const { start, end } = preset.getRange();
    startDate = start;
    endDate = end;
    onchange?.(start, end);
    open = false;
  }

  /**
   * @param {import('@internationalized/date').DateValue | undefined} dateValue
   */
  function handleDateSelect(dateValue) {
    if (!dateValue) return;
    const dateStr = dateValue.toString();

    if (!selectingEnd) {
      startDate = dateStr;
      endDate = '';
      selectingEnd = true;
    } else {
      // Ensure end is after start
      if (dateStr < startDate) {
        endDate = startDate;
        startDate = dateStr;
      } else {
        endDate = dateStr;
      }
      selectingEnd = false;
      onchange?.(startDate, endDate);
      open = false;
    }
  }

  function handleClear() {
    startDate = '';
    endDate = '';
    selectingEnd = false;
    onchange?.('', '');
  }

  const hasValue = $derived(!!startDate || !!endDate);
</script>

<Popover.Root
    bind:open
    onOpenChange={(o) => {
      if (!o) selectingEnd = false;
    }}
  >
    <Popover.Trigger asChild class="">
      {#snippet child({ props })}
        <button
          type="button"
          {...props}
          class={cn(
            'inline-flex h-7 items-center gap-1.5 rounded-[var(--r-sm)] border px-2.5 text-[11.5px] font-medium leading-none transition-colors focus:outline-none focus:ring-1 focus:ring-[color:var(--ring)]',
            hasValue
              ? 'border-[color:var(--violet)]/40 bg-[color:var(--violet-soft)] text-[color:var(--violet-soft-text)]'
              : 'border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)] hover:bg-[color:var(--bg-hover)]',
            className
          )}
        >
          <CalendarDays class="size-3.5 shrink-0" />
          <span class="truncate">{displayText}</span>
          {#if hasValue}
            <span
              role="button"
              tabindex="0"
              onclick={(e) => { e.stopPropagation(); e.preventDefault(); handleClear(); }}
              onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.stopPropagation(); e.preventDefault(); handleClear(); } }}
              class="-mr-1 ml-0.5 flex size-3.5 shrink-0 items-center justify-center rounded-sm hover:bg-[color:var(--violet)]/15"
              aria-label="Clear filter"
            >
              <X class="size-3" />
            </span>
          {:else}
            <ChevronDown class="size-3.5 shrink-0 opacity-60" />
          {/if}
        </button>
      {/snippet}
    </Popover.Trigger>

    <Popover.Content
      align="start"
      sideOffset={4}
      class="overflow-hidden rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-card)] p-0 shadow-lg shadow-black/5"
    >
      <div class="flex">
        <!-- Presets sidebar -->
        <div
          class={cn(
            'border-border/40 flex flex-col gap-0.5 border-r p-2',
            'bg-muted/30 dark:border-white/[0.04] dark:bg-white/[0.02]'
          )}
        >
          <div class="mb-1 px-2 py-1">
            <span
              class="text-muted-foreground/60 text-[10px] font-semibold tracking-wider uppercase"
            >
              Quick select
            </span>
          </div>
          {#each presets as preset, i}
            <Button
              variant="ghost"
              size="sm"
              class={cn(
                'h-8 justify-start px-3 text-xs font-medium',
                'text-muted-foreground hover:text-foreground',
                'hover:bg-primary/10 dark:hover:bg-primary/20',
                'transition-all duration-150',
                'animate-in fade-in slide-in-from-left-1'
              )}
              style="animation-delay: {i * 30}ms"
              onclick={() => handlePreset(preset)}
            >
              <Clock class="mr-2 h-3 w-3 opacity-50" />
              {preset.label}
            </Button>
          {/each}
        </div>

        <!-- Calendar section -->
        <div class="p-3">
          <!-- Date selection status -->
          <div
            class={cn(
              'mb-3 flex items-center justify-center gap-2',
              'bg-muted/50 rounded-lg px-3 py-2',
              'dark:bg-white/[0.03]'
            )}
          >
            {#if startDate}
              <div class="flex items-center gap-1.5">
                <div class="bg-primary h-2 w-2 rounded-full"></div>
                <span class="text-foreground text-xs font-medium">
                  {formatDateShort(startDate)}
                </span>
              </div>
            {:else}
              <span class="text-muted-foreground text-xs">Start date</span>
            {/if}

            <ArrowRight class="text-muted-foreground/50 h-3 w-3" />

            {#if endDate}
              <div class="flex items-center gap-1.5">
                <div class="bg-primary h-2 w-2 rounded-full"></div>
                <span class="text-foreground text-xs font-medium">
                  {formatDateShort(endDate)}
                </span>
              </div>
            {:else}
              <span class="text-muted-foreground text-xs">
                {selectingEnd ? 'Select end' : 'End date'}
              </span>
            {/if}
          </div>

          <!-- Selection hint -->
          <div
            class={cn(
              'mb-2 text-center text-xs font-medium',
              'transition-colors duration-200',
              selectingEnd ? 'text-primary' : 'text-muted-foreground'
            )}
          >
            {#if selectingEnd}
              <span class="animate-pulse">Click to select end date</span>
            {:else}
              Select start date
            {/if}
          </div>

          <!-- Calendar -->
          <div class="date-calendar-wrapper">
            <Calendar
              value={selectingEnd ? endDateValue : startDateValue}
              onValueChange={handleDateSelect}
            />
          </div>
        </div>
      </div>
    </Popover.Content>
  </Popover.Root>
