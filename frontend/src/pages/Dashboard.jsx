import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FiFileText, FiUpload, FiUsers, FiActivity, FiPlus, FiFolder } from 'react-icons/fi';
import useAuthStore from '../store/authStore';
import useProjectStore from '../store/projectStore';
import Sidebar from '../components/Sidebar';
import ProjectCard from '../components/ProjectCard';
import CreateProjectModal from '../components/CreateProjectModal';
import projectService from '../services/projectService';
import toast from 'react-hot-toast';

const Dashboard = () => {
    const { user } = useAuthStore();
    const { projects, setProjects, addProject } = useProjectStore();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    // Load projects on mount
    useEffect(() => {
        const loadProjects = async () => {
            try {
                setIsLoading(true);
                const userProjects = await projectService.getProjects();
                setProjects(userProjects);
            } catch (error) {
                console.error('Error loading projects:', error);
                toast.error('Failed to load projects');
            } finally {
                setIsLoading(false);
            }
        };

        loadProjects();
    }, [setProjects]);

    // Handle create project
    const handleCreateProject = async (data) => {
        try {
            const newProject = await projectService.createProject(data);
            addProject(newProject);
        } catch (error) {
            console.error('Error creating project:', error);
            throw error;
        }
    };

    const quickActions = [
        {
            icon: FiUpload,
            title: 'Upload Document',
            description: 'Upload and process new documents',
            path: '/upload',
            color: 'from-primary-600 to-primary-700',
            roles: ['SENIOR_ANALYST', 'SUPER_ADMIN'],
        },
        {
            icon: FiUsers,
            title: 'Manage Onboarding',
            description: 'Review and approve access requests',
            path: '/onboarding',
            color: 'from-blue-600 to-blue-700',
            roles: ['SUPER_ADMIN'],
        },
        {
            icon: FiFileText,
            title: 'View Profile',
            description: 'Manage your account settings',
            path: '/profile',
            color: 'from-purple-600 to-purple-700',
            roles: [],
        },
    ];

    const filteredActions = quickActions.filter(
        (action) => action.roles.length === 0 || (user && action.roles.includes(user.role))
    );

    return (
        <div className="flex h-screen bg-dark-950">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
                <div className="p-8">
                    {/* Welcome Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <h1 className="text-4xl font-bold gradient-text mb-2">
                            Welcome back, {user?.first_name || user?.username}!
                        </h1>
                        <p className="text-gray-500">
                            Manage your projects, documents and collaborate with your team
                        </p>
                    </motion.div>

                    {/* Create New Project Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="mb-8"
                    >
                        <h2 className="text-2xl font-bold text-white mb-4">Create Project</h2>
                        <motion.div
                            whileHover={{ scale: 1.02 }}
                            onClick={() => setIsModalOpen(true)}
                            className="card cursor-pointer group hover:shadow-2xl transition-all duration-300 max-w-md"
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-lg group-hover:shadow-primary-500/50 transition-shadow">
                                    <FiPlus className="text-white text-3xl" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-1 group-hover:text-primary-400 transition-colors">
                                        New Project
                                    </h3>
                                    <p className="text-gray-500 text-sm">
                                        Create a new project to organize your documents and chats
                                    </p>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>

                    {/* Featured Projects Section */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="mb-8"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-2xl font-bold text-white">Featured Projects</h2>
                            {projects.length > 0 && (
                                <span className="text-sm text-gray-500">
                                    {projects.length} {projects.length === 1 ? 'project' : 'projects'}
                                </span>
                            )}
                        </div>

                        {isLoading ? (
                            <div className="flex items-center justify-center py-12">
                                <div className="spinner w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
                            </div>
                        ) : projects.length === 0 ? (
                            <div className="card text-center py-12">
                                <FiFolder className="text-6xl text-gray-600 mx-auto mb-4" />
                                <p className="text-gray-500 mb-2">No projects yet</p>
                                <p className="text-sm text-gray-600">
                                    Create your first project to get started
                                </p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {projects.map((project, index) => (
                                    <motion.div
                                        key={project.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.3 + index * 0.1 }}
                                    >
                                        <ProjectCard project={project} />
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </motion.div>

                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                            className="card"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-gray-500 text-sm mb-1">Total Projects</p>
                                    <p className="text-3xl font-bold text-white">{projects.length}</p>
                                </div>
                                <div className="w-12 h-12 rounded-lg bg-primary-500/20 flex items-center justify-center">
                                    <FiFolder className="text-primary-400 text-2xl" />
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                            className="card"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-gray-500 text-sm mb-1">Total Documents</p>
                                    <p className="text-3xl font-bold text-white">
                                        {projects.reduce((sum, p) => sum + p.document_count, 0)}
                                    </p>
                                </div>
                                <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                    <FiFileText className="text-blue-400 text-2xl" />
                                </div>
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.6 }}
                            className="card"
                        >
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-gray-500 text-sm mb-1">Login Count</p>
                                    <p className="text-3xl font-bold text-white">{user?.login_count || 0}</p>
                                </div>
                                <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                    <FiUsers className="text-purple-400 text-2xl" />
                                </div>
                            </div>
                        </motion.div>
                    </div>

                    {/* Quick Actions */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7 }}
                    >
                        <h2 className="text-2xl font-bold text-white mb-4">Quick Actions</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredActions.map((action, index) => (
                                <motion.a
                                    key={action.path}
                                    href={action.path}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.8 + index * 0.1 }}
                                    className="card hover:scale-105 transition-transform duration-200 cursor-pointer group"
                                >
                                    <div
                                        className={`w-14 h-14 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center mb-4 shadow-lg group-hover:shadow-xl transition-shadow`}
                                    >
                                        <action.icon className="text-white text-2xl" />
                                    </div>
                                    <h3 className="text-xl font-bold text-white mb-2">{action.title}</h3>
                                    <p className="text-gray-500 text-sm">{action.description}</p>
                                </motion.a>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </main>

            {/* Create Project Modal */}
            <CreateProjectModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreateProject={handleCreateProject}
            />
        </div>
    );
};

export default Dashboard;

