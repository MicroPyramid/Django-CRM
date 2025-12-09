<script>
  import { Calendar } from 'bits-ui';
  import { ChevronLeft, ChevronRight } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import { today, getLocalTimeZone } from '@internationalized/date';

  /**
   * @type {{
   *   value?: import('@internationalized/date').DateValue | undefined,
   *   onValueChange?: (value: import('@internationalized/date').DateValue | undefined) => void,
   *   class?: string,
   * }}
   */
  let { value = $bindable(), onValueChange, class: className } = $props();

  // Placeholder controls which month/year is displayed
  let placeholder = $state(value || today(getLocalTimeZone()));

  // Sync placeholder when value changes
  $effect(() => {
    if (value) {
      placeholder = value;
    }
  });

  // Generate year options (100 years back, 10 years forward)
  const currentYear = today(getLocalTimeZone()).year;
  const years = Array.from({ length: 111 }, (_, i) => currentYear - 100 + i);

  const months = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
  ];
</script>

<Calendar.Root
  type="single"
  weekdayFormat="short"
  fixedWeeks={true}
  bind:value
  bind:placeholder
  {onValueChange}
  class={cn('p-3', className)}
>
  {#snippet children({ months: calendarMonths, weekdays })}
    <Calendar.Header class="relative flex w-full items-center justify-between gap-1 pb-2">
      <Calendar.PrevButton
        class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-gray-200 bg-transparent p-0 opacity-50 transition-opacity hover:opacity-100 dark:border-gray-700"
      >
        <ChevronLeft class="h-4 w-4" />
      </Calendar.PrevButton>

      <div class="flex items-center gap-1">
        <!-- Month Select -->
        <select
          class="h-7 rounded-md border border-gray-200 bg-transparent px-2 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-700"
          value={placeholder?.month}
          onchange={(e) => {
            const target = /** @type {HTMLSelectElement} */ (e.target);
            if (placeholder) {
              placeholder = placeholder.set({ month: parseInt(target.value) });
            }
          }}
        >
          {#each months as month, i}
            <option value={i + 1}>{month}</option>
          {/each}
        </select>

        <!-- Year Select -->
        <select
          class="h-7 rounded-md border border-gray-200 bg-transparent px-2 text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-700"
          value={placeholder?.year}
          onchange={(e) => {
            const target = /** @type {HTMLSelectElement} */ (e.target);
            if (placeholder) {
              placeholder = placeholder.set({ year: parseInt(target.value) });
            }
          }}
        >
          {#each years as year}
            <option value={year}>{year}</option>
          {/each}
        </select>
      </div>

      <Calendar.NextButton
        class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-gray-200 bg-transparent p-0 opacity-50 transition-opacity hover:opacity-100 dark:border-gray-700"
      >
        <ChevronRight class="h-4 w-4" />
      </Calendar.NextButton>
    </Calendar.Header>

    {#each calendarMonths as month}
      <Calendar.Grid class="w-full border-collapse space-y-1">
        <Calendar.GridHead>
          <Calendar.GridRow class="flex">
            {#each weekdays as day}
              <Calendar.HeadCell
                class="w-8 rounded-md text-[0.8rem] font-normal text-gray-500 dark:text-gray-400"
              >
                {day.slice(0, 2)}
              </Calendar.HeadCell>
            {/each}
          </Calendar.GridRow>
        </Calendar.GridHead>
        <Calendar.GridBody>
          {#each month.weeks as week}
            <Calendar.GridRow class="mt-2 flex w-full">
              {#each week as date}
                <Calendar.Cell {date} month={month.value} class="relative p-0 text-center text-sm">
                  <Calendar.Day
                    class="inline-flex h-8 w-8 items-center justify-center rounded-md p-0 text-sm font-normal transition-colors hover:bg-gray-100 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 data-[disabled]:text-gray-400 data-[outside-month]:text-gray-400 data-[outside-month]:opacity-50 data-[selected]:bg-blue-600 data-[selected]:text-white data-[today]:bg-gray-100 data-[today]:font-semibold dark:hover:bg-gray-800 dark:data-[selected]:bg-blue-600 dark:data-[today]:bg-gray-800"
                  >
                    {date.day}
                  </Calendar.Day>
                </Calendar.Cell>
              {/each}
            </Calendar.GridRow>
          {/each}
        </Calendar.GridBody>
      </Calendar.Grid>
    {/each}
  {/snippet}
</Calendar.Root>
