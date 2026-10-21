# Connect to a self-hosted backend

Read this page before you run or build the mobile app against anything other than
`api.bottlecrm.io`. The short version: the backend URL is fixed when the app is compiled, and you
choose it with a build flag, not by editing source.

## The compile-time base URL

`mobile/lib/config/api_config.dart` resolves one host for every request:

| Build | No `API_BASE_URL` | With `--dart-define=API_BASE_URL=<url>` |
| --- | --- | --- |
| Debug (`flutter run`) | `http://localhost:8000` | `<url>`, `http://` allowed |
| Release (`flutter build`) | `https://api.bottlecrm.io` | `<url>`, which must start with `https://` |

The choice is compile-time on purpose. A runtime setting would let anything able to write the
app's storage redirect every request, and every JWT with it, to a server of its own choosing. So
whatever the URL was when the app was built is what it talks to for the life of that install, and a
store-distributed build can only ever reach `https://api.bottlecrm.io`.

## Pointing at your backend

```bash
# Debug build against a backend on your machine (Android emulator)
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000

# Release build against your own server
flutter build appbundle --release --dart-define=API_BASE_URL=https://crm.example.com
```

A trailing slash is dropped. A release build given a plain `http://` URL refuses to start rather
than send tokens unencrypted. Hot reload does not pick up a changed define: stop and re-run, or
rebuild (see [Release builds](release-builds.md)). Google Sign-In needs its own client id for your
backend, also passed as a define; see below.

A few things to get right about the URL itself:

- **Scheme and reachability depend on where the app runs, not just what your backend serves.**
  - An **Android emulator** does not see the host machine as `localhost`, from inside the
    emulator, `localhost`/`127.0.0.1` refers to the emulator itself. The documented address for
    the host loopback interface is `10.0.2.2`. If your backend is `docker compose up` on your dev
    machine (see [Docker](../self-hosting/docker.md), which binds `0.0.0.0:8000`), point the
    emulator build at `http://10.0.2.2:8000`, not `http://localhost:8000`.
  - An **iOS Simulator** runs natively on the Mac (it isn't a separate virtual network namespace
    the way the Android emulator is), so `http://localhost:8000` from inside the simulator does
    reach a backend bound on the host Mac.
  - A **physical device** (Android or iOS) can't reach "the developer machine" via `localhost` or
    `10.0.2.2` at all: it needs your machine's LAN IP address, both devices on the same network,
    and no firewall blocking the port.
