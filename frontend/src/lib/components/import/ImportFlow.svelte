<script>
  import { onDestroy } from 'svelte';
  import { deserialize } from '$app/forms';
  import { resolve } from '$app/paths';
  import { AlertCircle, CheckCircle2, Download, FileSpreadsheet, Upload } from '@lucide/svelte';
  import { IMPORT_ENTITIES } from '#lib/import/entities.js';
  import {
    droppedLines,
    hasAnyMatch,
    mappingPayload,
    setColumnField,
    skippedRowsCsv,
    suggestLeads,
    summaryLine
  } from '#lib/import/mapping.js';
  import { downloadCsv } from '#lib/utils/csv.js';
  import { asInternalPath } from '#lib/utils/paths.js';

  /**
   * Import a spreadsheet of contacts or leads: choose a file, check how its
   * columns match the fields, import.
   *
   * The first preview lets the server guess the columns (`mapping=auto`).
   * Changing a column's field re-runs the preview with the full choice, 400 ms
   * after the last change, since preview and commit share a per-user throttle.
   * The import sends the same choice the preview showed. Both go through the
   * list page's form actions (`IMPORT_ENTITIES[entity].actionPath`), so the
   * flow works from any page.
   *
   * `singular` and `plural` override the entity's default words (the leads
   * drawer passes the org's terminology). `onDone(created)` runs after a
   * successful import. `onUseLeads`, when given, turns the "import as leads"
   * suggestion into a button; it must switch `entity` to `leads`, and the
   * flow then previews the same file again. Without it the suggestion is text.
   *
   * @type {{
   *   entity: 'contacts' | 'leads',
   *   singular?: string,
   *   plural?: string,
   *   onDone?: (created: number) => void,
   *   onUseLeads?: () => void
   * }}
   */
  let { entity, singular, plural, onDone, onUseLeads } = $props();

  /** @typedef {import('#lib/import/mapping.js').Column} Column */
  /** @typedef {import('#lib/import/mapping.js').Skipped} Skipped */
  /**
   * @typedef {{
   *   columns: (Column & { header: string, samples: string[] })[],
   *   fields: { name: string, label: string, required: boolean }[],
   *   skipped: Skipped[],
   *   dropped: { field: string, count: number }[],
   *   summary: { total: number, valid: number, skipped: number }
   * }} Preview
   */

  const DEBOUNCE_MS = 400;
  const SKIPPED_SHOWN = 50;
  const TOO_LARGE = 'This file is too large to upload. Split it into smaller files.';
  const OFFLINE = 'Could not reach BottleCRM. Check your connection and try again.';

  let cfg = $derived(IMPORT_ENTITIES[entity]);
  let nouns = $derived({ singular: singular ?? cfg.singular, plural: plural ?? cfg.plural });

  let step = $state(/** @type {'select' | 'match' | 'done'} */ ('select'));
  /** @type {File | null} */
  let file = $state(null);
  /** @type {HTMLInputElement | null} */
  let fileInput = $state(null);
  let dragOver = $state(false);
  let loading = $state(false);
  let committing = $state(false);
  /** @type {string | null} */
  let error = $state(null);
  /** @type {Preview | null} */
  let preview = $state(null);
  /** @type {Preview['columns']} */
  let columns = $state([]);
  /** The `mapping` the shown preview was computed for. */
  let previewed = $state('');
  let showEmpty = $state(false);
  /** @type {{ created: number, skipped?: Skipped[], dropped?: { field: string, count: number }[] } | null} */
  let result = $state(null);

  /** Only the latest preview request may change the screen. */
  let seq = 0;
  /** @type {ReturnType<typeof setTimeout> | undefined} */
  let timer;
  let destroyed = false;
  onDestroy(() => {
    destroyed = true;
    clearTimeout(timer);
  });

  let stale = $derived(step === 'match' && mappingPayload(columns) !== previewed);
  let canImport = $derived(
    !!preview && !stale && !loading && !committing && preview.summary.valid > 0
  );
  // A column with no value in any row cannot import anything. Exports such as
  // Outlook's carry dozens of them, so they wait behind a toggle.
  let shown = $derived(showEmpty ? columns : columns.filter((c) => c.field || c.samples.length));
  let hiddenCount = $derived(columns.length - shown.length);

  /**
   * @param {'importPreview' | 'importCommit'} action
   * @param {string} mapping
   */
  async function post(action, mapping) {
    const fd = new FormData();
    fd.append('file', /** @type {File} */ (file));
    fd.append('mapping', mapping);
    const res = await fetch(`${resolve(asInternalPath(cfg.actionPath))}?/${action}`, {
      method: 'POST',
      body: fd
    });
    // The Node adapter refuses a body over BODY_SIZE_LIMIT (512K by default;
    // the image sets 6M) with a plain-text
    // 413 before the action runs, which `deserialize` cannot parse.
    if (res.status === 413) return { type: 'failure', data: { importError: TOO_LARGE } };
    return /** @type {any} */ (deserialize(await res.text()));
  }

  /** @param {any} out @param {string} fallback */
  function failureText(out, fallback) {
    return out?.type === 'failure' && out.data?.importError
      ? String(out.data.importError)
      : fallback;
  }

  /** @param {string} mapping `auto` for the server's guess, else `mappingPayload` */
  async function runPreview(mapping) {
    if (!file) return;
    const mine = ++seq;
    loading = true;
    error = null;
    try {
      const out = await post('importPreview', mapping);
      if (mine !== seq || destroyed) return;
      const body = out.type === 'success' ? out.data?.importPreview : null;
      if (body?.columns) {
        preview = body;
        if (mapping === 'auto') columns = body.columns;
        previewed = mapping === 'auto' ? mappingPayload(body.columns) : mapping;
        step = 'match';
      } else {
        error = failureText(out, 'The preview did not go through. Try again.');
      }
    } catch {
      if (mine === seq && !destroyed) error = OFFLINE;
    } finally {
      if (mine === seq) loading = false;
    }
  }

  /** @param {File | null | undefined} f */
  function choose(f) {
    if (!f) return;
    clearTimeout(timer);
    file = f;
    preview = null;
    columns = [];
    previewed = '';
    showEmpty = false;
    step = 'select';
    runPreview('auto');
  }

  function startOver() {
    clearTimeout(timer);
    seq++;
    file = null;
    preview = null;
    columns = [];
    previewed = '';
    error = null;
    loading = false;
    step = 'select';
  }

  /** @param {number} index @param {string} value '' for Don't import */
  function change(index, value) {
    columns = setColumnField(columns, index, value || null);
    // A new choice replaces whatever the last failed request said, as on the
    // phone. Reverting to the previewed choice sends nothing, so an error
    // left here would outlive its cause.
    error = null;
    clearTimeout(timer);
    timer = setTimeout(() => {
      const mapping = mappingPayload(columns);
      // A request still in flight was for another choice; this one replaces it.
      if (mapping !== previewed || loading) runPreview(mapping);
    }, DEBOUNCE_MS);
  }

  function useLeads() {
    onUseLeads?.();
    choose(file);
  }

  async function commit() {
    if (!canImport || !preview) return;
    committing = true;
    error = null;
    try {
      const out = await post('importCommit', mappingPayload(columns));
      if (out.type === 'success' && out.data?.importCommit) {
        const done = out.data.importCommit;
        if (!destroyed) {
          // No pending or in-flight preview may pull the flow back from done.
          clearTimeout(timer);
          seq++;
          result = done;
          step = 'done';
        }
        // Even when the flow was closed mid-import: the records exist now, so
        // the caller still refreshes.
        onDone?.(done.created);
        return;
      }
      if (destroyed) return;
      const skipped = out.type === 'failure' ? out.data?.importSkipped : null;
      if (Array.isArray(skipped) && skipped.length) {
        // Nothing was importable after all, e.g. the records arrived since the
        // preview. Show the import's own account; the summary line says why.
        preview = {
          ...preview,
          skipped,
          dropped: [],
          summary: { total: skipped.length, valid: 0, skipped: skipped.length }
        };
      } else {
        error = failureText(out, 'The import did not go through. Try again.');
      }
    } catch {
      if (!destroyed) error = OFFLINE;
    } finally {
      committing = false;
    }
  }

  function downloadTemplate() {
    const csv = [
      cfg.templateHeaders.join(','),
      cfg.templateExample.map((v) => (v.includes(',') ? `"${v}"` : v)).join(',')
    ].join('\n');
    downloadCsv(csv, `${entity}-import-template.csv`);
  }

  /** @param {Skipped[]} skipped */
  function downloadSkipped(skipped) {
    // A byte-order mark, as the server's exports carry, so Excel reads
    // accented names as UTF-8. The importer reads the file with or without it.
    const csv = skippedRowsCsv(
      columns.map((c) => c.header),
      skipped
    );
    downloadCsv(`\uFEFF${csv}`, `${entity}-skipped-rows.csv`);
  }

  /** @param {number} n */
  function rows(n) {
    return `${n} ${n === 1 ? 'row' : 'rows'}`;
  }
