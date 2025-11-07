# backend/app/main.py
from __future__ import annotations
import io
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .core.normalize import fix_name
from .schemas import BatchRenameResponse, RenameResult
from .core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# CORS: 프론트 도메인 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/rename", response_model=BatchRenameResponse)
async def rename(files: List[UploadFile] = File(...), zip: bool = False):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results: List[RenameResult] = []

    # 단일 파일 모드
    if len(files) == 1 and not zip:
        f = files[0]
        # 파일 크기 체크
        chunk = await f.read()
        size = len(chunk)
        if size > settings.MAX_FILE_MB * 1024 * 1024:
            raise HTTPException(413, detail=f"{f.filename}: file too large")
        
        new_name = fix_name(f.filename)
        
        # ZIP 파일인 경우: 내부 파일명도 정규화
        if f.filename and f.filename.lower().endswith('.zip'):
            try:
                import zipfile
                
                # 원본 ZIP 읽기
                original_zip = io.BytesIO(chunk)
                
                # 새 ZIP 생성
                new_zip_buf = io.BytesIO()
                
                with zipfile.ZipFile(original_zip, 'r') as zf_in:
                    with zipfile.ZipFile(new_zip_buf, 'w', compression=zipfile.ZIP_DEFLATED) as zf_out:
                        for item in zf_in.infolist():
                            # 디렉토리는 건너뛰기
                            if item.is_dir():
                                continue
                            
                            # 파일 읽기
                            file_data = zf_in.read(item.filename)
                            
                            # 파일명 정규화 (경로 포함)
                            normalized_filename = fix_name(item.filename)
                            
                            # 새 ZIP에 쓰기
                            zf_out.writestr(normalized_filename, file_data)
                
                new_zip_buf.seek(0)
                headers = {
                    "Content-Disposition": f'attachment; filename="{new_name}"'
                }
                return StreamingResponse(new_zip_buf, media_type="application/zip", headers=headers)
                
            except zipfile.BadZipFile:
                # ZIP 파일이 손상된 경우, 일반 파일로 처리
                pass
        
        # 일반 파일을 직접 반환
        buf = io.BytesIO(chunk)
        buf.seek(0)
        headers = {
            "Content-Disposition": f'attachment; filename="{new_name}"'
        }
        # 파일 타입 추정 (간단한 버전)
        media_type = "application/octet-stream"
        if new_name.endswith('.txt'):
            media_type = "text/plain"
        elif new_name.endswith('.pdf'):
            media_type = "application/pdf"
        elif new_name.endswith(('.jpg', '.jpeg')):
            media_type = "image/jpeg"
        elif new_name.endswith('.png'):
            media_type = "image/png"
        
        return StreamingResponse(buf, media_type=media_type, headers=headers)

    # ZIP 모드일 경우 in-memory zip 생성
    if zip or len(files) > 1:
        try:
            import zipfile
        except ImportError:  # 표준 라이브러리이므로 실제로는 발생 X
            raise HTTPException(500, detail="zipfile module not available")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                # 간단한 크기 제한 (선택)
                size = 0
                chunk = await f.read()
                size = len(chunk)
                if size > settings.MAX_FILE_MB * 1024 * 1024:
                    raise HTTPException(413, detail=f"{f.filename}: file too large")
                new_name = fix_name(f.filename)
                zf.writestr(new_name, chunk)
                results.append(RenameResult(original=f.filename, renamed=new_name))
        buf.seek(0)
        headers = {"Content-Disposition": 'attachment; filename="renamed-files.zip"'}
        # 본문은 스트리밍, 메타는 JSON으로도 반환하고 싶다면 별도 엔드포인트 구성
        return StreamingResponse(buf, media_type="application/zip", headers=headers)

    # 비 ZIP 모드: 메타만 JSON으로 반환 (실제 파일은 프론트에서 개별 저장)
    for f in files:
        new_name = fix_name(f.filename)
        results.append(RenameResult(original=f.filename, renamed=new_name))
    return JSONResponse(BatchRenameResponse(results=results, zipped=False).model_dump())