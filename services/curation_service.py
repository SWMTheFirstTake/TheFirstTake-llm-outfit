import asyncio
from typing import List, Dict
import openai
import sys
import os
# 상위 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
from models.curation_models import CurationStyle, CurationRequest, CurationResponse
from services.prompt_manager import PromptManager
import logging

logger = logging.getLogger(__name__)

class CurationService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.prompt_manager = PromptManager()
    
    async def generate_curation_response(self, request: CurationRequest) -> CurationResponse:
        """메인 큐레이션 생성 메서드"""
        # 1. 프롬프트 컨텍스트 가져오기
        current_context = self.prompt_manager.get_or_create_prompt_context(
            request.room_id, 
            request.user_input
        )
        
        # 2. 스타일별 비동기 큐레이션 생성
        tasks = []
        for style in request.styles:
            task = self._generate_single_curation(current_context, style)
            tasks.append(task)
        
        # 3. 모든 큐레이션 결과 대기
        curation_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. 결과 정리
        results = []
        context_builder = [current_context]
        
        for i, (style, result) in enumerate(zip(request.styles, curation_results)):
            if isinstance(result, Exception):
                logger.error(f"큐레이션 생성 실패 - 스타일: {style}, 에러: {result}")
                content = "큐레이션 결과를 가져오는 중 오류가 발생했습니다."
            else:
                content = result + f" ({i+1}번째 AI)"
                context_builder.append(content)
            
            results.append({
                "style": style.value,
                "content": content
            })
        
        # 5. 프롬프트 컨텍스트 업데이트
        updated_context = '\n'.join(context_builder)
        self.prompt_manager.update_prompt_context(request.room_id, updated_context)
        
        return CurationResponse(
            room_id=request.room_id,
            results=results,
            prompt_history=updated_context if settings.RETURN_PROMPT_HISTORY else None
        )
    
    async def _generate_single_curation(self, context: str, style: CurationStyle) -> str:
        """단일 스타일 큐레이션 생성"""
        try:
            style_prompt = self.prompt_manager.build_style_prompt(context, style)
            system_prompt = self.prompt_manager.get_system_prompt()
            
            # 비동기 OpenAI 호출
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._call_openai_sync,
                system_prompt,
                style_prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI 호출 실패 - 스타일: {style}, 에러: {e}")
            raise e
    
    def _call_openai_sync(self, system_prompt: str, user_prompt: str) -> str:
        """동기 OpenAI 호출 (executor에서 실행)"""
        response = self.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE
        )
        
        return response.choices[0].message.content
    
    def ask_single_prompt(self, prompt: str) -> str:
        """기존 단일 프롬프트 API 호환성 유지"""
        try:
            system_prompt = self.prompt_manager.get_system_prompt()
            return self._call_openai_sync(system_prompt, prompt)
        except Exception as e:
            logger.error(f"단일 프롬프트 처리 실패: {e}")
            return f"오류가 발생했습니다: {str(e)}"