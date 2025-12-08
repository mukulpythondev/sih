import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiLock, FiUser, FiAlertCircle } from 'react-icons/fi';
import toast from 'react-hot-toast';
import useAuthStore from '../store/authStore';
import { authService } from '../services/authService';
import LoadingSpinner from '../components/LoadingSpinner';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const setAuth = useAuthStore((state) => state.setAuth);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const response = await authService.login(username, password);
            const { access, refresh, user, must_change_password } = response;

            // Set authentication
            await setAuth(user, access, refresh);

            toast.success('Login successful!');

            // Redirect based on must_change_password flag
            if (must_change_password) {
                navigate('/change-password', { state: { firstLogin: true } });
            } else {
                navigate('/dashboard');
            }
        } catch (err) {
            const errorMessage =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                'Invalid username or password';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-dark-950 relative overflow-hidden">
            {/* Animated Background */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-1/2 -left-1/2 w-full h-full bg-gradient-to-br from-primary-600/20 to-transparent rounded-full blur-3xl animate-pulse-slow"></div>
                <div className="absolute -bottom-1/2 -right-1/2 w-full h-full bg-gradient-to-tl from-primary-700/20 to-transparent rounded-full blur-3xl animate-pulse-slow"></div>
            </div>

            {/* Login Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card max-w-md w-full mx-4 relative z-10"
            >
                {/* Logo & Title */}
                <div className="text-center mb-8">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-500/50">
                        <FiLock className="text-white text-3xl" />
                    </div>
                    <h1 className="text-3xl font-bold gradient-text mb-2">Welcome to Jalsetu</h1>
                    <p className="text-gray-500">Sign in to access the document management system</p>
                </div>

                {/* Error Alert */}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3"
                    >
                        <FiAlertCircle className="text-red-400 text-xl flex-shrink-0 mt-0.5" />
                        <p className="text-red-400 text-sm">{error}</p>
                    </motion.div>
                )}

                {/* Login Form */}
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                        <div className="relative">
                            <FiUser className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="input-field pl-11"
                                placeholder="Enter your username"
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                        <div className="relative">
                            <FiLock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="input-field pl-11"
                                placeholder="Enter your password"
                                required
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? (
                            <>
                                <LoadingSpinner size="sm" />
                                <span>Signing in...</span>
                            </>
                        ) : (
                            'Sign In'
                        )}
                    </button>
                </form>

                {/* Onboarding Link */}
                <div className="mt-6 text-center">
                    <p className="text-gray-500 text-sm">
                        Don't have an account?{' '}
                        <button
                            onClick={() => navigate('/onboarding-request')}
                            className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
                        >
                            Request Access
                        </button>
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Login;
