from fastapi import APIRouter, HTTPException, Depends
from models.curation_models import CurationRequest, CurationResponse, PromptRequest
from services.curation_service import CurationService
from models.response_models import ResponseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 의존성 주입
def get_curation_service() -> CurationService:
    return CurationService()

@router.post("/api/curation", response_model=ResponseModel[CurationResponse])
async def generate_curation(
    request: CurationRequest,
    curation_service: CurationService = Depends(get_curation_service)
):
    """스타일별 큐레이션 생성 API"""
    try:
        result = await curation_service.generate_curation_response(request)
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"큐레이션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="큐레이션 생성 중 오류가 발생했습니다.")

@router.post("/api/ask", response_model=ResponseModel[str])
async def ask_single(
    request: PromptRequest,
    curation_service: CurationService = Depends(get_curation_service)
):
    """기존 단일 프롬프트 API (호환성 유지)"""
    try:
        result = curation_service.ask_single_prompt(request.prompt)
        return ResponseModel(data=result)
    except Exception as e:
        logger.error(f"단일 프롬프트 처리 실패: {e}")
        raise HTTPException(status_code=500, detail="프롬프트 처리 중 오류가 발생했습니다.")

@router.delete("/api/curation/{room_id}/context")
async def clear_context(
    room_id: int,
    curation_service: CurationService = Depends(get_curation_service)
):
    """특정 방의 컨텍스트 초기화"""
    try:
        curation_service.prompt_manager.clear_context(room_id)
        return ResponseModel(data="컨텍스트가 초기화되었습니다.")
    except Exception as e:
        logger.error(f"컨텍스트 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail="컨텍스트 초기화 중 오류가 발생했습니다.")
