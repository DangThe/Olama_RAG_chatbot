// src/contexts/authContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/apiService';
import config from '../config/config';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Kiểm tra token khi component mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Kiểm tra nếu đã có token trong localStorage
        const token = localStorage.getItem(config.storageKeys.token);
        const username = localStorage.getItem(config.storageKeys.username);
        
        if (token && username) {
          // Đã có thông tin đăng nhập, set user
          setUser({ username });
          console.log('User logged in:', username);
        } else {
          // Không có thông tin đăng nhập
          console.log('No auth token found');
        }
      } catch (error) {
        console.error('Auth check error:', error);
      } finally {
        // Dù thành công hay thất bại, cũng set loading = false
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (username, password, rememberMe) => {
    try {
      const res = await authService.login(username, password);
      
      localStorage.setItem(config.storageKeys.token, res.data.token);
      localStorage.setItem(config.storageKeys.username, username);
      
      if (rememberMe) {
        localStorage.setItem(config.storageKeys.rememberMe, 'true');
      } else {
        localStorage.removeItem(config.storageKeys.rememberMe);
      }
      
      setUser({ username });
      return { success: true };
    } catch (err) {
      return { 
        success: false, 
        message: err?.response?.data?.detail || 'Đăng nhập thất bại. Nếu bạn chưa có tài khoản, hãy đăng ký.'
      };
    }
  };

  const register = async (username, password) => {
    try {
      await authService.register(username, password);
      return { success: true };
    } catch (err) {
      return { 
        success: false, 
        message: err?.response?.data?.detail || 'Đăng ký thất bại. Vui lòng thử lại.'
      };
    }
  };

  const logout = () => {
    localStorage.removeItem(config.storageKeys.token);
    localStorage.removeItem(config.storageKeys.username);
    localStorage.removeItem(config.storageKeys.rememberMe);
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);