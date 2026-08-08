import { SvelteURLSearchParams } from 'svelte/reactivity';
/**
 * In-app notifications store.
 *
 * Single source of truth for the bell badge, the panel list, and
 * svelte-sonner toasts. Talks to the SvelteKit proxies under
 * `/api/notifications/...` (which forward to Django with the JWT cookie).
 *
 * Delivery is by polling `?since=<iso>`. This replaced an EventSource stream
 * on 2026-08-03. The SSE endpoint was the only async code in the backend, so
 * it forced the entire deployment onto ASGI, where each in-flight request
 * takes its own database connection with no ceiling. It was also silently
 * delivering nothing under a correctly configured database role, and the
 * `error` handler here was an empty placeholder, so in practice the bell
 * already only updated on page load. Polling is strictly better than that and
 * costs about one concurrent request per 900 open tabs.
 */

import { toast } from 'svelte-sonner';

const PANEL_LIMIT = 20;

// Delivery latency ceiling. Notifications here are "you were assigned a lead",
// not chat, so tens of seconds is fine and the load is flat and predictable
// rather than proportional to how long tabs stay open.
const POLL_INTERVAL_MS = 45_000;

// Verbs that should fire an in-page toast in addition to bumping the badge.
// Keep this conservative: too noisy and users mute the channel.
// NOTE: `case.*` keys are backend wire-format strings. Do not rename.
const TOAST_VERBS = new Set([
  'case.mentioned',
  'case.assigned',
  'case.sla_breached',
  'support.replied'
]);

class NotificationsStore {
  notifications = $state([]);
  unread_count = $state(0);
  total_count = $state(0);
  loading = $state(false);
  error = $state('');

  /** @type {ReturnType<typeof setInterval> | null} */
  #timer = null;
  /** @type {boolean} */
  #started = false;
  /** @type {boolean} */
  #polling = false;
  /** High-water mark: `created_at` of the newest row we have ingested. */
  /** @type {string | null} */
  #since = null;
  /** @type {(() => void) | null} */
  #onVisibility = null;

