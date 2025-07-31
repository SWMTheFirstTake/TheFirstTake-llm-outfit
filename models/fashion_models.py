from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum

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
    json_data: Optional[Dict] = None  # JSON 분석 결과 데이터

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

class ImageAnalysisRequest(BaseModel):
    image_url: str
    prompt: Optional[str] = None 