# CLAUDE.md

Flutter client for the BottleCRM API: Riverpod 3 (hand-written `AsyncNotifier` and `Notifier` providers, no codegen), go_router, Material 3 and Lucide icons. `../CLAUDE.md` applies here as well (security, web and mobile parity, comments, em dashes); this file covers only what is specific to the app.

## House rules

- **The app is not a security boundary.** Any rule enforced here (required fields, role-based hiding, ownership) must also exist in the DRF serializer or view. If the backend does not enforce it, say so.
- **Tokens live only in `lib/services/token_storage.dart`** (Keystore/Keychain). Never in `SharedPreferences`, logs, crash reports or analytics; never `print()` a JWT, refresh token or PII. Never disable TLS validation, even behind a debug flag.
- **Screens do not call the network.** A provider in `lib/providers/` calls `ApiService()` (`lib/services/api_service.dart`) with a URL from `ApiConfig` (`lib/config/api_config.dart`). Unwrap lists with `listFromEnvelope()` (`lib/data/api_envelope.dart`). Models live in `lib/data/models/`.
- **Icons are `LucideIcons.*`.** `lib/` names zero Material `Icons.*`; keep it that way.
- **Style comes from `lib/core/theme/theme.dart`** (`AppColors`, `AppTypography`, `AppSpacing`, `AppLayout`), whose values follow `DESIGN_SYSTEM.md`. Cards are flat: a bordered `Container`, no elevation or shadow.
- **Mobile first is the baseline, so check the other direction**: a new screen at tablet width and with the system font scaled up, with tap targets of about 44px or more.

## Reuse before writing

- Admin gate: `isOrgAdminProvider` (`lib/providers/auth_provider.dart`). Never read `role` directly. Ownership: `myEmailProvider`.
- "Today" is the org's, not the device's: `lib/services/org_date.dart` (`orgToday`, `todayIn`, `orgDaysUntil`, `orgTimeZoneOf`).
- Currency: `Currency.symbolFor(code)` (`lib/data/models/deal.dart`), which never falls back to `$`. Invoice amounts: `money()` and `compactMoney()` in `lib/screens/invoices/invoice_format.dart`.
- Attachments: `lib/services/attachment_upload.dart` (`AttachmentTarget`, `downloadAttachment`) and nowhere else. Each record type posts its own multipart field (`task_attachment`, `lead_attachment`, `opportunity_attachment`, `case_attachment`). A wrong name is answered 200 with nothing stored, so `test/unit/attachment_upload_test.dart` pins all four.
- Forms: `lib/widgets/forms/custom_fields_form.dart`, `unsaved_changes.dart` (`UnsavedChangesGuard`), `multi_select_sheet.dart`. Shared widgets: the `lib/widgets/common/common.dart` barrel and `badge.dart` (`StatusBadge`, `PriorityBadge`, `LabelPill`).

## Commands

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://<host>:8000    # debug allows http
flutter test
flutter test test/unit/attachment_upload_test.dart           # one file
flutter analyze --no-fatal-infos
dart format .
flutter build appbundle --release --dart-define=API_BASE_URL=https://crm.example.com
```

**No CI runs any of these.** `../.github/workflows/` covers the backend, frontend and docs only, so local `flutter analyze` and `flutter test` are the whole gate. Run both before calling a change done.

## Tests

- Layout: `test/unit/`, `test/screens/<feature>/`, `test/widgets/`. Fake file picks: `test/helpers/fake_platform_file.dart`. JWTs carrying an org timezone: `test/support/org_zone.dart`.
- `test/screens/phone_viewport_test.dart` renders screens at 390x844 at two text scales (`usePhone()`), asserting no overflow. Add a case for every new screen: it catches overflows that review misses.

## Gotchas

- **The API base URL is compile-time** (`--dart-define=API_BASE_URL`), on purpose: a runtime setting would let anything that can write app storage redirect every JWT. A release build throws unless it is `https://`. Without the define, debug builds use the maintainer's dev server, so pass it. `GOOGLE_SERVER_CLIENT_ID` overrides the same way.
- **Keep `cupertino_icons`.** Nothing names `CupertinoIcons`, but `SwitchListTile.adaptive` needs the font and the build fails without it.
- **Do not set `android.builtInKotlin=true`.** AGP 8.x hardcodes built-in Kotlin to 2.0.0, a downgrade from our 2.4.10 and below Flutter's 2.2.20 floor. The Kotlin Gradle Plugin warning from `file_picker` is hidden by Flutter until AGP 9, not fixed.
- **`file_picker` and `flutter_secure_storage` upgrade together**: file_picker below 12 pins `win32 ^5`, and flutter_secure_storage 11 needs `win32 ^6`.
- **`PlatformFile` is abstract since file_picker 12.** Size via `length()` (null means unmeasurable, which the attachment paths refuse), bytes via `readAsBytes()`, pick with `pickFile()`; `saveFile()` returns `Uri?`.
- **`flutter pub upgrade` is not monotonic.** A patch release can tighten a constraint and move another package backwards, so read the `pubspec.lock` diff after upgrading.
- Crashlytics starts on Android only and collects nothing in debug (`lib/main.dart`).
