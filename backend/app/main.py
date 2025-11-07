# backend/app/main.py
from __future__ import annotations
import io
import time
import logging
from datetime import datetime
from typing import List
from urllib.parse import quote
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .core.normalize import fix_name, fix_text_content, fix_hwp_content
from .schemas import BatchRenameResponse, RenameResult
from .core.config import settings
from .stats import load_stats, increment_view, increment_files
from .database import init_db, log_conversion_to_db, get_recent_logs, get_stats_from_db

# 로깅 설정
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 변환 로그용 로거 설정
conversion_logger = logging.getLogger("conversion")
conversion_logger.setLevel(logging.INFO)

# 파일 핸들러 (logs/conversion.log)
file_handler = logging.FileHandler(log_dir / "conversion.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)

# 콘솔 핸들러
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '[CONVERSION] %(asctime)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)

conversion_logger.addHandler(file_handler)
conversion_logger.addHandler(console_handler)

app = FastAPI(title=settings.PROJECT_NAME)

# 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 데이터베이스 테이블 생성"""
    init_db()
    print("[INFO] 데이터베이스 초기화 완료")

# CORS: 프론트 도메인 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],  # 프론트엔드가 이 헤더를 읽을 수 있도록 허용
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def get_stats():
    """통계 정보 조회"""
    stats = load_stats()
    return {
        "total_views": stats.get("total_views", 0),
        "today_views": stats.get("today_views", 0),
        "total_files": stats.get("total_files", 0),
    }

@app.post("/stats/view")
def record_view():
    """페이지 뷰 기록"""
    stats = increment_view()
    return {
        "total_views": stats.get("total_views", 0),
        "today_views": stats.get("today_views", 0),
        "total_files": stats.get("total_files", 0),
    }

@app.get("/logs")
def get_logs(limit: int = 100):
    """변환 로그 조회 (최근 N개)"""
    logs = get_recent_logs(limit)
    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "original": log.original_filename,
                "converted": log.converted_filename,
                "processing_time": log.processing_time,
                "type": log.file_type
            }
            for log in logs
        ]
    }

@app.get("/logs/stats")
def get_log_stats():
    """로그 통계 조회"""
    return get_stats_from_db()

