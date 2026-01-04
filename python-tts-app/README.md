# Python Text-to-Speech Desktop App

🎙️ Ứng dụng GUI Desktop Python chuyển văn bản thành giọng nói, sử dụng Google Labs Little Language Lessons API.

## ✨ Tính Năng

- 📝 Nhập văn bản với giới hạn 600 ký tự
- 🌍 Hỗ trợ 7 ngôn ngữ:
  - English (US, UK)
  - Vietnamese
  - Spanish
  - French
  - German
  - Italian
- 🎙️ 8 giọng nói khác nhau: Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr
- ⚡ 5 quick presets sẵn có
- ▶️ Tạo và nghe preview audio
- 💾 Tải xuống file MP3

## 📋 Yêu Cầu

- Python 3.8+
- Internet connection
- Các thư viện: `requests`, `pygame` (optional)

## 🚀 Cài Đặt

```bash
# Clone repository
git clone <repo-url>
cd python-tts-app

# Cài đặt dependencies
pip install -r requirements.txt

# Hoặc cài thủ công
pip install requests pygame
```

## 💻 Sử Dụng

```bash
python tts_app.py
```

### Hướng Dẫn:

1. **Nhập văn bản** vào ô Script
2. **Chọn ngôn ngữ** phù hợp
3. **Chọn giọng nói** bạn muốn
4. Nhấn **Generate Speech**
5. Nhấn **Play** để nghe
6. Nhấn **Download MP3** để lưu file

## 📁 Cấu Trúc File

```
python-tts-app/
├── tts_app.py          # Main application
├── requirements.txt    # Dependencies
├── ANALYSIS.md         # Phân tích mã nguồn
└── README.md           # File này
```

## 🔧 API

Ứng dụng sử dụng Google Labs Little Language Lessons API:
- **Endpoint**: `https://labs.google/lll/api/text-to-speech`
- **Method**: POST
- **Body**: `{ text, languageCode, voiceName }`
- **Response**: Base64 encoded audio

## 📖 Xem Thêm

Đọc file [ANALYSIS.md](ANALYSIS.md) để hiểu chi tiết cơ chế hoạt động và so sánh với web app gốc.

## ⚠️ Lưu Ý

- API miễn phí của Google Labs có thể thay đổi
- Không nên gọi quá nhiều request liên tục
- Cần kết nối internet để sử dụng

## 📜 License

MIT License
