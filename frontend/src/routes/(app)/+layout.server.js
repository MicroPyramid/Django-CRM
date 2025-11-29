/** @type {import('./$types').LayoutServerLoad} */
export async function load({ locals }) {
	// console.log("locals", locals.user);
	return {
		user: locals.user,
		org_name: locals.org_name || 'BottleCRM'
	};
}

export const ssr = false;
