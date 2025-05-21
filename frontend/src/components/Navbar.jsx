// src/components/Navbar.jsx
import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import config from '../config/config';
import { useAuth } from '../contexts/authContext';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const username = user?.username || localStorage.getItem(config.storageKeys.username);
  
  const handleLogout = () => {
    logout();
  };

  // Nếu đang ở trang login hoặc register thì không hiển thị navbar
  if (['/login', '/register'].includes(location.pathname)) {
    return null;
  }

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
      <div className="container">
        <Link className="navbar-brand" to="/">
          <i className="bi bi-robot me-2"></i>
          RAG Chatbot
        </Link>
        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link 
                className={`nav-link ${location.pathname === '/' ? 'active' : ''}`} 
                to="/"
              >
                <i className="bi bi-chat-dots me-1"></i> Chat
              </Link>
            </li>
            <li className="nav-item">
              <Link 
                className={`nav-link ${location.pathname === '/upload' ? 'active' : ''}`} 
                to="/upload"
              >
                <i className="bi bi-file-earmark-arrow-up me-1"></i> Upload
              </Link>
            </li>
            <li className="nav-item">
              <Link 
                className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`} 
                to="/dashboard"
              >
                <i className="bi bi-bar-chart me-1"></i> Thống kê
              </Link>
            </li>
          </ul>
          <div className="d-flex align-items-center">
            <span className="text-light me-3">
              <i className="bi bi-person-circle me-1"></i> {username}
            </span>
            <button 
              className="btn btn-outline-light btn-sm" 
              onClick={handleLogout}
            >
              <i className="bi bi-box-arrow-right me-1"></i> Đăng xuất
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}