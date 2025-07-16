import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 개발용)
load_dotenv()

class Settings:
    """애플리케이션 설정"""
    
    # 기본 설정
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # API 설정
    LLM_API_HOST: str = os.getenv("LLM_API_HOST", "0.0.0.0")
    LLM_API_PORT: int = int(os.getenv("LLM_API_PORT", "6020"))
    
    # 데이터베이스 설정 (필요시)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # 외부 API 키 (필요시)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # LLM 관련 설정
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # 로그 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def is_production(cls) -> bool:
        """프로덕션 환경인지 확인"""
        return cls.ENVIRONMENT.lower() == "production"
    
    @classmethod
    def is_development(cls) -> bool:
        """개발 환경인지 확인"""
        return cls.ENVIRONMENT.lower() == "development"

# 전역 설정 인스턴스
settings = Settings() 