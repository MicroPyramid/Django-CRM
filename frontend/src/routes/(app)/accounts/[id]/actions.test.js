import { describe, it, expect, vi } from 'vitest';

const refusal = vi.hoisted(() =>
  Object.assign(new Error('refused'), {
    status: 409,
    body: {
      errors: 'This account has 3 tickets. Remove them first.',
      code: 'module_off'
    }
  })
);

vi.mock('#lib/server/v2/accounts.js', () => ({
  getAccount: async () => ({}),
  deleteAccount: async () => {
    throw refusal;
  }
}));
vi.mock('#lib/server/v2/related-records.js', () => ({
  loadRelated: async () => null,
  relatedActions: () => ({})
}));
vi.mock('#lib/server/v2/duplicates.js', () => ({ recordDuplicates: async () => ({}) }));

const { actions } = await import('./+page.server.js');

describe('account delete', () => {
  it('shows the module refusal when deleting an account with tickets while Tickets is off', async () => {
    const result = await actions.delete(/** @type {any} */ ({ cookies: {}, params: { id: 'a1' } }));
    expect(result).toMatchObject({
      status: 409,
      data: { deleteError: 'This account has 3 tickets. Remove them first.' }
    });
  });
});
