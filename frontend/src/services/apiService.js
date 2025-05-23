// src/services/apiService.js
import axios from 'axios';
import config from '../config/config';

// Tạo instance axios với cấu hình mặc định
const api = axios.create({
  baseURL: config.apiUrl
});

// Thêm interceptor để tự động gắn token vào header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth services
export const authService = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (username, password) => api.post('/auth/register', { username, password })
};

// File services
export const fileService = {
  getStats: (year = '', department = '') => {
    let url = '/files/stats';
    const params = [];
    
    if (year) params.push(`year=${year}`);
    if (department) params.push(`department=${department}`);
    
    if (params.length > 0) {
      url += `?${params.join('&')}`;
    }
    
    return api.get(url);
  },
  getList: () => api.get('/files/list'),
  uploadFile: (formData) => api.post('/files/upload', formData),
  deleteFile: (filename) => api.delete(`/files/delete/${filename}`)
};

// Chat services
// Cập nhật phần Chat Service trong apiService.js
export const chatService = {
  // Gửi tin nhắn đến chatbot với timeout tùy chỉnh
  sendMessage: async (message, timeout = 60000) => { // Mặc định 60 giây
    try {
      const response = await api.post('/chat/ask', { question: message }, {
        timeout: timeout // Tăng timeout cho request này
      });
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  }
};

export default api;