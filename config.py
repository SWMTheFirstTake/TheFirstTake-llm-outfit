import os
from dotenv import load_dotenv

# .env 파일 로드 (로컬 개발용)
load_dotenv()

# API 키 디버깅 (개발 환경에서만)
if os.getenv("ENVIRONMENT", "development") == "development":
    print(f"🔍 환경변수 CLAUDE_API_KEY: {'설정됨' if os.getenv('CLAUDE_API_KEY') else 'NOT_SET'}")
    print(f"🔍 환경변수 CLAUDE_API_KEY 길이: {len(os.getenv('CLAUDE_API_KEY', ''))}")
    print(f"🔍 환경변수 AWS_ACCESS_KEY: {'설정됨' if os.getenv('AWS_ACCESS_KEY') else 'NOT_SET'}")
    print(f"🔍 환경변수 AWS_SECRET_KEY: {'설정됨' if os.getenv('AWS_SECRET_KEY') else 'NOT_SET'}")
    print(f"🔍 환경변수 AWS_REGION: {os.getenv('AWS_REGION', 'NOT_SET')}")
    print(f"🔍 환경변수 S3_COMBINATION_BUCKET_NAME: {os.getenv('S3_COMBINATION_BUCKET_NAME', 'NOT_SET')}")

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
    CLAUDE_API_KEY: str = os.getenv("CLAUDE_API_KEY", "")

    # LLM 관련 설정
    # LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-4o-mini")
    # LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "claude-3-5-sonnet-20241022")  # Claude 모델로 변경
    # LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "claude-sonnet-4-20250514")  # Claude 모델로 변경
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "claude-3-haiku-20240307")  # Claude 모델로 변경
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "1000"))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # 로그 설정
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Redis 설정
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

    # AWS S3 설정
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-2")
    S3_COMBINATION_BUCKET_NAME: str = os.getenv("S3_COMBINATION_BUCKET_NAME", "thefirsttake-combination")
    S3_COMBINATION_BUCKET_IMAGE_PREFIX: str = os.getenv("S3_COMBINATION_BUCKET_IMAGE_PREFIX", "image")
    S3_COMBINATION_BUCKET_JSON_PREFIX: str = os.getenv("S3_COMBINATION_BUCKET_JSON_PREFIX", "json")

    # 프롬프트 관리 설정
    MAX_CONTEXT_LENGTH = 10000  # 최대 컨텍스트 길이
    MAX_CONTEXT_LINES = 20      # 최대 컨텍스트 라인 수
    CONTEXT_EXPIRE_TIME = 86400  # 24시간 (초)
    RETURN_PROMPT_HISTORY = False  # 프롬프트 히스토리 반환 여부
    
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