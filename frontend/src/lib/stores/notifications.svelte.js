/**
 * In-app notifications store.
 *
 * Single source of truth for the bell badge, the panel list, and
 * svelte-sonner toasts. Talks to the SvelteKit proxies under
 * `/api/notifications/...` (which forward to Django with the JWT cookie).
 */

import { toast } from 'svelte-sonner';

const PANEL_LIMIT = 20;

// Verbs that should fire an in-page toast in addition to bumping the badge.
// Keep this conservative — too noisy and users mute the channel.
// NOTE: `case.*` keys are backend wire-format strings — do not rename.
const TOAST_VERBS = new Set([
  'case.mentioned',
  'case.assigned',
  'case.sla_breached'
]);

class NotificationsStore {
  notifications = $state([]);
  unread_count = $state(0);
  total_count = $state(0);
  loading = $state(false);
  error = $state('');

  /** @type {EventSource | null} */
  #stream = null;
  /** @type {boolean} */
  #started = false;

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
    this.notifications = this.notifications.map((n) =>
      n.read_at ? n : { ...n, read_at: now }
    );
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

  startStream() {
    if (this.#started || typeof window === 'undefined') return;
    this.#started = true;
    this.fetch();
    try {
      this.#stream = new EventSource('/api/notifications/stream/');
      this.#stream.addEventListener('notification', (ev) => {
        try {
          const row = JSON.parse(/** @type {MessageEvent} */ (ev).data);
          this.#ingest(row);
        } catch (err) {
          console.error('notifications: bad SSE payload', err);
        }
      });
      this.#stream.addEventListener('error', () => {
        // Browser will auto-retry; nothing to do unless we want to fall back
        // to polling. Leaving this as a placeholder.
      });
    } catch (err) {
      console.error('notifications: EventSource open failed', err);
    }
  }

  stopStream() {
    if (this.#stream) {
      this.#stream.close();
      this.#stream = null;
    }
    this.#started = false;
  }

  /** @param {any} row */
  #ingest(row) {
    if (!row || !row.id) return;
    if (this.notifications.some((n) => n.id === row.id)) return;
    this.notifications = [row, ...this.notifications];
    this.total_count += 1;
    if (!row.read_at) this.unread_count += 1;
    if (TOAST_VERBS.has(row.verb)) {
      const message = row.entity_name
        ? `${row.verb}: ${row.entity_name}`
        : row.verb;
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
