import React from 'react';
import { Navigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
    const { isAuthenticated, isLoading, user } = useAuthStore();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-dark-950">
                <div className="spinner w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    // Check role-based access
    if (allowedRoles.length > 0 && user && !allowedRoles.includes(user.role)) {
        return (
            <div className="flex items-center justify-center h-screen bg-dark-950">
                <div className="card max-w-md text-center">
                    <h2 className="text-2xl font-bold text-red-400 mb-2">Access Denied</h2>
                    <p className="text-gray-400">You don't have permission to access this page.</p>
                </div>
            </div>
        );
    }

    return children;
};

export default ProtectedRoute;
