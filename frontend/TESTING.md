# 🧪 Mock API Testing Guide

## Quick Start

The application is now configured to use **Mock API** for testing without a backend.

### Test Credentials

Login with any of these users:

| Username | Password | Role | Features |
|----------|----------|------|----------|
| `admin` | `Admin@123` | SUPER_ADMIN | All features + Onboarding Management |
| `analyst1` | `Analyst@123` | SENIOR_ANALYST | Dashboard, Profile, Document Upload |
| `user1` | `User@123` | ANALYST | Dashboard, Profile only |
| `newuser` | `TempPass123` | ANALYST | First-login (must change password) |

---

## How to Switch Between Mock and Real API

### Using Mock API (Current - For Testing)

In `src/config.js`:
```javascript
export const USE_MOCK_API = true;
```

### Using Real Backend API (For Production)

In `src/config.js`:
```javascript
export const USE_MOCK_API = false;
export const API_BASE_URL = 'http://localhost:8000/api'; // Update if needed
```

**That's it!** Just change the flag and restart the dev server.

---

## Testing Scenarios

### 1. Login Flow
- **Try**: Login with `admin` / `Admin@123`
- **Expected**: Redirects to Dashboard with SUPER_ADMIN access
- **Try**: Login with `newuser` / `TempPass123`
- **Expected**: Redirects to Password Change page

### 2. Dashboard
- **View**: Stats cards (login count will show real data)
- **View**: Quick action cards (filtered by role)

### 3. Profile Management
- **Edit**: First name, last name, department
- **Save**: Changes persist in mock storage
- **Navigate**: Click "Change Password"

### 4. Password Change
- **Test**: Real-time validation
- **Requirements**: 8+ chars, uppercase, lowercase, number, special char
- **Success**: Shows success toast

### 5. Document Upload (SENIOR_ANALYST or SUPER_ADMIN)
- **Upload**: Any file (PDF, DOCX, TXT, images, audio)
- **Watch**: Progress bar (0-100%)
- **Watch**: Job status polling (RUNNING → COMPLETED/FAILED)
- **Note**: Mock API randomly returns COMPLETED (90%) or FAILED (10%)

### 6. Onboarding Management (SUPER_ADMIN only)
- **View**: 4 mock requests (2 pending, 1 approved, 1 rejected)
- **Approve**: Add remark and approve a pending request
- **Reject**: Add remark and reject a pending request
- **View**: Status updates in real-time

### 7. Onboarding Request (Public)
- **Submit**: New access request
- **Fields**: Full name, email, department, role
- **Success**: Request added to mock database

---

## Mock Data Details

### Mock Users
- **admin**: Super Admin with full access
- **analyst1**: Senior Analyst (can upload documents)
- **user1**: Regular Analyst (view only)
- **newuser**: First-time user (must change password)

### Mock Onboarding Requests
- **4 requests** with different statuses
- **Pending requests** can be approved/rejected
- **Completed requests** show admin remarks

### Mock Document Upload
- **Simulated progress**: 0% → 100% over ~1 second
- **Job polling**: Returns status every 2 seconds
- **Random completion**: 90% success, 10% failure

---

## What Works in Mock Mode

✅ **Full Authentication**
- Login with credentials
- Token storage (localStorage/electron-store)
- Auto-logout on invalid token
- Password change flow

✅ **Profile Management**
- View user info
- Edit profile fields
- Changes persist in session

✅ **Document Upload**
- File validation
- Upload progress
- Job status polling
- Success/failure simulation

✅ **Onboarding Workflow**
- Submit requests
- View all requests (SUPER_ADMIN)
- Approve/reject with remarks
- Status updates

✅ **Role-Based Access**
- Menu items filtered by role
- Protected routes
- Access denied messages

---

## Switching to Real Backend

When your backend is ready:

1. **Update config**:
   ```javascript
   // src/config.js
   export const USE_MOCK_API = false;
   export const API_BASE_URL = 'http://localhost:8000/api';
   ```

2. **Restart dev server**:
   ```bash
   # Stop current server (Ctrl+C)
   npm run dev
   ```

3. **Test with real data**:
   - Use real credentials from backend
   - Upload actual documents
   - Verify API responses

---

## Troubleshooting

**Q: Login not working?**
- Check you're using exact credentials (case-sensitive)
- Verify `USE_MOCK_API = true` in `src/config.js`

**Q: Can't see Upload menu?**
- Login as `admin` or `analyst1` (SENIOR_ANALYST/SUPER_ADMIN only)

**Q: Can't see Onboarding Management?**
- Login as `admin` (SUPER_ADMIN only)

**Q: Want to reset mock data?**
- Refresh the page or restart the app
- Mock data resets on each reload

---

## Next Steps

1. ✅ Test all features with mock API
2. ✅ Verify UI/UX flows
3. ✅ Test role-based access
4. 🔄 Start backend API
5. 🔄 Switch to `USE_MOCK_API = false`
6. 🔄 Test with real backend

Enjoy testing! 🚀
