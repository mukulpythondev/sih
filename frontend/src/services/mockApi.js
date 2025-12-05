// Mock API service for testing without backend

// Mock users database
const mockUsers = {
    admin: {
        username: 'admin',
        password: 'Admin@123',
        user: {
            id: 1,
            username: 'admin',
            email: 'admin@jalsetu.com',
            first_name: 'Super',
            last_name: 'Admin',
            role: 'SUPER_ADMIN',
            department: 'Administration',
            login_count: 42,
        },
    },
    analyst1: {
        username: 'analyst1',
        password: 'Analyst@123',
        user: {
            id: 2,
            username: 'analyst1',
            email: 'analyst@jalsetu.com',
            first_name: 'John',
            last_name: 'Doe',
            role: 'SENIOR_ANALYST',
            department: 'Research',
            login_count: 15,
        },
    },
    user1: {
        username: 'user1',
        password: 'User@123',
        user: {
            id: 3,
            username: 'user1',
            email: 'user@jalsetu.com',
            first_name: 'Jane',
            last_name: 'Smith',
            role: 'ANALYST',
            department: 'Operations',
            login_count: 8,
        },
    },
    newuser: {
        username: 'newuser',
        password: 'TempPass123',
        mustChangePassword: true,
        user: {
            id: 4,
            username: 'newuser',
            email: 'newuser@jalsetu.com',
            first_name: '',
            last_name: '',
            role: 'ANALYST',
            department: '',
            login_count: 1,
        },
    },
};

// Mock projects database
let mockProjects = [
    {
        id: 1,
        name: 'Water Quality Analysis',
        description: 'Analysis of water quality data from various sources',
        created_at: '2025-11-20T10:00:00Z',
        updated_at: '2025-11-30T15:30:00Z',
        user_id: 1,
        document_count: 3,
        chat_count: 2,
    },
    {
        id: 2,
        name: 'Pollution Monitoring',
        description: 'Monitoring pollution levels across different regions',
        created_at: '2025-11-25T14:20:00Z',
        updated_at: '2025-11-29T09:15:00Z',
        user_id: 1,
        document_count: 1,
        chat_count: 1,
    },
    {
        id: 3,
        name: 'Environmental Impact Study',
        description: 'Comprehensive study on environmental impact of industrial activities in the region',
        created_at: '2025-11-28T08:00:00Z',
        updated_at: '2025-12-01T18:45:00Z',
        user_id: 1,
        document_count: 5,
        chat_count: 3,
    },
];

// Mock chats database
let mockChats = [
    {
        id: 1,
        project_id: 1,
        name: 'Initial Analysis',
        created_at: '2025-11-20T10:30:00Z',
        message_count: 5,
    },
    {
        id: 2,
        project_id: 1,
        name: 'Follow-up Questions',
        created_at: '2025-11-28T16:00:00Z',
        message_count: 3,
    },
    {
        id: 3,
        project_id: 2,
        name: 'General Discussion',
        created_at: '2025-11-25T14:30:00Z',
        message_count: 2,
    },
    {
        id: 4,
        project_id: 3,
        name: 'Impact Assessment',
        created_at: '2025-11-28T09:00:00Z',
        message_count: 8,
    },
    {
        id: 5,
        project_id: 3,
        name: 'Mitigation Strategies',
        created_at: '2025-11-30T14:15:00Z',
        message_count: 6,
    },
    {
        id: 6,
        project_id: 3,
        name: 'Compliance Review',
        created_at: '2025-12-01T11:30:00Z',
        message_count: 4,
    },
];

