<script>
  /**
   * @type {{
   *   points: Array<{ x: string, y: number | null }>,
   *   width?: number,
   *   height?: number,
   *   color?: string,
   *   format?: (n: number) => string,
   *   label?: string,
   * }}
   */
  let {
    points,
    width = 320,
    height = 80,
    color = 'var(--color-primary-default)',
    format = (n) => String(Math.round(n)),
    label = ''
  } = $props();

  const padding = 6;

  const numericPoints = $derived(
    points.filter((p) => p.y !== null && Number.isFinite(p.y))
  );
  const yMax = $derived(
    Math.max(1, ...numericPoints.map((p) => /** @type {number} */ (p.y)))
  );
  const linePath = $derived.by(() => {
    if (numericPoints.length === 0) return '';
    const stepX = (width - 2 * padding) / Math.max(1, points.length - 1);
    return points
      .map((p, i) => {
        const x = padding + i * stepX;
        if (p.y === null || !Number.isFinite(p.y)) return null;
        const y = height - padding - (p.y / yMax) * (height - 2 * padding);
        return `${x},${y}`;
      })
      .filter((v) => v !== null)
      .map((v, i) => `${i === 0 ? 'M' : 'L'}${v}`)
      .join(' ');
  });
  const areaPath = $derived.by(() => {
    if (!linePath) return '';
    const stepX = (width - 2 * padding) / Math.max(1, points.length - 1);
    const firstIdx = points.findIndex((p) => p.y !== null && Number.isFinite(p.y));
    const lastIdx = (() => {
      for (let i = points.length - 1; i >= 0; i--) {
        if (points[i].y !== null && Number.isFinite(points[i].y)) return i;
      }
      return -1;
    })();
    if (firstIdx < 0 || lastIdx < 0) return '';
    const firstX = padding + firstIdx * stepX;
    const lastX = padding + lastIdx * stepX;
    return `${linePath} L${lastX},${height - padding} L${firstX},${height - padding} Z`;
  });
</script>

<div class="text-[var(--text-secondary)]">
  {#if numericPoints.length === 0}
    <div class="flex h-20 items-center justify-center text-xs italic">
      Not enough data for the selected window.
    </div>
  {:else}
    <svg
      viewBox="0 0 {width} {height}"
      class="h-20 w-full"
      role="img"
      aria-label={label || 'sparkline'}
    >
      <path d={areaPath} fill={color} fill-opacity="0.12" />
      <path
        d={linePath}
        fill="none"
        stroke={color}
        stroke-width="1.6"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
    </svg>
    <div class="mt-1 flex justify-between text-[10px]">
      <span>{points[0]?.x}</span>
      <span class="font-medium">peak: {format(yMax)}</span>
      <span>{points[points.length - 1]?.x}</span>
    </div>
  {/if}
</div>
