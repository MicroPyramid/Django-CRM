# Build and configure

This page covers getting the Flutter source running from a clone. Dependencies, local runs, and
the test/lint commands. It does not cover pointing the app at your own backend or producing a
signed release build; see [Connect to a self-hosted backend](connect-to-self-hosted.md) and
[Release builds](release-builds.md) for those.

## Prerequisites

`mobile/pubspec.yaml` declares:

```yaml
environment:
  sdk: ^3.8.1
```

This is the only entry under `environment:`. There is no `flutter:` key. In a Flutter
`pubspec.yaml`, the `sdk:` constraint under `environment:` pins the **Dart** SDK, not the Flutter
SDK; a `flutter: ">=x.y.z"` line would pin Flutter separately, and this project doesn't have one.
So the project itself declares no explicit Flutter version floor, `^3.8.1` only says "Dart SDK
3.8.1 or newer, below 4.0.0."

That said, the checked-in `mobile/pubspec.lock` records the SDK constraints actually resolved
against the full dependency graph, in its trailing `sdks:` block:

```yaml
sdks:
  dart: ">=3.12.0 <4.0.0"
  flutter: ">=3.44.0"
```

This is narrower than the project's own `^3.8.1` floor because several dependencies (for example
`flutter_riverpod: ^3.3.1`, `go_router: ^17.2.3`, `google_fonts: ^8.1.0`) have their own, higher
SDK requirements, and `pub` resolves to the intersection of all of them. In practice, **Flutter
3.44.0 or newer** (which is what ships Dart 3.12+) is the version that will actually resolve this
project's dependencies. That number comes from the lockfile, not from a guess at which Flutter
release maps to which Dart version. There is no `.fvmrc`, and neither of the two GitHub Actions
workflows in this repository (`.github/workflows/tests.yml`, `codeql-analysis.yml`) mentions
Flutter, Dart, or `mobile/` at all, so there's no CI-enforced version either. The lockfile is the
only pin that exists.

(`mobile/README.md` states "Flutter SDK: 3.8.1 or later", the same Dart-constraint-copied-as-a-
Flutter-version error. Use the lockfile numbers above instead.)

Beyond the SDK itself:

- **Android builds** need the Android SDK (via Android Studio or the standalone command-line
  tools). `mobile/android/app/build.gradle.kts` sets `compileSdk = flutter.compileSdkVersion` and
  `targetSdk = flutter.targetSdkVersion`: both come from whatever your installed Flutter SDK
  defines as current, not from a number hardcoded in this project. It does pin two things itself:
  `ndkVersion = "28.2.13676358"` (the comment notes this was "bumped to satisfy jni plugin
  requirement") and Java/Kotlin compatibility at **17** (`compileOptions.sourceCompatibility` /
  `targetCompatibility = JavaVersion.VERSION_17`, mirrored in the `kotlin { compilerOptions {
  jvmTarget } }` block). You need a JDK 17-compatible toolchain available to Gradle.
- **iOS builds** need Xcode and CocoaPods, and only work on macOS. `mobile/README.md` states "iOS:
  iOS 11.0+", but the actual deployment target in `mobile/ios/Runner.xcodeproj/project.pbxproj` is
  `IPHONEOS_DEPLOYMENT_TARGET = 12.0`, set identically across all three build configurations
  (Debug, Release, Profile). 12.0 is the real floor.

## Getting dependencies

```bash
cd mobile
flutter pub get
```

This resolves and downloads the packages declared in `pubspec.yaml` into your local pub cache and
writes/updates `pubspec.lock` (already checked in; `flutter pub get` should reproduce it exactly
if nothing has changed upstream). Android's Firebase/Crashlytics integration
(`firebase_core`, `firebase_crashlytics`) is wired up for Android only. See
[Connect to a self-hosted backend](connect-to-self-hosted.md#google-sign-in-configuration) for
what that does and doesn't require from you.

## Running against a local backend

`flutter run` starts the app in debug mode against whichever device or emulator is attached
(`flutter devices` lists them). **Before you do this, read [Connect to a self-hosted
backend](connect-to-self-hosted.md) first**, the backend URL the debug build talks to is a
compile-time constant in `lib/config/api_config.dart`, and as shipped it does **not** point at
`localhost` or any backend you're likely to be running yourself. Running `flutter run` without
changing that constant first will build successfully and simply talk to a stranger's backend.

Once `lib/config/api_config.dart` points at your own backend:

```bash
flutter run
```

Press `r` for hot reload, `R` for hot restart, `q` to quit. If you change the URL constant while
the app is already running, restart the run (`R`, or stop and re-run) rather than relying on hot
reload. See the compile-time-constant caveat on the linked page.

## Tests and analysis

```bash
flutter test                        # run the test suite
flutter analyze --no-fatal-infos    # static analysis (analysis_options.yaml + flutter_lints)
dart format .                       # format all Dart source
```

`mobile/README.md` describes a `test/unit/`, `test/widget/`, `test/integration/` structure. As of
this writing the actual `test/` tree holds one file,
`test/screens/deals/deals_list_screen_test.dart`, a widget test for the deals list screen, the
three-way split described in the README doesn't exist yet. `flutter test` runs whatever is there
regardless of directory layout, so the command itself is accurate even though the described
structure isn't.

`flutter analyze --no-fatal-infos` runs against the rules in `analysis_options.yaml`, which
includes `package:flutter_lints/flutter.yaml` with no project-specific rules added or disabled.