</script>

<div class="v2-root flow">
  {#if step === 'select'}
    <button
      type="button"
      class="drop"
      class:over={dragOver}
      disabled={loading}
      ondragover={(e) => {
        e.preventDefault();
        dragOver = true;
      }}
      ondragleave={() => (dragOver = false)}
      ondrop={(e) => {
        e.preventDefault();
        dragOver = false;
        choose(e.dataTransfer?.files?.[0]);
      }}
      onclick={() => fileInput?.click()}
    >
      {#if loading && file}
        <span class="v2-spin"></span>
        <span class="drop-text"><b>Reading {file.name}</b></span>
      {:else}
        <Upload />
        <span class="drop-text">
          <b>Choose a spreadsheet</b>
          <span>or drop it here. .xlsx or .csv, up to 5 MB.</span>
        </span>
      {/if}
    </button>
    <input
      bind:this={fileInput}
      type="file"
      accept=".csv,.xlsx"
      hidden
      onchange={(e) => {
        const f = e.currentTarget.files?.[0];
        // Cleared so picking the same file again still fires a change.
        e.currentTarget.value = '';
        choose(f);
      }}
    />
    <p class="v2-hint">
      Any column names work. You'll check how they match before anything is imported.
    </p>
    {#if error}
      <p class="v2-error" role="alert"><AlertCircle size={14} />{error}</p>
    {/if}
    <p class="v2-hint">
      Starting from scratch?
      <button type="button" class="link" onclick={downloadTemplate}>Download a template</button>
    </p>
  {:else if step === 'match' && preview && file}
    <div class="file">
      <FileSpreadsheet />
      <span class="file-name">{file.name}</span>
      <button type="button" class="v2-btn v2-btn-quiet" disabled={committing} onclick={startOver}>
        Choose another file
      </button>
    </div>

    {#if !hasAnyMatch(columns)}
      <p class="note" role="status">
        We couldn't match any columns. Make sure the first row of your sheet holds the column names.
      </p>
    {/if}

    <div class="v2-table-wrap cols">
      <table class="v2-table">
        <thead>
          <tr>
            <th>Column in your file</th>
            <th>Sample values</th>
            <th>Import as</th>
          </tr>
        </thead>
        <tbody>
          {#each shown as c (c.index)}
            {@const name = c.header || `Column ${c.index + 1}`}
            <tr>
              <td class="col-name">{name}</td>
              <td class="col-samples">
                {#if c.samples.length}{c.samples.join(' · ')}{:else}<span class="v2-muted"
                    >No values</span
                  >{/if}
              </td>
              <td class="col-pick">
                <select
                  class="v2-input"
                  disabled={committing}
                  aria-label="Import {name} as"
                  value={c.field ?? ''}
                  onchange={(e) => change(c.index, e.currentTarget.value)}
                >
                  <option value="">Don't import</option>
                  {#each preview.fields as f (f.name)}
                    <option value={f.name}>{f.label}</option>
                  {/each}
                </select>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    {#if hiddenCount > 0 || showEmpty}
      <button type="button" class="link" onclick={() => (showEmpty = !showEmpty)}>
        {showEmpty
          ? 'Hide the empty columns'
          : `Show ${hiddenCount} empty column${hiddenCount === 1 ? '' : 's'}`}
      </button>
    {/if}

    <div class="report">
      <!-- After a failed preview nothing is updating until "Try again". -->
      {#if loading || (stale && !error)}
        <p class="v2-hint busy"><span class="v2-spin"></span>Updating the preview</p>
      {/if}
      {#each droppedLines(preview.dropped, preview.fields) as line (line)}
        <p class="v2-hint">{line}</p>
      {/each}
      {#if preview.skipped.length}
        <ul class="skipped">
          {#each preview.skipped.slice(0, SKIPPED_SHOWN) as s (s.row)}
            <li><span class="v2-num">Row {s.row}</span> {s.message}</li>
          {/each}
        </ul>
        {#if preview.skipped.length > SKIPPED_SHOWN}
          <p class="v2-hint">
            {rows(preview.skipped.length - SKIPPED_SHOWN)} more are in the download.
          </p>
        {/if}
        <div>
          <button
            type="button"
            class="v2-btn"
            onclick={() => downloadSkipped(/** @type {Preview} */ (preview).skipped)}
          >
            <Download />Download skipped rows
          </button>
        </div>
      {/if}
      {#if suggestLeads(entity, preview.skipped)}
        <p class="note">
          Some rows were skipped for a missing first or last name. A lead needs only one of the two,
          so this file could go in as leads instead.
          {#if onUseLeads}
            <button type="button" class="v2-btn" disabled={committing} onclick={useLeads}>
              Import as leads instead
            </button>
          {/if}
        </p>
      {/if}
      <p class="summary" aria-live="polite">{summaryLine(nouns, preview)}</p>
    </div>

    {#if error}
      <p class="v2-error" role="alert">
        <AlertCircle size={14} />{error}
        {#if stale && !loading}
          <button type="button" class="link" onclick={() => runPreview(mappingPayload(columns))}
            >Try again</button
          >
        {/if}
      </p>
    {/if}

    <div class="actions">
      <button type="button" class="v2-btn v2-btn-primary" disabled={!canImport} onclick={commit}>
        {#if committing}<span class="v2-spin"></span>{/if}
        Import {preview.summary.valid}
        {preview.summary.valid === 1 ? nouns.singular : nouns.plural}
      </button>
    </div>
  {:else if step === 'done' && result}
    <p class="v2-auth-note v2-auth-note-ok" role="status">
      <CheckCircle2 />
      <span>
        Imported <b>{result.created}</b>
        {result.created === 1 ? nouns.singular : nouns.plural}.
      </span>
    </p>
    {#each droppedLines(result.dropped ?? [], preview?.fields ?? []) as line (line)}
      <p class="v2-hint">{line}</p>
    {/each}
    {#if result.skipped?.length}
      {@const skipped = result.skipped}
      <p class="v2-hint">{rows(skipped.length)} skipped.</p>
      <div>
        <button type="button" class="v2-btn" onclick={() => downloadSkipped(skipped)}>
          <Download />Download skipped rows
        </button>
      </div>
    {/if}
  {/if}
</div>

<style>
  /* `.v2-root` brings the v2 tokens into a dialog, which portals outside the
     app shell; the dialog keeps its own background. */
  .flow {
    background: transparent;
    display: grid;
    gap: 12px;
    min-width: 0;
  }
  .flow p {
    margin: 0;
  }
  .drop {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
    min-height: 88px;
    padding: 18px;
    border: 1.5px dashed var(--v2-line);
    border-radius: var(--v2-radius);
    background: var(--v2-line-soft);
    color: var(--v2-ink);
    font: inherit;
    text-align: left;
    cursor: pointer;
  }
  .drop:hover,
  .drop.over {
    border-color: var(--v2-slate);
    background: var(--v2-card);
  }
  .drop:disabled {
    cursor: progress;
  }
  .drop :global(svg) {
    width: 22px;
    height: 22px;
    flex: none;
    color: var(--v2-slate);
  }
  .drop-text {
    display: grid;
    gap: 2px;
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .drop-text span {
    font-size: 12.5px;
    color: var(--v2-slate);
  }
  .link {
    border: 0;
    padding: 0;
    background: none;
    font: inherit;
    color: var(--v2-ink);
    text-decoration: underline;
    cursor: pointer;
    justify-self: start;
  }
  .file {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .file :global(svg) {
    width: 18px;
    height: 18px;
    color: var(--v2-slate);
  }
  .file-name {
    font-weight: 600;
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .note {
    padding: 10px 12px;
    border-radius: 9px;
    background: var(--v2-ember-soft);
    font-size: 13px;
    line-height: 1.45;
  }
  .note .v2-btn {
    margin-top: 8px;
  }
  .cols {
    margin: 0;
  }
  .cols td.col-name,
  .cols td.col-samples {
    white-space: normal;
    overflow-wrap: anywhere;
    padding-top: 8px;
    padding-bottom: 8px;
  }
  .cols td.col-name {
    font-weight: 600;
    width: 30%;
  }
  .cols td.col-samples {
    color: var(--v2-slate);
    font-size: 12.5px;
  }
  .cols td.col-pick {
    width: 32%;
  }
  .cols select {
    min-width: 170px;
    padding: 7px 9px;
  }
  .report {
    display: grid;
    gap: 8px;
  }
  .busy {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .busy .v2-spin {
    width: 12px;
    height: 12px;
  }
  .skipped {
    margin: 0;
    padding: 8px 12px;
    list-style: none;
    max-height: 160px;
    overflow-y: auto;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    font-size: 12.5px;
    overflow-wrap: anywhere;
  }
  .skipped li + li {
    margin-top: 4px;
  }
  .skipped .v2-num {
    color: var(--v2-slate);
    margin-right: 6px;
  }
  .summary {
    font-weight: 600;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
  }
  .flow .v2-error {
    align-items: center;
    flex-wrap: wrap;
  }

  @media (max-width: 768px) {
    .flow .v2-btn,
    .cols select {
      min-height: 44px;
    }
    .link {
      min-height: 44px;
    }
    .actions .v2-btn-primary {
      width: 100%;
      justify-content: center;
    }
    /* `.v2-table` rows are already cards here; the column name keeps the
       whole first line (no status tag to make room for) and the field picker
       takes a line of its own. */
    .cols td.col-name {
      width: auto;
      padding: 0;
    }
    .cols td.col-samples {
      padding: 0;
    }
    .cols td.col-pick {
      display: block;
      width: auto;
      margin: 8px 0 0;
    }
    .cols select {
      width: 100%;
      min-width: 0;
    }
  }
</style>
