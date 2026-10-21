/**
 * What `ImportFlow` needs to know about each importable record.
 *
 * - `singular`, `plural`: default words for the record; the leads drawer
 *   passes the org's own terminology instead.
 * - `actionPath`: the list page whose form actions (`?/importPreview`,
 *   `?/importCommit`) forward the upload to Django, so the flow works from any
 *   page, not only from that list.
 * - `listHref`: where the imported records are listed.
 * - `templateHeaders`, `templateExample`: the downloadable template, one
 *   header row and one example row. The headers are the importer's own field
 *   names, so a filled-in template matches itself.
 */
export const IMPORT_ENTITIES = {
  contacts: {
    singular: 'contact',
    plural: 'contacts',
    actionPath: '/contacts',
    listHref: '/contacts',
    templateHeaders: [
      'first_name',
      'last_name',
      'email',
      'phone',
      'organization',
      'title',
      'department',
      'do_not_call',
      'linkedin_url',
      'address_line',
      'city',
      'state',
      'postcode',
      'country',
      'description',
      'account_name',
      'assigned_emails',
      'team_names',
      'tags'
    ],
    templateExample: [
      'Alice',
      'Smith',
      'alice@acme.test',
      '+1 (555) 123-4567',
      'Acme Corp',
      'VP of Sales',
      'Sales',
      'no',
      'https://linkedin.com/in/alice',
      '500 Main St',
      'Austin',
      'TX',
      '78701',
      'US',
      'Met at SaaStr 2024',
      'Acme Corp',
      'agent@yourco.com',
      'Sales',
      'vip;newsletter'
    ]
  },
  leads: {
    singular: 'lead',
    plural: 'leads',
    actionPath: '/leads',
    listHref: '/leads',
    templateHeaders: [
      'first_name',
      'last_name',
      'email',
      'phone',
      'title',
      'company_name',
      'job_title',
      'status',
      'source',
      'rating',
      'opportunity_amount',
      'close_date',
      'description',
      'assigned_emails',
      'team_names',
      'tags'
    ],
    templateExample: [
      'Alice',
      'Smith',
      'alice@acme.test',
      '+1 (555) 123-4567',
      'Enterprise rollout',
      'Acme Corp',
      'VP of Sales',
      'assigned',
      'email',
      'HOT',
      '12000',
      '2026-12-31',
      'Met at SaaStr',
      'agent@yourco.com',
      'Sales',
      'vip;trade-show'
    ]
  }
};
