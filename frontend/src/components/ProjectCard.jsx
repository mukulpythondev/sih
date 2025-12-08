import React from 'react';
import { motion } from 'framer-motion';
import { FiFolder, FiFileText, FiMessageSquare, FiClock } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

const ProjectCard = ({ project }) => {
    const navigate = useNavigate();

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.02 }}
            onClick={() => navigate(`/projects/${project.id}`)}
            className="card cursor-pointer group hover:shadow-2xl transition-all duration-300"
        >
            <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center flex-shrink-0 shadow-lg group-hover:shadow-primary-500/50 transition-shadow">
                    <FiFolder className="text-white text-xl" />
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-bold text-white mb-1 truncate group-hover:text-primary-400 transition-colors">
                        {project.name}
                    </h3>
                    <p className="text-gray-500 text-sm line-clamp-2 mb-3">
                        {project.description || 'No description'}
                    </p>

                    <div className="flex items-center gap-4 text-xs text-gray-600">
                        <div className="flex items-center gap-1">
                            <FiFileText className="text-blue-400" />
                            <span>{project.document_count} docs</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <FiMessageSquare className="text-purple-400" />
                            <span>{project.chat_count} chats</span>
                        </div>
                        <div className="flex items-center gap-1 ml-auto">
                            <FiClock className="text-gray-500" />
                            <span>{formatDate(project.updated_at)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default ProjectCard;
