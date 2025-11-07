# backend/app/core/normalize.py
from __future__ import annotations
import re
import unicodedata
from typing import Tuple

_FORBIDDEN = re.compile(r"[\\/:*?\"<>|]")  # Windows 금지문자
_CTRL = re.compile(r"[\x00-\x1f\x7f]")     # 제어문자
_MULTISPACE = re.compile(r"\s{2,}")         # 연속 공백
_TRIM_DOT_SPACE = re.compile(r"^[ .]+|[ .]+$")

# 한글 자음/모음 매핑 (U+3131 ~ U+318E)
JAMO_CHOSEONG = "ㄱㄲㄴㄴㄷㄸㄹㄹㅁㅁㅂㅃㅅㅆㅇㅇㅈㅉㅊㅊㅋㅋㅌㅌㅍㅍㅎㅎ"
JAMO_JUNGSEONG = " ㅏㅐㅑㅒㅓㅔㅕㅖㅗ ㅛ ㅜ ㅠㅡㅢㅣ"
JAMO_JONGSEONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"

# 호환 자모 → 조합용 자모 변환 테이블
COMPAT_TO_JAMO = {
    # 초성 (자음)
    'ㄱ': (0, -1), 'ㄲ': (1, -1), 'ㄴ': (2, -1), 'ㄷ': (3, -1), 'ㄸ': (4, -1),
    'ㄹ': (5, -1), 'ㅁ': (6, -1), 'ㅂ': (7, -1), 'ㅃ': (8, -1), 'ㅅ': (9, -1),
    'ㅆ': (10, -1), 'ㅇ': (11, -1), 'ㅈ': (12, -1), 'ㅉ': (13, -1), 'ㅊ': (14, -1),
    'ㅋ': (15, -1), 'ㅌ': (16, -1), 'ㅍ': (17, -1), 'ㅎ': (18, -1),
    # 중성 (모음)
    'ㅏ': (-1, 0), 'ㅐ': (-1, 1), 'ㅑ': (-1, 2), 'ㅒ': (-1, 3), 'ㅓ': (-1, 4),
    'ㅔ': (-1, 5), 'ㅕ': (-1, 6), 'ㅖ': (-1, 7), 'ㅗ': (-1, 8), 'ㅘ': (-1, 9),
    'ㅙ': (-1, 10), 'ㅚ': (-1, 11), 'ㅛ': (-1, 12), 'ㅜ': (-1, 13), 'ㅝ': (-1, 14),
    'ㅞ': (-1, 15), 'ㅟ': (-1, 16), 'ㅠ': (-1, 17), 'ㅡ': (-1, 18), 'ㅢ': (-1, 19),
    'ㅣ': (-1, 20),
}

# 종성 매핑 (받침)
JONGSEONG_MAP = {
    'ㄱ': 1, 'ㄲ': 2, 'ㄳ': 3, 'ㄴ': 4, 'ㄵ': 5, 'ㄶ': 6, 'ㄷ': 7, 'ㄹ': 8,
    'ㄺ': 9, 'ㄻ': 10, 'ㄼ': 11, 'ㄽ': 12, 'ㄾ': 13, 'ㄿ': 14, 'ㅀ': 15, 'ㅁ': 16,
    'ㅂ': 17, 'ㅄ': 18, 'ㅅ': 19, 'ㅆ': 20, 'ㅇ': 21, 'ㅈ': 22, 'ㅊ': 23, 'ㅋ': 24,
    'ㅌ': 25, 'ㅍ': 26, 'ㅎ': 27,
}


