/**
 * The line under an installed app that has an update. The server also flags
 * an update at the installed version, when a skipped module has since been
 * switched on, so a version alone would read "Version 2 adds more" under v2.
 *
 * @param {{ version?: unknown, installedVersion?: unknown }} app
 */
export function updateLine(app) {
  const version = app.version == null ? '' : String(app.version);
  const installed = app.installedVersion == null ? '' : String(app.installedVersion);
  if (version && version === installed) {
    return 'An update adds the parts skipped while a module was off.';
  }
  return version ? `Version ${version} adds more.` : 'An update adds more.';
}
