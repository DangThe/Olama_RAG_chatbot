// src/pages/ChatPage.jsx
import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/authContext';
import { chatService } from '../services/apiService';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const { user } = useAuth();
  
  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  async function sendMessage(e) {
    e?.preventDefault();
    
    if (!input.trim() || loading) return;
    
    const userMessage = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    setError(null);
    
    try {
      // Tăng timeout lên 120 giây (2 phút)
      const response = await chatService.sendMessage(input, 120000);
      const reply = response?.answer || 'Không nhận được phản hồi từ server.';
      
      setMessages([
        ...newMessages, 
        { role: 'assistant', content: reply }
      ]);
    } catch (err) {
      console.error('Lỗi khi gửi tin nhắn:', err);
      
      // Xác định loại lỗi
      let errorMessage = 'Đã xảy ra lỗi kết nối. Vui lòng thử lại sau hoặc kiểm tra xem Ollama đã được khởi động chưa.';
      
      // Kiểm tra nếu là lỗi timeout
      if (err.code === 'ECONNABORTED' || (err.response && err.response.status === 504)) {
        errorMessage = 'Yêu cầu mất quá nhiều thời gian để xử lý. Vui lòng thử lại với câu hỏi ngắn gọn hơn hoặc kiểm tra kết nối đến Ollama.';
        setError('timeout');
      } 
      // Kiểm tra nếu là lỗi kết nối
      else if (!err.response) {
        errorMessage = 'Không thể kết nối đến server. Vui lòng kiểm tra kết nối mạng và đảm bảo Ollama đang chạy.';
        setError('connection');
      }
      // Lỗi server 
      else if (err.response && err.response.status >= 500) {
        errorMessage = `Lỗi server (${err.response.status}): ${err.response.data?.detail || 'Không có thông tin chi tiết'}. Vui lòng thử lại sau.`;
        setError('server');
      }
      
      setMessages([
        ...newMessages, 
        { 
          role: 'assistant', 
          content: errorMessage,
          error: true
        }
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mt-4">
      <div className="content-card">
        <h4 className="mb-4">
          <i className="bi bi-chat-square-text me-2"></i>
          Chat với Mistral (RAG)
        </h4>
        
        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 ? (
              <div className="text-center text-muted my-5">
                <i className="bi bi-chat-dots display-1 mb-3"></i>
                <p>Hãy bắt đầu cuộc trò chuyện với chatbot</p>
                <p className="small">Chatbot có thể trả lời về tài liệu đã được tải lên</p>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div 
                  key={i} 
                  className={`message ${msg.role === 'user' ? 'message-user' : 'message-bot'} ${msg.error ? 'bg-danger bg-opacity-10 text-danger' : ''}`}
                >
                  {msg.role === 'user' ? (
                    <div className="d-flex justify-content-between">
                      <span className="badge bg-primary bg-opacity-75 mb-1">Bạn</span>
                      <span></span>
                    </div>
                  ) : (
                    <div className="d-flex justify-content-between">
                      <span className="badge bg-success bg-opacity-75 mb-1">Mistral</span>
                      <span></span>
                    </div>
                  )}
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {msg.content}
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="typing-indicator">
                <div className="typing-indicator-bubble">
                  <div className="typing-indicator-dot"></div>
                  <div className="typing-indicator-dot"></div>
                  <div className="typing-indicator-dot"></div>
                </div>
                <div className="text-muted small mt-1">
                  Đang xử lý câu trả lời... (có thể mất đến 2 phút với câu hỏi phức tạp)
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div className="chat-input">
            <form onSubmit={sendMessage}>
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Nhập câu hỏi..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                />
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={loading || !input.trim()}
                >
                  {loading ? (
                    <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  ) : (
                    <i className="bi bi-send"></i>
                  )}
                </button>
              </div>
              {error === 'timeout' && (
                <div className="mt-2 text-danger small">
                  <i className="bi bi-exclamation-triangle me-1"></i>
                  Lưu ý: Yêu cầu trước đã hết thời gian chờ. Thử câu hỏi ngắn hơn.
                </div>
              )}
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}