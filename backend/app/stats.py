# backend/app/stats.py
import json
from pathlib import Path
from datetime import datetime

STATS_FILE = Path("data/stats.json")

def _ensure_data_dir():
    """data 디렉토리 생성"""
    STATS_FILE.parent.mkdir(exist_ok=True)

def load_stats():
    """통계 로드"""
    _ensure_data_dir()
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "total_views": 0,
        "today_views": 0,
        "total_files": 0,
        "last_date": datetime.now().strftime("%Y-%m-%d")
    }

def save_stats(stats):
    """통계 저장"""
    _ensure_data_dir()
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def increment_view():
    """방문자 수 증가"""
    stats = load_stats()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 날짜가 바뀌면 오늘 방문자 수 초기화
    if stats.get("last_date") != today:
        stats["today_views"] = 0
        stats["last_date"] = today
    
    stats["total_views"] = stats.get("total_views", 0) + 1
    stats["today_views"] = stats.get("today_views", 0) + 1
    
    save_stats(stats)
    return stats

def increment_files(count=1):
    """처리된 파일 수 증가"""
    stats = load_stats()
    stats["total_files"] = stats.get("total_files", 0) + count
    save_stats(stats)
    return stats
