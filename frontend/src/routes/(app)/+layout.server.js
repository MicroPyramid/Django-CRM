/** @type {import('./$types').LayoutServerLoad} */
export async function load({ locals }) {
  // console.log("locals", locals.user);
  return {
    user: locals.user,
    org_name: locals.org_name || 'BottleCRM',
    org_settings: locals.org_settings || {
      default_currency: 'USD',
      currency_symbol: '$',
      default_country: null
    }
  };
}

export const ssr = true;
