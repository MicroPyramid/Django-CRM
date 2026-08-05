import { fail } from '@sveltejs/kit';
import {
  createBoard,
  createCard,
  createColumn,
  getBoard,
  moveBoardTask
} from '$lib/server/v2/board.js';
import { readableError } from '$lib/server/v2/form-errors.js';

/** Map an api-helpers error to a form `fail`, preserving a 403 as a 403. */
function toFail(/** @type {any} */ err, /** @type {string} */ fallback) {
  const status = err?.status === 403 ? 403 : 400;
  return fail(status, { error: readableError(err, fallback) });
}

/** @type {import('./$types').PageServerLoad} */
export async function load({ cookies, url }) {
  const boardId = url.searchParams.get('board');
  return await getBoard({ cookies, boardId });
}

/** @type {import('./$types').Actions} */
export const actions = {
  // Persist a drag: relocate a card to `column` at position `order`. Called
  // programmatically from the drop handler, so it returns a plain success /
  // `fail` that the page reads and, on failure, reloads to snap back.
  move: async ({ request, cookies }) => {
    const form = await request.formData();
    const id = String(form.get('id') || '');
    const column = String(form.get('column') || '');
    const order = Number(form.get('order') || 0);
    if (!id || !column) return fail(400, { error: 'Missing card or column.' });
    try {
      await moveBoardTask({ cookies }, id, { column, order });
      return { success: true };
    } catch (err) {
      return toFail(err, 'Could not move the card.');
    }
  },

  // Create the org's first board, or another one.
  //
  // The empty state used to send people to the mobile app for this. The mobile
  // app has no board feature, and no client called `POST /boards/` at all, so
  // an org that had never been handed a board through the API had no way to
  // get one. The backend seeds the three default columns, so the board is
  // usable as soon as it lands.
  create: async ({ request, cookies }) => {
    const form = await request.formData();
    const name = String(form.get('name') || '').trim();
    if (!name) return fail(400, { error: 'A board needs a name.' });
    try {
      await createBoard({ cookies }, { name });
      return { added: 'board' };
    } catch (err) {
      return toFail(err, 'Could not create the board.');
    }
  },

  // Add a card to a column. Any board member may; the backend is the boundary.
  addCard: async ({ request, cookies }) => {
    const form = await request.formData();
    const columnId = String(form.get('column') || '');
    const title = String(form.get('title') || '').trim();
    const description = String(form.get('description') || '').trim();
    const priority = String(form.get('priority') || 'medium');
    if (!columnId) return fail(400, { error: 'Which column?' });
    if (!title) return fail(400, { error: 'A card needs a title.' });
    try {
      await createCard({ cookies }, columnId, { title, description, priority });
      return { added: 'card' };
    } catch (err) {
      return toFail(err, 'Could not add the card.');
    }
  },

  // Add a column. Owner/admin only. The page hides the control for a member,
  // but the backend refuses it either way, so a hand-rolled POST still 403s.
  addColumn: async ({ request, cookies }) => {
    const form = await request.formData();
    const boardId = String(form.get('board') || '');
    const name = String(form.get('name') || '').trim();
    const color = String(form.get('color') || '').trim();
    const rawOrder = form.get('order');
    const order = rawOrder != null && rawOrder !== '' ? Number(rawOrder) : undefined;
    if (!boardId) return fail(400, { error: 'Which board?' });
    if (!name) return fail(400, { error: 'A column needs a name.' });
    try {
      await createColumn({ cookies }, boardId, {
        name,
        color: color || undefined,
        order: Number.isFinite(order) ? order : undefined
      });
      return { added: 'column' };
    } catch (err) {
      return toFail(err, 'Could not add the column.');
    }
  }
};
