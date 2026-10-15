import * as Sentry from '@sentry/sveltekit';
import * as env from '$app/env/public';

const dsn = env.PUBLIC_SENTRY_DSN || '';

Sentry.init({
  dsn,
  enabled: !!dsn,
  tracesSampleRate: 1.0,
  // Sentry 11 collects all of these by default. Keep the server where v10 left
  // it: SSR form actions carry customer contact data and the request cookies
  // carry the session, so none of it goes to Sentry.
  dataCollection: {
    userInfo: false,
    cookies: false,
    httpBodies: [],
    stackFrameVariables: false
  }
});
