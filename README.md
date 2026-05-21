# AI Story Adventure

AI Story Adventure là một ứng dụng web kể chuyện tương tác bằng AI.  
Người chơi có thể tạo thế giới, xây dựng nhân vật, chơi theo lựa chọn, hoặc viết tiếp câu chuyện theo hướng tiểu thuyết tương tác.

Dự án hỗ trợ hai chế độ chính:

- **Adventure Mode**: game phiêu lưu văn bản, tập trung vào hành động, lựa chọn nhanh và diễn biến trực tiếp.
- **Novel Mode**: chế độ tiểu thuyết tương tác, tập trung vào văn xuôi dài, bối cảnh, nhân vật, story bible và lựa chọn dạng định hướng câu chuyện.

AI sẽ viết nội dung hiển thị cho người chơi bằng **tiếng Việt**.

---

## Tính năng chính

### Game Portal Frontend

Frontend được thiết kế như một cổng game hiện đại:

- Trang Home hiển thị các thế giới preset do người tạo chuẩn bị.
- Trang Saves lưu các câu chuyện đang chơi.
- Trang About giới thiệu dự án.
- Modal Create cho phép chọn:
  - Adventure Mode
  - Novel Mode
- Đăng nhập / đăng ký bằng Firebase Authentication.
- Avatar người dùng sau khi đăng nhập.
- Giao diện đọc truyện cho Novel Mode.
- Giao diện hành động cho Adventure Mode.

### Adventure Mode

Adventure Mode phù hợp với lối chơi nhanh.

Luồng chơi:

1. Người chơi chọn Adventure Mode hoặc chọn một preset world.
2. Nhập thông tin nhân vật.
3. AI tạo hồ sơ thế giới và nhân vật.
4. Người chơi bắt đầu phiêu lưu.
5. Người chơi chọn một lựa chọn có sẵn hoặc tự nhập hành động.
6. Câu chuyện được lưu để tiếp tục về sau.

### Novel Mode

Novel Mode phù hợp với trải nghiệm tiểu thuyết tương tác.

Luồng chơi:

1. Người chơi nhập world seed hoặc bỏ qua để AI tự tạo.
2. AI tạo world draft.
3. Người chơi trả lời các câu hỏi thiết lập thế giới.
4. Người chơi nhập hồ sơ nhân vật.
5. AI tạo foundation / novel profile / story bible.
6. AI viết cảnh truyện bằng tiếng Việt.
7. Người chơi chọn hướng đi tiếp theo hoặc tự nhập hướng kể chuyện.

### Hệ thống Memory

Backend giữ mạch truyện bằng nhiều lớp memory:

- Raw messages
- World summary
- Character summary
- Story summary
- Important facts
- Relevant memory chunks
- Session persistence
- Vector memory bằng ChromaDB

`novel_profile` chỉ dùng để AI tham khảo khi viết truyện, không phải gameplay state hiển thị cho người chơi.

---

## Công nghệ sử dụng

### Backend

- Python
- FastAPI
- Pydantic
- Firebase Admin SDK
- ChromaDB
- Multi-provider AI architecture

### Frontend

- HTML
- CSS
- JavaScript
- Firebase Authentication
- Firestore client SDK

### AI Providers

Dự án có thể cấu hình nhiều provider AI:

- Gemini
- OpenAI
- Groq
- Ollama
- Mock provider để test

Hiện tại khuyến nghị dùng:

```env
AI_PROVIDER=gemini
TEXT_MODEL=gemini-2.5-flash
```

---

## Cấu trúc thư mục hiện tại

Cấu trúc hiện tại của project:

```txt
AI-Story-Adventure/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── prompt.py
│   ├── routes/
│   ├── services/
│   ├── memory/
│   └── providers/
│
├── chroma_db/
│
├── data/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── assets/
│
├── frontend2/
│
├── node_modules/
│
├── venv/
│
├── .env
├── aistoryadventure-8796...
├── package-lock.json
├── package.json
├── README.md
└── requirements.txt
```

---

## Giải thích các thư mục / file

### `app/`

Đây là thư mục backend chính của FastAPI.

Các file quan trọng:

```txt
app/main.py
```

File khởi động FastAPI app, khai báo routes và middleware.

```txt
app/models.py
```

Chứa các Pydantic model như:

- Session state
- Message
- Choices
- Memory chunk
- Game request
- Novel request

```txt
app/prompt.py
```

Chứa các hàm build prompt cho AI:

- Start prompt
- Turn prompt
- Summary prompt
- Memory extract prompt
- Novel world prompt
- Novel foundation prompt