// Mock messages database
let mockMessages = [
    {
        id: 1,
        chat_id: 1,
        content: 'What are the key findings from the water quality data?',
        sender: 'user',
        timestamp: '2025-11-20T10:35:00Z',
        attachments: [],
    },
    {
        id: 2,
        chat_id: 1,
        content: 'Based on the uploaded documents, the key findings show elevated pH levels in 3 out of 5 samples, indicating potential contamination.',
        sender: 'assistant',
        timestamp: '2025-11-20T10:35:30Z',
        attachments: [],
        citations: [
            {
                document_id: 1,
                document_name: 'water_sample_report.pdf',
                page_number: 3,
                excerpt: 'pH levels ranged from 8.2 to 9.1 in samples A, C, and E'
            },
            {
                document_id: 2,
                document_name: 'lab_results.xlsx',
                page_number: 1,
                excerpt: 'Sample analysis summary'
            }
        ]
    },
    {
        id: 3,
        chat_id: 4,
        content: 'Can you summarize the main environmental impacts identified in the baseline study?',
        sender: 'user',
        timestamp: '2025-11-28T09:15:00Z',
        attachments: [],
    },
    {
        id: 4,
        chat_id: 4,
        content: 'The baseline study identifies three major impacts: 1) Air quality degradation due to particulate matter emissions, 2) Soil contamination from industrial runoff, and 3) Disruption to local wildlife habitats. Each impact has been assessed with severity ratings.',
        sender: 'assistant',
        timestamp: '2025-11-28T09:15:45Z',
        attachments: [],
        citations: [
            {
                document_id: 3,
                document_name: 'environmental_baseline_study.pdf',
                page_number: 12,
                excerpt: 'Air Quality Impact Assessment - PM2.5 and PM10 levels'
            },
            {
                document_id: 3,
                document_name: 'environmental_baseline_study.pdf',
                page_number: 18,
                excerpt: 'Soil contamination analysis showing heavy metal concentrations'
            },
            {
                document_id: 6,
                document_name: 'wildlife_impact_assessment.pdf',
                page_number: 5,
                excerpt: 'Habitat disruption severity matrix'
            }
        ]
    },
    {
        id: 5,
        chat_id: 4,
        content: 'What are the recommended mitigation measures for the air quality issues?',
        sender: 'user',
        timestamp: '2025-11-28T09:20:00Z',
        attachments: [],
    },
    {
        id: 6,
        chat_id: 4,
        content: 'Recommended measures include: installing high-efficiency particulate air (HEPA) filters, implementing a green buffer zone around the facility, regular monitoring of air quality, and transitioning to cleaner fuel sources where possible.',
        sender: 'assistant',
        timestamp: '2025-11-28T09:20:30Z',
        attachments: [],
        citations: [
            {
                document_id: 3,
                document_name: 'environmental_baseline_study.pdf',
                page_number: 45,
                excerpt: 'Mitigation strategies for air quality management'
            }
        ]
    },
];

// Mock documents database
let mockDocuments = [
    {
        id: 1,
        project_id: 1,
        filename: 'water_sample_report.pdf',
        file_size: 2048576,
        file_type: 'application/pdf',
        uploaded_at: '2025-11-20T10:15:00Z',
        status: 'READY',
    },
    {
        id: 2,
        project_id: 1,
        filename: 'lab_results.xlsx',
        file_size: 1024000,
        file_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        uploaded_at: '2025-11-22T14:20:00Z',
        status: 'READY',
    },
    {
        id: 3,
        project_id: 3,
        filename: 'environmental_baseline_study.pdf',
        file_size: 4567890,
        file_type: 'application/pdf',
        uploaded_at: '2025-11-28T08:30:00Z',
        status: 'READY',
    },
    {
        id: 4,
        project_id: 3,
        filename: 'air_quality_measurements.csv',
        file_size: 856432,
        file_type: 'text/csv',
        uploaded_at: '2025-11-29T10:15:00Z',
        status: 'READY',
    },
    {
        id: 5,
        project_id: 3,
        filename: 'soil_contamination_report.docx',
        file_size: 1234567,
        file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        uploaded_at: '2025-11-30T13:45:00Z',
        status: 'READY',
    },
    {
        id: 6,
        project_id: 3,
        filename: 'wildlife_impact_assessment.pdf',
        file_size: 3456789,
        file_type: 'application/pdf',
        uploaded_at: '2025-12-01T09:20:00Z',
        status: 'READY',
    },
    {
        id: 7,
        project_id: 3,
        filename: 'regulatory_compliance_checklist.xlsx',
        file_size: 654321,
        file_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        uploaded_at: '2025-12-01T16:30:00Z',
        status: 'READY',
    },
];

