# Hintify - AI-Powered Study Assistant

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/AryanVBW/Hintify)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/AryanVBW/Hintify)

**Hintify SnapAssist AI** is an intelligent study companion that provides instant homework hints and guidance. Using advanced AI technology and OCR, it analyzes screenshots of questions and provides helpful hints without giving away the complete answers.

## 🌟 Features

### 🤖 **AI-Powered Hints**
- **Smart Analysis**: Automatically classifies questions (MCQ, Descriptive, etc.)
- **Difficulty Assessment**: Detects question difficulty levels
- **Progressive Hints**: Provides step-by-step guidance without spoilers
- **Multi-Provider Support**: Gemini AI and Ollama integration

### 📸 **Screenshot Processing**
- **Instant Capture**: One-click screenshot functionality
- **Advanced OCR**: Text extraction from images using Tesseract
- **Clipboard Integration**: Process copied images with hotkeys
- **Global Shortcuts**: `Cmd+Shift+H` (Mac) / `Ctrl+Shift+H` (Windows)

### 🔐 **User Authentication & Data Management**
- **Seamless Sign-In**: Web-based authentication with deep link integration
- **Database Integration**: Neon PostgreSQL for data persistence
- **Automatic Sync**: Real-time data transfer to Portal
- **Privacy Controls**: Data export and management capabilities

### 📊 **Analytics & Tracking**
- **Usage Analytics**: Comprehensive interaction tracking
- **Performance Metrics**: Response times and success rates
- **Session Management**: App usage sessions and statistics
- **History Access**: Complete question/answer timeline

## 🚀 **Quick Start**

### Prerequisites
- **Node.js** 18+ and npm
- **Electron** (automatically installed)
- **macOS 10.12+** / **Windows 10+** / **Linux**

### Installation

```bash
# Clone the repository
git clone https://github.com/AryanVBW/Hintify.git
cd Hintify

# Install dependencies for the app
cd Hintify_app
npm install

# Install dependencies for the website
cd ../Hintidy_website
npm install
```

### Configuration

1. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   ```

2. **Configure your `.env.local`**:
   ```env
   # Database Configuration
   DATABASE_URL=\"your_neon_database_url\"
   
   # Authentication
   NEXT_PUBLIC_STACK_PROJECT_ID=\"your_stack_project_id\"
   STACK_SECRET_SERVER_KEY=\"your_stack_secret_key\"
   
   # AI Provider (choose one)
   GEMINI_API_KEY=\"your_gemini_api_key\"
   ```

3. **Set up the database**:
   ```bash
   ./setup-database.sh
   ```

### Running the Application

```bash
# Development mode
cd Hintify_app
npm run dev

# Production mode
npm start
```

### Building for Distribution

```bash
# Build for macOS
npm run build-mac

# Build for Windows
npm run build-win

# Build for Linux
npm run build-linux
```

## 🏗️ **Project Structure**

```
Hintify/
├── Hintify_app/                 # Electron desktop application
│   ├── src/
│   │   ├── main.js              # Main Electron process
│   │   ├── renderer/            # Frontend UI
│   │   └── services/            # Backend services
│   │       ├── AuthService.js   # Authentication management
│   │       ├── DatabaseService.js # Database operations
│   │       └── PortalDataTransferService.js # Portal sync
│   └── package.json
├── Hintidy_website/             # Next.js website for authentication
│   ├── app/                     # Next.js app directory
│   ├── components/              # React components
│   └── package.json
├── database_schema.sql          # Database schema
└── docs/                        # Documentation
```

## 🛠️ **Technology Stack**

### Desktop Application
- **Electron**: Cross-platform desktop app framework
- **Node.js**: Backend runtime
- **Tesseract.js**: OCR text extraction
- **Neon PostgreSQL**: Database for data persistence

### Website
- **Next.js 14**: React framework for the web interface
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives

### AI & Machine Learning
- **Google Gemini**: Advanced AI for hint generation
- **Ollama**: Local AI model support
- **Custom Prompt Engineering**: Optimized for educational hints

### Database & Authentication
- **Neon**: Serverless PostgreSQL database
- **Stack Auth**: Modern authentication system
- **JWT**: Secure token-based authentication

## 🔧 **Configuration Options**

### AI Providers

#### Gemini AI (Recommended)
```env
GEMINI_API_KEY=\"your_api_key_here\"
GEMINI_MODEL=\"gemini-2.0-flash\"  # or gemini-1.5-pro
```

#### Ollama (Local)
```bash
# Install Ollama
brew install ollama  # macOS

# Pull a vision model
ollama pull granite3.2-vision:2b
```

### Themes
- **Dark Mode** (default)
- **Light Mode**
- **Glass Mode**

## 📱 **Usage Guide**

### Getting Started
1. **Complete Onboarding**: Set up AI provider and preferences
2. **Sign In**: Authenticate through the web interface
3. **Take Screenshots**: Use capture button or global hotkey
4. **Get Hints**: AI analyzes and provides step-by-step guidance

### Keyboard Shortcuts
- `Cmd+Shift+H` (Mac) / `Ctrl+Shift+H` (Windows): Global screenshot capture
- `Cmd+Shift+V` (Mac) / `Ctrl+Shift+V` (Windows): Process clipboard image
- `Cmd+,` (Mac) / `Ctrl+,` (Windows): Open settings

### Question Types Supported
- **Multiple Choice Questions (MCQ)**
- **Descriptive Questions**
- **Mathematical Problems**
- **Scientific Diagrams**
- **Text-based Questions**

## 🔐 **Privacy & Security**

- **Local Processing**: OCR and analysis happen on your device
- **Encrypted Storage**: Database connections use SSL/TLS
- **User Control**: Export and delete your data anytime
- **GDPR Compliant**: Full data transparency and control

## 🌐 **Website Deployment**

The Hintify website is deployed on Vercel and serves as the authentication portal:

```bash
# Deploy to Vercel
cd Hintidy_website
npm run build
vercel deploy
```

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `npm test`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Google Gemini** for advanced AI capabilities
- **Tesseract.js** for OCR functionality
- **Electron** for cross-platform desktop development
- **Next.js** for the web framework
- **Neon** for serverless PostgreSQL

## 📞 **Support**

- **Email**: demo@hintify.app
- **GitHub Issues**: [Report a bug](https://github.com/AryanVBW/Hintify/issues)
- **Documentation**: [Full documentation](https://github.com/AryanVBW/Hintify/wiki)

## 🚀 **Roadmap**

- [ ] **Mobile App**: iOS and Android versions
- [ ] **Advanced AI**: Custom model training
- [ ] **Collaboration**: Study groups and sharing
- [ ] **Integrations**: Google Classroom, Canvas, etc.
- [ ] **Offline Mode**: Complete offline functionality

---

**Built with ❤️ by [AryanVBW](https://github.com/AryanVBW)**

*Hintify - Making learning smarter, one hint at a time.*