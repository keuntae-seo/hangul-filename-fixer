# backend/app/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# config에서 DATABASE_URL 가져오기
try:
    from .core.config import settings
    DATABASE_URL = settings.DATABASE_URL
except ImportError:
    # 만약 임포트 실패하면 환경 변수에서 직접 가져오기
    import os
    DATABASE_URL = os.getenv("DATABASE_URL")

# PostgreSQL 연결이 설정되어 있는지 확인
if DATABASE_URL:
    # Render는 postgres://를 사용하지만 SQLAlchemy는 postgresql://를 요구함
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    # 로그 테이블 정의
    class ConversionLog(Base):
        __tablename__ = "conversion_logs"
        
        id = Column(Integer, primary_key=True, index=True)
        timestamp = Column(DateTime, default=datetime.now, index=True)
        original_filename = Column(String(500), nullable=False)
        converted_filename = Column(String(500), nullable=False)
        processing_time = Column(Float, nullable=True)  # 초 단위
        file_type = Column(String(50), nullable=True)  # 단일/ZIP내부/복수
        
        def __repr__(self):
            return f"<ConversionLog(id={self.id}, original='{self.original_filename}', converted='{self.converted_filename}')>"
    
    # 테이블 생성
    def init_db():
        """데이터베이스 테이블 초기화"""
        try:
            Base.metadata.create_all(bind=engine)
            print("[INFO] PostgreSQL 테이블 생성 완료")
        except Exception as e:
            print(f"[WARNING] 데이터베이스 연결 실패: {e}")
            print("[INFO] 데이터베이스 로깅이 비활성화되었습니다. 파일 로그만 사용됩니다.")
    
    # 로그 기록 함수
    def log_conversion_to_db(
        original_filename: str,
        converted_filename: str,
        processing_time: float = None,
        file_type: str = "단일"
    ):
        """변환 로그를 데이터베이스에 기록"""
        try:
            db = SessionLocal()
            log_entry = ConversionLog(
                original_filename=original_filename,
                converted_filename=converted_filename,
                processing_time=processing_time,
                file_type=file_type
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            db.close()
            return True
        except Exception as e:
            print(f"[ERROR] DB 로그 기록 실패: {e}")
            return False
    
    # 로그 조회 함수
    def get_recent_logs(limit: int = 100):
        """최근 로그 조회"""
        try:
            db = SessionLocal()
            logs = db.query(ConversionLog).order_by(
                ConversionLog.timestamp.desc()
            ).limit(limit).all()
            db.close()
            return logs
        except Exception as e:
            print(f"[ERROR] DB 로그 조회 실패: {e}")
            return []
    
    def get_stats_from_db():
        """데이터베이스에서 통계 조회"""
        try:
            db = SessionLocal()
            total_conversions = db.query(ConversionLog).count()
            
            # 오늘 날짜의 변환 수
            from sqlalchemy import func
            today = datetime.now().date()
            today_conversions = db.query(ConversionLog).filter(
                func.date(ConversionLog.timestamp) == today
            ).count()
            
            # 평균 처리 시간
            avg_time = db.query(func.avg(ConversionLog.processing_time)).scalar()
            
            db.close()
            return {
                "total_conversions": total_conversions,
                "today_conversions": today_conversions,
                "avg_processing_time": round(avg_time, 3) if avg_time else 0
            }
        except Exception as e:
            print(f"[ERROR] DB 통계 조회 실패: {e}")
            return {
                "total_conversions": 0,
                "today_conversions": 0,
                "avg_processing_time": 0
            }

else:
    # DATABASE_URL이 없으면 더미 함수 제공
    print("[INFO] DATABASE_URL이 설정되지 않았습니다. 파일 로그만 사용됩니다.")
    
    def init_db():
        pass
    
    def log_conversion_to_db(*args, **kwargs):
        return False
    
    def get_recent_logs(limit: int = 100):
        return []
    
    def get_stats_from_db():
        return {
            "total_conversions": 0,
            "today_conversions": 0,
            "avg_processing_time": 0
        }