  async fetch() {
    this.loading = true;
    this.error = '';
    try {
      const res = await window.fetch(`/api/notifications/?limit=${PANEL_LIMIT}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.notifications = data.results || [];
      this.unread_count = data.unread_count ?? 0;
      this.total_count = data.count ?? this.notifications.length;
      this.#advanceSince(this.notifications);
    } catch (err) {
      console.error('notifications fetch failed', err);
      this.error = 'Could not load notifications.';
    } finally {
      this.loading = false;
    }
  }

  /** @param {string} id */
  async markRead(id) {
    const idx = this.notifications.findIndex((n) => n.id === id);
    if (idx === -1) return;
    if (this.notifications[idx].read_at) return; // already read
    // Optimistic
    const before = this.notifications[idx].read_at;
    this.notifications[idx] = { ...this.notifications[idx], read_at: new Date().toISOString() };
    this.unread_count = Math.max(0, this.unread_count - 1);
    try {
      const res = await window.fetch(`/api/notifications/${id}/read/`, { method: 'POST' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      console.error('notifications markRead failed', err);
      // Roll back
      this.notifications[idx] = { ...this.notifications[idx], read_at: before };
      this.unread_count += 1;
    }
  }

  async markAllRead() {
    const now = new Date().toISOString();
    const snapshot = this.notifications.map((n) => ({ ...n }));
    const prevUnread = this.unread_count;
    this.notifications = this.notifications.map((n) => (n.read_at ? n : { ...n, read_at: now }));
    this.unread_count = 0;
    try {
      const res = await window.fetch('/api/notifications/read-all/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      console.error('notifications markAllRead failed', err);
      this.notifications = snapshot;
      this.unread_count = prevUnread;
    }
  }

  /** @param {string} id */
  async remove(id) {
    const idx = this.notifications.findIndex((n) => n.id === id);
    if (idx === -1) return;
    const removed = this.notifications[idx];
    this.notifications = this.notifications.filter((n) => n.id !== id);
    if (!removed.read_at) this.unread_count = Math.max(0, this.unread_count - 1);
    this.total_count = Math.max(0, this.total_count - 1);
    try {
      const res = await window.fetch(`/api/notifications/${id}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      console.error('notifications remove failed', err);
      this.notifications = [...this.notifications, removed].sort(
        (a, b) => new Date(b.created_at).valueOf() - new Date(a.created_at).valueOf()
      );
      if (!removed.read_at) this.unread_count += 1;
      this.total_count += 1;
    }
  }

  start() {
    if (this.#started || typeof window === 'undefined') return;
    this.#started = true;
    this.fetch();
    this.#timer = setInterval(() => this.#poll(), POLL_INTERVAL_MS);

    // Don't poll a tab nobody is looking at, and catch up immediately when
    // the user comes back rather than making them wait out the interval.
    this.#onVisibility = () => {
      if (document.visibilityState === 'visible') this.#poll();
    };
    document.addEventListener('visibilitychange', this.#onVisibility);
  }

  stop() {
    if (this.#timer !== null) {
      clearInterval(this.#timer);
      this.#timer = null;
    }
    if (this.#onVisibility) {
      document.removeEventListener('visibilitychange', this.#onVisibility);
      this.#onVisibility = null;
    }
    this.#started = false;
  }

  async #poll() {
    // Skip while hidden, and never let a slow request stack up behind itself.
    if (this.#polling || document.visibilityState === 'hidden') return;
    this.#polling = true;
    try {
      const qs = new SvelteURLSearchParams({ limit: String(PANEL_LIMIT) });
      if (this.#since) qs.set('since', this.#since);
      const res = await window.fetch(`/api/notifications/?${qs}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // Oldest first, so the panel ends up newest-first after each unshift
      // and the toasts fire in the order things actually happened.
      const rows = (data.results || []).slice().reverse();
      for (const row of rows) this.#ingest(row);
      this.#advanceSince(rows);

      // `unread_count` is computed over the whole feed server-side, unlike
      // `count`, which is scoped to the `since` window. Trust it over the
      // increments #ingest made, so a read on another device converges here.
      if (typeof data.unread_count === 'number') this.unread_count = data.unread_count;
    } catch (err) {
      // A failed poll is not worth surfacing: the next tick retries, and
      // showing an error banner for a transient blip is worse than silence.
      console.error('notifications poll failed', err);
    } finally {
      this.#polling = false;
    }
  }

  /**
   * Move the high-water mark to the newest `created_at` we have seen.
   *
   * Compares parsed instants, never the raw strings. DRF omits the
   * microseconds component when it is zero, so `...T10:00:00Z` and
   * `...T10:00:00.123456Z` differ in length, and under a `Z` suffix the
   * shorter one sorts *later* lexicographically ('Z' > '.') while being
   * earlier in time. That would advance `since` past a notification and drop
   * it. The bug is invisible on the default `TIME_ZONE = "Asia/Kolkata"`
   * (a '+' offset happens to sort correctly) and appears only for deployments
   * that set `TIME_ZONE = "UTC"`, which is exactly the sort of thing that
   * survives every local test and fails in someone else's production.
   *
   * @param {any[]} rows
   */
  #advanceSince(rows) {
    let best = this.#since === null ? -Infinity : Date.parse(this.#since);
    for (const row of rows) {
      if (!row?.created_at) continue;
      const t = Date.parse(row.created_at);
      if (!Number.isNaN(t) && t > best) {
        best = t;
        this.#since = row.created_at;
      }
    }
  }

  /** @param {any} row */
  #ingest(row) {
    if (!row || !row.id) return;
    if (this.notifications.some((n) => n.id === row.id)) return;
    this.notifications = [row, ...this.notifications];
    this.total_count += 1;
    if (!row.read_at) this.unread_count += 1;
    if (TOAST_VERBS.has(row.verb)) {
      const message = row.entity_name ? `${row.verb}: ${row.entity_name}` : row.verb;
      toast(message, {
        description: row.data?.comment_excerpt || undefined,
        action: row.link
          ? { label: 'Open', onClick: () => (window.location.href = row.link) }
          : undefined
      });
    }
  }
}

export const notifications = new NotificationsStore();
