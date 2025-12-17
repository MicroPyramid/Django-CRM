# Firebase Setup

## Initial Setup for New Developers

1. **Google Services Configuration**:
   - Copy `android/app/google-services.json.template` to `android/app/google-services.json`
   - Replace all placeholder values with your actual Firebase project configuration
   - Get this file from the Firebase Console > Project Settings > General > Your apps

2. **Required Configuration Files**:
   - `android/app/google-services.json` - Firebase configuration for Android
   - `ios/Runner/GoogleService-Info.plist` - Firebase configuration for iOS (if applicable)

3. **Environment Variables** (if using):
   - Create `.env` file in project root
   - Add your API keys and configuration

## Security Notes

- Never commit sensitive files like:
  - `google-services.json`
  - `GoogleService-Info.plist` 
  - `.keystore` files
  - `key.properties`
  - Any files containing API keys or secrets

- These files are in `.gitignore` for security reasons
- Use template files and environment variables for team development
