import api from './api';
import { mockApi } from './mockApi';
import { USE_MOCK_API } from '../config';
import { transformChatSession, transformChatMessage, transformArray } from '../utils/dataTransformers';

const projectService = {
    // Projects
    async getProjects() {
        if (USE_MOCK_API) {
            return mockApi.getProjects();
        }
        const response = await api.get('/projects/');
        return response.data;
    },

    async getProject(projectId) {
        if (USE_MOCK_API) {
            return mockApi.getProject(projectId);
        }
        const response = await api.get(`/projects/${projectId}/`);
        return response.data;
    },

    async createProject(data) {
        if (USE_MOCK_API) {
            return mockApi.createProject(data);
        }
        const response = await api.post('/projects/', data);
        return response.data;
    },

    async updateProject(projectId, data) {
        if (USE_MOCK_API) {
            return mockApi.updateProject(projectId, data);
        }
        const response = await api.put(`/projects/${projectId}/`, data);
        return response.data;
    },

    async deleteProject(projectId) {
        if (USE_MOCK_API) {
            return mockApi.deleteProject(projectId);
        }
        const response = await api.delete(`/projects/${projectId}/`);
        return response.data;
    },

    // Chats (chat-sessions in backend)
    async getProjectChats(projectId) {
        if (USE_MOCK_API) {
            return mockApi.getProjectChats(projectId);
        }
        // Backend filters by project automatically based on user membership
        const response = await api.get(`/chat-sessions/?project=${projectId}`);
        // Transform backend format to frontend format
        return transformArray(response.data, transformChatSession);
    },

    async createChat(projectId, data) {
        if (USE_MOCK_API) {
            return mockApi.createChat(projectId, data);
        }
        // Backend expects 'title' instead of 'name', and 'project' field
        const response = await api.post(`/chat-sessions/`, {
            project: projectId,
            title: data.name || data.title || 'New Chat',
            status: 'ACTIVE'
        });
        // Transform response to frontend format
        return transformChatSession(response.data);
    },

    async deleteChat(chatId) {
        if (USE_MOCK_API) {
            return mockApi.deleteChat(chatId);
        }
        const response = await api.delete(`/chat-sessions/${chatId}/`);
        return response.data;
    },

    // Messages (chat-messages in backend)
    async getChatMessages(chatId) {
        if (USE_MOCK_API) {
            return mockApi.getChatMessages(chatId);
        }
        const response = await api.get(`/chat-messages/?session=${chatId}`);
        // Transform backend format to frontend format
        return transformArray(response.data, transformChatMessage);
    },

    async sendMessage(chatId, data) {
        if (USE_MOCK_API) {
            return mockApi.sendMessage(chatId, data);
        }
        // Backend expects 'session', 'role', and 'content'
        const userMessage = await api.post(`/chat-messages/`, {
            session: chatId,
            role: 'USER',
            content: data.content,
            metadata: data.attachments ? { attachments: data.attachments } : null
        });

        // Transform and return user message
        // Note: Backend may send assistant response separately via websocket or polling
        return {
            user: transformChatMessage(userMessage.data),
            assistant: null // Will be handled by real-time updates
        };
    },

    // Documents
    async getProjectDocuments(projectId) {
        if (USE_MOCK_API) {
            return mockApi.getProjectDocuments(projectId);
        }
        const response = await api.get(`/projects/${projectId}/documents/`);
        return response.data;
    },

    async uploadDocumentToProject(projectId, file, onUploadProgress) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId);

        if (USE_MOCK_API) {
            return mockApi.uploadDocumentToProject(projectId, formData, onUploadProgress);
        }

        const response = await api.post(`/projects/${projectId}/documents/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
            onUploadProgress: (progressEvent) => {
                if (onUploadProgress) {
                    onUploadProgress(progressEvent);
                }
            },
        });
        return response.data;
    },

    async deleteDocument(projectId, documentId) {
        if (USE_MOCK_API) {
            return mockApi.deleteDocument(projectId, documentId);
        }
        const response = await api.delete(`/projects/${projectId}/documents/${documentId}/`);
        return response.data;
    },
};

export default projectService;
