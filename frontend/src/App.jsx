import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import ChangePassword from './pages/ChangePassword';
import OnboardingRequest from './pages/OnboardingRequest';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import DocumentUpload from './pages/DocumentUpload';
import OnboardingManagement from './pages/OnboardingManagement';
import ProjectWorkspace from './pages/ProjectWorkspace';

function App() {
    const { initAuth, isLoading } = useAuthStore();

    useEffect(() => {
        initAuth();
    }, [initAuth]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-dark-950">
                <div className="spinner w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    return (
        <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/onboarding-request" element={<OnboardingRequest />} />

            {/* Protected Routes */}
            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <Dashboard />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/projects/:projectId"
                element={
                    <ProtectedRoute>
                        <ProjectWorkspace />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/profile"
                element={
                    <ProtectedRoute>
                        <Profile />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/change-password"
                element={
                    <ProtectedRoute>
                        <ChangePassword />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/upload"
                element={
                    <ProtectedRoute allowedRoles={['SENIOR_ANALYST', 'SUPER_ADMIN']}>
                        <DocumentUpload />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/onboarding"
                element={
                    <ProtectedRoute allowedRoles={['SUPER_ADMIN']}>
                        <OnboardingManagement />
                    </ProtectedRoute>
                }
            />

            {/* Default Redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
    );
}

export default App;
