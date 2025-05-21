// src/pages/UploadPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { fileService } from '../services/apiService';
import config from '../config/config';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [department, setDepartment] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const res = await fileService.getList();
      setDocuments(res.data);
    } catch (err) {
      console.error('Không thể lấy danh sách tài liệu:', err);
      setError('Không thể tải danh sách tài liệu. Vui lòng thử lại sau.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Vui lòng chọn tài liệu để tải lên.');
      return;
    }
    
    if (!department) {
      setError('Vui lòng chọn phòng ban.');
      return;
    }
    
    setError('');
    setSuccess('');
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('department', department);

    try {
      await fileService.uploadFile(formData);
      setSuccess('Tải tài liệu thành công!');
      setFile(null);
      setDepartment('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      fetchDocuments();
    } catch (err) {
      console.error('Lỗi khi tải lên:', err);
      setError('Tải tài liệu thất bại. Vui lòng thử lại sau.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (filename) => {
    if (!window.confirm(`Bạn có chắc muốn xóa tài liệu "${filename}"?`)) return;
    
    try {
      await fileService.deleteFile(filename);
      setSuccess(`Đã xóa tài liệu "${filename}"`);
      fetchDocuments();
    } catch (err) {
      console.error('Xóa thất bại:', err);
      setError('Không thể xóa tài liệu. Vui lòng thử lại sau.');
    }
  };

  return (
    <div className="container mt-4">
      <div className="row">
        <div className="col-lg-4 mb-4">
          <div className="content-card">
            <h4 className="mb-3">
              <i className="bi bi-cloud-upload me-2"></i>
              Tải tài liệu mới
            </h4>
            
            {error && (
              <div className="alert alert-danger" role="alert">
                <i className="bi bi-exclamation-triangle-fill me-2"></i>
                {error}
              </div>
            )}
            
            {success && (
              <div className="alert alert-success" role="alert">
                <i className="bi bi-check-circle-fill me-2"></i>
                {success}
              </div>
            )}
            
            <form onSubmit={handleUpload}>
              <div className="mb-3">
                <label htmlFor="file" className="form-label">Chọn tài liệu</label>
                <input
                  type="file"
                  className="form-control"
                  id="file"
                  onChange={handleFileChange}
                  ref={fileInputRef}
                  disabled={uploading}
                />
                {file && (
                  <div className="form-text text-success">
                    <i className="bi bi-check-circle me-1"></i>
                    Đã chọn: {file.name}
                  </div>
                )}
              </div>
              
              <div className="mb-3">
                <label htmlFor="department" className="form-label">Phòng ban</label>
                <select
                  className="form-select"
                  id="department"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  disabled={uploading}
                >
                  <option value="">-- Chọn phòng ban --</option>
                  {config.departments.map((dept, index) => (
                    <option key={index} value={dept}>{dept}</option>
                  ))}
                  <option value="Khác">Khác</option>
                </select>
              </div>
              
              <button
                type="submit"
                className="btn btn-primary w-100"
                disabled={uploading || !file || !department}
              >
                {uploading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Đang tải lên...
                  </>
                ) : (
                  <>
                    <i className="bi bi-upload me-2"></i>
                    Tải lên
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
        
        <div className="col-lg-8">
          <div className="content-card">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h4 className="mb-0">
                <i className="bi bi-folder2-open me-2"></i>
                Danh sách tài liệu
              </h4>
              
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={fetchDocuments}
                disabled={loading}
              >
                <i className="bi bi-arrow-clockwise me-1"></i>
                Làm mới
              </button>
            </div>
            
            {loading ? (
              <div className="text-center my-5">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Đang tải...</span>
                </div>
                <p className="mt-2">Đang tải danh sách tài liệu...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center my-5 text-muted">
                <i className="bi bi-folder2 display-1 mb-3"></i>
                <p>Chưa có tài liệu nào được tải lên</p>
                <p className="small">Hãy tải tài liệu đầu tiên của bạn!</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover">
                  <thead>
                    <tr>
                      <th scope="col">#</th>
                      <th scope="col">Tên tài liệu</th>
                      <th scope="col">Phòng ban</th>
                      <th scope="col">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc, index) => (
                      <tr key={index}>
                        <td>{index + 1}</td>
                        <td>
                          <i className="bi bi-file-earmark-text me-2"></i>
                          {doc.filename}
                        </td>
                        <td>
                          <span className="badge bg-info text-dark">
                            {doc.department || 'Không xác định'}
                          </span>
                        </td>
                        <td>
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => handleDelete(doc.filename)}
                          >
                            <i className="bi bi-trash me-1"></i>
                            Xóa
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}