# backend/app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Hangul Filename Fixer API"
    MAX_FILE_MB: int = 100  # 개별 파일 크기 제한 (필요시 조정)
    
    # CORS 설정 - 프론트엔드 URL
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    
    # 환경 구분
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # PostgreSQL 데이터베이스 URL (선택 사항)
    DATABASE_URL: Optional[str] = None
    
    @property
    def cors_origins(self) -> List[str]:
        """CORS 허용 오리진 리스트 반환 (쉼표로 구분)"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()