// Hand-written Firebase config (not from `flutterfire configure`). Android
// is the only configured platform. Values mirror `android/app/google-services.json`.
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      throw UnsupportedError(
        'DefaultFirebaseOptions: web is not configured for this app.',
      );
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions: ${defaultTargetPlatform.name} '
          'is not configured for this app.',
        );
    }
  }

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyDsA2wgQIw-bVgwODNMIF482gVRn5xdANU',
    appId: '1:1072513761792:android:c170ae72445200ecd74ee5',
    messagingSenderId: '1072513761792',
    projectId: 'bottlecrm-io',
    storageBucket: 'bottlecrm-io.firebasestorage.app',
  );
}
