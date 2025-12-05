// API Endpoints matching Django backend
import apiClient from './client';

// Authentication endpoints
export const authAPI = {
    login: (credentials) => apiClient.post('/auth/login/', credentials),
    logout: () => apiClient.post('/auth/logout/'),
    register: (userData) => apiClient.post('/auth/register/', userData),
    getUser: () => apiClient.get('/auth/user/'),
};

// Wallet endpoints
export const walletAPI = {
    getWallets: () => apiClient.get('/wallets/'),
    getWallet: (id) => apiClient.get(`/wallets/${id}/`),
    getPrimaryWallet: () => apiClient.get('/wallets/primary/'),
    createWallet: (data) => apiClient.post('/wallets/', data),
    updateWallet: (id, data) => apiClient.patch(`/wallets/${id}/`, data),
};

// Transaction endpoints
export const transactionAPI = {
    getTransactions: (params) => apiClient.get('/transactions/', { params }),
    getTransaction: (id) => apiClient.get(`/transactions/${id}/`),
    createTransaction: (data) => apiClient.post('/transactions/', data),
    getTransactionHistory: (walletId, params) =>
        apiClient.get(`/transactions/`, { params: { wallet_id: walletId, ...params } }),
};

// Goals endpoints
export const goalsAPI = {
    getGoals: () => apiClient.get('/goals/'),
    getGoal: (id) => apiClient.get(`/goals/${id}/`),
    createGoal: (data) => apiClient.post('/goals/', data),
    updateGoal: (id, data) => apiClient.patch(`/goals/${id}/`, data),
    deleteGoal: (id) => apiClient.delete(`/goals/${id}/`),
};

// Summary/Analytics endpoints
export const summaryAPI = {
    getSummary: (range = '7d') => apiClient.get(`/summary/?range=${range}`),
    getCategoryBreakdown: () => apiClient.get('/summary/categories/'),
};

// Nudges/Alerts endpoints
export const nudgesAPI = {
    getNudges: () => apiClient.get('/nudges/'),
    markNudgeRead: (id) => apiClient.patch(`/nudges/${id}/`, { is_read: true }),
    clearNudge: (id) => apiClient.delete(`/nudges/${id}/`),
};

export default {
    auth: authAPI,
    wallet: walletAPI,
    transaction: transactionAPI,
    goals: goalsAPI,
    summary: summaryAPI,
    nudges: nudgesAPI,
};
