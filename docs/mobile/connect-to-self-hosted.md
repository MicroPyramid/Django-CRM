# Connect to a self-hosted backend

Read this page before you run or build the mobile app against anything other than
`api.bottlecrm.io`. The short version: the backend URL is baked into the binary at compile time,
there is no way to point a build at a different server without editing source and rebuilding, and
the two URLs shipped in source today aren't `localhost` or any generic placeholder. They're a
specific developer's tunnel and BottleCRM's own production API.

## The compile-time base URL

`mobile/lib/config/api_config.dart` (lines 12-19):

```dart
/// Development API URL
static const String _developmentUrl = 'https://msi-8000.rcdev.in';

/// Production API URL
static const String _productionUrl = 'https://api.bottlecrm.io';

/// Get the current base URL based on build mode
static String get baseUrl => kDebugMode ? _developmentUrl : _productionUrl;
```

Both URLs are `static const` Dart strings, and the choice between them is `kDebugMode`. A
compile-time flag set by which `flutter run`/`flutter build` mode you use, not anything read at
runtime. There is no `--dart-define`, no `String.fromEnvironment` anywhere in `lib/`, and no
runtime settings screen: grepping `lib/` for `SharedPreferences` turns up exactly four files, and
none of them touch the base URL, `auth_service.dart` (auth tokens/user data), list-view
filter/sort state in `screens/tickets/tickets_list_screen.dart` and
`screens/deals/deals_list_screen.dart`, and `providers/tickets_provider.dart`, which only defines
the JSON-serialization helper (`TicketListFilters.toJson()`) that `tickets_list_screen.dart`
persists. It doesn't call the `SharedPreferences` API itself. Whatever `baseUrl` resolves to when
the app is *compiled* is what it talks to for the life of that install.

The practical consequences:

- **A store-distributed release build can only ever talk to `https://api.bottlecrm.io`.** If
  you're self-hosting, a generic APK/AAB/IPA built from this source with the constants unchanged
  will authenticate against and read/write data on BottleCRM's own hosted API, not yours. There is
  no in-app way to redirect it.
- **A debug build (`flutter run`) does not point at `localhost` either.** `_developmentUrl` is
  `https://msi-8000.rcdev.in`: an individual developer's personal tunnel/host, not a generic
  loopback address, and not one you control. If you want to run the app against a backend on your
  own machine, you have to edit this constant regardless of whether you're in debug or release
  mode.
- **This means self-hosting the mobile app is source-edit-and-rebuild, not configure-and-run.**
  There's no middle ground between "use BottleCRM's hosted API" and "maintain your own fork of
  this one file." If that's a blocker for your deployment, treat it as a known limitation rather
  than something you missed a flag for.

## Pointing at your backend

1. Edit `mobile/lib/config/api_config.dart` and change `_developmentUrl` and/or `_productionUrl`
   to your backend's URL, which one(s) you need depends on which build modes you'll use. If you
   don't need a separate dev/prod split, it's simplest to set both to the same value.
2. Rebuild. Because these are compile-time constants, don't rely on hot reload to pick up the
   change reliably. Stop and re-run (`flutter run`) for a debug build, or do a full `flutter build
   apk --release` / `appbundle --release` / iOS build (see [Release builds](release-builds.md)) for
   a release one.

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

1. `mobile/lib/services/auth_service.dart` (lines 70-73) hardcodes a **Web** OAuth client ID as
   `serverClientId`:
   ```dart
   await _googleSignIn.initialize(
     serverClientId:
         '1072513761792-p59rct7b1c3go7l58e51r3geuqff2tfl.apps.googleusercontent.com',
   );
   ```
   The code comment identifies this as "the audience the Django backend's `GOOGLE_CLIENT_ID`
   verifies against." For your self-hosted backend to accept tokens from your own mobile build,
   this constant must be a Web client ID from **your own** Google Cloud project, and your
   backend's `GOOGLE_CLIENT_ID` must be that same value. Reusing BottleCRM's own client ID here
   will not work against your backend, because your `GOOGLE_CLIENT_ID` won't match it.
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