@app.post("/rename", response_model=BatchRenameResponse)
async def rename(files: List[UploadFile] = File(...), zip: bool = False):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # 변환 시작 시간 기록
    start_time = datetime.now()
    
    results: List[RenameResult] = []

    # 단일 파일 모드
    if len(files) == 1 and not zip:
        f = files[0]
        # 파일 크기 체크
        chunk = await f.read()
        size = len(chunk)
        if size > settings.MAX_FILE_MB * 1024 * 1024:
            raise HTTPException(413, detail=f"{f.filename}: file too large")
        
        original_name = f.filename or "unknown"
        new_name = fix_name(original_name)
        
        # 변환 로그 기록
        elapsed = (datetime.now() - start_time).total_seconds()
        conversion_logger.info(f"'{original_name}' → '{new_name}' | {elapsed:.2f}초")
        
        # 데이터베이스에 로그 기록
        log_conversion_to_db(original_name, new_name, elapsed, "단일")
        
        # ZIP 파일인 경우: 내부 파일명도 정규화
        if f.filename and f.filename.lower().endswith('.zip'):
            try:
                import zipfile
                
                # 원본 ZIP 읽기
                original_zip = io.BytesIO(chunk)
                
                # 새 ZIP 생성
                new_zip_buf = io.BytesIO()
                
                with zipfile.ZipFile(original_zip, 'r') as zf_in:
                    with zipfile.ZipFile(new_zip_buf, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zf_out:
                        # 생성된 디렉토리 추적
                        created_dirs = set()
                        
                        for item in zf_in.infolist():
                            # 디렉토리는 건너뛰기
                            if item.is_dir():
                                continue
                            
                            # macOS 메타데이터 파일 제외
                            if item.filename.startswith('__MACOSX/') or '/__MACOSX/' in item.filename:
                                print(f"[DEBUG] 제외: {item.filename} (macOS 메타데이터)")
                                continue
                            
                            # macOS 리소스 포크 파일 제외 (._로 시작하는 파일)
                            filename_only = item.filename.split('/')[-1]
                            if filename_only.startswith('._'):
                                print(f"[DEBUG] 제외: {item.filename} (리소스 포크)")
                                continue
                            
                            # .DS_Store 파일 제외
                            if filename_only == '.DS_Store':
                                print(f"[DEBUG] 제외: {item.filename} (.DS_Store)")
                                continue
                            
                            # 파일 읽기
                            file_data = zf_in.read(item.filename)
                            
                            # 디버깅: 원본 파일명 출력
                            print(f"[DEBUG] 원본 파일명: {repr(item.filename)}")
                            print(f"[DEBUG] UTF-8 플래그: {item.flag_bits & 0x800}")
                            
                            # 파일명 인코딩 처리
                            original_filename = item.filename
                            if not (item.flag_bits & 0x800):  # UTF-8 플래그가 없으면
                                try:
                                    # CP437(macOS/Unix 기본)에서 바이트로 변환 후 UTF-8로 재해석
                                    original_filename = item.filename.encode('cp437').decode('utf-8')
                                    print(f"[DEBUG] CP437→UTF-8: {repr(original_filename)}")
                                except:
                                    try:
                                        # CP949(Windows 한글) 시도
                                        original_filename = item.filename.encode('cp437').decode('cp949')
                                        print(f"[DEBUG] CP437→CP949: {repr(original_filename)}")
                                    except:
                                        print(f"[DEBUG] 인코딩 실패, 원본 사용")
                                        pass
                            
                            # 파일명 정규화 (경로 포함)
                            path_parts = original_filename.replace('\\', '/').split('/')
                            normalized_parts = [fix_name(part) for part in path_parts]
                            normalized_filename = '/'.join(normalized_parts)
                            
                            print(f"[DEBUG] 정규화된 파일명: {repr(normalized_filename)}")
                            
                            # ZIP 내부 파일 변환 로그
                            if original_filename != normalized_filename:
                                conversion_logger.info(f"[ZIP 내부] '{original_filename}' → '{normalized_filename}'")
                                log_conversion_to_db(original_filename, normalized_filename, None, "ZIP내부")
                            
                            # .txt 파일의 경우 내용도 수정
                            if normalized_filename.lower().endswith('.txt'):
                                try:
                                    # 텍스트로 디코딩
                                    text_content = file_data.decode('utf-8')
                                    # 자모 조합
                                    fixed_content = fix_text_content(text_content)
                                    # 다시 바이트로 인코딩
                                    file_data = fixed_content.encode('utf-8')
                                    print(f"[DEBUG] .txt 파일 내용 정규화 완료")
                                except Exception as e:
                                    print(f"[DEBUG] .txt 내용 처리 실패: {e}")
                                    # 실패하면 원본 그대로 사용
                            
                            # .hwp 파일의 경우 내용도 수정
                            elif normalized_filename.lower().endswith('.hwp'):
                                try:
                                    file_data, modified = fix_hwp_content(file_data)
                                    if modified:
                                        print(f"[DEBUG] .hwp 파일 내용 정규화 완료")
                                except Exception as e:
                                    print(f"[DEBUG] .hwp 내용 처리 실패: {e}")
                            
                            # 상위 디렉토리 생성
                            if '/' in normalized_filename:
                                dirs = normalized_filename.split('/')
                                for i in range(1, len(dirs)):
                                    dir_path = '/'.join(dirs[:i]) + '/'
                                    if dir_path not in created_dirs:
                                        dir_info = zipfile.ZipInfo(dir_path)
                                        dir_info.date_time = time.localtime()[:6]
                                        dir_info.external_attr = 0o755 << 16 | 0x10  # 디렉토리 플래그
                                        zf_out.writestr(dir_info, '')
                                        created_dirs.add(dir_path)
                                        print(f"[DEBUG] 디렉토리 생성: {dir_path}")
                            
                            # 새 ZipInfo 생성
                            zip_info = zipfile.ZipInfo(normalized_filename)
                            zip_info.date_time = item.date_time or time.localtime()[:6]
                            zip_info.compress_type = zipfile.ZIP_DEFLATED
                            zip_info.flag_bits = 0x800  # UTF-8 파일명 플래그
                            # external_attr 설정 (파일 권한)
                            if item.external_attr:
                                zip_info.external_attr = item.external_attr
                            else:
                                zip_info.external_attr = 0o644 << 16  # 기본 권한
                            
                            # 새 ZIP에 쓰기
                            zf_out.writestr(zip_info, file_data, compress_type=zipfile.ZIP_DEFLATED)
                
                new_zip_buf.seek(0)
                # 한글 파일명을 URL 인코딩 (RFC 2231)
                encoded_filename = quote(new_name, safe='')
                headers = {
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
                return StreamingResponse(new_zip_buf, media_type="application/zip", headers=headers)
                
            except Exception as e:
                # ZIP 파일 처리 실패 시, 일반 파일로 처리
                print(f"ZIP processing error: {str(e)}")
                # 원본 ZIP을 그대로 정규화된 이름으로 반환
                pass
        
        # 일반 파일을 직접 반환
        # .txt 파일의 경우 내용도 수정
        if new_name.lower().endswith('.txt'):
            try:
                # 텍스트로 디코딩
                text_content = chunk.decode('utf-8')
                # 자모 조합
                fixed_content = fix_text_content(text_content)
                # 다시 바이트로 인코딩
                chunk = fixed_content.encode('utf-8')
                print(f"[DEBUG] 단일 .txt 파일 내용 정규화 완료")
            except Exception as e:
                print(f"[DEBUG] .txt 내용 처리 실패: {e}")
                # 실패하면 원본 그대로 사용
        
        # .hwp 파일의 경우 내용도 수정
        elif new_name.lower().endswith('.hwp'):
            try:
                chunk, modified = fix_hwp_content(chunk)
                if modified:
                    print(f"[DEBUG] 단일 .hwp 파일 내용 정규화 완료")
            except Exception as e:
                print(f"[DEBUG] .hwp 내용 처리 실패: {e}")
        
        # 통계: 파일 처리 수 증가
        increment_files(1)
        
        buf = io.BytesIO(chunk)
        buf.seek(0)
        # 한글 파일명을 URL 인코딩 (RFC 2231)
        encoded_filename = quote(new_name, safe='')
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
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
        with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=False) as zf:
            for f in files:
                # 간단한 크기 제한 (선택)
                size = 0
                chunk = await f.read()
                size = len(chunk)
                if size > settings.MAX_FILE_MB * 1024 * 1024:
                    raise HTTPException(413, detail=f"{f.filename}: file too large")
                
                original_name = f.filename or "unknown"
                new_name = fix_name(original_name)
                
                # 변환 로그 기록
                conversion_logger.info(f"[복수 파일] '{original_name}' → '{new_name}'")
                log_conversion_to_db(original_name, new_name, None, "복수")
                
                # ZipInfo 생성 (UTF-8 플래그 설정)
                zip_info = zipfile.ZipInfo(new_name)
                zip_info.date_time = time.localtime(time.time())[:6]  # 현재 시간
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                zip_info.flag_bits = 0x800  # UTF-8 파일명 플래그
                zip_info.external_attr = 0o644 << 16  # 파일 권한 (rw-r--r--)
                
                zf.writestr(zip_info, chunk, compress_type=zipfile.ZIP_DEFLATED)
                results.append(RenameResult(original=f.filename, renamed=new_name))
        buf.seek(0)
        # 통계: 파일 처리 수 증가
        increment_files(len(files))
        
        # 전체 처리 시간 로그
        elapsed = (datetime.now() - start_time).total_seconds()
        conversion_logger.info(f"[완료] 총 {len(files)}개 파일 처리 | {elapsed:.2f}초")
        
        # 한글 파일명을 URL 인코딩 (RFC 2231)
        encoded_filename = quote('renamed-files.zip', safe='')
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        # 본문은 스트리밍, 메타는 JSON으로도 반환하고 싶다면 별도 엔드포인트 구성
        return StreamingResponse(buf, media_type="application/zip", headers=headers)

    # 비 ZIP 모드: 메타만 JSON으로 반환 (실제 파일은 프론트에서 개별 저장)
    for f in files:
        new_name = fix_name(f.filename)
        results.append(RenameResult(original=f.filename, renamed=new_name))
    return JSONResponse(BatchRenameResponse(results=results, zipped=False).model_dump())