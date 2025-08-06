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
    
    def get_recent_used_outfits(self, room_id: int, limit: int = 5) -> list:
        """최근 사용된 아이템 목록 가져오기"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return []
        
        try:
            key = f"{room_id}:recent_outfits"
            recent_outfits = self.redis_client.lrange(key, 0, limit - 1)
            logger.info(f"Redis에서 최근 사용 아이템 조회: {key} = {len(recent_outfits)}개")
            return recent_outfits
        except Exception as e:
            logger.error(f"최근 사용 아이템 조회 실패: {e}")
            return []
    
    def add_recent_used_outfit(self, room_id: int, filename: str) -> bool:
        """최근 사용된 아이템 목록에 추가"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return False
        
        try:
            key = f"{room_id}:recent_outfits"
            
            # 기존 목록에서 같은 아이템 제거 (중복 방지)
            removed_count = self.redis_client.lrem(key, 0, filename)
            if removed_count > 0:
                logger.info(f"기존 중복 아이템 제거: {filename} ({removed_count}개)")
            
            # 새로운 아이템을 맨 앞에 추가
            self.redis_client.lpush(key, filename)
            
            # 최대 30개까지만 유지 (더 많은 중복 방지)
            self.redis_client.ltrim(key, 0, 29)
            
            # 4시간 만료 (더 긴 시간 동안 중복 방지)
            self.redis_client.expire(key, 14400)
            
            logger.info(f"최근 사용 아이템 추가: {room_id}:{filename}")
            return True
        except Exception as e:
            logger.error(f"최근 사용 아이템 추가 실패: {e}")
            return False
    
    # 인덱스 서비스를 위한 추가 메서드들
    def set_json(self, key: str, data: dict, expire_time: int = 86400) -> bool:
        """JSON 데이터를 Redis에 저장"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return False
        
        try:
            json_data = json.dumps(data, ensure_ascii=False)
            self.redis_client.setex(key, expire_time, json_data)
            logger.info(f"Redis에 JSON 데이터 저장: {key}")
            return True
        except Exception as e:
            logger.error(f"Redis JSON 데이터 저장 실패: {e}")
            return False
    
    def get_json(self, key: str) -> Optional[dict]:
        """Redis에서 JSON 데이터 조회"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return None
        
        try:
            json_data = self.redis_client.get(key)
            if json_data:
                return json.loads(json_data)
            return None
        except Exception as e:
            logger.error(f"Redis JSON 데이터 조회 실패: {e}")
            return None
    
    def sadd(self, key: str, *members) -> int:
        """Set에 멤버 추가"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return 0
        
        try:
            return self.redis_client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis Set 추가 실패: {e}")
            return 0
    
    def smembers(self, key: str) -> set:
        """Set의 모든 멤버 조회"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return set()
        
        try:
            return self.redis_client.smembers(key)
        except Exception as e:
            logger.error(f"Redis Set 조회 실패: {e}")
            return set()
    
    def keys(self, pattern: str) -> list:
        """패턴에 맞는 키들 조회"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis 키 조회 실패: {e}")
            return []
    
    def delete(self, *keys) -> int:
        """키들 삭제"""
        if not self.redis_client:
            logger.warning("Redis 클라이언트가 연결되지 않았습니다")
            return 0
        
        try:
            return self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis 키 삭제 실패: {e}")
            return 0

# 전역 Redis 서비스 인스턴스
redis_service = RedisService() 