# Jalsetu Desktop Application

A modern desktop application for document management built with Electron, React, Vite, and Tailwind CSS, featuring a DeepSeek-inspired UI.

## 🚀 Quick Start

### Installation
```bash
npm install
```

### Development (with Mock API)
```bash
# Terminal 1: Start Vite dev server
npm run dev

# Terminal 2: Start Electron
npm run electron:dev
```

### Test Credentials (Mock API)
- **Super Admin**: `admin` / `Admin@123`
- **Senior Analyst**: `analyst1` / `Analyst@123`
- **Analyst**: `user1` / `User@123`

See [TESTING.md](./TESTING.md) for complete testing guide.

---

## 📋 Features

- 🔐 **JWT Authentication** - Secure login with token refresh
- 📄 **Document Upload** - Drag-and-drop file upload with progress tracking
- 👥 **User Management** - Profile management and onboarding workflow
- 🎨 **Modern UI** - DeepSeek-inspired dark theme with glassmorphism
- 🔒 **Role-Based Access** - SUPER_ADMIN, SENIOR_ANALYST, ANALYST roles
- 💾 **Persistent Storage** - Secure credential storage with electron-store
- 🧪 **Mock API** - Test without backend using mock data

---

## ⚙️ Configuration

### Switch Between Mock and Real API

**Mock API (Testing - Default)**
```javascript
// src/config.js
export const USE_MOCK_API = true;
```

**Real Backend API (Production)**
```javascript
// src/config.js
export const USE_MOCK_API = false;
export const API_BASE_URL = 'http://localhost:8000/api';
```

---

## 🛠️ Tech Stack

- **Electron** - Desktop application framework
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Zustand** - State management
- **Axios** - HTTP client
- **Framer Motion** - Animation library
- **React Router** - Client-side routing
- **React Hot Toast** - Toast notifications
- **React Dropzone** - File upload

---

## 📁 Project Structure

```
frontend-jalsetu/
├── electron/              # Electron main process
│   ├── main.js           # Main process entry
│   └── preload.js        # Preload script
├── src/
│   ├── components/       # Reusable components
│   ├── pages/            # Application pages
│   ├── services/         # API services
│   │   ├── api.js        # Axios instance
│   │   ├── authService.js
│   │   ├── ingestionService.js
│   │   └── mockApi.js    # Mock API for testing
│   ├── store/            # State management
│   ├── config.js         # App configuration
│   ├── App.jsx           # Main app component
│   └── index.css         # Global styles
├── TESTING.md            # Testing guide
└── README.md
```

---

## 🎯 Role-Based Access

| Feature | ANALYST | SENIOR_ANALYST | SUPER_ADMIN |
|---------|---------|----------------|-------------|
| Dashboard | ✓ | ✓ | ✓ |
| Profile | ✓ | ✓ | ✓ |
| Document Upload | ✗ | ✓ | ✓ |
| Onboarding Management | ✗ | ✗ | ✓ |

---

## 🏗️ Building for Production

```bash
# Build React app
npm run build

# Build Electron app
npm run electron:build
```

The built application will be in the `release` folder.

---

## 📚 Documentation

- [TESTING.md](./TESTING.md) - Complete testing guide with mock credentials
- [Implementation Plan](./docs/implementation_plan.md) - Technical implementation details
- [Walkthrough](./docs/walkthrough.md) - Feature walkthrough

---

## 🔌 API Integration

The application integrates with the Jalsetu backend API:

- **Base URL**: `/api/`
- **Auth Endpoints**: `/auth/login/`, `/auth/token/refresh/`, `/auth/me/`, etc.
- **Ingestion Endpoints**: `/ingestion/upload/`, `/ingestion/jobs/{id}/`

See `src/services/` for full API integration.

---

## 🎨 UI Features

- DeepSeek-inspired dark theme (#0f172a)
- Glassmorphism effects with backdrop blur
- Purple/blue gradient accents (#667eea → #764ba2)
- Smooth animations with Framer Motion
- Collapsible sidebar navigation
- Toast notifications
- Loading states

---

## 📝 License

MIT
