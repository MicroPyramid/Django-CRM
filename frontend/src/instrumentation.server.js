import * as Sentry from '@sentry/sveltekit';
import { env } from '$env/dynamic/public';

const dsn = env.PUBLIC_SENTRY_DSN || '';

Sentry.init({
  dsn,
  enabled: !!dsn,
  tracesSampleRate: 1.0,
  enableLogs: true,
});