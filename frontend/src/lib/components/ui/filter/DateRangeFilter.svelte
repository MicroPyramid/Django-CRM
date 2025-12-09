<script>
  import { CalendarDays, ChevronDown, X } from '@lucide/svelte';
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
    label = '',
    placeholder = 'Select date range',
    class: className,
    onchange
  } = $props();

  let open = $state(false);
  let selectingEnd = $state(false);

  const todayDate = today(getLocalTimeZone());

  // Convert string dates to DateValue for calendar
  const startDateValue = $derived(startDate ? parseDate(startDate) : undefined);
  const endDateValue = $derived(endDate ? parseDate(endDate) : undefined);

  /** @type {{ label: string, getRange: () => { start: string, end: string } }[]} */
  const presets = [
    {
      label: 'Today',
      getRange: () => {
        const d = todayDate.toString();
        return { start: d, end: d };
      }
    },
    {
      label: 'Last 7 days',
      getRange: () => ({
        start: todayDate.subtract({ days: 7 }).toString(),
        end: todayDate.toString()
      })
    },
    {
      label: 'Last 30 days',
      getRange: () => ({
        start: todayDate.subtract({ days: 30 }).toString(),
        end: todayDate.toString()
      })
    },
    {
      label: 'This month',
      getRange: () => ({
        start: todayDate.set({ day: 1 }).toString(),
        end: todayDate.toString()
      })
    },
    {
      label: 'Last month',
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
    }
  ];

  const displayText = $derived.by(() => {
    if (!startDate && !endDate) return placeholder;
    if (startDate && endDate) {
      if (startDate === endDate) return formatDate(startDate);
      return `${formatDate(startDate)} - ${formatDate(endDate)}`;
    }
    if (startDate) return `From ${formatDate(startDate)}`;
    return `Until ${formatDate(endDate)}`;
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
   * @param {{ label: string, getRange: () => { start: string, end: string } }} preset
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

<div class={cn('flex flex-col gap-1', className)}>
  {#if label}
    <span class="text-muted-foreground text-xs font-medium">{label}</span>
  {/if}
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
          class={cn(
            'border-input bg-background hover:bg-accent/50 focus-visible:ring-ring flex h-9 w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm shadow-xs transition-colors focus-visible:ring-2 focus-visible:outline-none',
            hasValue && 'border-primary/50'
          )}
          {...props}
        >
          <div class="flex items-center gap-2">
            <CalendarDays class="text-muted-foreground h-4 w-4" />
            <span class={cn('truncate', !hasValue && 'text-muted-foreground')}>
              {displayText}
            </span>
          </div>
          <div class="flex items-center gap-1">
            {#if hasValue}
              <!-- svelte-ignore node_invalid_placement_ssr -->
              <span
                role="button"
                tabindex="0"
                onclick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  handleClear();
                }}
                onkeydown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    e.preventDefault();
                    handleClear();
                  }
                }}
                class="hover:bg-muted cursor-pointer rounded p-0.5"
              >
                <X class="h-3 w-3" />
              </span>
            {/if}
            <ChevronDown class="h-4 w-4 opacity-50" />
          </div>
        </button>
      {/snippet}
    </Popover.Trigger>
    <Popover.Content align="start" class="w-auto p-0">
      <div class="flex">
        <!-- Presets sidebar -->
        <div class="flex flex-col gap-1 border-r p-2">
          {#each presets as preset}
            <Button
              variant="ghost"
              size="sm"
              class="justify-start"
              onclick={() => handlePreset(preset)}
            >
              {preset.label}
            </Button>
          {/each}
        </div>
        <!-- Calendar -->
        <div class="p-2">
          <div class="text-muted-foreground mb-2 text-center text-sm">
            {#if selectingEnd}
              Select end date
            {:else}
              Select start date
            {/if}
          </div>
          <Calendar
            value={selectingEnd ? endDateValue : startDateValue}
            onValueChange={handleDateSelect}
          />
          {#if startDate && !endDate}
            <div class="text-muted-foreground mt-2 text-center text-xs">
              Start: {formatDate(startDate)}
            </div>
          {/if}
        </div>
      </div>
    </Popover.Content>
  </Popover.Root>
</div>
