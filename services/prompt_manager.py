import redis
import json
from typing import Optional, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
import logging
# prompt_manager.py 맨 위에 추가


from models.curation_models import CurationStyle  # 이거 추가!
logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        # 스타일별 프롬프트 템플릿
        self.style_templates = {
            CurationStyle.FORMAL: "라는 사용자의 질문에 대해 웬만하면 포멀한 스타일로 스타일 한 개만 추천해줘",
            CurationStyle.CASUAL: "라는 사용자의 질문에 대해 웬만하면 캐쥬얼한 스타일로 스타일 한 개만 추천해줘",
            CurationStyle.CITY_BOY: "라는 사용자의 질문에 대해 웬만하면 시티보이 스타일로 스타일 한 개만 추천해줘"
        }
        
        self.base_system_prompt = "당신은 의상 추천 전문가입니다. 사용자의 질문에 친근하고 도움이 되는 답변을 해주세요."
    
    def get_prompt_key(self, room_id: int) -> str:
        return f"{room_id}:prompt"
    
    def get_or_create_prompt_context(self, room_id: int, user_input: str) -> str:
        """기존 프롬프트 컨텍스트를 가져오거나 새로 생성"""
        prompt_key = self.get_prompt_key(room_id)
        
        try:
            existing_context = self.redis_client.get(prompt_key)
            if existing_context:
                return existing_context + "\n" + user_input
            else:
                return user_input
        except Exception as e:
            logger.error(f"Redis에서 프롬프트 컨텍스트 조회 실패: {e}")
            return user_input
    
    def build_style_prompt(self, context: str, style: CurationStyle) -> str:
        """스타일별 프롬프트 빌드"""
        style_addition = self.style_templates.get(style, "")
        return context + style_addition
    
    def update_prompt_context(self, room_id: int, new_context: str):
        """프롬프트 컨텍스트 업데이트"""
        prompt_key = self.get_prompt_key(room_id)
        
        try:
            # 컨텍스트를 일정 크기로 제한 (토큰 수 관리)
            if len(new_context) > settings.MAX_CONTEXT_LENGTH:
                # 최근 컨텍스트만 유지
                lines = new_context.split('\n')
                new_context = '\n'.join(lines[-settings.MAX_CONTEXT_LINES:])
            
            self.redis_client.setex(
                prompt_key, 
                settings.CONTEXT_EXPIRE_TIME,  # 24시간 후 만료
                new_context
            )
        except Exception as e:
            logger.error(f"Redis에 프롬프트 컨텍스트 저장 실패: {e}")
    
    def get_system_prompt(self) -> str:
        return self.base_system_prompt
    
    def clear_context(self, room_id: int):
        """컨텍스트 초기화"""
        prompt_key = self.get_prompt_key(room_id)
        try:
            self.redis_client.delete(prompt_key)
        except Exception as e:
            logger.error(f"Redis 컨텍스트 삭제 실패: {e}")