def compose_hangul(text: str) -> str:
    """한글 자모를 완성형으로 조합"""
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        
        # 호환 자모가 아니면 그대로 추가
        if char not in COMPAT_TO_JAMO:
            result.append(char)
            i += 1
            continue
        
        cho_idx, jung_idx = COMPAT_TO_JAMO[char]
        
        # 자음으로 시작하는 경우
        if cho_idx >= 0 and i + 1 < len(text):
            next_char = text[i + 1]
            if next_char in COMPAT_TO_JAMO:
                next_cho, next_jung = COMPAT_TO_JAMO[next_char]
                
                # 자음 + 모음
                if next_jung >= 0:
                    jong_idx = 0  # 받침 없음
                    consumed = 2  # 기본적으로 2글자 소비 (초성 + 중성)
                    
                    # 받침 확인
                    if i + 2 < len(text):
                        third_char = text[i + 2]
                        # 다음 글자가 모음이면 받침이 아님
                        if third_char in COMPAT_TO_JAMO:
                            third_cho, third_jung = COMPAT_TO_JAMO[third_char]
                            # 모음이 아니고 종성으로 사용 가능한 자음이면 받침
                            if third_jung < 0 and third_char in JONGSEONG_MAP:
                                # 그 다음 글자를 확인
                                if i + 3 < len(text):
                                    fourth_char = text[i + 3]
                                    if fourth_char in COMPAT_TO_JAMO:
                                        fourth_cho, fourth_jung = COMPAT_TO_JAMO[fourth_char]
                                        # 다음이 모음이면 받침이 아님
                                        if fourth_jung < 0:
                                            jong_idx = JONGSEONG_MAP[third_char]
                                            consumed = 3
                                        # 다음이 모음이면 현재 자음은 다음 음절의 초성
                                    else:
                                        # 다음이 자모가 아니면 받침
                                        jong_idx = JONGSEONG_MAP[third_char]
                                        consumed = 3
                                else:
                                    # 마지막 글자면 받침
                                    jong_idx = JONGSEONG_MAP[third_char]
                                    consumed = 3
                    
                    # 완성형 한글 생성: 0xAC00 + (초성 × 588) + (중성 × 28) + 종성
                    syllable = 0xAC00 + (cho_idx * 588) + (next_jung * 28) + jong_idx
                    result.append(chr(syllable))
                    i += consumed
                    continue
        
        # 조합 실패 시 원본 문자 추가
        result.append(char)
        i += 1
    
    return ''.join(result)


def sanitize_base(base: str) -> str:
    # 0) 한글 자모 조합
    out = compose_hangul(base)
    # 1) NFC 정규화 (자모 → 완성형)
    out = unicodedata.normalize("NFC", out)
    # 2) 금지문자/제어문자 제거
    out = _FORBIDDEN.sub("_", out)
    out = _CTRL.sub("", out)
    # 3) 연속 공백 1칸
    out = _MULTISPACE.sub(" ", out)
    # 4) 앞/뒤 공백·점 제거 (Windows 규칙)
    out = _TRIM_DOT_SPACE.sub("", out)
    # 5) 빈 문자열 대비
    return out or "renamed"


def fix_name(filename: str) -> str:
    # 확장자 분리
    dot = filename.rfind(".")
    has_ext = dot > 0
    base = filename[:dot] if has_ext else filename
    ext = filename[dot:] if has_ext else ""
    clean = sanitize_base(base)
    return f"{clean}{ext}"


def fix_text_content(content: str) -> str:
    """텍스트 내용의 한글 자모를 완성형으로 조합"""
    return compose_hangul(content)


def fix_hwp_content(hwp_data: bytes) -> tuple[bytes, bool]:
    """
    HWP 파일 내용의 한글 자모를 조합
    Returns: (수정된 데이터, 수정 여부)
    """
    import zipfile
    import io
    import zlib
    
    try:
        # HWP 5.0+ (ZIP 기반) 확인
        zip_file = io.BytesIO(hwp_data)
        if zipfile.is_zipfile(zip_file):
            print("[DEBUG] HWP 5.0+ ZIP 포맷 감지")
            return fix_hwp5_content(hwp_data)
        
        # HWP 3.0~4.0 (OLE 기반)
        print("[DEBUG] HWP 3.0~4.0 OLE 포맷 시도")
        return fix_hwp3_content(hwp_data)
        
    except Exception as e:
        print(f"[DEBUG] HWP 처리 실패: {e}")
        return hwp_data, False


