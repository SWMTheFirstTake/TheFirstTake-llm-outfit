import redis
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

class RedisService:
    """Redis 연결 및 프롬프트 관리 서비스"""
    
    def __init__(self):
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Redis 연결"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                # db=int(os.getenv("REDIS_DB", "0")),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 연결 테스트
            self.redis_client.ping()
            logger.info(f"✅ Redis 연결 성공: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            self.redis_client = None
    
    def get_prompt(self, room_id: int) -> Optional[str]:
        """Redis에서 프롬프트 히스토리 가져오기"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return None
        
        try:
            key = f"{room_id}:prompt"
            value = self.redis_client.get(key)
            logger.info(f"Redis에서 프롬프트 조회: {key} = {value[:100] if value else 'None'}...")
            return value
        except Exception as e:
            logger.error(f"Redis 프롬프트 조회 실패: {e}")
            return None
    
    def append_prompt(self, room_id: int, content: str) -> bool:
        """Redis에 프롬프트 히스토리 추가"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return False
        
        try:
            key = f"{room_id}:prompt"
            current_value = self.redis_client.get(key) or ""
            
            # 새로운 내용 추가
            new_value = current_value + "\n" + content if current_value else content
            
            # 최대 길이 제한 (환경변수에서 직접 참조)
            max_context_length = int(os.getenv("MAX_CONTEXT_LENGTH", "10000"))
            max_context_lines = int(os.getenv("MAX_CONTEXT_LINES", "20"))
            
            if len(new_value) > max_context_length:
                # 라인별로 분할하여 최근 N라인만 유지
                lines = new_value.split('\n')
                if len(lines) > max_context_lines:
                    lines = lines[-max_context_lines:]
                new_value = '\n'.join(lines)
            
            # Redis에 저장 (24시간 만료)
            context_expire_time = int(os.getenv("CONTEXT_EXPIRE_TIME", "86400"))
            self.redis_client.setex(key, context_expire_time, new_value)
            logger.info(f"Redis에 프롬프트 추가: {key} (길이: {len(new_value)})")
            return True
        except Exception as e:
            logger.error(f"Redis 프롬프트 추가 실패: {e}")
            return False
    
    def set_prompt(self, room_id: int, content: str) -> bool:
        """Redis에 프롬프트 히스토리 설정 (덮어쓰기)"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return False
        
        try:
            key = f"{room_id}:prompt"
            context_expire_time = int(os.getenv("CONTEXT_EXPIRE_TIME", "86400"))
            self.redis_client.setex(key, context_expire_time, content)
            logger.info(f"Redis에 프롬프트 설정: {key} (길이: {len(content)})")
            return True
        except Exception as e:
            logger.error(f"Redis 프롬프트 설정 실패: {e}")
            return False

# 전역 Redis 서비스 인스턴스
redis_service = RedisService() 