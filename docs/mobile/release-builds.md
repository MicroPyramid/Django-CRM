# Release builds

This page covers producing an installable Android/iOS artifact and what signing configuration
already exists in the repository versus what you have to create yourself. It assumes you've
already pointed the app at your own backend: see [Connect to a self-hosted
backend](connect-to-self-hosted.md), since building a release binary bakes in whatever
`lib/config/api_config.dart` says at build time, same as a debug build.

Both platforms read app identity and version from a few shared sources: `applicationId`
`io.bottlecrm` (Android, `android/app/build.gradle.kts`) and bundle identifier `io.bottlecrm` (iOS,
`ios/Runner.xcodeproj/project.pbxproj`) are the same string on both platforms; `pubspec.yaml`'s
`version: 1.2.0+11` supplies both the build name (`1.2.0`) and build number (`11`) via
`flutter.versionName`/`flutter.versionCode` on Android and `$(FLUTTER_BUILD_NAME)`/
`$(FLUTTER_BUILD_NUMBER)` on iOS. `io.bottlecrm` is BottleCRM's own identifier. It's also the
package ID of BottleCRM's own Play Store listing referenced in `mobile/README.md`. If you're
distributing your own build through your own Play Console/App Store Connect listing, you'll want
your own identifier here, which has knock-on effects on the Google Sign-In client registrations
covered on [Connect to a self-hosted backend](connect-to-self-hosted.md#google-sign-in-configuration)
(the Android OAuth client and `google-services.json`'s `package_name` are both tied to whatever
`applicationId` you ship). For a sideloaded APK you build and install yourself, changing it isn't
necessary.

## Android

```bash
flutter build apk --release        # single APK, build/app/outputs/flutter-apk/app-release.apk
flutter build appbundle --release  # Play Store .aab, build/app/outputs/bundle/release/
```

Real minimum/target/compile SDK levels, from `android/app/build.gradle.kts`:

- `minSdk = 28` (Android 9). Set directly in this file, with the comment `// Android 9 (API 28)`.
  `mobile/README.md`'s "Android: API level 31+ (Android 12+)" and `pubspec.yaml`'s
  `flutter_launcher_icons.min_sdk_android: 31` (which only controls whether that tool generates
  adaptive icons, not the app's own floor) both say something different from the actual Gradle
  config. 28 is what the build enforces.
- `compileSdk = flutter.compileSdkVersion`, `targetSdk = flutter.targetSdkVersion`. Both come
  from your installed Flutter SDK's defaults, not a number pinned in this project.

The build also requires `ndkVersion = "28.2.13676358"` (pinned in the same file, "Bumped to
satisfy jni plugin requirement") and a JDK 17-compatible toolchain (`compileOptions` and the
`kotlin { compilerOptions { jvmTarget } }` block both target Java/Kotlin 17). See [Build and
configure](build-and-configure.md#prerequisites) for the rest of the local environment needs.

`android/app/build.gradle.kts` applies the `com.google.gms.google-services` and
`com.google.firebase.crashlytics` Gradle plugins unconditionally (classpath versions pinned in
`android/build.gradle.kts`: `com.google.gms:google-services:4.5.0`,
`com.google.firebase:firebase-crashlytics-gradle:3.0.7`). The google-services plugin's documented
behavior is to fail the build outright if `android/app/google-services.json` isn't present. This
repository ships only `android/app/google-services.json.template`. The real file is gitignored
(`**/google-services.json` in `mobile/.gitignore`) and not present in a fresh clone. You need your
own `google-services.json` from a Firebase/Google Cloud project before `flutter build apk` or
`flutter build appbundle` will get past that plugin. See [Connect to a self-hosted
backend](connect-to-self-hosted.md#google-sign-in-configuration) for what that file is for beyond
just satisfying the build.

## iOS

macOS and Xcode only.

```bash
flutter build ios --release              # produces build/ios/iphoneos/Runner.app; needs code signing
flutter build ios --release --no-codesign  # same, skipping signing (e.g. building without a team configured yet)
```

For an archive ready to upload to App Store Connect, `flutter build ipa --release` is the
Flutter-managed equivalent of `appbundle` for iOS (it drives `xcodebuild -archive` and an export
step, and needs valid signing to succeed. See below).

The real deployment target is `IPHONEOS_DEPLOYMENT_TARGET = 12.0`, set identically in all three
build configurations in `ios/Runner.xcodeproj/project.pbxproj` (Debug, Release, Profile);
`mobile/README.md`'s "iOS: iOS 11.0+" doesn't match the project file.

Firebase/Crashlytics is deliberately not wired up for iOS in this codebase (`main.dart` skips
`Firebase.initializeApp` outside `TargetPlatform.android`, with a comment noting there's no iOS
`GoogleService-Info.plist` yet), so there's no equivalent of the Android google-services plugin
gate blocking an iOS build, a plain `flutter build ios --release --no-codesign` will get through
without any Firebase config. Getting past code signing is the separate concern covered next.

## Signing

**Android.** `android/app/build.gradle.kts` loads a `key.properties` file from the Android project
root, if one exists:

```kotlin
val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}
```

It reads four properties from that file: `keyAlias`, `keyPassword`, `storeFile`,
`storePassword`: to build a `release` signing config, and applies that to the `release` build
type. **`key.properties` doesn't ship in this repository**. It's listed in
`android/.gitignore` and there's no committed template for it the way there is for
`google-services.json`. Critically, look at what happens to the `release` build type when the
file is absent:

```kotlin
buildTypes {
    release {
        signingConfig = if (keystorePropertiesFile.exists())
            signingConfigs.getByName("release")
        else
            signingConfigs.getByName("debug")
    }
    ...
}
```

**On a fresh clone, with no `key.properties` created, `flutter build apk --release` and `flutter
build appbundle --release` fall back to the Android Gradle Plugin's built-in `debug` signing
config**, not a Flutter-provided key, and not one shared across installations. That config is
backed by a `debug.keystore` the Android SDK tooling generates itself, per machine, the first time
one is needed (conventionally at `~/.android/debug.keystore`, with a fixed alias/password pair
`androiddebugkey`/`android`): Flutter has no involvement in it beyond invoking Gradle, and two
different machines will generate two different debug keystores. That has a concrete consequence
beyond "not a real release key": a debug-signed release build from your laptop and one from your
CI machine carry different signatures, and Android treats differently-signed builds as unrelated
apps for update purposes. One can't silently update an install that came from the other, or from
a build signed with a real upload key later. That's fine for a build you sideload once and don't
expect to update; it is not a build you should distribute publicly, since anyone can reproduce a
"signed" update off their own machine's debug keystore too. Before a release build is meant to go
further than your own device, generate your own keystore. The standard `keytool` invocation is:

```bash
keytool -genkey -v -keystore <path-to-keystore>.jks -keyalg RSA -keysize 2048 \
  -validity 10000 -alias <your-key-alias>
```

And create `android/key.properties` (never commit it) with `storeFile`, `storePassword`,
`keyAlias`, `keyPassword` pointing at it.

One more effect of that same conditional worth knowing about, on the *debug* build type:

```kotlin
debug {
    if (keystorePropertiesFile.exists()) {
        signingConfig = signingConfigs.getByName("release")
    }
}
```

If `key.properties` exists, **debug builds are signed with your release key too**, not the
machine-local Android Gradle Plugin debug keystore described above. The code comment explains why:
so a debug build installed for local testing has the same SHA-1 fingerprint as what you registered
for Google Sign-In (see [Connect to a self-hosted backend → Google Sign-In
configuration](connect-to-self-hosted.md#google-sign-in-configuration)), rather than needing a
second, separate OAuth Android client just for debug installs.

**iOS.** `ios/Runner.xcodeproj/project.pbxproj` sets `CODE_SIGN_IDENTITY[sdk=iphoneos*] = "iPhone
Developer"` for device builds at the project level, inherited by both targets.
`CODE_SIGN_STYLE = Automatic` also appears in the file, but only on the **`RunnerTests`** target's
three build configurations. The `Runner` app target and the project level don't set
`CODE_SIGN_STYLE` at all, and the project's `TargetAttributes` block doesn't set a
`ProvisioningStyle` for either target either. What is consistent across the whole file: there is
no `DEVELOPMENT_TEAM` key anywhere in it (checked directly; it's simply absent), so regardless of
what signing style Xcode shows you when you first open the project, you'll need to open
`ios/Runner.xcworkspace` in Xcode, select the Runner target's Signing & Capabilities tab, and pick
your Apple Developer team before `flutter build ios` (without `--no-codesign`) or `flutter build
ipa` will succeed. There's no keystore-equivalent file to create by hand here, Xcode manages
provisioning profiles itself once a team is selected.