def fix_hwp5_content(hwp_data: bytes) -> tuple[bytes, bool]:
    """HWP 5.0+ (ZIP 기반) 파일 처리"""
    import zipfile
    import io
    import re
    
    try:
        zip_file = io.BytesIO(hwp_data)
        modified = False
        
        # 새 ZIP 생성
        new_zip = io.BytesIO()
        
        with zipfile.ZipFile(zip_file, 'r') as zf_in:
            with zipfile.ZipFile(new_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf_out:
                for item in zf_in.infolist():
                    data = zf_in.read(item.filename)
                    
                    # section*.xml 파일 처리
                    if 'section' in item.filename.lower() and item.filename.endswith('.xml'):
                        try:
                            text = data.decode('utf-8')
                            # XML 태그 내의 텍스트만 처리
                            fixed_text = re.sub(
                                r'>([^<]+)<',
                                lambda m: '>' + compose_hangul(m.group(1)) + '<',
                                text
                            )
                            if fixed_text != text:
                                data = fixed_text.encode('utf-8')
                                modified = True
                                print(f"[DEBUG] {item.filename} 수정됨")
                        except Exception as e:
                            print(f"[DEBUG] {item.filename} 처리 실패: {e}")
                    
                    zf_out.writestr(item, data)
        
        if modified:
            new_zip.seek(0)
            return new_zip.read(), True
        
        return hwp_data, False
        
    except Exception as e:
        print(f"[DEBUG] HWP 5.0 처리 실패: {e}")
        return hwp_data, False


def fix_hwp3_content(hwp_data: bytes) -> tuple[bytes, bool]:
    """HWP 3.0~4.0 (OLE 기반) 파일 처리"""
    import io
    import zlib
    
    try:
        import olefile
        
        ole_file = io.BytesIO(hwp_data)
        ole = olefile.OleFileIO(ole_file)
        modified = False
        
        # 새 OLE 파일 생성
        new_ole_buf = io.BytesIO()
        new_ole = olefile.OleFileIO()
        
        # 모든 스트림 복사
        for entry in ole.listdir():
            stream_path = entry
            stream_name = '/'.join(entry)
            stream_data = ole.openstream(entry).read()
            
            # BodyText/Section* 스트림 처리
            if len(entry) >= 2 and entry[0] == 'BodyText' and entry[1].startswith('Section'):
                try:
                    # zlib 압축 해제 시도
                    try:
                        decompressed = zlib.decompress(stream_data)
                    except:
                        decompressed = stream_data
                    
                    # UTF-16LE로 디코딩 시도
                    text = decompressed.decode('utf-16le', errors='ignore')
                    
                    # 자모 조합
                    fixed_text = compose_hangul(text)
                    
                    if fixed_text != text:
                        # 다시 인코딩 및 압축
                        fixed_data = fixed_text.encode('utf-16le')
                        try:
                            stream_data = zlib.compress(fixed_data)
                        except:
                            stream_data = fixed_data
                        
                        modified = True
                        print(f"[DEBUG] {stream_name} 수정됨")
                        
                except Exception as e:
                    print(f"[DEBUG] {stream_name} 처리 중 오류: {e}")
            
            # 스트림 저장
            new_ole.save(stream_path, stream_data)
        
        if modified:
            new_ole.save(new_ole_buf)
            new_ole_buf.seek(0)
            result = new_ole_buf.read()
            ole.close()
            new_ole.close()
            return result, True
        
        ole.close()
        new_ole.close()
        return hwp_data, False
        
    except Exception as e:
        print(f"[DEBUG] HWP 3.0 처리 실패: {e}")
        return hwp_data, False