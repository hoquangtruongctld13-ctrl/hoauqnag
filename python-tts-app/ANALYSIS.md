# Phân Tích Mã Nguồn TTS và Python GUI App

## 📋 Mục Lục

1. [Tổng Quan Mã Nguồn](#tổng-quan-mã-nguồn)
2. [Cơ Chế Hoạt Động](#cơ-chế-hoạt-động)
3. [Phân Tích Chi Tiết](#phân-tích-chi-tiết)
4. [Tại Sao Tạo Được TTS](#tại-sao-tạo-được-tts)
5. [Python Desktop App](#python-desktop-app)
6. [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)

---

## 🔍 Tổng Quan Mã Nguồn

Mã nguồn `free-tts-main` là một ứng dụng web Next.js cho phép chuyển đổi văn bản thành giọng nói (Text-to-Speech) sử dụng **Google Labs Little Language Lessons API**.

### Cấu Trúc Thư Mục

```
free-tts-main/
├── app/
│   ├── api/
│   │   └── text-to-speech/
│   │       └── route.ts          # Server-side API route
│   ├── page.tsx                  # Trang chính
│   └── layout.tsx                # Layout chung
├── components/
│   └── text-to-speech.tsx        # Component UI chính
├── lib/
│   └── google-lll-tts.ts         # Client-side API helper
└── package.json
```

---

## ⚙️ Cơ Chế Hoạt Động

### Sơ Đồ Luồng Dữ Liệu

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   User Input    │───>│  Frontend       │───>│  Backend API     │
│   (Text, Lang,  │    │  (React)        │    │  (Next.js)       │
│    Voice)       │    │                 │    │                  │
└─────────────────┘    └─────────────────┘    └────────┬─────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Audio Player  │<───│  Decode Base64  │<───│  Google Labs API │
│   (Preview/     │    │  to Audio URL   │    │  (TTS Service)   │
│    Download)    │    │                 │    │                  │
└─────────────────┘    └─────────────────┘    └──────────────────┘
```

### Bước 1: Frontend Component (`components/text-to-speech.tsx`)

```typescript
// Người dùng nhập văn bản, chọn ngôn ngữ và giọng nói
const [text, setText] = useState("");
const [language, setLanguage] = useState<LanguageCode>("en-US");
const [voiceStyle, setVoiceStyle] = useState<VoiceName>("Orus");

// Khi nhấn "Generate Speech"
const handleGenerate = async () => {
  const dataBase64 = await generateSpeech(text, language, voiceStyle);
  const url = `data:audio/mp3;base64,${dataBase64}`;
  setAudioUrl(url);
};
```

### Bước 2: Client-side API Helper (`lib/google-lll-tts.ts`)

```typescript
export const generateSpeech = async (
  text: string,
  languageCode: LanguageCode = "en-US",
  voiceName: VoiceName = "Orus"
) => {
  const response = await fetch("/api/text-to-speech", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      languageCode,
      // Format voice name theo chuẩn Google Labs
      voiceName: languageCode + "-Chirp3-HD-" + voiceName,
    }),
  });
  
  const dataBase64 = await response.json();
  return dataBase64;
};
```

**Quan trọng**: Voice name được tạo theo format: `{languageCode}-Chirp3-HD-{voiceName}`
- Ví dụ: `en-US-Chirp3-HD-Orus`, `vi-VN-Chirp3-HD-Leda`

### Bước 3: Server-side API Route (`app/api/text-to-speech/route.ts`)

```typescript
export async function POST(request: Request) {
  const { text, languageCode, voiceName } = await request.json();
  
  // Gọi API Google Labs
  const url = "https://labs.google/lll/api/text-to-speech";
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, languageCode, voiceName }),
  });

  // Trả về audio base64
  const dataBase64 = await response.json();
  return NextResponse.json(dataBase64);
}
```

---

## 🎯 Tại Sao Tạo Được TTS

### 1. Google Labs Little Language Lessons API

Mã nguồn sử dụng **API miễn phí** của Google tại:
```
https://labs.google/lll/api/text-to-speech
```

Đây là API từ dự án "Little Language Lessons" của Google Labs:
- **URL Project**: https://labs.google/lll/en
- **Mục đích**: Hỗ trợ học ngôn ngữ với giọng nói tự nhiên
- **Miễn phí**: Không yêu cầu API key

### 2. Voice Model: Chirp3-HD

API sử dụng model `Chirp3-HD` - một trong những model TTS chất lượng cao của Google:
- **Chất lượng cao**: HD (High Definition)
- **Đa ngôn ngữ**: Hỗ trợ nhiều ngôn ngữ (en-US, vi-VN, es-ES, v.v.)
- **Đa giọng nói**: 8 giọng nói khác nhau (Puck, Charon, Kore, Fenrir, Aoede, Leda, Orus, Zephyr)

### 3. Request Format

```json
{
  "text": "Hello, this is a test",
  "languageCode": "en-US",
  "voiceName": "en-US-Chirp3-HD-Orus"
}
```

### 4. Response Format

API trả về audio dưới dạng **Base64 encoded string**:
```
"UklGRiQAAABXQVZFZm10IBAAAAABAAEARKw..."
```

Sau đó, frontend decode thành audio URL:
```javascript
const url = `data:audio/mp3;base64,${dataBase64}`;
```

---

## 🐍 Python Desktop App

### Cài Đặt

```bash
cd python-tts-app
pip install -r requirements.txt
python tts_app.py
```

### Tính Năng

| Tính Năng | Mô Tả |
|-----------|-------|
| 📝 Text Input | Nhập văn bản với giới hạn 600 ký tự |
| 🌍 Multi-language | Hỗ trợ 7 ngôn ngữ (English, Vietnamese, Spanish, v.v.) |
| 🎙️ Voice Selection | 8 giọng nói khác nhau |
| ⚡ Quick Presets | 5 preset mẫu sẵn có |
| ▶️ Generate | Tạo audio từ văn bản |
| 🔊 Playback | Nghe trực tiếp trong app |
| 💾 Download | Lưu file MP3 |

### Architecture

```python
class TextToSpeechApp:
    """
    Cấu trúc tương tự Next.js app:
    
    1. UI Layer (tkinter)
       ├── Text Input (textarea)
       ├── Language/Voice Selector (combobox)
       └── Action Buttons
    
    2. API Layer
       └── generate_speech() -> Google Labs API
    
    3. Audio Processing
       ├── Base64 decode
       ├── Save to temp file
       └── Playback with pygame
    """
