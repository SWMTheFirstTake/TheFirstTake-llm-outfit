from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
from models.fashion_models import (
    ResponseModel, 
    ExpertAnalysisRequest, 
    ExpertChainRequest, 
    PromptRequest,
    FashionExpertType
)
from services.fashion_expert_service import SimpleFashionExpertService
from services.redis_service import redis_service
from config import settings
from services.claude_vision_service import ClaudeVisionService

logger = logging.getLogger(__name__)

# 서비스 인스턴스
expert_service = SimpleFashionExpertService()

# ✅ ClaudeVisionService 한 번만 초기화
claude_vision_service = None
try:
    claude_vision_service = ClaudeVisionService(
        api_key=settings.CLAUDE_API_KEY
    )
    print("✅ ClaudeVisionService 초기화 성공")
    print(f"✅ 서비스 타입: {type(claude_vision_service)}")
except Exception as e:
    print(f"❌ ClaudeVisionService 초기화 실패: {e}")
    claude_vision_service = None

# 라우터 생성
router = APIRouter(prefix="/api", tags=["fashion"])

@router.get("/health")
def health_check():
    return ResponseModel(
        success=True,
        message="패션 전문가 시스템 정상 작동 중",
        data={"service": "fashion_expert_system"}
    )

@router.get("/test")
def test():
    return ResponseModel(
        success=True,
        message="Fashion Expert API Test",
        data={"experts": list(FashionExpertType)}
    )

@router.post("/expert/single")
async def single_expert_analysis(request: ExpertAnalysisRequest):
    """단일 전문가 분석"""
    try:
        # Redis에서 기존 프롬프트 히스토리 가져오기
        existing_prompt = redis_service.get_prompt(request.room_id)
        
        # 기존 프롬프트와 새로운 user_input 합치기
        if existing_prompt:
            combined_input = existing_prompt + "\n" + request.user_input
            logger.info(f"기존 프롬프트와 새로운 입력 합침: room_id={request.room_id}, 기존길이={len(existing_prompt)}, 새길이={len(request.user_input)}")
        else:
            combined_input = request.user_input
            logger.info(f"새로운 입력만 사용: room_id={request.room_id}, 길이={len(request.user_input)}")
        
        # 수정된 요청 객체 생성
        modified_request = ExpertAnalysisRequest(
            user_input=combined_input,
            room_id=request.room_id,
            expert_type=request.expert_type,
            user_profile=request.user_profile,
            context_info=request.context_info
        )
        
        # 전문가 분석 실행
        result = await expert_service.get_single_expert_analysis(modified_request)
        
        # 분석 결과를 Redis에 추가
        analysis_content = f"[{request.expert_type.value}] {result.get('analysis', '분석 결과 없음')}"
        redis_service.append_prompt(request.room_id, analysis_content)
        
        return ResponseModel(
            success=True,
            message="단일 전문가 분석이 완료되었습니다",
            data=result
        )
    except Exception as e:
        logger.error(f"단일 전문가 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/expert/chain")
async def expert_chain_analysis(request: ExpertChainRequest):
    """전문가 체인 분석 - 모든 전문가가 순차적으로 분석"""
    try:
        # Redis에서 기존 프롬프트 히스토리 가져오기
        existing_prompt = redis_service.get_prompt(request.room_id)
        
        # 기존 프롬프트와 새로운 user_input 합치기
        if existing_prompt:
            combined_input = existing_prompt + "\n" + request.user_input
            logger.info(f"기존 프롬프트와 새로운 입력 합침: room_id={request.room_id}, 기존길이={len(existing_prompt)}, 새길이={len(request.user_input)}")
        else:
            combined_input = request.user_input
            logger.info(f"새로운 입력만 사용: room_id={request.room_id}, 길이={len(request.user_input)}")
        
        # 수정된 요청 객체 생성
        modified_request = ExpertChainRequest(
            user_input=combined_input,
            room_id=request.room_id,
            expert_sequence=request.expert_sequence,
            user_profile=request.user_profile,
            context_info=request.context_info
        )
        
        # 전문가 체인 분석 실행
        result = await expert_service.get_expert_chain_analysis(modified_request)
        
        # 각 전문가 분석 결과를 Redis에 추가
        if "expert_analyses" in result:
            for expert_result in result["expert_analyses"]:
                expert_type = expert_result.get("expert_type", "unknown")
                analysis = expert_result.get("analysis", "분석 결과 없음")
                analysis_content = f"[{expert_type}] {analysis}"
                redis_service.append_prompt(request.room_id, analysis_content)
        
        return ResponseModel(
            success=True,
            message="전문가 체인 분석이 완료되었습니다",
            data=result
        )
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
    return ResponseModel(
        success=True,
        message="전문가 타입 정보를 성공적으로 조회했습니다",
        data=expert_info
    )

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
        
        return ResponseModel(
            success=True,
            message="패션 큐레이션이 성공적으로 생성되었습니다",
            data={
                "room_id": request.room_id,
                "results": converted_results,
                "comprehensive_analysis": result.get("comprehensive_recommendation", "")
            }
        )
    except Exception as e:
        logger.error(f"큐레이션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Vision 서비스 상태 확인
@router.get("/vision/status")
async def vision_status():
    """Vision 서비스 상태 확인"""
    return ResponseModel(
        success=True,
        message="Vision 서비스 상태를 성공적으로 조회했습니다",
        data={
            "service_initialized": claude_vision_service is not None,
            "service_type": str(type(claude_vision_service)) if claude_vision_service else "None",
            "status": "정상" if claude_vision_service else "서비스가 초기화되지 않았습니다"
        }
    )

# ✅ 이미지 분석 API
@router.post("/vision/analyze-outfit")
async def analyze_outfit(file: UploadFile = File(...)):
    """이미지 기반 착장 분석 API"""
    
    print(f"🔍 analyze_outfit 호출됨")
    print(f"🔍 claude_vision_service 상태: {claude_vision_service is not None}")
    print(f"🔍 파일명: {file.filename}")
    
    # 서비스 초기화 확인
    if claude_vision_service is None:
        print("❌ claude_vision_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="Claude Vision 서비스가 초기화되지 않았습니다."
        )
    
    try:
        # 파일 유효성 검증
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="이미지 파일만 업로드 가능합니다."
            )
        
        image_bytes = await file.read()
        print(f"✅ 이미지 읽기 완료: {len(image_bytes)} bytes")
        
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=400, 
                detail="빈 파일입니다."
            )
        
        # Claude API 호출
        result = claude_vision_service.analyze_outfit(image_bytes)
        print("✅ Claude API 호출 완료")
        
        return ResponseModel(
            success=True,
            message="이미지 분석이 성공적으로 완료되었습니다",
            data={"analysis": result}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        logger.error(f"이미지 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")
