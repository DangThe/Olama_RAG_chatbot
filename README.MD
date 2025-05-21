## Frontend

### Yêu cầu

- Node.js 14+
- npm hoặc yarn

### Cài đặt

1. Vào thư mục frontend:

```bash
cd rag-chatbot/frontend
```

2. Cài đặt dependencies:

```bash
npm install
# hoặc
yarn install
```

3. Khởi động ứng dụng:

```bash
npm start
# hoặc
yarn start
```

Ứng dụng sẽ chạy tại địa chỉ: http://localhost:3000

## Cải tiến dự án

### Backend

1. **Tổ chức lại cấu trúc**
   - Tạo file `config.py` để quản lý cấu hình tập trung
   - Tạo `database.py` để quản lý kết nối database
   - Tạo `auth_utils.py` để tập trung logic xác thực
   - Sử dụng environment variables thông qua `.env`

2. **Bảo mật và hiệu suất**
   - Sử dụng connection pool để tối ưu kết nối database
   - Cải thiện lỗi bảo mật trong xác thực
   - Thêm global exception handler
   - Thêm middleware đo thời gian xử lý request

3. **Code chất lượng hơn**
   - Thêm docstrings và type hinting
   - Sửa lỗi trùng lặp route
   - Chuẩn hóa response formats
   - Sử dụng status codes đúng chuẩn HTTP

### Frontend

1. **Tổ chức lại cấu trúc**
   - Tạo folder `components` để quản lý UI components tái sử dụng
   - Tạo folder `contexts` để quản lý state toàn cục
   - Tạo folder `services` để quản lý API calls
   - Tạo folder `styles` để quản lý CSS toàn cục
   - Tạo folder `config` để quản lý cấu hình

2. **Cải thiện UX/UI**
   - Thêm Bootstrap Icons cho giao diện trực quan
   - Cải thiện responsive design
   - Thêm loading states và error handling
   - Thông báo thành công/thất bại
   - Animate UI elements

3. **Performance**
   - Tối ưu hóa re-renders với React hooks
   - Tổ chức API calls với Axios interceptors
   - Lazy load components

## Tính năng

- **Authentication**
  - Đăng ký & đăng nhập
  - JWT authentication
  - "Remember me" functionality

- **Tài liệu**
  - Upload tài liệu với phân loại phòng ban
  - Xem danh sách tài liệu đã upload
  - Xóa tài liệu
  - Thống kê tài liệu theo phòng ban, theo thời gian

- **Chat**
  - Chatbot trả lời dựa trên tài liệu đã upload
  - Tìm kiếm thông tin liên quan bằng vector embeddings
  - Interface chat thân thiện với người dùng

## License

MIT# RAG Chatbot

Ứng dụng Chatbot sử dụng kỹ thuật Retrieval Augmented Generation (RAG) để trả lời câu hỏi dựa trên tài liệu nội bộ.

## Cấu trúc dự án

```
rag-chatbot/
├── backend/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── files.py
│   ├── utils/
│   │   ├── auth_utils.py
│   │   └── embedding.py
│   ├── .env
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── components/
    │   │   └── Navbar.jsx
    │   ├── config/
    │   │   └── config.js
    │   ├── contexts/
    │   │   └── authContext.js
    │   ├── pages/
    │   │   ├── ChatPage.jsx
    │   │   ├── DashboardPage.jsx
    │   │   ├── LoginPage.jsx
    │   │   ├── RegisterPage.jsx
    │   │   └── UploadPage.jsx
    │   ├── services/
    │   │   └── apiService.js
    │   ├── styles/
    │   │   └── styles.css
    │   ├── App.jsx
    │   └── index.js
    ├── package.json
    └── README.md
```

## Backend

### Yêu cầu

- Python 3.8+
- MySQL
- Ollama (đã cài đặt model Mistral)

### Cài đặt

1. Clone repository và vào thư mục backend:

```bash
git clone https://github.com/your-username/rag-chatbot.git
cd rag-chatbot/backend
```

2. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

3. Cấu hình database:

```sql
CREATE DATABASE chatbot;
CREATE USER 'chatbot'@'localhost' IDENTIFIED BY 'chatbot';
GRANT ALL PRIVILEGES ON chatbot.* TO 'chatbot'@'localhost';
FLUSH PRIVILEGES;

USE chatbot;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE documents (
  id INT AUTO_INCREMENT PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  user_id INT NOT NULL,
  department VARCHAR(255),
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE embeddings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  document_id INT NOT NULL,
  chunk TEXT NOT NULL,
  vector TEXT NOT NULL,
  FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);
```

4. Tạo file `.env` từ template:

```bash
cp .env.example .env
```

5. Chỉnh sửa file `.env` để phù hợp với môi trường của bạn.

6. Khởi động server:

```bash
uvicorn main:app --reload
```

Server sẽ chạy tại địa chỉ: http://localhost:8000

### API Endpoints

- **Authentication**
  - `POST /auth/register` - Đăng ký tài khoản mới
  - `POST /auth/login` - Đăng nhập và nhận JWT token

- **Files**
  - `POST /files/upload` - Tải lên tài liệu mới
  - `GET /files/list` - Lấy danh sách tài liệu
  - `DELETE /files/delete/{filename}` - Xóa tài liệu
  - `GET /files/stats` - Lấy thống kê về tài liệu

- **Chat**
  - `POST /chat/ask` - Gửi câu hỏi đến chatbot