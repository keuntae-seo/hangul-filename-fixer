# backend/app/core/normalize.py
from __future__ import annotations
import re
import unicodedata
from typing import Tuple

_FORBIDDEN = re.compile(r"[\\/:*?\"<>|]")  # Windows 금지문자
_CTRL = re.compile(r"[\x00-\x1f\x7f]")     # 제어문자
_MULTISPACE = re.compile(r"\s{2,}")         # 연속 공백
_TRIM_DOT_SPACE = re.compile(r"^[ .]+|[ .]+$")


def sanitize_base(base: str) -> str:
    # 1) NFC 정규화 (자모 → 완성형)
    out = unicodedata.normalize("NFC", base)
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