// Mock onboarding requests
let mockOnboardingRequests = [
    {
        id: 1,
        email: 'alice@example.com',
        full_name: 'Alice Johnson',
        requested_role: 'SENIOR_ANALYST',
        department: 'Data Science',
        status: 'PENDING',
        created_at: '2025-11-28T10:30:00Z',
        remark: null,
    },
    {
        id: 2,
        email: 'bob@example.com',
        full_name: 'Bob Williams',
        requested_role: 'ANALYST',
        department: 'Finance',
        status: 'PENDING',
        created_at: '2025-11-29T14:20:00Z',
        remark: null,
    },
    {
        id: 3,
        email: 'charlie@example.com',
        full_name: 'Charlie Brown',
        requested_role: 'SENIOR_ANALYST',
        department: 'Engineering',
        status: 'APPROVED',
        created_at: '2025-11-25T09:15:00Z',
        remark: 'Approved based on manager recommendation',
    },
    {
        id: 4,
        email: 'diana@example.com',
        full_name: 'Diana Prince',
        requested_role: 'ADMIN',
        department: 'Security',
        status: 'REJECTED',
        created_at: '2025-11-26T16:45:00Z',
        remark: 'Insufficient clearance level',
    },
];

// Current logged in user (for profile updates)
let currentUser = null;

