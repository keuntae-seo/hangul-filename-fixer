# 배포 체크리스트 📝

이 문서는 Render(백엔드)와 Netlify(프론트엔드) 배포를 위한 단계별 가이드입니다.

## 사전 준비

- [ ] GitHub 저장소에 코드 푸시 완료
- [ ] Render 계정 생성 (https://render.com)
- [ ] Netlify 계정 생성 (https://netlify.com)

## 1단계: 백엔드 배포 (Render)

### 1-1. Render에 배포

1. Render 대시보드 접속
2. **"New +"** → **"Web Service"** 클릭
3. GitHub 저장소 연결
4. 설정:
   ```
   Name: hangul-filename-fixer-api (또는 원하는 이름)
   Environment: Docker
   Region: 가장 가까운 지역 선택 (Singapore 추천)
   Branch: main (또는 사용 중인 브랜치)
   ```

### 1-2. Docker 설정

**방법 1: render.yaml 사용 (권장)**
- 프로젝트 루트의 `render.yaml` 파일이 자동으로 인식됩니다
- "Apply" 클릭하여 설정 적용

**방법 2: 수동 설정**
```
Dockerfile Path: ./backend/Dockerfile
Docker Build Context Directory: ./backend
```

### 1-3. 환경변수 설정

Environment 탭에서 다음 변수 추가:

| Key | Value | 비고 |
|-----|-------|------|
| `ENVIRONMENT` | `production` | 프로덕션 환경 |
| `ALLOWED_ORIGINS` | `*` | 임시 (나중에 Netlify URL로 변경) |
| `MAX_FILE_MB` | `100` | 파일 크기 제한 |

### 1-4. 배포 및 URL 확인

1. **"Create Web Service"** 클릭
2. 배포 로그 확인 (약 3-5분 소요)
3. 배포 완료 후 URL 확인
   - 예: `https://hangul-filename-fixer-api.onrender.com`
4. Health check 확인:
   ```bash
   curl https://your-app.onrender.com/health
   # 응답: {"status":"ok"}
   ```

✅ **백엔드 URL을 메모하세요!** 프론트엔드 설정에 필요합니다.

---

## 2단계: 프론트엔드 배포 (Netlify)

### 2-1. Netlify에 배포

1. Netlify 대시보드 접속
2. **"Add new site"** → **"Import an existing project"** 클릭
3. GitHub 저장소 연결
4. 설정:
   ```
   Base directory: frontend
   Build command: npm run build
   Publish directory: frontend/dist
   ```

### 2-2. 환경변수 설정

**Site configuration** → **Environment variables** 탭에서:

| Key | Value | 비고 |
|-----|-------|------|
| `VITE_API_URL` | `https://your-app.onrender.com` | ⚠️ 1단계에서 받은 Render URL |

⚠️ **중요**: 
- Render URL 끝에 `/`를 붙이지 마세요
- `https://`를 포함해야 합니다

### 2-3. 배포

1. **"Deploy site"** 클릭
2. 배포 로그 확인 (약 1-2분 소요)
3. 배포 완료 후 사이트 URL 확인
   - 예: `https://hangul-filename-fixer.netlify.app`

✅ **프론트엔드 URL을 메모하세요!** 백엔드 CORS 설정에 필요합니다.

---

## 3단계: CORS 설정 업데이트

### 3-1. Render 환경변수 업데이트

1. Render 대시보드로 돌아가기
2. **Environment** 탭 접속
3. `ALLOWED_ORIGINS` 값을 Netlify URL로 변경:
   ```
   ALLOWED_ORIGINS=https://your-actual-site.netlify.app
   ```
4. 저장 후 서비스 자동 재배포 대기 (약 1분)

### 3-2. 여러 도메인 허용 (선택사항)

개발 환경과 프로덕션을 동시에 허용하려면:
```
ALLOWED_ORIGINS=https://your-site.netlify.app,http://localhost:5173
```

---

## 4단계: 동작 확인

### 4-1. 프론트엔드 접속

1. Netlify URL로 접속
2. 파일 업로드 테스트:
   - 한글 파일명 (예: `테스트.txt`) 업로드
   - ZIP 다운로드 확인

### 4-2. 백엔드 API 테스트

```bash
# Health check
curl https://your-app.onrender.com/health

# API 문서 접속
open https://your-app.onrender.com/docs
```

---

## 5단계: 커스텀 도메인 설정 (선택사항)

### Netlify 커스텀 도메인

1. **Domain management** → **Add custom domain**
2. 도메인 입력 및 DNS 설정
3. SSL 자동 활성화 확인

**변경 후**: Render의 `ALLOWED_ORIGINS`를 새 도메인으로 업데이트!

### Render 커스텀 도메인

1. **Settings** → **Custom domain**
2. 도메인 입력 및 DNS 설정
3. SSL 자동 활성화 확인

**변경 후**: Netlify의 `VITE_API_URL`을 새 도메인으로 업데이트!

---

## 문제 해결

### ❌ CORS 오류

**증상**: 브라우저 콘솔에 CORS 에러
```
Access to fetch at 'https://...' has been blocked by CORS policy
```

**해결**:
1. Render의 `ALLOWED_ORIGINS`에 정확한 Netlify URL 입력
2. URL 끝에 `/` 없는지 확인
3. Render 서비스 재배포 대기

### ❌ 백엔드 응답 없음

**증상**: 프론트엔드에서 "처리 중..." 무한 로딩

**해결**:
1. Render 서비스가 슬립 모드인지 확인 (무료 플랜)
2. 직접 백엔드 URL 접속하여 깨우기
3. Netlify `VITE_API_URL` 확인

### ❌ 빌드 실패 (Netlify)

**증상**: "Build failed" 에러

**해결**:
```bash
# 로컬에서 빌드 테스트
cd frontend
npm install
npm run build

# 성공하면 커밋 후 재배포
```

### ❌ 환경변수가 적용되지 않음

**해결**:
1. Netlify: 환경변수 변경 후 **"Trigger deploy"** 클릭
2. Render: 환경변수 변경 후 자동 재배포 (약 1분)

---

## 유지보수

### 업데이트 배포

**자동 배포**: GitHub에 푸시하면 자동 배포됩니다.

```bash
git add .
git commit -m "Update: 기능 개선"
git push origin main
```

**수동 배포**:
- Netlify: **"Trigger deploy"** 클릭
- Render: **"Manual Deploy"** → **"Deploy latest commit"**

### 로그 확인

**Render**: 
- Dashboard → 서비스 선택 → **Logs** 탭

**Netlify**:
- Site overview → **Deploy log** 또는 **Function log**

### 무료 플랜 제한

**Render**:
- 15분 비활성 시 슬립 모드
- 월 750시간 무료 (약 31일)
- 첫 요청 시 웜업 시간: 30초 정도

**Netlify**:
- 월 100GB 대역폭
- 월 300분 빌드 시간

---

## 배포 완료 체크리스트 ✅

- [ ] 백엔드가 Render에 정상 배포됨
- [ ] 프론트엔드가 Netlify에 정상 배포됨
- [ ] CORS 설정 완료 (Netlify URL → Render 환경변수)
- [ ] 파일 업로드 및 다운로드 테스트 성공
- [ ] 백엔드 `/health` 엔드포인트 정상 응답
- [ ] 백엔드 `/docs` API 문서 접속 가능
- [ ] README.md 업데이트 (배포 URL 추가)

---

## 다음 단계

1. **모니터링 설정**: Uptime 체크 서비스 연동 (예: UptimeRobot)
2. **분석 도구**: Google Analytics 추가
3. **에러 추적**: Sentry 연동
4. **성능 최적화**: CDN 활용

배포 완료를 축하합니다! 🎉

