import { describe, it, expect, vi, beforeEach } from 'vitest';

const apiRequest = vi.fn();
vi.mock('$lib/api-helpers.js', () => ({
  apiRequest: (/** @type {any[]} */ ...args) => apiRequest(...args)
}));

const { createInvoiceTemplate, CREATE_FIELDS } = await import('./templates.js');

const cookies = /** @type {any} */ ({});

describe('createInvoiceTemplate', () => {
  beforeEach(() => {
    apiRequest.mockReset();
    apiRequest.mockResolvedValue({ id: 't1' });
  });

  it('never accepts the raw markup fields', () => {
    expect(CREATE_FIELDS).not.toContain('template_html');
    expect(CREATE_FIELDS).not.toContain('template_css');
  });

  it('posts to the templates collection', async () => {
    await createInvoiceTemplate({ cookies }, { name: 'Clean' });
    const [url, options] = apiRequest.mock.calls[0];
    expect(url).toBe('/invoices/templates/');
    expect(options.method).toBe('POST');
  });

  it('drops the markup fields even when a caller forces them in', async () => {
    await createInvoiceTemplate(
      { cookies },
      { name: 'Clean', template_html: '<script>x</script>', template_css: 'body{}' }
    );
    const [, options] = apiRequest.mock.calls[0];
    const sent = options.body;
    expect(sent.template_html).toBeUndefined();
    expect(sent.template_css).toBeUndefined();
  });

  it('drops server-derived keys', async () => {
    await createInvoiceTemplate({ cookies }, { name: 'Clean', org: 'attacker-org', id: 'forged' });
    const [, options] = apiRequest.mock.calls[0];
    expect(options.body.org).toBeUndefined();
    expect(options.body.id).toBeUndefined();
  });

  it('requires a name', async () => {
    await expect(createInvoiceTemplate({ cookies }, { name: '  ' })).rejects.toThrow();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('rejects a colour that is not a hex value, which the server does not check', async () => {
    await expect(
      createInvoiceTemplate({ cookies }, { name: 'Clean', primary_color: 'purple' })
    ).rejects.toThrow();
    await expect(
      createInvoiceTemplate({ cookies }, { name: 'Clean', secondary_color: '#12' })
    ).rejects.toThrow();
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it('accepts a valid hex colour', async () => {
    await createInvoiceTemplate(
      { cookies },
      { name: 'Clean', primary_color: '#3B82F6', secondary_color: '#1e40af' }
    );
    expect(apiRequest).toHaveBeenCalled();
  });

  it('omits an empty colour rather than sending it as an empty string', async () => {
    // Neither colour field has `blank=True` on the model, so a literal `''`
    // earns a raw 400 ("This field may not be blank"). Omitting the key lets
    // the model default apply instead.
    await createInvoiceTemplate(
      { cookies },
      { name: 'Clean', primary_color: '', secondary_color: '#1e40af' }
    );
    const [, options] = apiRequest.mock.calls[0];
    expect(options.body.primary_color).toBeUndefined();
    expect(options.body.secondary_color).toBe('#1e40af');
  });

  it('sends FormData when a logo file is supplied', async () => {
    const file = new File(['x'], 'logo.png', { type: 'image/png' });
    await createInvoiceTemplate({ cookies }, { name: 'Clean' }, file);
    const [, options] = apiRequest.mock.calls[0];
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get('name')).toBe('Clean');
    expect(options.body.get('logo')).toBe(file);
  });

  it('sends a plain object when there is no logo', async () => {
    await createInvoiceTemplate({ cookies }, { name: 'Clean' });
    const [, options] = apiRequest.mock.calls[0];
    expect(options.body).not.toBeInstanceOf(FormData);
    expect(options.body.name).toBe('Clean');
  });

  it('unwraps the created template from the envelope', async () => {
    apiRequest.mockResolvedValue({
      error: false,
      message: 'Template created',
      template: { id: 't1', name: 'Clean' }
    });
    const result = await createInvoiceTemplate({ cookies }, { name: 'Clean' });
    expect(result).toEqual({ id: 't1', name: 'Clean' });
  });

  it('falls back to the raw response if it has no template envelope', async () => {
    apiRequest.mockResolvedValue({ id: 't1', name: 'Clean' });
    const result = await createInvoiceTemplate({ cookies }, { name: 'Clean' });
    expect(result).toEqual({ id: 't1', name: 'Clean' });
  });
});
