// src/components/Navbar.jsx
import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
// import config from '../config/config'; // config không được sử dụng trực tiếp trong file này
import { useAuth } from '../contexts/authContext';

export default function Navbar() {
  // const navigate = useNavigate(); // navigate không được sử dụng
  const location = useLocation();
  const { user, logout } = useAuth();
  // Lấy username từ context user trước, nếu không có thì thử từ localStorage
  const username = user?.username || user?.user?.username || localStorage.getItem('username'); // Đảm bảo key "username" đúng

  const handleLogout = () => {
    logout();
    // navigate('/login'); // Không cần navigate ở đây nếu useAuth đã xử lý
  };

  if (['/login', '/register'].includes(location.pathname)) {
    return null;
  }

  return (
    // THÊM CLASS "fixed-top" VÀO ĐÂY
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm fixed-top">
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
          aria-controls="navbarNav" // Thêm aria-controls
          aria-expanded="false"    // Thêm aria-expanded
          aria-label="Toggle navigation" // Thêm aria-label
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0"> {/* Thêm mb-2 mb-lg-0 cho responsive */}
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
            {/* Ví dụ thêm link Admin Settings nếu user là admin */}
            {/* {user && user.isAdmin && (
              <li className="nav-item">
                <Link
                  className={`nav-link ${location.pathname === '/admin/settings' ? 'active' : ''}`}
                  to="/admin/settings"
                >
                  <i className="bi bi-gear me-1"></i> Cài đặt Admin
                </Link>
              </li>
            )} */}
          </ul>
          <div className="d-flex align-items-center">
            {username ? (
              <>
                <span className="navbar-text me-3"> {/* Dùng navbar-text cho styling tốt hơn */}
                  <i className="bi bi-person-circle me-1"></i> {username}
                </span>
                <button
                  className="btn btn-outline-light btn-sm"
                  onClick={handleLogout}
                >
                  <i className="bi bi-box-arrow-right me-1"></i> Đăng xuất
                </button>
              </>
            ) : (
              // Có thể hiển thị nút Login/Register ở đây nếu chưa đăng nhập và không phải trang login/register
              // Nhưng logic hiện tại của bạn là ẩn toàn bộ navbar trên trang login/register
              null
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}