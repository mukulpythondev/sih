import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiChevronLeft, FiUpload, FiFile, FiTrash2, FiDownload } from 'react-icons/fi';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

const DocumentsPanel = ({
    documents,
    isCollapsed,
    onToggleCollapse,
    onUploadDocument,
    onDeleteDocument
}) => {
    const [isUploading, setIsUploading] = useState(false);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: async (acceptedFiles) => {
            if (acceptedFiles.length === 0) return;

            setIsUploading(true);
            try {
                for (const file of acceptedFiles) {
                    await onUploadDocument(file);
                }
                toast.success('Document(s) uploaded successfully!');
            } catch (error) {
                toast.error('Failed to upload document');
                console.error('Upload error:', error);
            } finally {
                setIsUploading(false);
            }
        },
        disabled: isUploading,
    });

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <motion.div
            initial={false}
            animate={{ width: isCollapsed ? 60 : 320 }}
            transition={{ duration: 0.3 }}
            className="glass border-r border-dark-600 flex flex-col overflow-hidden"
        >
            {!isCollapsed ? (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col h-full"
                >
                    {/* Header */}
                    <div className="p-4 border-b border-dark-600 flex items-center justify-between">
                        <h2 className="text-lg font-bold text-white">Sources</h2>
                        <button
                            onClick={onToggleCollapse}
                            className="p-2 hover:bg-dark-700 rounded-lg transition-colors"
                            title="Minimize panel"
                        >
                            <FiChevronLeft className="text-xl text-gray-400" />
                        </button>
                    </div>

                    {/* Upload Zone */}
                    <div className="p-4 border-b border-dark-600">
                        <div
                            {...getRootProps()}
                            className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-all ${isDragActive
                                ? 'border-primary-500 bg-primary-500/10'
                                : 'border-dark-600 hover:border-primary-500/50 hover:bg-dark-700/50'
                                } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <input {...getInputProps()} />
                            <FiUpload className="text-3xl text-primary-400 mx-auto mb-2" />
                            <p className="text-sm text-gray-400">
                                {isUploading ? 'Uploading...' : 'Drop files or click to upload'}
                            </p>
                        </div>
                    </div>

                    {/* Documents List */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-2">
                        {documents.length === 0 ? (
                            <div className="text-center text-gray-500 text-sm py-8">
                                <FiFile className="text-4xl mx-auto mb-2 opacity-50" />
                                <p>No documents yet</p>
                                <p className="text-xs mt-1">Upload files to get started</p>
                            </div>
                        ) : (
                            documents.map((doc) => (
                                <motion.div
                                    key={doc.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="glass-light rounded-lg p-3 group hover:bg-dark-700/50 transition-colors"
                                >
                                    <div className="flex items-start gap-2">
                                        <FiFile className="text-blue-400 mt-1 flex-shrink-0" />
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-white font-medium truncate">
                                                {doc.filename}
                                            </p>
                                            <p className="text-xs text-gray-500">
                                                {formatFileSize(doc.file_size)}
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => onDeleteDocument(doc.id)}
                                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition-all"
                                            title="Delete document"
                                        >
                                            <FiTrash2 className="text-red-400 text-sm" />
                                        </button>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>
                </motion.div>
            ) : (
                /* Collapsed State - Vertical Sidebar */
                <div className="flex flex-col items-center justify-between h-full py-4">
                    <div className="flex flex-col items-center gap-4">
                        <div className="vertical-text text-sm font-semibold text-gray-400">
                            SOURCES
                        </div>
                        <div className="text-gray-500 text-xs">
                            {documents.length}
                        </div>
                    </div>
                    <button
                        onClick={onToggleCollapse}
                        className="p-2 hover:bg-dark-700 rounded-lg transition-colors rotate-180"
                        title="Expand panel"
                    >
                        <FiChevronLeft className="text-xl text-gray-400" />
                    </button>
                </div>
            )}
        </motion.div>
    );
};

export default DocumentsPanel;
