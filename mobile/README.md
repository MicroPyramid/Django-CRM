# BottleCRM Mobile

<div align="center">

![Flutter](https://img.shields.io/badge/Flutter-3.8.1+-02569B?style=for-the-badge&logo=flutter&logoColor=white)
![Dart](https://img.shields.io/badge/Dart-3.0.0+-0175C2?style=for-the-badge&logo=dart&logoColor=white)
![Android](https://img.shields.io/badge/Android-API%2031+-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![iOS](https://img.shields.io/badge/iOS-11.0+-000000?style=for-the-badge&logo=ios&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

[![Get it on Google Play](https://img.shields.io/badge/Get%20it%20on-Google%20Play-black?style=for-the-badge&logo=google-play&logoColor=white)](https://play.google.com/store/apps/details?id=io.bottlecrm)

</div>

A modern, feature-rich Flutter CRM application for startups and enterprises. Built with a scalable architecture, BottleCRM Mobile provides comprehensive customer relationship management capabilities with multi-tenant support, real-time synchronization, and intuitive user experience.

## 🚀 Overview

BottleCRM Mobile is designed to streamline your sales and customer management processes with:
- **Multi-tenant Architecture**: Organization-based data isolation and role management
- **Offline-First Design**: Local caching with smart synchronization
- **Modern UI/UX**: Material Design 3 with adaptive layouts
- **Enterprise Security**: OAuth 2.0, JWT tokens, and secure API communication

## ✨ Features

### 🔐 Authentication & Security
- **Google OAuth 2.0**: Seamless single sign-on integration
- **JWT Authentication**: Secure token-based API communication
- **Multi-tenant Support**: Organization-based data isolation
- **Role-based Access**: Granular permissions and user management

### 📊 Core CRM Modules
- **Dashboard**: Real-time metrics, KPIs, and activity feeds
- **Contacts**: Complete contact management with search and filtering
- **Leads**: Lead capture, qualification, and conversion tracking
- **Opportunities**: Sales pipeline management with stages
- **Tasks**: Task assignment, tracking, and deadline management
- **Accounts**: Customer account profiles and relationship history
- **Cases**: Customer support ticket management
- **Events**: Calendar integration and meeting scheduling
- **Documents**: File management with cloud storage
- **Teams**: Collaboration tools and team management
- **Invoices**: Billing and invoice generation

### 🎨 User Experience
- **Material Design 3**: Modern, consistent UI patterns
- **Responsive Design**: Optimized for phones, tablets, and foldables
- **Dark/Light Theme**: System-aware theme switching
- **Offline Support**: Local data caching with smart sync
- **Pull-to-Refresh**: Intuitive data refresh patterns
- **Infinite Scrolling**: Smooth pagination for large datasets

## 📋 Requirements

### System Requirements
- **Flutter SDK**: 3.8.1 or later
- **Dart SDK**: 3.0.0 or later
- **Android Studio/VS Code**: Latest stable version
- **Git**: For version control

### Platform Support
- **Android**: API level 31+ (Android 12+)
- **iOS**: iOS 11.0+ (for iOS builds)
- **Web**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **Desktop**: Windows, macOS, Linux (experimental)

### Development Tools
- **Android SDK**: For Android development
- **Xcode**: For iOS development (macOS only)
- **CocoaPods**: iOS dependency management

## 🚀 Getting Started

### 📱 For End Users

**Download the app directly from Google Play Store:**

<div align="center">

[![Get it on Google Play](https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png)](https://play.google.com/store/apps/details?id=io.bottlecrm)

*Package ID: `io.bottlecrm`*

</div>

### 👨‍💻 For Developers

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/bottlecrm_mobile_v2.git
   cd bottlecrm_mobile_v2
   ```

2. **Install Flutter dependencies**:
   ```bash
   flutter pub get
   ```

3. **Set up Firebase & Google Sign-In**:
   ```bash
   # Copy template and configure
   cp android/app/google-services.json.template android/app/google-services.json
   # Edit the file with your Firebase project configuration
   ```

4. **Run the application**:
   ```bash
   flutter run
   ```

### 🔧 Detailed Setup

#### Firebase Configuration
1. Create a new Firebase project at [Firebase Console](https://console.firebase.google.com)
2. Enable Google Sign-In authentication
3. Download `google-services.json` for Android
4. Download `GoogleService-Info.plist` for iOS (if building for iOS)
5. Place files in their respective directories:
   - Android: `android/app/google-services.json`
   - iOS: `ios/Runner/GoogleService-Info.plist`

#### Google Cloud Console Setup
1. Navigate to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth 2.0 Client ID for Android:
   ```bash
   # Get your SHA-1 fingerprint
   cd android
   ./gradlew signingReport
   ```
3. Add the SHA-1 fingerprint to your OAuth client
4. Configure OAuth consent screen

#### Environment Configuration
The app automatically switches between environments:
- **Debug builds**: Uses development API (ngrok URL)
- **Release builds**: Uses production API (bottlecrm.io)

You can modify URLs in `lib/config/api_config.dart`

## 🛠 Development

### Development Commands

```bash
# Run the app with hot reload
flutter run

# Run with specific device
flutter run -d <device-id>

# Run in debug mode with detailed logging
flutter run --debug --verbose

# Format code
dart format .

# Analyze code quality
flutter analyze --no-fatal-infos

# Run tests
flutter test

# Generate code coverage
flutter test --coverage
```

### Code Quality & Standards

This project follows strict coding standards:
- **Linting**: Uses `flutter_lints` for consistent code style
- **Architecture**: Singleton services with dependency injection
- **Error Handling**: Comprehensive try-catch with user-friendly messages
- **Naming**: Dart conventions (camelCase, PascalCase, snake_case)
- **Documentation**: Comprehensive inline documentation

### Debugging

```bash
# Connect to Android device over WiFi
adb connect <device-ip>:5555

# View logs
flutter logs

# Launch DevTools
flutter pub global activate devtools
flutter pub global run devtools
```

## 📦 Build & Deployment

### Android Builds

```bash
# Clean and prepare
flutter clean
flutter pub get

# Debug build (uses development API)
flutter build apk --debug

# Release build (uses production API)
flutter build apk --release

# App Bundle for Play Store
flutter build appbundle --release

# Install APK directly
flutter install build/app/outputs/flutter-apk/app-release.apk
```

### iOS Builds (macOS only)

```bash
# Build for iOS
flutter build ios --release

# Build for iOS Simulator
flutter build ios --debug --simulator
```

### Build Configurations

The app uses different API endpoints based on build type:
- **Debug builds**: Development server (ngrok tunnel)
- **Release builds**: Production API (`https://api.bottlecrm.io`)

Build configurations are managed in:
- `lib/config/api_config.dart` - API endpoint configuration
- `android/app/build.gradle.kts` - Android build settings
- `ios/Runner.xcodeproj` - iOS build settings

## 🏗 Architecture

BottleCRM Mobile follows a robust, scalable architecture designed for enterprise applications:

### Core Architecture Patterns

- **Singleton Services**: All services use the singleton pattern for consistent state management
- **Service-First Design**: Business logic is encapsulated in service classes
- **Repository Pattern**: Data access abstraction with caching layers
- **Multi-tenant Support**: Organization-based data isolation at the API level

### Project Structure

```
lib/
├── app.dart                 # Main app configuration & routing
├── main.dart               # Application entry point
├── config/
│   └── api_config.dart     # Environment-aware API configuration
├── models/
│   └── api_models.dart     # Type-safe data models with JSON serialization
├── services/               # Business logic & API communication
│   ├── api_service.dart    # HTTP client with auto-authentication
│   ├── auth_service.dart   # Google OAuth & organization management
│   ├── contacts_service.dart
│   ├── dashboard_service.dart
│   ├── leads_service.dart
│   └── tasks_service.dart
└── screens/                # UI screens organized by feature
    ├── dashboard_screen.dart
    ├── login_screen.dart
    ├── company_selection_screen.dart
    └── ...
```

### Key Architecture Components

#### 1. Authentication Flow
```
Login → Google OAuth → JWT Token → Organization Selection → Dashboard
```

#### 2. Service Pattern
```dart
class SomeService {
  static final SomeService _instance = SomeService._internal();
  factory SomeService() => _instance;
  SomeService._internal();
  
  // Service methods...
}
```

#### 3. API Communication
- Centralized HTTP client with automatic JWT token injection
- Organization header (`X-Organization-ID`) for multi-tenant requests
- Automatic logout on 401 responses
- Comprehensive error handling with user-friendly messages

#### 4. State Management
- Service-based state management with singleton pattern
- Local caching using SharedPreferences
- Reactive UI updates with StatefulWidget patterns
- Navigation state preserved with IndexedStack

### Data Flow

1. **Authentication**: Google OAuth → JWT storage → Organization selection
2. **API Requests**: Service → ApiService → HTTP → Backend API
3. **Data Processing**: JSON → Model classes → UI widgets
4. **Local Storage**: Critical data cached in SharedPreferences
5. **Error Handling**: Service level → UI feedback → User notification

For detailed architectural guidelines, see [CLAUDE.md](CLAUDE.md) and [.github/copilot-instructions.md](.github/copilot-instructions.md).

## ⚙️ Configuration

### API Configuration

The application uses environment-based API URLs configured in `lib/config/api_config.dart`:

```dart
// Development (debug builds)
static const String _developmentUrl = 'https://b2ad5166b831.ngrok-free.app';

// Production (release builds) 
static const String _productionUrl = 'https://api.bottlecrm.io';
```

**Environment Detection**: Automatic switching based on `kDebugMode` flag

### Authentication Setup

#### Google Sign-In Configuration

1. **Firebase Console Setup**:
   - Create Firebase project
   - Enable Google Sign-In authentication provider
   - Configure OAuth consent screen

2. **Get Android SHA-1 fingerprint**:
   ```bash
   cd android
   ./gradlew signingReport
   ```

3. **Google Cloud Console**:
   - Create OAuth 2.0 Client ID for Android
   - Add SHA-1 fingerprint to OAuth client
   - Download `google-services.json`

4. **Firebase Configuration Files**:
   ```bash
   android/app/google-services.json       # Android configuration
   ios/Runner/GoogleService-Info.plist    # iOS configuration (if applicable)
   ```

#### Authentication Flow

```
1. User clicks "Sign in with Google"
2. Google OAuth flow → JWT token received
3. Token stored in SharedPreferences
4. User selects organization from available list
5. Organization ID added to all API requests via X-Organization-ID header
6. Dashboard and metadata loaded for selected organization
```

### Multi-tenancy Configuration

- **Organization-based Data Isolation**: All API requests include organization context
- **Automatic Header Injection**: `ApiService` adds `X-Organization-ID` to requests
- **Organization Switching**: Clear cached data when switching organizations
- **Role-based Access**: Different permissions based on user role in organization

### Storage Configuration

- **JWT Tokens**: Stored securely in SharedPreferences
- **Organization Data**: Cached locally for offline access
- **Metadata Caching**: Lead statuses, sources, and other metadata cached per organization
- **Auto-cleanup**: Cached data cleared on logout and organization switch

## 📚 Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `flutter` | SDK | Flutter framework |
| `cupertino_icons` | ^1.0.8 | iOS-style icons |
| `http` | ^1.1.0 | HTTP client for API requests |
| `google_sign_in` | ^7.1.1 | Google OAuth authentication |
| `shared_preferences` | ^2.2.2 | Local data persistence |
| `jwt_decoder` | ^2.0.1 | JWT token parsing |
| `font_awesome_flutter` | ^10.7.0 | FontAwesome icons |
| `intl` | ^0.19.0 | Internationalization support |
| `package_info_plus` | ^8.0.2 | App version and build info |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `flutter_test` | SDK | Testing framework |
| `flutter_lints` | ^6.0.0 | Dart linting rules |
| `flutter_launcher_icons` | ^0.14.4 | App icon generation |

### Key Features by Dependency

- **Authentication**: Google Sign-In with JWT token management
- **HTTP Communication**: Robust API client with error handling
- **Local Storage**: Secure token and metadata caching
- **UI Components**: Material Design with FontAwesome icons
- **Code Quality**: Comprehensive linting and formatting

## 🧪 Testing

### Test Structure
```bash
test/
├── unit/           # Unit tests for services and models
├── widget/         # Widget tests for UI components
└── integration/    # End-to-end integration tests
```

### Running Tests
```bash
# Run all tests
flutter test

# Run with coverage
flutter test --coverage

# Run specific test file
flutter test test/unit/auth_service_test.dart
```

### Testing Guidelines
- **Unit Tests**: All service methods and model classes
- **Widget Tests**: Critical UI components and interactions
- **Integration Tests**: End-to-end user flows
- **Mocking**: Use mockito for external dependencies

## 🚀 Performance Optimization

### App Performance
- **Lazy Loading**: Screens and data loaded on demand
- **Image Optimization**: Compressed assets and caching
- **Memory Management**: Proper disposal of controllers and streams
- **Network Optimization**: Request batching and intelligent caching

## 🔧 Troubleshooting

### Common Issues

#### Firebase/Google Sign-In Issues
```bash
# Problem: Google Sign-In not working
# Solution: Check SHA-1 fingerprint configuration
cd android && ./gradlew signingReport

# Problem: google-services.json not found
# Solution: Ensure file is in correct location
ls android/app/google-services.json
```

#### Build Issues
```bash
# Problem: Build failures after dependency updates
# Solution: Clean and rebuild
flutter clean
flutter pub get
flutter run

# Problem: Android build issues
# Solution: Verify Android SDK and NDK versions
flutter doctor -v
```

#### API Connection Issues
```bash
# Problem: API requests failing in debug mode
# Solution: Check ngrok tunnel status and update URL in api_config.dart

# Problem: 401 Unauthorized errors
# Solution: Clear app data and re-authenticate
flutter clean
# Uninstall app from device and reinstall
```

### Development Tips

1. **Hot Reload**: Use `r` in terminal for hot reload during development
2. **Hot Restart**: Use `R` for hot restart when changing app state
3. **DevTools**: Use Flutter DevTools for debugging and performance analysis
4. **Logging**: Check console output for detailed error information

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow coding standards**: Use `dart format` and `flutter analyze`
4. **Write tests**: Ensure adequate test coverage
5. **Commit changes**: Use conventional commit messages
6. **Create Pull Request**: Provide detailed description

### Code Style Guidelines

- Follow Dart naming conventions
- Use meaningful variable and function names
- Add inline documentation for complex logic
- Implement proper error handling
- Write unit tests for new features

### Commit Message Format
```
type(scope): description

feat(auth): add biometric authentication
fix(api): resolve null pointer exception
docs(readme): update installation instructions
```

## 📄 License

```
MIT License

Copyright (c) 2024 BottleCRM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🌟 Support

- ** Documentation**: [CLAUDE.md](CLAUDE.md) for detailed architecture information
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/bottlecrm_mobile_v2/issues) for bug reports
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-username/bottlecrm_mobile_v2/discussions) for questions
- **🔥 Firebase Setup**: [FIREBASE_SETUP.md](FIREBASE_SETUP.md) for Firebase configuration

---

<div align="center">

**BottleCRM Mobile** - Free CRM for startups and enterprises

Made with ❤️ using Flutter

</div> 
