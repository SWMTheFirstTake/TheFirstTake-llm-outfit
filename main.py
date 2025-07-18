# from fastapi import FastAPI
# from pydantic import BaseModel
# from services.gpt_service import ask_gpt
# from typing import Generic, TypeVar, Optional, List
# from pydantic.generics import GenericModel
# import re

# # 공통 응답 모델 정의
# T = TypeVar("T")

# class ResponseModel(BaseModel, Generic[T]):
#     status: str = "success"
#     message: str = "Operation was successful."
#     data: Optional[T]  # 제너릭 타입으로 데이터 정의

# # 실제 응답에 들어갈 데이터 모델
# class AskResponseData(BaseModel):
#     question: str
#     options: List[str]  # 응답을 리스트로 저장

# # 실제 FastAPI 애플리케이션 설정
# app = FastAPI()

# class PromptRequest(BaseModel):
#     prompt: str

# # 질문과 응답을 분리하는 함수
# def split_question_and_answers(generated_text: str):
#     # 전체 줄을 분리
#     lines = generated_text.strip().splitlines()

#     question = ""
#     options = []

#     # 1. 먼저 질문 찾기 (Q. 로 시작하는 줄)
#     for line in lines:
#         if line.strip().startswith("Q."):
#             question = line.strip().replace("Q.", "").strip()
#             break  # 첫 번째 질문만 추출

#     # 2. 그 외의 줄 중에서 A., B., C. 등으로 시작하는 줄을 답변으로 추출
#     for line in lines:
#         line = line.strip()
#         match = re.match(r"^[A-PR-Z]\.\s*(.*)", line)  # Q 제외
#         if match:
#             options.append(match.group(1).strip())

#     return question, options
    
# @app.post("/api/ask")
# def ask(request: PromptRequest):
#     generated_text = ask_gpt(request.prompt)
#     return ResponseModel(data=generated_text)

# @app.get("/api/test")
# def test():
#     return {"message": "Hello, World!"}
# app = FastAPI(title="Fashion Curation API", version="2.0.0")

# # 라우터 등록
# app.include_router(curation_router)

# # main_simple.py - Redis 없이 간단 테스트용
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional, Any
# from enum import Enum
# import asyncio
# import openai
# from config import settings
# import logging

# app = FastAPI(title="Fashion Curation API", version="2.0.0")

# # 모델 정의
# class ResponseModel(BaseModel):
#     success: bool = True
#     message: str = "Success"
#     data: Any = None

# class CurationStyle(str, Enum):
#     FORMAL = "formal"
#     CASUAL = "casual"
#     CITY_BOY = "city_boy"

# class CurationRequest(BaseModel):
#     user_input: str
#     room_id: int
#     styles: Optional[List[CurationStyle]] = [CurationStyle.FORMAL, CurationStyle.CASUAL, CurationStyle.CITY_BOY]

# class PromptRequest(BaseModel):
#     prompt: str

# # 간단한 프롬프트 매니저 (메모리 기반)
# class SimplePromptManager:
#     def __init__(self):
#         self.contexts = {}  # 메모리에 저장
#         self.style_templates = {
#             CurationStyle.FORMAL: "라는 사용자의 질문에 대해 웬만하면 포멀한 스타일로 스타일 한 개만 추천해줘",
#             CurationStyle.CASUAL: "라는 사용자의 질문에 대해 웬만하면 캐쥬얼한 스타일로 스타일 한 개만 추천해줘",
#             CurationStyle.CITY_BOY: "라는 사용자의 질문에 대해 웬만하면 시티보이 스타일로 스타일 한 개만 추천해줘"
#         }
    
#     def get_or_create_prompt_context(self, room_id: int, user_input: str) -> str:
#         existing_context = self.contexts.get(room_id, "")
#         if existing_context:
#             return existing_context + "\n" + user_input
#         else:
#             return user_input
    
#     def build_style_prompt(self, context: str, style: CurationStyle) -> str:
#         style_addition = self.style_templates.get(style, "")
#         return context + style_addition
    
#     def update_prompt_context(self, room_id: int, new_context: str):
#         self.contexts[room_id] = new_context
    
#     def clear_context(self, room_id: int):
#         self.contexts.pop(room_id, None)

# # 간단한 큐레이션 서비스
# class SimpleCurationService:
#     def __init__(self):
#         self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
#         self.prompt_manager = SimplePromptManager()
    
#     async def generate_curation_response(self, request: CurationRequest):
#         current_context = self.prompt_manager.get_or_create_prompt_context(
#             request.room_id, 
#             request.user_input
#         )
        
