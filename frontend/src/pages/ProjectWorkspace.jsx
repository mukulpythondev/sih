import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import Sidebar from '../components/Sidebar';
import DocumentsPanel from '../components/DocumentsPanel';
import ChatPanel from '../components/ChatPanel';
import StudioPanel from '../components/StudioPanel';
import useProjectStore from '../store/projectStore';
import projectService from '../services/projectService';

const ProjectWorkspace = () => {
    const { projectId } = useParams();
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);

    const {
        currentProject,
        setCurrentProject,
        documents,
        setDocuments,
        addDocument,
        deleteDocument: removeDocument,
        chats,
        setChats,
        currentChat,
        setCurrentChat,
        addChat,
        messages,
        setMessages,
        addMessage,
        isLeftPanelCollapsed,
        isRightPanelCollapsed,
        isFullscreenMode,
        toggleLeftPanel,
        toggleRightPanel,
        toggleFullscreen,
        clearCurrentProject,
        deleteChat,
        deleteProject,
    } = useProjectStore();

    const [projects, setProjects] = useState([]);

    // Load project data
    useEffect(() => {
        const loadProject = async () => {
            try {
                setIsLoading(true);

                // Load all projects for the dropdown
                const allProjects = await projectService.getProjects();
                // Sort by updated_at descending (most recent first)
                const sortedProjects = allProjects.sort((a, b) =>
                    new Date(b.updated_at) - new Date(a.updated_at)
                );
                setProjects(sortedProjects);

                // Load project details
                const project = await projectService.getProject(projectId);
                setCurrentProject(project);

                // Load project documents
                const docs = await projectService.getProjectDocuments(projectId);
                setDocuments(docs);

                // Load project chats
                const projectChats = await projectService.getProjectChats(projectId);
                setChats(projectChats);

                // If there are chats, load the first one
                if (projectChats.length > 0) {
                    const firstChat = projectChats[0];
                    setCurrentChat(firstChat);
                    const chatMessages = await projectService.getChatMessages(firstChat.id);
                    setMessages(chatMessages);
                } else {
                    // Create initial chat if none exist
                    const newChat = await projectService.createChat(projectId, {
                        name: 'Initial Chat',
                    });
                    setChats([newChat]);
                    setCurrentChat(newChat);
                    setMessages([]);
                }
            } catch (error) {
                console.error('Error loading project:', error);
                toast.error('Failed to load project');
                navigate('/dashboard');
            } finally {
                setIsLoading(false);
            }
        };

        loadProject();

        return () => {
            clearCurrentProject();
        };
    }, [projectId]);

    // Handle document upload
    const handleUploadDocument = async (file) => {
        try {
            const doc = await projectService.uploadDocumentToProject(
                projectId,
                file,
                (progress) => {
                    console.log('Upload progress:', progress);
                }
            );
            addDocument(doc);
        } catch (error) {
            console.error('Error uploading document:', error);
            throw error;
        }
    };

    // Handle document delete
    const handleDeleteDocument = async (documentId) => {
        try {
            await projectService.deleteDocument(projectId, documentId);
            removeDocument(documentId);
            toast.success('Document deleted');
        } catch (error) {
            console.error('Error deleting document:', error);
            toast.error('Failed to delete document');
        }
    };

    // Handle create new chat
    const handleCreateChat = async () => {
        try {
            const newChat = await projectService.createChat(projectId, {
                name: `Chat ${new Date().toLocaleString()}`,
            });
            addChat(newChat);
        } catch (error) {
            console.error('Error creating chat:', error);
            throw error;
        }
    };

    // Handle select chat
    const handleSelectChat = async (chat) => {
        try {
            setCurrentChat(chat);
            const chatMessages = await projectService.getChatMessages(chat.id);
            setMessages(chatMessages);
        } catch (error) {
            console.error('Error loading chat messages:', error);
            toast.error('Failed to load chat');
        }
    };

    // Handle send message
    const handleSendMessage = async (content) => {
        if (!currentChat) return;

        try {
            const response = await projectService.sendMessage(currentChat.id, {
                content,
                attachments: [],
            });

            // Add both user and assistant messages
            if (response.user) addMessage(response.user);
            if (response.assistant) addMessage(response.assistant);
        } catch (error) {
            console.error('Error sending message:', error);
            toast.error('Failed to send message');
        }
    };

    // Handle create new project
    const handleCreateProject = () => {
        navigate('/dashboard?openModal=true');
    };

    // Handle select project
    const handleSelectProject = (project) => {
        navigate(`/projects/${project.id}`);
    };

    // Handle delete chat
    const handleDeleteChat = async (chatId) => {
        try {
            await projectService.deleteChat(chatId);
            deleteChat(chatId);

            // If we deleted the current chat, select another one or clear
            if (currentChat?.id === chatId) {
                const remainingChats = chats.filter(c => c.id !== chatId);
                if (remainingChats.length > 0) {
                    await handleSelectChat(remainingChats[0]);
                } else {
                    setCurrentChat(null);
                    setMessages([]);
                }
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
            throw error;
        }
    };

    // Handle delete project
    const handleDeleteProject = async (projectId) => {
        try {
            await projectService.deleteProject(projectId);
            deleteProject(projectId);

            // If we deleted the current project, navigate to dashboard
            if (currentProject?.id === projectId) {
                navigate('/dashboard');
            } else {
                // Refresh projects list
                const allProjects = await projectService.getProjects();
                const sortedProjects = allProjects.sort((a, b) =>
                    new Date(b.updated_at) - new Date(a.updated_at)
                );
                setProjects(sortedProjects);
            }
        } catch (error) {
            console.error('Error deleting project:', error);
            throw error;
        }
    };

    if (isLoading) {
        return (
            <div className="flex h-screen bg-dark-950">
                <Sidebar />
                <div className="flex-1 flex items-center justify-center">
                    <div className="spinner w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-dark-950">
            <Sidebar />

            <div className="flex-1 flex overflow-hidden">
                {/* Left Panel - Documents (Always visible, collapsed or expanded) */}
                <DocumentsPanel
                    documents={documents}
                    isCollapsed={isLeftPanelCollapsed || isFullscreenMode}
                    onToggleCollapse={toggleLeftPanel}
                    onUploadDocument={handleUploadDocument}
                    onDeleteDocument={handleDeleteDocument}
                />

                {/* Middle Panel - Chat */}
                <ChatPanel
                    messages={messages}
                    isFullscreen={isFullscreenMode}
                    onToggleFullscreen={toggleFullscreen}
                    onSendMessage={handleSendMessage}
                    currentChat={currentChat}
                />

                {/* Right Panel - Studio (Always visible, collapsed or expanded) */}
                <StudioPanel
                    chats={chats}
                    currentChat={currentChat}
                    currentProject={currentProject}
                    projects={projects}
                    isCollapsed={isRightPanelCollapsed || isFullscreenMode}
                    onToggleCollapse={toggleRightPanel}
                    onSelectChat={handleSelectChat}
                    onSelectProject={handleSelectProject}
                    onCreateChat={handleCreateChat}
                    onCreateProject={handleCreateProject}
                    onDeleteChat={handleDeleteChat}
                    onDeleteProject={handleDeleteProject}
                />
            </div>
        </div>
    );
};

export default ProjectWorkspace;
