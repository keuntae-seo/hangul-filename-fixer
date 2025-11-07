# 한글 파일명 고쳐주기 🇰🇷

한글 파일명이 자음/모음으로 분해되어 깨진 경우(예: `ㅂㅗㄱㅗㅅㅓ.hwp`)를 정상적인 한글(예: `보고서.hwp`)로 복구하는 웹 서비스입니다.

## 문제 상황

macOS에서 생성한 한글 파일명이 Windows나 다른 시스템에서 자음/모음으로 분해되어 보이는 현상을 해결합니다:
- ❌ `ㅂㅗㄱㅗㅅㅓ.hwp` (NFD 형식 - 분해됨)
- ✅ `보고서.hwp` (NFC 형식 - 정상)

## 기능

- 🔄 **유니코드 정규화**: NFD → NFC 변환으로 자모 분해 문제 해결
- 📦 **일괄 처리**: 여러 파일을 한 번에 업로드하여 ZIP으로 다운로드
- 🚫 **금지 문자 처리**: Windows 파일 시스템 규칙에 맞게 자동 변환
- 🔒 **개인정보 보호**: 파일은 서버에 저장되지 않고 즉시 처리 후 삭제

## 기술 스택

### 백엔드
- **FastAPI**: Python 웹 프레임워크
- **Python 3.12**: unicodedata를 이용한 NFC 정규화
- **Docker**: 컨테이너 배포
- **Render**: 백엔드 호스팅

### 프론트엔드
- **React 18** + **TypeScript**
- **Vite**: 빌드 도구
- **Netlify**: 프론트엔드 호스팅

## 프로젝트 구조

```
hangul-filename-fixer/
├── backend/              # FastAPI 백엔드
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py      # 환경 설정
│   │   │   └── normalize.py   # 파일명 정규화 로직
│   │   ├── main.py            # API 엔드포인트
│   │   └── schemas.py         # Pydantic 모델
│   ├── test/
│   │   └── test_normalize.py  # 테스트
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # React 프론트엔드
│   ├── src/
│   │   ├── App.tsx            # 메인 컴포넌트
│   │   ├── api.ts             # API 클라이언트
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── netlify.toml           # Netlify 배포 설정
│   └── package.json
├── render.yaml           # Render 배포 설정
└── docker-compose.yml    # 로컬 개발 환경
```

## 로컬 개발 환경 설정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd hangul-filename-fixer
```

### 2. Docker Compose로 실행 (권장)

```bash
docker-compose up --build
```

- 백엔드: http://localhost:8000
- 프론트엔드: http://localhost:5173
- API 문서: http://localhost:8000/docs

### 3. 개별 실행

#### 백엔드

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

## 테스트 실행

```bash
cd backend
pytest test/test_normalize.py -v
```

## 배포 가이드

### 백엔드 배포 (Render)

1. **Render 계정 생성 및 로그인**
   - https://render.com 접속

2. **새 Web Service 생성**
   - "New +" → "Web Service" 선택
   - GitHub 저장소 연결

3. **설정**
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./backend/Dockerfile`
   - **Docker Context**: `./backend`
   - 또는 프로젝트 루트에 `render.yaml` 사용

4. **환경변수 설정**
   
   Render 대시보드 → Environment 탭에서 다음 추가:
   
   ```
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://your-app.netlify.app
   MAX_FILE_MB=100
   ```

5. **배포**
   - "Create Web Service" 클릭
   - 배포 완료 후 URL 복사 (예: `https://your-app.onrender.com`)

### 프론트엔드 배포 (Netlify)

1. **Netlify 계정 생성 및 로그인**
   - https://netlify.com 접속

2. **새 사이트 배포**
   - "Add new site" → "Import an existing project"
   - GitHub 저장소 연결

3. **빌드 설정**
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`

4. **환경변수 설정**
   
   Netlify 대시보드 → Site settings → Environment variables:
   
   ```
   VITE_API_URL=https://your-app.onrender.com
   ```
   
   ⚠️ **중요**: Render에서 받은 백엔드 URL을 정확히 입력하세요!

5. **배포**
   - "Deploy site" 클릭
   - 배포 완료 후 사이트 URL 확인

6. **CORS 설정 업데이트**
   
   Netlify URL을 받은 후, Render의 환경변수 업데이트:
   ```
   ALLOWED_ORIGINS=https://your-actual-site.netlify.app
   ```

## API 엔드포인트

### `GET /health`
서버 상태 확인

**Response:**
```json
{
  "status": "ok"
}
```

### `POST /rename`
파일명 정규화

**Parameters:**
- `files`: 업로드할 파일들 (multipart/form-data)
- `zip`: ZIP으로 다운로드 여부 (boolean, query parameter)

**Response (zip=false):**
```json
{
  "results": [
    {
      "original": "ㅂㅗㄱㅗㅅㅓ.hwp",
      "renamed": "보고서.hwp"
    }
  ],
  "zipped": false
}
```

**Response (zip=true):**
- `Content-Type: application/zip`
- ZIP 파일 다운로드

## 환경변수

### 백엔드

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `ENVIRONMENT` | 실행 환경 | `development` | ❌ |
| `ALLOWED_ORIGINS` | CORS 허용 오리진 (쉼표 구분) | `http://localhost:5173` | ⚠️ 프로덕션에서 필수 |
| `MAX_FILE_MB` | 개별 파일 최대 크기 (MB) | `100` | ❌ |

### 프론트엔드

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `VITE_API_URL` | 백엔드 API URL | `/api` (개발 시 프록시) | ⚠️ 프로덕션에서 필수 |

## 주의사항

1. **CORS 설정**: 프로덕션 배포 시 반드시 프론트엔드 URL을 백엔드의 `ALLOWED_ORIGINS`에 추가하세요.

2. **파일 크기 제한**: 기본값은 100MB입니다. 필요 시 `MAX_FILE_MB` 환경변수로 조정하세요.

3. **무료 플랜 제한**:
   - Render 무료 플랜: 15분 비활성 시 슬립 모드 (첫 요청 시 재시작 지연)
   - Netlify 무료 플랜: 월 100GB 대역폭

4. **개인정보 보호**: 서버는 파일을 저장하지 않습니다. 처리 후 즉시 메모리에서 삭제됩니다.

## 문제 해결

### CORS 오류
```
Access to fetch at '...' has been blocked by CORS policy
```

**해결방법**: Render 환경변수 `ALLOWED_ORIGINS`에 Netlify URL을 정확히 추가하세요.

### 빌드 오류 (프론트엔드)
```
Cannot find module '@vitejs/plugin-react'
```

**해결방법**:
```bash
cd frontend
npm install
```

### Render 슬립 모드
무료 플랜에서 15분 비활성 시 서버가 슬립 모드로 전환됩니다. 첫 요청 시 30초 정도 소요될 수 있습니다.

## 라이선스

MIT License

## 기여

이슈 및 PR을 환영합니다!

## 작성자

- GitHub: [your-username]
- Email: [your-email]

