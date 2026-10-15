import { defineEnvVars } from '@sveltejs/kit/env';

/**
 * Every environment variable the app reads. SvelteKit 3 exposes only what is
 * declared here, through `$app/env/public` and `$app/env/private`.
 *
 * None is `static`, so each is read when the server starts rather than baked
 * in at build time: one Docker image serves any deployment. Each schema passes
 * the raw value through, so an unset variable is `undefined`, which is what
 * every caller already handles.
 */
/** @param {string | undefined} value */
const optional = (value) => value;

export const variables = defineEnvVars({
  PUBLIC_DJANGO_API_URL: {
    public: true,
    schema: optional,
    description: 'The Django API origin, without a trailing /api.'
  },
  PUBLIC_SENTRY_DSN: {
    public: true,
    schema: optional,
    description: 'Sentry DSN. Unset disables Sentry.'
  },
  RELAY_SECRET: {
    schema: optional,
    description: "Shared with the API's RELAY_SECRET so it believes the relayed visitor address."
  },
  GOOGLE_CLIENT_ID: { schema: optional },
  GOOGLE_LOGIN_DOMAIN: { schema: optional },
  NODE_ENV: { schema: optional }
});
