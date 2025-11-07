# Quick Start Guide 🚀

5분 안에 배포를 시작하세요!

## 📋 준비물

- [ ] GitHub 계정
- [ ] Render 계정 (https://render.com - 무료)
- [ ] Netlify 계정 (https://netlify.com - 무료)

---

## 🏃‍♂️ 빠른 배포 (3단계)

### 1️⃣ 백엔드 배포 (Render)

1. **Render 접속**: https://render.com
2. **New + → Web Service** 클릭
3. GitHub 저장소 연결
4. **자동 감지**: `render.yaml` 파일이 자동으로 설정을 불러옵니다
5. **환경변수 추가**:
   ```
   ALLOWED_ORIGINS=*
   ```
   (나중에 프론트엔드 URL로 변경)
6. **Deploy** 클릭
7. ✅ URL 복사 (예: `https://your-app.onrender.com`)

⏱️ 예상 시간: 3-5분

---

### 2️⃣ 프론트엔드 배포 (Netlify)

1. **Netlify 접속**: https://netlify.com
2. **Add new site → Import project** 클릭
3. GitHub 저장소 연결
4. **빌드 설정**:
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/dist
   ```
5. **환경변수 추가** (Site settings → Environment variables):
   ```
   VITE_API_URL=https://your-app.onrender.com
   ```
   (1단계에서 받은 Render URL)
6. **Deploy** 클릭
7. ✅ URL 복사 (예: `https://your-app.netlify.app`)

⏱️ 예상 시간: 1-2분

---

### 3️⃣ CORS 설정 완료

1. **Render 대시보드** 돌아가기
2. **Environment** 탭에서 `ALLOWED_ORIGINS` 수정:
   ```
   ALLOWED_ORIGINS=https://your-app.netlify.app
   ```
   (2단계에서 받은 Netlify URL)
3. 저장하면 자동 재배포 (1분 대기)

⏱️ 예상 시간: 1분

---

## ✅ 완료!

이제 Netlify URL로 접속하여 테스트하세요:

1. 브라우저에서 `https://your-app.netlify.app` 접속
2. 한글 파일 업로드 (예: `테스트.txt`)
3. ZIP 다운로드 확인

---

## 🔧 로컬 개발 (선택사항)

### Docker Compose 사용 (권장)

```bash
docker-compose up --build
```

- 백엔드: http://localhost:8000
- 프론트엔드: http://localhost:5173

### 개별 실행

**터미널 1 - 백엔드:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**터미널 2 - 프론트엔드:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📖 상세 가이드

더 자세한 내용은 다음 문서를 참고하세요:

- **[README.md](./README.md)**: 전체 프로젝트 설명
- **[DEPLOYMENT.md](./DEPLOYMENT.md)**: 상세 배포 가이드 및 문제 해결

---

## ❓ 자주 묻는 질문

### Q: CORS 오류가 나요
**A**: Render의 `ALLOWED_ORIGINS`에 정확한 Netlify URL을 입력했는지 확인하세요. URL 끝에 `/`가 없어야 합니다.

### Q: 백엔드 응답이 느려요
**A**: Render 무료 플랜은 15분 비활성 시 슬립 모드로 전환됩니다. 첫 요청 시 30초 정도 소요될 수 있습니다.

### Q: 프론트엔드 빌드가 실패해요
**A**: `frontend/package.json`에 `@vitejs/plugin-react`가 추가되었는지 확인하세요.

---

## 🎉 축하합니다!

성공적으로 배포를 완료했습니다! 

다음 단계:
- [ ] 커스텀 도메인 연결
- [ ] Google Analytics 추가
- [ ] 모니터링 설정 (UptimeRobot)
- [ ] 소셜 공유 버튼 추가

문제가 있으면 [Issues](https://github.com/your-repo/issues)에 남겨주세요! 🙏

