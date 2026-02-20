import * as Sentry from '@sentry/sveltekit';

Sentry.init({
  dsn: 'https://59bf64c93be48f6cd30087fef7bbc54f@o4509449489088512.ingest.de.sentry.io/4510910257496144',

  tracesSampleRate: 1.0,

  // Enable logs to be sent to Sentry
  enableLogs: true,

  // uncomment the line below to enable Spotlight (https://spotlightjs.com)
  // spotlight: import.meta.env.DEV,
});