// Helper to simulate API delay
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Mock API implementation
export const mockApi = {
    // Login
    login: async (username, password) => {
        await delay(500);

        const user = mockUsers[username];
        if (!user || user.password !== password) {
            throw {
                response: {
                    status: 401,
                    data: { detail: 'Invalid username or password' },
                },
            };
        }

        currentUser = { ...user.user };

        return {
            access: `mock-access-token-${user.user.id}`,
            refresh: `mock-refresh-token-${user.user.id}`,
            must_change_password: user.mustChangePassword || false,
            user: user.user,
        };
    },

    // Refresh token
    refreshToken: async (refreshToken) => {
        await delay(300);
        return {
            access: `mock-access-token-refreshed-${Date.now()}`,
        };
    },

    // Get profile
    getProfile: async () => {
        await delay(300);
        if (!currentUser) {
            throw {
                response: {
                    status: 401,
                    data: { detail: 'Not authenticated' },
                },
            };
        }
        return currentUser;
    },

    // Update profile
    updateProfile: async (data) => {
        await delay(500);
        if (!currentUser) {
            throw {
                response: {
                    status: 401,
                    data: { detail: 'Not authenticated' },
                },
            };
        }
        currentUser = { ...currentUser, ...data };
        return currentUser;
    },

    // Change password
    changePassword: async (oldPassword, newPassword) => {
        await delay(500);
        // Simulate success
        return { message: 'Password changed successfully' };
    },

    // Submit onboarding request
    submitOnboardingRequest: async (data) => {
        await delay(500);
        const newRequest = {
            id: mockOnboardingRequests.length + 1,
            ...data,
            status: 'PENDING',
            created_at: new Date().toISOString(),
            remark: null,
        };
        mockOnboardingRequests.push(newRequest);
        return newRequest;
    },

    // Get onboarding requests
    getOnboardingRequests: async () => {
        await delay(500);
        return mockOnboardingRequests;
    },

    // Get onboarding request detail
    getOnboardingRequestDetail: async (id) => {
        await delay(300);
        const request = mockOnboardingRequests.find((r) => r.id === parseInt(id));
        if (!request) {
            throw {
                response: {
                    status: 404,
                    data: { detail: 'Request not found' },
                },
            };
        }
        return request;
    },

    // Decide on onboarding request
    decideOnboardingRequest: async (id, action, remark) => {
        await delay(500);
        const request = mockOnboardingRequests.find((r) => r.id === parseInt(id));
        if (!request) {
            throw {
                response: {
                    status: 404,
                    data: { detail: 'Request not found' },
                },
            };
        }
        request.status = action === 'APPROVE' ? 'APPROVED' : 'REJECTED';
        request.remark = remark;
        return request;
    },

    // Upload document
    uploadDocument: async (formData, onUploadProgress) => {
        // Simulate upload progress
        for (let i = 0; i <= 100; i += 10) {
            await delay(100);
            if (onUploadProgress) {
                onUploadProgress({ loaded: i, total: 100 });
            }
        }

        return {
            document_id: Math.floor(Math.random() * 1000) + 100,
            version_id: 1,
            job_id: `job-mock-${Date.now()}`,
            job_status: 'RUNNING',
            doc_status: 'PROCESSING',
        };
    },

    // Get job status
    getJobStatus: async (jobId) => {
        await delay(500);

        // Simulate job progression
        const random = Math.random();
        if (random < 0.3) {
            return {
                id: jobId,
                status: 'RUNNING',
                error_message: null,
                created_at: new Date(Date.now() - 10000).toISOString(),
                started_at: new Date(Date.now() - 8000).toISOString(),
                finished_at: null,
            };
        } else if (random < 0.9) {
            return {
                id: jobId,
                status: 'COMPLETED',
                error_message: null,
                created_at: new Date(Date.now() - 10000).toISOString(),
                started_at: new Date(Date.now() - 8000).toISOString(),
                finished_at: new Date().toISOString(),
            };
        } else {
            return {
                id: jobId,
                status: 'FAILED',
                error_message: 'Simulated processing error for testing',
                created_at: new Date(Date.now() - 10000).toISOString(),
                started_at: new Date(Date.now() - 8000).toISOString(),
                finished_at: new Date().toISOString(),
            };
        }
    },

    // Projects
    getProjects: async () => {
        await delay(500);
        if (!currentUser) {
            throw {
                response: {
                    status: 401,
                    data: { detail: 'Not authenticated' },
                },
            };
        }
        // Return projects for current user
        return mockProjects.filter((p) => p.user_id === currentUser.id);
    },

    getProject: async (projectId) => {
        await delay(300);
        const project = mockProjects.find((p) => p.id === parseInt(projectId));
        if (!project) {
            throw {
                response: {
                    status: 404,
                    data: { detail: 'Project not found' },
                },
            };
        }
        return project;
    },

    createProject: async (data) => {
        await delay(500);
        if (!currentUser) {
            throw {
                response: {
                    status: 401,
                    data: { detail: 'Not authenticated' },
                },
            };
        }
        const newProject = {
            id: Math.max(...mockProjects.map((p) => p.id), 0) + 1,
            name: data.name,
            description: data.description || '',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            user_id: currentUser.id,
            document_count: 0,
            chat_count: 0,
        };
        mockProjects.push(newProject);
        return newProject;
    },

    updateProject: async (projectId, data) => {
        await delay(500);
        const project = mockProjects.find((p) => p.id === parseInt(projectId));
        if (!project) {
            throw {
                response: {
                    status: 404,
                    data: { detail: 'Project not found' },
                },
            };
        }
        Object.assign(project, data, { updated_at: new Date().toISOString() });
        return project;
    },

    deleteProject: async (projectId) => {
        await delay(500);
        const index = mockProjects.findIndex((p) => p.id === parseInt(projectId));
        if (index === -1) {
            throw {
                response: {
                    status: 404,
                    data: { detail: 'Project not found' },
                },
            };
        }
        mockProjects.splice(index, 1);
        // Also delete related chats, messages, and documents
        mockChats = mockChats.filter((c) => c.project_id !== parseInt(projectId));
        mockDocuments = mockDocuments.filter((d) => d.project_id !== parseInt(projectId));
        return { message: 'Project deleted successfully' };
    },

    // Chats
    getProjectChats: async (projectId) => {
        await delay(300);
        return mockChats.filter((c) => c.project_id === parseInt(projectId));
    },

    createChat: async (projectId, data) => {
        await delay(500);
        const newChat = {
            id: Math.max(...mockChats.map((c) => c.id), 0) + 1,
            project_id: parseInt(projectId),
            name: data.name || `Chat ${new Date().toLocaleString()}`,
            created_at: new Date().toISOString(),
            message_count: 0,
        };
        mockChats.push(newChat);

        // Update project chat count
        const project = mockProjects.find((p) => p.id === parseInt(projectId));
        if (project) {
            project.chat_count += 1;
        }

        return newChat;
    },

    // Messages
    getChatMessages: async (chatId) => {
        await delay(300);
        return mockMessages.filter((m) => m.chat_id === parseInt(chatId));
    },

    sendMessage: async (chatId, data) => {
        await delay(800); // Simulate AI response time

        // Add user message
        const userMessage = {
            id: Math.max(...mockMessages.map((m) => m.id), 0) + 1,
            chat_id: parseInt(chatId),
            content: data.content,
            sender: 'user',
            timestamp: new Date().toISOString(),
            attachments: data.attachments || [],
        };
        mockMessages.push(userMessage);

        // Simulate AI response
        const aiMessage = {
            id: userMessage.id + 1,
            chat_id: parseInt(chatId),
            content: `This is a simulated AI response to: "${data.content}". In production, this would be replaced with actual AI-generated content based on the project documents.`,
            sender: 'assistant',
            timestamp: new Date(Date.now() + 1000).toISOString(),
            attachments: [],
        };
        mockMessages.push(aiMessage);

        // Update chat message count
        const chat = mockChats.find((c) => c.id === parseInt(chatId));
        if (chat) {
            chat.message_count += 2;
        }

        return { user: userMessage, assistant: aiMessage };
    },

    // Documents
    getProjectDocuments: async (projectId) => {
        await delay(300);
        return mockDocuments.filter((d) => d.project_id === parseInt(projectId));
    },

    uploadDocumentToProject: async (projectId, formData, onUploadProgress) => {
        // Simulate upload progress
        for (let i = 0; i <= 100; i += 10) {
            await delay(100);
            if (onUploadProgress) {
                onUploadProgress({ loaded: i, total: 100 });
            }
        }

        const newDocument = {
            id: Math.max(...mockDocuments.map((d) => d.id), 0) + 1,
            project_id: parseInt(projectId),
            filename: `document_${Date.now()}.pdf`,
            file_size: Math.floor(Math.random() * 5000000) + 500000,
            file_type: 'application/pdf',
            uploaded_at: new Date().toISOString(),
            status: 'READY',
        };
        mockDocuments.push(newDocument);

        // Update project document count
        const project = mockProjects.find((p) => p.id === parseInt(projectId));
        if (project) {
            project.document_count += 1;
        }

        return newDocument;
    },

    deleteDocument: async (projectId, documentId) => {
        await delay(300);
        const index = mockDocuments.findIndex((d) => d.id === parseInt(documentId));
        if (index === -1) {
            throw {
                response: {
                    status: 404,
                    data: { detail: 'Document not found' },
                },
            };
        }
        mockDocuments.splice(index, 1);

        // Update project document count
        const project = mockProjects.find((p) => p.id === parseInt(projectId));
        if (project) {
            project.document_count = Math.max(0, project.document_count - 1);
        }

        return { message: 'Document deleted successfully' };
    },
};
