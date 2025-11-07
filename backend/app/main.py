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

    # ZIP 모드일 경우 in-memory zip 생성
    if zip:
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