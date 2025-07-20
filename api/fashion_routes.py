from fastapi import APIRouter, HTTPException
import logging
from models.fashion_models import (
    ResponseModel, 
    ExpertAnalysisRequest, 
    ExpertChainRequest, 
    PromptRequest,
    FashionExpertType
)
from services.fashion_expert_service import SimpleFashionExpertService
from config import settings

logger = logging.getLogger(__name__)

# 서비스 인스턴스
expert_service = SimpleFashionExpertService()

# 라우터 생성
router = APIRouter(prefix="/api", tags=["fashion"])

@router.get("/health")
def health_check():
    return {"status": "healthy", "message": "패션 전문가 시스템 정상 작동 중"}

@router.get("/test")
def test():
    return {"message": "Fashion Expert API Test", "experts": list(FashionExpertType)}

@router.post("/ask")
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

@router.post("/expert/single")
async def single_expert_analysis(request: ExpertAnalysisRequest):
    """단일 전문가 분석"""
    try:
        result = await expert_service.get_single_expert_analysis(request)
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"단일 전문가 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/expert/chain")
async def expert_chain_analysis(request: ExpertChainRequest):
    """전문가 체인 분석 - 모든 전문가가 순차적으로 분석"""
    try:
        result = await expert_service.get_expert_chain_analysis(request)
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"전문가 체인 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/expert/types")
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

@router.post("/curation")
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
            "comprehensive_analysis": result.get("comprehensive_recommendation", "")
        })
    except Exception as e:
        logger.error(f"큐레이션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 