#         tasks = []
#         for style in request.styles:
#             task = self._generate_single_curation(current_context, style)
#             tasks.append(task)
        
#         curation_results = await asyncio.gather(*tasks, return_exceptions=True)
        
#         results = []
#         context_builder = [current_context]
        
#         for i, (style, result) in enumerate(zip(request.styles, curation_results)):
#             if isinstance(result, Exception):
#                 content = "큐레이션 결과를 가져오는 중 오류가 발생했습니다."
#             else:
#                 content = result + f" ({i+1}번째 AI)"
#                 context_builder.append(content)
            
#             results.append({
#                 "style": style.value,
#                 "content": content
#             })
        
#         updated_context = '\n'.join(context_builder)
#         self.prompt_manager.update_prompt_context(request.room_id, updated_context)
        
#         return {
#             "room_id": request.room_id,
#             "results": results
#         }
    
#     async def _generate_single_curation(self, context: str, style: CurationStyle) -> str:
#         try:
#             style_prompt = self.prompt_manager.build_style_prompt(context, style)
            
#             loop = asyncio.get_event_loop()
#             response = await loop.run_in_executor(
#                 None, 
#                 self._call_openai_sync,
#                 style_prompt
#             )
            
#             return response
#         except Exception as e:
#             logging.error(f"OpenAI 호출 실패: {e}")
#             raise e
    
#     def _call_openai_sync(self, user_prompt: str) -> str:
#         response = self.client.chat.completions.create(
#             model=settings.LLM_MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": "당신은 의상 추천 전문가입니다."},
#                 {"role": "user", "content": user_prompt}
#             ],
#             max_tokens=settings.LLM_MAX_TOKENS,
#             temperature=settings.LLM_TEMPERATURE
#         )
#         return response.choices[0].message.content

# # 서비스 인스턴스
# curation_service = SimpleCurationService()

# # API 엔드포인트
# @app.post("/api/curation")
# async def generate_curation(request: CurationRequest):
#     try:
#         result = await curation_service.generate_curation_response(request)
#         return ResponseModel(data=result)
#     except Exception as e:
#         logging.error(f"큐레이션 생성 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/ask")
# def ask_single(request: PromptRequest):
#     try:
#         response = curation_service.client.chat.completions.create(
#             model=settings.LLM_MODEL_NAME,
#             messages=[
#                 {"role": "system", "content": "당신은 의상 추천 전문가입니다."},
#                 {"role": "user", "content": request.prompt}
#             ],
#             max_tokens=settings.LLM_MAX_TOKENS,
#             temperature=settings.LLM_TEMPERATURE
#         )
#         return ResponseModel(data=response.choices[0].message.content)
#     except Exception as e:
#         logging.error(f"단일 프롬프트 실패: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/test")
# def test():
#     return {"message": "Hello, World!"}

# @app.get("/health")
# def health_check():
#     return {"status": "healthy"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main_simple:app", host="0.0.0.0", port=6020, reload=True)
# main_simple_experts.py - 전문가 시스템 적용
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum
import asyncio
import openai
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fashion Expert API", version="2.0.0")

