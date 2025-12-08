import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FiHome,
    FiUpload,
    FiUser,
    FiUsers,
    FiLogOut,
    FiMenu,
    FiX,
    FiFileText,
} from 'react-icons/fi';
import useAuthStore from '../store/authStore';

const Sidebar = () => {
    const [isCollapsed, setIsCollapsed] = useState(false);
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const menuItems = [
        { path: '/dashboard', icon: FiHome, label: 'Dashboard', roles: [] },
        {
            path: '/upload',
            icon: FiUpload,
            label: 'Upload Document',
            roles: ['SENIOR_ANALYST', 'SUPER_ADMIN'],
        },
        { path: '/profile', icon: FiUser, label: 'Profile', roles: [] },
        {
            path: '/onboarding',
            icon: FiUsers,
            label: 'Onboarding',
            roles: ['SUPER_ADMIN'],
        },
    ];

    const filteredMenuItems = menuItems.filter(
        (item) => item.roles.length === 0 || (user && item.roles.includes(user.role))
    );

    return (
        <motion.div
            initial={false}
            animate={{ width: isCollapsed ? 80 : 280 }}
            className="glass h-screen flex flex-col border-r border-dark-600 relative"
        >
            {/* Header */}
            <div className="p-6 flex items-center justify-between border-b border-dark-600">
                <AnimatePresence mode="wait">
                    {!isCollapsed && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex items-center gap-3"
                        >
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center">
                                <FiFileText className="text-white text-xl" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold gradient-text">Jalsetu</h1>
                                <p className="text-xs text-gray-500">Document System</p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                >
                    {isCollapsed ? <FiMenu className="text-xl" /> : <FiX className="text-xl" />}
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
                {filteredMenuItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                                ? 'bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg shadow-primary-500/30'
                                : 'text-gray-400 hover:bg-dark-700 hover:text-white'
                            }`
                        }
                    >
                        <item.icon className="text-xl flex-shrink-0" />
                        <AnimatePresence mode="wait">
                            {!isCollapsed && (
                                <motion.span
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="font-medium"
                                >
                                    {item.label}
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </NavLink>
                ))}
            </nav>

            {/* User Profile & Logout */}
            <div className="p-4 border-t border-dark-600">
                {user && (
                    <div className="mb-3 p-3 glass-light rounded-lg">
                        <AnimatePresence mode="wait">
                            {!isCollapsed ? (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <p className="font-medium text-sm text-white truncate">
                                        {user.first_name || user.username}
                                    </p>
                                    <p className="text-xs text-gray-500 truncate">{user.email}</p>
                                    <span className="inline-block mt-1 px-2 py-0.5 bg-primary-600/20 text-primary-400 text-xs rounded">
                                        {user.role}
                                    </span>
                                </motion.div>
                            ) : (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto"
                                >
                                    <span className="text-white font-bold">
                                        {user.first_name?.[0] || user.username?.[0] || 'U'}
                                    </span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}
                <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-400 hover:bg-red-500/10 transition-all duration-200"
                >
                    <FiLogOut className="text-xl flex-shrink-0" />
                    <AnimatePresence mode="wait">
                        {!isCollapsed && (
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="font-medium"
                            >
                                Logout
                            </motion.span>
                        )}
                    </AnimatePresence>
                </button>
            </div>
        </motion.div>
    );
};

export default Sidebar;