- **Both platforms default to blocking plain HTTP, and nothing in this project opts back in, but
  whether that default actually reaches this app's traffic isn't something this repository can
  settle.** The two policies, and what's (not) configured for each:
  - **Android** disables cleartext traffic by default for apps whose `targetSdkVersion` is 28 or
    higher. That's keyed on `targetSdk`, not `minSdk`. `android/app/build.gradle.kts` pins
    `minSdk = 28` (line 40), but `targetSdk = flutter.targetSdkVersion` on the next line is *not*
    pinned in this project. It tracks whatever Flutter SDK you have installed (see
    [Release builds](release-builds.md)). Either way, there's no `android:usesCleartextTraffic`
    attribute and no `android:networkSecurityConfig` in `AndroidManifest.xml`, and no
    `network_security_config.xml` resource anywhere under `android/app/src/main/res/` (checked
    directly), nothing here opts back into cleartext.
  - **iOS** has the equivalent default: App Transport Security blocks plain HTTP unless the app's
    `Info.plist` carries an `NSAppTransportSecurity` exception, and `ios/Runner/Info.plist` has
    none.
  - On both platforms, though, that default is normally enforced by the platform's own HTTP stack:
    Android's `NetworkSecurityPolicy`, consulted by `HttpURLConnection`/OkHttp/WebView; iOS's
    App Transport Security, enforced inside `NSURLSession`/CFNetwork. This app's requests don't
    obviously go through either: `api_service.dart` builds its client from `package:http`'s
    default `Client()` (`final http.Client _client = http.Client();`), which on a non-web platform
    resolves to `IOClient`, a thin wrapper around `dart:io`'s own `HttpClient` (`http` package
    source, `lib/src/client.dart` / `lib/src/io_client.dart`), not `cronet_http` or
    `cupertino_http`, neither of which is a dependency here. Whether `dart:io`'s socket layer on
    either platform consults the OS's cleartext/ATS policy at all isn't something reading source
    can settle; it would take an actual build tested against a plain-HTTP host, which is out of
    scope for this page.

  Treat HTTPS as required regardless of how that ambiguity resolves in practice: this connection
  carries JWTs and customer data (see [above](#the-compile-time-base-url)), and it should be
  encrypted on its own merits, not because a platform default happens to force it. If you do need
  to test against the plain-HTTP [Docker](../self-hosting/docker.md) stack directly, try it, if
  the connection fails in a way that looks like a cleartext/ATS block, the Android-side escape
  hatch is adding your own `android:usesCleartextTraffic="true"` (or a scoped
  `network_security_config.xml`) to `AndroidManifest.xml`; the durable fix on either platform is
  putting a TLS-terminating [reverse proxy](../self-hosting/production-deploy.md#reverse-proxy) in
  front of your backend, since nothing in the backend itself terminates TLS either.

## Google Sign-In configuration

[Magic-link email sign-in](../getting-started/first-sign-in.md#magic-links) needs no
configuration on either end and works against any backend. Google Sign-In needs configuration on
**both** the backend and the mobile app, and the two have to agree with each other. This is more
involved than the [web app's Google OAuth setup](../self-hosting/google-oauth.md), because the
mobile flow is [ID-token-based, not
redirect-based](../self-hosting/google-oauth.md#mobile-id-tokens).

**Backend side** (prerequisite, covered in full on [Google
OAuth](../self-hosting/google-oauth.md)): `GOOGLE_CLIENT_ID` must be set to a real Google OAuth
Web client ID, because `GoogleIdTokenView` verifies every ID token's audience against exactly that
value (`google.oauth2.id_token.verify_oauth2_token(..., settings.GOOGLE_CLIENT_ID)`). Leave it
blank and Google Sign-In stays off. Magic links are the only path in.

**Android side**: three things, all tied to BottleCRM's own Google Cloud project as shipped:

1. The app signs in with a **Web** OAuth client id as `serverClientId`, the audience your
   backend's `GOOGLE_CLIENT_ID` verifies against. It defaults to BottleCRM's own, which your
   backend will reject. Build with a Web client id from **your own** Google Cloud project, the
   same value as your backend's `GOOGLE_CLIENT_ID`:
   ```bash
   --dart-define=GOOGLE_SERVER_CLIENT_ID=<your-web-client-id>.apps.googleusercontent.com
   ```
2. Android sign-in additionally needs an **Android**-type OAuth client (separate from the Web
   client above) registered in Google Cloud, tied to your app's `applicationId` and the SHA-1
   fingerprint of whatever certificate signs the build. Get the fingerprint with `cd android &&
   ./gradlew signingReport`. This needs `android/local.properties` to already exist with a
   `flutter.sdk` entry (`settings.gradle.kts` `require`s it and fails with `"flutter.sdk not set in
   local.properties"` otherwise); that file is gitignored (`android/.gitignore:6`) and is written
   by Flutter's own Gradle-invoking commands (`flutter run`, `flutter build ...`), not by `flutter
   pub get` alone, so make sure you've run one of those at least once first. This is also why
   `build.gradle.kts`'s `debug` build type signs with the release key when `key.properties` exists
   (see [Release builds → Signing](release-builds.md#signing)) rather than the machine-local
   Android Gradle Plugin debug keystore, so a locally installed debug build's SHA-1 matches what
   you registered.
3. Firebase/Crashlytics config (`android/app/google-services.json`) is required for the Gradle
   build to succeed at all once the `com.google.gms.google-services` plugin is applied (it is,
   unconditionally, in `android/app/build.gradle.kts`), only a placeholder
   `google-services.json.template` is committed; you supply the real file from your own
   Firebase/Google Cloud project. See [Release builds](release-builds.md) for what that plugin
   does if the file is missing.

**iOS side, not configured in this repository at all as shipped**, independent of anything you
change on Android. The native SDK the `google_sign_in_ios` plugin wraps (pinned at `6.3.0` in
`pubspec.lock`) can get its client ID from three places, checked in this order by the plugin's own
`configureWithParameters:` handler (`FLTGoogleSignInPlugin.m:180-191`):

1. a runtime `clientId:` argument passed to `GoogleSignIn.instance.initialize(...)`;
2. a bundled `GoogleService-Info.plist`'s `CLIENT_ID` key;
3. `Info.plist`'s own `GIDClientID` key, which `GIDSignIn` reads automatically as its default when
   neither of the above is set. The plugin's own source comment calls this "the recommended
   configuration method."

All three are absent here: `auth_service.dart`'s `initialize()` call passes only `serverClientId`,
never `clientId`; `ios/Runner/GoogleService-Info.plist` doesn't exist (gitignored, and there's no
committed template the way Android has one); and grepping the whole `ios/` tree for `GIDClientID`,
`CFBundleURLTypes`, and `REVERSED_CLIENT_ID` returns nothing.

That doesn't raise an error at startup, though. When all three sources are absent, the plugin's
internal `configurationWithClientIdentifier:...` returns `nil`, and the handler simply skips
assigning a new configuration (`if (configuration) { self.signIn.configuration = configuration; }`)
rather than failing; `GIDSignIn`'s configuration is just left unset. `auth_service.dart`'s
`initialize()` call is wrapped in a `try`/`catch` that only `debugPrint`s on error regardless, so
the app starts up looking normal on iOS either way. The gap only becomes visible when a user
actually taps "Sign in with Google" and there's no configuration to sign in with.

**The least invasive fix is source #3 above, the `Info.plist` route `GIDSignIn` itself
recommends, since it needs no Dart code changes:**

```xml
<!-- ios/Runner/Info.plist -->
<key>GIDClientID</key>
<string>YOUR-IOS-CLIENT-ID.apps.googleusercontent.com</string>
```

plus the URL-scheme callback handler, which the `google_sign_in_ios` package's own README says is
required regardless of which of the three routes you use for the client ID itself:

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleTypeRole</key>
    <string>Editor</string>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>com.googleusercontent.apps.YOUR-REVERSED-CLIENT-ID</string>
    </array>
  </dict>
</array>
```

Both values come from an iOS-type OAuth client in your Google Cloud project, a
`GoogleService-Info.plist` for that project has them under `CLIENT_ID` and `REVERSED_CLIENT_ID`
respectively, or you can copy them from the Cloud Console directly without ever downloading that
file. The alternative is passing `clientId:` (and optionally `serverClientId:`) as arguments to
`_googleSignIn.initialize(...)` in `auth_service.dart` instead of setting `GIDClientID` (source #1
instead of #3), but the `CFBundleURLTypes` entry above is still required either way.

This is separate from Firebase Crashlytics, which is deliberately Android-only in this codebase,
`main.dart` explicitly guards Firebase initialization behind `defaultTargetPlatform ==
TargetPlatform.android` with a comment noting iOS has no `GoogleService-Info.plist` "yet." Don't
read the Crashlytics gap as evidence the Google Sign-In gap is equally intentional; the two are
separate config surfaces that happen to share the same missing file.
