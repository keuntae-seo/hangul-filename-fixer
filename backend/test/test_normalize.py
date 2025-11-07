# backend/tests/test_normalize.py
from app.core.normalize import fix_name, sanitize_base

def test_hangul_compose():
    assert fix_name("ㅂㅗㄱㅗㅅㅓ.hwp").startswith("보고서")

def test_forbidden_replaced():
    assert fix_name("회의:자료?.pptx").startswith("회의_자료_")

def test_trim_space_dot():
    assert fix_name("  제안서  최종  .pdf") == "제안서 최종.pdf"