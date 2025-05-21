// src/components/ProtectedRoute.jsx
import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/authContext';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();
  const token = localStorage.getItem('token');

  // Chuẩn bị dữ liệu để debug
  useEffect(() => {
    console.log('ProtectedRoute - Path:', location.pathname);
    console.log('ProtectedRoute - Token exists:', !!token);
    console.log('ProtectedRoute - User exists:', !!user);
    console.log('ProtectedRoute - Loading:', loading);
  }, [location.pathname, token, user, loading]);

  if (loading) {
    // Hiển thị loading spinner khi đang kiểm tra authentication
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Đang tải...</span>
        </div>
      </div>
    );
  }

  // Nếu không có token hoặc user, chuyển hướng đến trang đăng nhập
  if (!token || !user) {
    // Chuyển hướng đến trang đăng nhập và lưu lại URL hiện tại để quay lại sau khi đăng nhập
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Người dùng đã đăng nhập, hiển thị component con
  return children;
};

export default ProtectedRoute;