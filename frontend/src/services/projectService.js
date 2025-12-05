import api from './api';
import { mockApi } from './mockApi';
import { USE_MOCK_API } from '../config';

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

    // Chats
    async getProjectChats(projectId) {
        if (USE_MOCK_API) {
            return mockApi.getProjectChats(projectId);
        }
        const response = await api.get(`/projects/${projectId}/chats/`);
        return response.data;
    },

    async createChat(projectId, data) {
        if (USE_MOCK_API) {
            return mockApi.createChat(projectId, data);
        }
        const response = await api.post(`/projects/${projectId}/chats/`, data);
        return response.data;
    },

    // Messages
    async getChatMessages(chatId) {
        if (USE_MOCK_API) {
            return mockApi.getChatMessages(chatId);
        }
        const response = await api.get(`/chats/${chatId}/messages/`);
        return response.data;
    },

    async sendMessage(chatId, data) {
        if (USE_MOCK_API) {
            return mockApi.sendMessage(chatId, data);
        }
        const response = await api.post(`/chats/${chatId}/messages/`, data);
        return response.data;
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
