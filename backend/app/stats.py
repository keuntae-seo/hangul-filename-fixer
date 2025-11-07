"""방문자 통계 관리"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict

STATS_FILE = Path("stats.json")

def load_stats() -> Dict:
    """통계 파일 로드"""
    if not STATS_FILE.exists():
        return {
            "total_views": 0,
            "total_files": 0,
            "today": datetime.now().strftime("%Y-%m-%d"),
            "today_views": 0,
        }
    
    try:
        with open(STATS_FILE, "r") as f:
            stats = json.load(f)
            # 날짜가 바뀌었으면 today_views 초기화
            today = datetime.now().strftime("%Y-%m-%d")
            if stats.get("today") != today:
                stats["today"] = today
                stats["today_views"] = 0
            return stats
    except:
        return {
            "total_views": 0,
            "total_files": 0,
            "today": datetime.now().strftime("%Y-%m-%d"),
            "today_views": 0,
        }

def save_stats(stats: Dict):
    """통계 파일 저장"""
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
    except:
        pass

def increment_view():
    """페이지 뷰 증가"""
    stats = load_stats()
    stats["total_views"] += 1
    stats["today_views"] += 1
    save_stats(stats)
    return stats

def increment_files(count: int = 1):
    """파일 처리 수 증가"""
    stats = load_stats()
    stats["total_files"] += count
    save_stats(stats)
    return stats

