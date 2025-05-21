// src/pages/DashboardPage.jsx
import React, { useEffect, useState } from 'react';
import { saveAs } from 'file-saver';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line
} from 'recharts';
import { fileService } from '../services/apiService';
import config from '../config/config';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28EF5', '#F38181'];
const RADIAN = Math.PI / 180;

// Custom label cho biểu đồ tròn
const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

export default function DashboardPage() {
  const [stats, setStats] = useState({ 
    total: 0, 
    byDepartment: [], 
    byMonth: [], 
    documents: [] 
  });
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async (year = '', dept = '') => {
    setLoading(true);
    setError('');
    
    try {
      const res = await fileService.getStats(year, dept);
      setStats(res.data);
    } catch (err) {
      console.error('Lỗi khi tải thống kê:', err);
      setError('Không thể tải dữ liệu thống kê. Vui lòng thử lại sau.');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    const csvContent = [
      ['Phòng ban', 'Số lượng'],
      ...stats.byDepartment.map(item => [
        item.department || 'Không xác định', 
        item.count
      ])
    ].map(e => e.join(",")).join("\n");

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, `thongke_phongban_${new Date().toISOString().slice(0, 10)}.csv`);
  };

  return (
    <div className="container mt-4">
      <div className="content-card">
        <div className="d-flex justify-content-between align-items-center mb-4">
          <h4 className="mb-0">
            <i className="bi bi-bar-chart-line me-2"></i>
            Thống kê tài liệu
          </h4>
          
          <div>
            <button
              className="btn btn-outline-primary"
              onClick={handleExport}
              disabled={loading || stats.byDepartment.length === 0}
            >
              <i className="bi bi-download me-2"></i>
              Xuất CSV
            </button>
          </div>
        </div>
        
        {error && (
          <div className="alert alert-danger mb-4">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            {error}
          </div>
        )}
        
        {loading ? (
          <div className="text-center my-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Đang tải...</span>
            </div>
            <p className="mt-2">Đang tải dữ liệu thống kê...</p>
          </div>
        ) : (
          <>
            <div className="row mb-4">
              <div className="col-md-4">
                <div className="stats-card">
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 className="text-muted mb-1">Tổng số tài liệu</h6>
                      <h3 className="mb-0">{stats.total}</h3>
                    </div>
                    <div className="stats-icon">
                      <i className="bi bi-file-earmark-text"></i>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="col-md-4">
                <div className="stats-card" style={{ borderLeftColor: '#6f42c1' }}>
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 className="text-muted mb-1">Số phòng ban</h6>
                      <h3 className="mb-0">
                        {[...new Set(stats.byDepartment.map(d => d.department))].length}
                      </h3>
                    </div>
                    <div className="stats-icon" style={{ color: '#6f42c1' }}>
                      <i className="bi bi-buildings"></i>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="col-md-4">
                <div className="stats-card" style={{ borderLeftColor: '#fd7e14' }}>
                  <div className="d-flex justify-content-between align-items-center">
                    <div>
                      <h6 className="text-muted mb-1">Tài liệu trong tháng</h6>
                      <h3 className="mb-0">
                        {stats.byMonth.length > 0 
                          ? stats.byMonth[stats.byMonth.length - 1].count 
                          : 0}
                      </h3>
                    </div>
                    <div className="stats-icon" style={{ color: '#fd7e14' }}>
                      <i className="bi bi-calendar-check"></i>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mb-4 d-flex flex-wrap gap-3 align-items-center">
              <div>
                <label className="form-label me-2">Lọc theo năm:</label>
                <select 
                  className="form-select form-select-sm d-inline-block" 
                  style={{ width: 'auto' }}
                  value={selectedYear} 
                  onChange={e => {
                    setSelectedYear(e.target.value);
                    fetchStats(e.target.value, selectedDept);
                  }}
                >
                  <option value="">Tất cả</option>
                  {config.defaultAvailableYears.map((year, index) => (
                    <option key={index} value={year}>{year}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="form-label me-2">Lọc theo phòng ban:</label>
                <select 
                  className="form-select form-select-sm d-inline-block" 
                  style={{ width: 'auto' }}
                  value={selectedDept} 
                  onChange={e => {
                    setSelectedDept(e.target.value);
                    fetchStats(selectedYear, e.target.value);
                  }}
                >
                  <option value="">Tất cả</option>
                  {[...new Set(stats.byDepartment.map(d => d.department))].map((d, i) => (
                    <option key={i} value={d}>{d || 'Không xác định'}</option>
                  ))}
                </select>
              </div>
              
              <button 
                className="btn btn-sm btn-outline-secondary" 
                onClick={() => {
                  setSelectedYear('');
                  setSelectedDept('');
                  fetchStats();
                }}
              >
                <i className="bi bi-x-circle me-1"></i>
                Xóa bộ lọc
              </button>
            </div>
            
            <div className="row">
              <div className="col-md-6 mb-4">
                <div className="chart-container">
                  <h5 className="mb-3">Phân loại theo phòng ban</h5>
                  <div style={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                      <PieChart>
                        <Pie
                          data={stats.byDepartment}
                          dataKey="count"
                          nameKey="department"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label={renderCustomizedLabel}
                          labelLine={false}
                        >
                          {stats.byDepartment.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          formatter={(value, name, props) => [value, props.payload.department || 'Không xác định']}
                        />
                        <Legend 
                          formatter={(value, entry) => entry.payload.department || 'Không xác định'}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
              
              <div className="col-md-6 mb-4">
                <div className="chart-container">
                  <h5 className="mb-3">Phân loại theo phòng ban (biểu đồ cột)</h5>
                  <div style={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                      <BarChart 
                        data={stats.byDepartment} 
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="department" 
                          tick={{ fontSize: 12 }}
                          tickFormatter={(value) => value || 'Không xác định'}
                        />
                        <YAxis />
                        <Tooltip 
                          formatter={(value, name, props) => [value, props.payload.department || 'Không xác định']}
                        />
                        <Bar 
                          dataKey="count" 
                          name="Số lượng" 
                          fill="#8884d8"
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>
            
            {stats.byMonth && stats.byMonth.length > 0 && (
              <div className="chart-container">
                <h5 className="mb-3">Biểu đồ theo thời gian (số tài liệu theo tháng)</h5>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer>
                    <LineChart 
                      data={stats.byMonth} 
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="month" 
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="count" 
                        name="Số tài liệu" 
                        stroke="#82ca9d" 
                        activeDot={{ r: 8 }}
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}