# 모델 정의
class ResponseModel(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Any = None

class FashionExpertType(str, Enum):
    STYLE_ANALYST = "style_analyst"          # 스타일 분석가
    TREND_EXPERT = "trend_expert"            # 트렌드 전문가
    # BUDGET_MANAGER = "budget_manager"        # 예산 관리자
    COLOR_EXPERT = "color_expert"            # 색상 전문가
    # TPO_EXPERT = "tpo_expert"               # TPO 전문가
    FITTING_COORDINATOR = "fitting_coordinator"  # 가상피팅 코디네이터

class ExpertAnalysisRequest(BaseModel):
    user_input: str
    room_id: int
    expert_type: FashionExpertType
    user_profile: Optional[Dict] = None
    context_info: Optional[Dict] = None

class ExpertChainRequest(BaseModel):
    user_input: str
    room_id: int
    expert_sequence: Optional[List[FashionExpertType]] = [
        FashionExpertType.STYLE_ANALYST,
        FashionExpertType.COLOR_EXPERT, 
        FashionExpertType.TREND_EXPERT,
        # FashionExpertType.TPO_EXPERT,
        # FashionExpertType.BUDGET_MANAGER,
        FashionExpertType.FITTING_COORDINATOR
    ]
    user_profile: Optional[Dict] = None
    context_info: Optional[Dict] = None

class PromptRequest(BaseModel):
    prompt: str

# 전문가 시스템
class SimpleFashionExpertService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 전문가별 특성 정의
        self.expert_profiles = {
            FashionExpertType.STYLE_ANALYST: {
                "role": "패션 스타일 분석 전문가",
                "expertise": "체형분석, 핏감분석, 실루엣",
                "focus": "사용자의 체형과 어울리는 스타일을 분석하고 핏감을 고려한 추천을 제공합니다.",
                "prompt_template": "사용자에게 이전 템플릿이 존재할 경우에만, 이전 템플릿의 추천이 어울릴지에 대한 생각을 매우 간단하게 회의적 80% 긍정적 20%의 느낌으로 1줄과, 체형분석과 핏감을 중심으로 고려하고 있음을 알려주고 어울리는 실루엣과 스타일을 한 줄 이내로 추천해주세요. 성별은 모르겠으면 물어보거나, 20대 남자로 가정하세요."
            },
            FashionExpertType.TREND_EXPERT: {
                "role": "패션 트렌드 전문가",
                "expertise": "최신트렌드, 셀럽스타일",
                "focus": "최신 패션 트렌드, 인플루언서 스타일을 반영한 추천을 제공합니다.",
                "prompt_template": "사용자에게 이전 템플릿의 추천이 어울릴지에 대한 생각을 매우 간단하게 회의적 80% 긍정적 20%의 느낌으로 1줄과,현재 트렌드와 셀럽 스타일을 고려하고 있음을 알려주고 트렌디한 옷을 한 줄 이내로 추천해주세요."
            },
            # FashionExpertType.BUDGET_MANAGER: {
            #     "role": "패션 예산 관리 전문가", 
            #     "expertise": "가격비교, 가성비, 투자가치",
            #     "focus": "예산 대비 최적의 가성비와 장기적 투자가치를 고려한 현실적인 추천을 제공합니다.",
            #     "prompt_template": "예산을 고려하여 가성비 좋고 투자가치가 높은 실용적인 옷을 추천해주세요."
            # },
            FashionExpertType.COLOR_EXPERT: {
                "role": "퍼스널 컬러 전문가",
                "expertise": "퍼스널컬러, 색상조합, 톤온톤", 
                "focus": "개인의 피부톤과 어울리는 색상 분석과 조화로운 컬러 조합을 제안합니다.",
                "prompt_template": "사용자에게 이전 템플릿의 추천이 어울릴지에 대한 생각을 매우 간단하게 회의적 80% 긍정적 20%의 느낌으로 1줄과, 퍼스널 컬러와 색상 조합을 고려하고 있음을 알려주고 어울리는 색상의 옷을 한 줄 이내로 추천해주세요. 성별과 피부톤을 사용자가 알려주지 않은 경우에는 일반적인 20대 남자로 가정하고, 사용자에게 물어보세요."
            },
            # FashionExpertType.TPO_EXPERT: {
            #     "role": "TPO 상황별 패션 전문가",
            #     "expertise": "상황분석, 드레스코드, 예의범절",
            #     "focus": "시간, 장소, 상황에 맞는 적절한 드레스코드와 예의를 고려한 패션을 제안합니다.",
            #     "prompt_template": "상황과 장소에 맞는 적절한 드레스코드를 고려하여 예의에 맞는 옷을 추천해주세요."
            # },
            FashionExpertType.FITTING_COORDINATOR: {
                "role": "가상 피팅 코디네이터",
                "expertise": "피팅연동, 결과분석, 대안제시",
                "focus": "모든 전문가의 의견을 종합하여 최종 코디네이션을 완성합니다.",
                "prompt_template": "앞선 전문가들의 조언을 종합하여 평가 의견과 완성된 코디네이션을 한 줄 이내로 제안해주세요."
            }
        }
    
    async def get_single_expert_analysis(self, request: ExpertAnalysisRequest):
        """단일 전문가 분석"""
        expert_profile = self.expert_profiles[request.expert_type]
        
        # 전문가별 프롬프트 구성
        context_parts = [f"사용자 요청: {request.user_input}"]
        
        if request.user_profile:
            context_parts.append(f"사용자 정보: {request.user_profile}")
        
        if request.context_info:
            context_parts.append(f"상황 정보: {request.context_info}")
        
        context_parts.append(f"\n{expert_profile['role']}으로서 {expert_profile['prompt_template']}")
        
        expert_prompt = "\n\n".join(context_parts)
        
        # OpenAI 호출
        try:
            response = await self._call_openai_async(
                f"당신은 {expert_profile['role']}입니다. {expert_profile['focus']} 전문 영역: {expert_profile['expertise']}",
                expert_prompt
            )
            
            return {
                "expert_type": request.expert_type.value,
                "expert_role": expert_profile["role"],
                "analysis": response,
                "expertise_areas": expert_profile["expertise"]
            }
            
        except Exception as e:
            logger.error(f"전문가 분석 실패 - {request.expert_type}: {e}")
            raise e
    
    async def get_expert_chain_analysis(self, request: ExpertChainRequest):
        """전문가 체인 분석"""
        expert_results = []
        accumulated_insights = []
        
        for expert_type in request.expert_sequence:
            # 이전 전문가들의 결과를 컨텍스트에 포함
            current_context = request.context_info or {}
            if accumulated_insights:
                current_context["previous_expert_insights"] = accumulated_insights[-3:]  # 최근 3개만
            
            expert_request = ExpertAnalysisRequest(
                user_input=request.user_input,
                room_id=request.room_id,
                expert_type=expert_type,
                user_profile=request.user_profile,
                context_info=current_context
            )
            
            expert_result = await self.get_single_expert_analysis(expert_request)
            expert_results.append(expert_result)
            
            # 다음 전문가를 위한 인사이트 누적
            accumulated_insights.append({
                "expert": expert_type.value,
                "key_point": expert_result["analysis"][:100] + "..."  # 요약만
            })
        
        # 최종 종합
        return {
            "expert_analyses": expert_results,
            # "expert_count": len(expert_results),
            # "comprehensive_recommendation": self._synthesize_results(expert_results),
            # "collaboration_flow": accumulated_insights
        }
    
    def _synthesize_results(self, expert_results: List[Dict]) -> str:
        """전문가 결과 종합"""
        synthesis = "===== 종합 패션 추천 =====\n\n"
        
        for result in expert_results:
            synthesis += f"🔹 {result['expert_role']}: {result['analysis'][:150]}...\n\n"
        
        synthesis += "📋 최종 추천: 모든 전문가의 조언을 종합하여 가장 적합한 단 하나의 스타일을 선택하시기 바랍니다. 대안 없이."
        
        return synthesis
    
    async def _call_openai_async(self, system_prompt: str, user_prompt: str) -> str:
        """비동기 OpenAI 호출"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            self._call_openai_sync,
            system_prompt,
            user_prompt
        )
        return response
    
    def _call_openai_sync(self, system_prompt: str, user_prompt: str) -> str:
        """동기 OpenAI 호출"""
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

# 서비스 인스턴스
expert_service = SimpleFashionExpertService()

# API 엔드포인트
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "패션 전문가 시스템 정상 작동 중"}

@app.get("/api/test")
def test():
    return {"message": "Fashion Expert API Test", "experts": list(FashionExpertType)}

@app.post("/api/ask")
async def ask_single(request: PromptRequest):
    """기존 단일 프롬프트 API (호환성 유지)"""
    try:
        response = expert_service.client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "당신은 종합 패션 어드바이저입니다."},
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE
        )
        return ResponseModel(data=response.choices[0].message.content)
    except Exception as e:
        logger.error(f"단일 프롬프트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expert/single")
async def single_expert_analysis(request: ExpertAnalysisRequest):
    """단일 전문가 분석"""
    try:
        result = await expert_service.get_single_expert_analysis(request)
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"단일 전문가 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expert/chain")
async def expert_chain_analysis(request: ExpertChainRequest):
    """전문가 체인 분석 - 모든 전문가가 순차적으로 분석"""
    try:
        result = await expert_service.get_expert_chain_analysis(request)
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"전문가 체인 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/expert/types")
async def get_expert_types():
    """사용 가능한 전문가 타입과 설명"""
    expert_info = {}
    for expert_type, profile in expert_service.expert_profiles.items():
        expert_info[expert_type.value] = {
            "role": profile["role"],
            "expertise": profile["expertise"],
            "focus": profile["focus"]
        }
    return ResponseModel(data=expert_info)

# 기존 호환성을 위한 큐레이션 API
@app.post("/api/curation")
async def generate_curation(request: ExpertChainRequest):
    """기존 큐레이션 API - 이제 전문가 체인으로 처리"""
    try:
        result = await expert_service.get_expert_chain_analysis(request)
        
        # 기존 형식으로 변환
        converted_results = []
        for i, expert_result in enumerate(result["expert_analyses"]):
            converted_results.append({
                "style": expert_result["expert_type"], 
                "content": expert_result["analysis"] + f" ({i+1}번째 전문가)"
            })
        
        return ResponseModel(data={
            "room_id": request.room_id,
            "results": converted_results,
            "comprehensive_analysis": result["comprehensive_recommendation"]
        })
    except Exception as e:
        logger.error(f"큐레이션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("🏃‍♂️ 패션 전문가 시스템 실행 중... 포트 6020")
    uvicorn.run("main_simple_experts:app", host="0.0.0.0", port=6020, reload=True)