```

### Core Logic - Tạo TTS

```python
def generate_speech(self):
    # 1. Chuẩn bị payload (giống route.ts)
    payload = {
        "text": text,
        "languageCode": "en-US",
        "voiceName": "en-US-Chirp3-HD-Orus"  # Same format as JS
    }
    
    # 2. Gọi API Google Labs
    response = requests.post(
        "https://labs.google/lll/api/text-to-speech",
        json=payload
    )
    
    # 3. Decode base64 thành audio
    data_base64 = response.json()
    audio_bytes = base64.b64decode(data_base64)
    
    # 4. Lưu và phát audio
    with open("speech.mp3", "wb") as f:
        f.write(audio_bytes)
```

---

## 📖 Hướng Dẫn Sử Dụng

### Yêu Cầu Hệ Thống

- Python 3.8+
- Internet connection (để gọi API)
- Tkinter (thường có sẵn trong Python)

### Cài Đặt Dependencies

```bash
pip install requests pygame
```

### Chạy Ứng Dụng

```bash
python tts_app.py
```

### Sử Dụng

1. **Nhập văn bản** vào ô Script (tối đa 600 ký tự)
2. **Chọn ngôn ngữ** phù hợp với văn bản
3. **Chọn giọng nói** bạn muốn
4. Nhấn **Generate Speech** để tạo audio
5. Nhấn **Play** để nghe preview
6. Nhấn **Download MP3** để lưu file

### Quick Presets

Sử dụng các preset có sẵn để test nhanh:
- **Product teaser**: Giọng ấm áp (Aoede)
- **Learning module**: Giọng rõ ràng (Orus)
- **Customer support**: Giọng thân thiện (Leda)
- **Global greeting**: Tiếng Tây Ban Nha (Zephyr)
- **Tiếng Việt**: Demo tiếng Việt (Orus)

---

## 🔧 So Sánh Web App vs Desktop App

| Aspect | Next.js Web App | Python Desktop App |
|--------|-----------------|-------------------|
| **Frontend** | React + Tailwind CSS | Tkinter |
| **Backend** | Next.js API Routes | Direct requests |
| **API Call** | Server-side proxy | Direct to Google Labs |
| **Audio Format** | Data URL (base64) | MP3 file |
| **Playback** | HTML5 `<audio>` | pygame.mixer |
| **Distribution** | Web URL | Python script |

---

## ⚠️ Lưu Ý

1. **API miễn phí**: Google Labs API có thể thay đổi hoặc bị giới hạn
2. **Rate limiting**: Không nên gọi quá nhiều request liên tục
3. **Internet**: Cần kết nối internet để sử dụng
4. **Character limit**: Tối đa 600 ký tự mỗi lần

---

## 📚 Tham Khảo

- [Google Labs - Little Language Lessons](https://labs.google/lll/en)
- [Next.js Documentation](https://nextjs.org/docs)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [Pygame Mixer](https://www.pygame.org/docs/ref/mixer.html)