Prompt nội bộ có thể viết bằng tiếng Anh để AI hiểu cấu trúc tốt hơn, nhưng output hiển thị cho người chơi phải là tiếng Việt.

```txt
app/routes/
```

Chứa các API route.

Ví dụ:

- Start game
- Continue turn
- Load sessions
- Novel world setup
- Novel foundation setup

```txt
app/services/
```

Chứa logic xử lý chính:

- Gọi AI provider
- Tạo session
- Lưu session
- Load session
- Xử lý memory
- Xử lý turn gameplay

```txt
app/memory/
```

Chứa hệ thống memory:

- Summary memory
- Important facts
- Vector retrieval
- ChromaDB integration

```txt
app/providers/
```

Chứa các provider AI:

- Gemini
- OpenAI
- Groq
- Ollama
- Mock

---

### `frontend/`

Đây là frontend chính nên dùng.

Các file quan trọng:

```txt
frontend/index.html
```

Chứa cấu trúc giao diện:

- Login page
- Register page
- Home page
- Saves page
- About page
- Create modal
- Adventure setup
- Novel setup
- Foundation page
- Gameplay page

```txt
frontend/style.css
```

Chứa toàn bộ style giao diện.

Bao gồm:

- Portal navbar
- Home hero
- Preset world cards
- Login/Register UI
- Adventure wizard
- Novel reader
- Saves page
- About page
- Gameplay layout

```txt
frontend/app.js
```

Chứa logic frontend:

- Firebase Auth
- Page navigation
- Load preset worlds
- Start Adventure Mode
- Start Novel Mode
- Submit turn
- Render choices
- Save/load sessions
- Avatar dropdown
- Create modal

```txt
frontend/assets/
```

Chứa ảnh nền thế giới.

Ví dụ nên đặt:

```txt
frontend/assets/world-sunless-realm.png
frontend/assets/world-memory-market.png
frontend/assets/world-ashen-archive.png
frontend/assets/world-hollow-sea.png
```

Trong `app.js`, ảnh được dùng kiểu:

```js
image:
  "linear-gradient(90deg, rgba(0,0,0,.78), rgba(0,0,0,.28)), url('./assets/world-sunless-realm.png')"
```

---


### `chroma_db/`

Đây là dữ liệu local của ChromaDB.


### `data/`

Thư mục này có thể chứa dữ liệu local, file test hoặc cache.






### `node_modules/`

Đây là thư mục dependency của Node.js.


### `venv/`

Đây là môi trường ảo Python.


### `.env`

Chứa API key và biến môi trường.


---

### `aistoryadventure-8796...`

File này là Firebase service account hoặc Google credentials.



### `requirements.txt`

Chứa dependency Python.

Người tải về cài bằng:

```bash
pip install -r requirements.txt
```

---

### `package.json` và `package-lock.json`

Chứa dependency frontend/tooling nếu bạn dùng npm.

Người tải về cài bằng:

```bash
npm install
```

Nếu frontend chỉ dùng HTML/CSS/JS thuần và không cần npm, vẫn có thể giữ nếu bạn dùng Live Server hoặc package script.

---


Nội dung mẫu:

```env
# AI Provider
AI_PROVIDER=gemini
TEXT_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_gemini_api_key_here

# Optional providers
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Firebase
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
FIREBASE_DATABASE_URL=your_firebase_database_url

# App
APP_ENV=development
```

## File `serviceAccountKey.example.json`

Tạo file:

```txt
serviceAccountKey.example.json
```

Nội dung mẫu:

```json
{
  "type": "service_account",
  "project_id": "your_project_id",
  "private_key_id": "your_private_key_id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY\\n-----END PRIVATE KEY-----\\n",
  "client_email": "firebase-adminsdk@example.iam.gserviceaccount.com",
  "client_id": "your_client_id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "your_cert_url"
}
```

Người dùng thật phải tự tải file service account từ Firebase Console.

---

## Cài đặt project

### 1. Clone project

```bash
git clone https://github.com/your-username/ai-story-adventure.git
cd ai-story-adventure
```

---

### 2. Tạo môi trường Python

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

---

### 3. Cài dependency Python

```bash
pip install -r requirements.txt
```

---

### 4. Tạo file `.env`

Copy file mẫu:

```bash
copy .env.example .env
```

Hoặc trên macOS/Linux:

```bash
cp .env.example .env
```

Sau đó mở `.env` và điền API key thật.

---

### 5. Thêm Firebase service account

Tải service account từ Firebase Console.

Đặt file tại thư mục gốc project:

```txt
serviceAccountKey.json
```

Hoặc nếu code của bạn đang đọc file tên khác, đặt đúng tên theo code.

Ví dụ nếu code đang đọc:

