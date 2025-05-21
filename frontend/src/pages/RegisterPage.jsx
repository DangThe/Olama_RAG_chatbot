// src/pages/RegisterPage.jsx
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/authContext';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const navigate = useNavigate();
  const { register, user } = useAuth();

  useEffect(() => {
    // Nếu người dùng đã đăng nhập, chuyển hướng đến trang chính
    if (user) {
      navigate('/');
    }
  }, [user, navigate]);

  const validateForm = () => {
    if (!username || !password || !confirmPassword) {
      setError('Vui lòng điền đầy đủ thông tin.');
      return false;
    }
    
    if (password !== confirmPassword) {
      setError('Mật khẩu không khớp. Vui lòng nhập lại.');
      return false;
    }
    
    if (password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự.');
      return false;
    }
    
    return true;
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const result = await register(username, password);
      
      if (result.success) {
        navigate('/login', { state: { message: 'Đăng ký thành công! Vui lòng đăng nhập.' } });
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError('Đã xảy ra lỗi. Vui lòng thử lại sau.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6 col-lg-5">
          <div className="card shadow">
            <div className="card-body p-4">
              <div className="text-center mb-4">
                <h2 className="fw-bold text-primary">
                  <i className="bi bi-file-earmark-text me-2"></i>
                  Quản lý tài liệu
                </h2>
                <p className="text-muted">Đăng ký tài khoản mới</p>
              </div>
              
              {error && (
                <div className="alert alert-danger" role="alert">
                  <i className="bi bi-exclamation-triangle-fill me-2"></i>
                  {error}
                </div>
              )}
              
              <form onSubmit={handleRegister}>
                <div className="mb-3">
                  <div className="form-floating">
                    <input
                      type="text"
                      className="form-control"
                      id="username"
                      placeholder="Tên đăng nhập"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={loading}
                    />
                    <label htmlFor="username">
                      <i className="bi bi-person me-1"></i> Tên đăng nhập
                    </label>
                  </div>
                </div>
                
                <div className="mb-3">
                  <div className="form-floating">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className="form-control"
                      id="password"
                      placeholder="Mật khẩu"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      disabled={loading}
                    />
                    <label htmlFor="password">
                      <i className="bi bi-lock me-1"></i> Mật khẩu
                    </label>
                  </div>
                </div>
                
                <div className="mb-3">
                  <div className="form-floating">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      className="form-control"
                      id="confirmPassword"
                      placeholder="Xác nhận mật khẩu"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={loading}
                    />
                    <label htmlFor="confirmPassword">
                      <i className="bi bi-lock-fill me-1"></i> Xác nhận mật khẩu
                    </label>
                  </div>
                </div>
                
                <div className="mb-3">
                  <button
                    type="button"
                    className="btn btn-link text-decoration-none p-0"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={loading}
                  >
                    {showPassword ? (
                      <><i className="bi bi-eye-slash"></i> Ẩn mật khẩu</>
                    ) : (
                      <><i className="bi bi-eye"></i> Hiện mật khẩu</>
                    )}
                  </button>
                </div>
                
                <button
                  type="submit"
                  className="btn btn-primary w-100 py-2 mb-3"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-person-plus me-2"></i>
                      Đăng ký
                    </>
                  )}
                </button>
                
                <p className="text-center">
                  Đã có tài khoản?{' '}
                  <Link to="/login" className="text-decoration-none">
                    Đăng nhập
                  </Link>
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}