```txt
aistoryadventure-8796...
```

thì hoặc đổi tên file trong code, hoặc đổi tên file local cho khớp.

Khuyến nghị đổi về:

```txt
serviceAccountKey.json
```

cho dễ hiểu.

---

## Chạy backend

Từ thư mục gốc project:

```bash
uvicorn app.main:app --reload
```

Backend chạy tại:

```txt
http://localhost:8000
```

API docs:

```txt
http://localhost:8000/docs
```

Nếu `main.py` không nằm ở `app/main.py`, chỉnh lại command cho đúng.

---

## Chạy frontend

Frontend chính nằm trong:

```txt
frontend/
```

Có thể chạy bằng VS Code Live Server.

Hoặc dùng Python static server:

```bash
cd frontend
python -m http.server 5500
```

Mở trình duyệt:

```txt
http://localhost:5500
```

Đảm bảo trong `frontend/app.js` có API base đúng:

```js
const API_BASE = "http://localhost:8000";
```

---

## Firebase Frontend Config

Trong `frontend/app.js` cần có Firebase client config:

```js
const firebaseConfig = {
  apiKey: "your_api_key",
  authDomain: "your_project.firebaseapp.com",
  projectId: "your_project_id",
  storageBucket: "your_project.appspot.com",
  messagingSenderId: "your_sender_id",
  appId: "your_app_id"
};
```

Firebase frontend config thường không phải secret tuyệt đối, nhưng bạn vẫn cần cấu hình Firestore Security Rules đúng.

---

## Firestore Index

Nếu gặp lỗi:

```txt
The query requires an index.
```

hãy mở link Firebase mà lỗi cung cấp và tạo index.

Index thường dùng cho sessions:

```txt
Collection: sessions
Fields:
- user_id ascending
- updated_at descending
- __name__ descending
```

Chờ đến khi index có trạng thái `Enabled`.

---

## Cách dùng

### Adventure Mode

1. Đăng nhập hoặc chơi với guest.
2. Bấm `Create`.
3. Chọn `Adventure Mode`.
4. Nhập thông tin nhân vật.
5. AI tạo world foundation.
6. Bấm `Begin the Adventure`.
7. Chọn hành động hoặc tự nhập hành động.
8. Tiếp tục về sau trong `Saves`.

---

### Novel Mode

1. Bấm `Create`.
2. Chọn `Novel Mode`.
3. Nhập world seed hoặc bỏ qua.
4. AI tạo world draft.
5. Trả lời các câu hỏi setup.
6. Nhập hồ sơ nhân vật.
7. AI tạo foundation / novel profile.
8. Đọc cảnh truyện.
9. Chọn hướng đi hoặc tự nhập hướng kể tiếp.

---

## Preset Worlds

Preset worlds được cấu hình trong:

```txt
frontend/app.js
```

Ví dụ:

```js
const creatorWorlds = [
  {
    id: "memory-market",
    title: "The Memory Market",
    mode: "Novel",
    description:
      "A city where memories are bottled, traded, stolen, and used as currency.",
    image:
      "linear-gradient(90deg, rgba(0,0,0,.78), rgba(0,0,0,.28)), url('./assets/world-memory-market.png')",
    worldSeed:
      "A city where memories are bottled, traded, stolen, and used as currency..."
  }
];
```

Giải thích:

```txt
image     → chỉ frontend dùng để hiển thị ảnh nền
worldSeed → gửi lên backend để AI đọc và tạo thế giới
```

---

## Ảnh nền world

Đặt ảnh trong:

```txt
frontend/assets/
```

Tên file khuyến nghị:

```txt
world-sunless-realm.png
world-memory-market.png
world-ashen-archive.png
world-hollow-sea.png
```

Sau đó khai báo trong `creatorWorlds`:

```js
image:
  "linear-gradient(90deg, rgba(0,0,0,.78), rgba(0,0,0,.28)), url('./assets/world-sunless-realm.png')"
```

---

## AI Output

Prompt nội bộ có thể viết bằng tiếng Anh để giữ format tốt hơn.

Nhưng output hiển thị cho người chơi nên là tiếng Việt.

Luật nên có trong prompt:

```txt
All narration, prose, dialogue, descriptions, and choices visible to the player must be written in natural Vietnamese.
```

---


## Trạng thái phát triển

Dự án vẫn đang được phát triển.

Các tính năng có thể nâng cấp thêm:

- Discover page
- User profile page
- Admin memory debugger
- Token usage dashboard
- More creator-made worlds
- Better JSON repair for non-Gemini providers
- Better save preview
- More polished mobile layout

---

## License

This project is for educational and portfolio use.

You can replace this section with your intended license.
