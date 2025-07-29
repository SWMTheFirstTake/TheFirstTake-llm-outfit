from fastapi import APIRouter, HTTPException, UploadFile, File
import logging
import json
import os
from datetime import datetime
from models.fashion_models import (
    ResponseModel, 
    ExpertAnalysisRequest, 
    ExpertChainRequest, 
    PromptRequest,
    ImageAnalysisRequest,
    FashionExpertType
)
from pydantic import BaseModel
from services.fashion_expert_service import SimpleFashionExpertService
from services.redis_service import redis_service
from config import settings
from services.claude_vision_service import ClaudeVisionService
from services.s3_service import s3_service

logger = logging.getLogger(__name__)

# 서비스 인스턴스
expert_service=None
try:
    expert_service = SimpleFashionExpertService(api_key=settings.CLAUDE_API_KEY)
    print("✅ SimpleFashionExpertService 초기화 성공")
    print(f"✅ 서비스 타입: {type(expert_service)}")
except Exception as e:
    print(f"❌ SimpleFashionExpertService 초기화 실패: {e}")
    expert_service = None

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

def get_fashion_expert_service():
    """패션 전문가 서비스 인스턴스 반환"""
    return expert_service

def analyze_situations_from_outfit(extracted_items: dict) -> list:
    """착장 분석을 통해 적합한 상황 태그 추출"""
    situations = []
    
    # 상의 분석
    top_item = extracted_items.get("top", {}).get("item", "").lower()
    top_color = extracted_items.get("top", {}).get("color", "").lower()
    top_fit = extracted_items.get("top", {}).get("fit", "").lower()
    
    # 하의 분석
    bottom_item = extracted_items.get("bottom", {}).get("item", "").lower()
    bottom_color = extracted_items.get("bottom", {}).get("color", "").lower()
    bottom_fit = extracted_items.get("bottom", {}).get("fit", "").lower()
    
    # 신발 분석
    shoes_item = extracted_items.get("shoes", {}).get("item", "").lower()
    shoes_style = extracted_items.get("shoes", {}).get("style", "").lower()
    
    # 스타일링 방법 분석
    styling_methods = extracted_items.get("styling_methods", {})
    tuck_degree = styling_methods.get("tuck_degree", "").lower()
    fit_details = styling_methods.get("fit_details", "").lower()
    
    # 상황별 판단 로직
    # 소개팅/데이트
    if any(keyword in top_item for keyword in ["셔츠", "블라우스"]) and \
       any(keyword in bottom_item for keyword in ["슬랙스", "팬츠"]) and \
       any(keyword in shoes_item for keyword in ["로퍼", "옥스포드", "힐"]):
        situations.append("소개팅")
        situations.append("데이트")
    
    # 면접/비즈니스
    if any(keyword in top_item for keyword in ["셔츠", "블라우스"]) and \
       any(keyword in bottom_item for keyword in ["슬랙스"]) and \
       any(keyword in shoes_item for keyword in ["로퍼", "옥스포드", "펌프스"]) and \
       ("넣" in tuck_degree or "정돈" in fit_details):
        situations.append("면접")
        situations.append("비즈니스")
    
    # 캐주얼/일상
    if any(keyword in top_item for keyword in ["티셔츠", "맨투맨", "후드티"]) and \
       any(keyword in bottom_item for keyword in ["데님", "팬츠"]) and \
       any(keyword in shoes_item for keyword in ["스니커즈", "샌들"]):
        situations.append("캐주얼")
        situations.append("일상")
    
    # 여행/아웃도어
    if any(keyword in top_item for keyword in ["니트", "스웨터"]) and \
       any(keyword in bottom_item for keyword in ["팬츠", "데님"]) and \
       any(keyword in shoes_item for keyword in ["스니커즈", "부츠"]):
        situations.append("여행")
        situations.append("아웃도어")
    
    # 파티/이벤트
    if any(keyword in top_item for keyword in ["드레스", "블라우스"]) and \
       any(keyword in bottom_item for keyword in ["스커트", "드레스"]) and \
       any(keyword in shoes_item for keyword in ["힐", "샌들"]):
        situations.append("파티")
        situations.append("이벤트")
    
    # 중복 제거
    situations = list(set(situations))
    
    # 기본값 설정
    if not situations:
        situations = ["일상"]
    
    return situations

def save_outfit_analysis_to_json(extracted_items: dict, room_id: str = None) -> str:
    """착장 분석 결과를 JSON 파일로 저장"""
    try:
        # 상황 태그 분석
        situations = analyze_situations_from_outfit(extracted_items)
        
        # 저장할 데이터 구성
        save_data = {
            "extracted_items": extracted_items,
            "situations": situations,
            "analysis_timestamp": datetime.now().isoformat(),
            "room_id": room_id
        }
        
        # 저장 디렉토리 확인 및 생성
        save_dir = r"C:\fashion_summary\item"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"outfit_analysis_{timestamp}.json"
        
        filepath = os.path.join(save_dir, filename)
        
        # JSON 파일 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 착장 분석 결과 저장 완료: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ 착장 분석 결과 저장 실패: {e}")
        logger.error(f"착장 분석 결과 저장 실패: {e}")
        return None

def find_matching_outfits_from_s3(user_input: str, expert_type: str) -> dict:
    """S3의 JSON 파일들에서 사용자 입력과 매칭되는 착장 찾기"""
    try:
        if s3_service is None:
            print("❌ s3_service가 None입니다!")
            return None
        
        # S3에서 모든 JSON 파일 가져오기
        json_files = s3_service.list_json_files()
        if not json_files:
            print("❌ S3에 JSON 파일이 없습니다!")
            return None
        
        matching_outfits = []
        
        # 각 JSON 파일 분석
        for file_info in json_files:
            try:
                # JSON 내용 가져오기
                json_content = s3_service.get_json_content(file_info['filename'])
                
                # 매칭 점수 계산
                match_score = calculate_match_score(user_input, json_content, expert_type)
                
                if match_score > 0.1:  # 임계값을 낮춰서 더 많은 착장 포함
                    matching_outfits.append({
                        'filename': file_info['filename'],
                        'content': json_content,
                        'score': match_score,
                        's3_url': file_info['s3_url']
                    })
                    
            except Exception as e:
                print(f"❌ JSON 파일 분석 실패: {file_info['filename']} - {e}")
                continue
        
        # 점수순으로 정렬
        matching_outfits.sort(key=lambda x: x['score'], reverse=True)
        
        # 상위 5개만 반환
        top_matches = matching_outfits[:5]
        
        print(f"✅ S3 매칭 완료: {len(top_matches)}개 착장 발견")
        return {
            'matches': top_matches,
            'all_files': json_files,  # 모든 파일 정보 추가
            'total_files': len(json_files),
            'matching_count': len(matching_outfits)
        }
        
    except Exception as e:
        print(f"❌ S3 매칭 실패: {e}")
        logger.error(f"S3 매칭 실패: {e}")
        return None

def calculate_match_score(user_input: str, json_content: dict, expert_type: str) -> float:
    """사용자 입력과 JSON 내용의 매칭 점수 계산"""
    score = 0.0
    
    try:
        # 사용자 입력을 소문자로 변환
        user_input_lower = user_input.lower()
        
        # JSON에서 추출된 아이템들
        extracted_items = json_content.get('extracted_items', {})
        situations = json_content.get('situations', [])
        
        # 상황 태그 매칭 (가중치 높음)
        situation_matched = False
        for situation in situations:
            if situation.lower() in user_input_lower:
                score += 0.4
                situation_matched = True
                break
        
        # 상황 태그가 매칭되지 않은 경우, 상황별 유사성 점수 부여
        if not situation_matched:
            situation_similarity_score = calculate_situation_similarity(user_input_lower, situations)
            score += situation_similarity_score
        
        # 아이템 매칭
        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict):
                item_name = item_info.get('item', '').lower()
                item_color = item_info.get('color', '').lower()
                item_fit = item_info.get('fit', '').lower()
                
                # 아이템명 매칭
                if item_name and item_name in user_input_lower:
                    score += 0.3
                
                # 색상 매칭
                if item_color and item_color in user_input_lower:
                    score += 0.2
                
                # 핏 매칭
                if item_fit and item_fit in user_input_lower:
                    score += 0.2
        
        # 스타일링 방법 매칭
        styling_methods = extracted_items.get('styling_methods', {})
        if isinstance(styling_methods, dict):
            for method_key, method_value in styling_methods.items():
                if isinstance(method_value, str) and method_value.lower() in user_input_lower:
                    score += 0.2
        
        # 전문가 타입별 가중치
        if expert_type == "stylist":
            # 스타일리스트는 스타일링 방법에 더 높은 가중치
            if styling_methods:
                score += 0.1
        
        return min(score, 1.0)  # 최대 1.0으로 제한
        
    except Exception as e:
        print(f"❌ 매칭 점수 계산 실패: {e}")
        return 0.0

def calculate_situation_similarity(user_input: str, situations: list) -> float:
    """사용자 입력과 상황 태그의 유사성 점수 계산"""
    score = 0.0
    
    # 상황별 키워드 매핑
    situation_keywords = {
        "일상": ["일상", "평상시", "데일리", "일반", "보통", "스터디", "공부", "학교", "대학"],
        "캐주얼": ["캐주얼", "편안", "편한", "자유", "스터디", "공부", "학교", "대학"],
        "소개팅": ["소개팅", "데이트", "연애", "만남", "미팅"],
        "면접": ["면접", "비즈니스", "업무", "회사", "직장", "오피스"],
        "파티": ["파티", "이벤트", "축하", "기념", "특별"],
        "여행": ["여행", "아웃도어", "야외", "레저", "휴가"]
    }
    
    # 사용자 입력에서 상황 키워드 찾기
    for situation, keywords in situation_keywords.items():
        for keyword in keywords:
            if keyword in user_input:
                # 해당 상황이 JSON의 situations에 있는지 확인
                if situation in situations:
                    score += 0.5  # 유사한 상황에 대한 점수를 높임
                    break
    
    return score

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
    """단일 전문가 분석 - S3 JSON 파일 기반 매칭"""
    print(f"🔍 single_expert_analysis 호출됨: {request.expert_type.value}")
    
    try:
        # S3에서 매칭되는 착장 찾기
        matching_result = find_matching_outfits_from_s3(request.user_input, request.expert_type.value)
        
        if not matching_result:
            # S3 연결 실패 등의 경우 기존 방식 사용
            print("ℹ️ S3 연결 실패로 기존 방식 사용")
            return await fallback_expert_analysis(request)
        
        if not matching_result['matches']:
            # 매칭 점수가 낮은 경우에도 가장 높은 점수의 착장 선택
            print("ℹ️ 매칭 점수가 낮지만 가장 높은 점수의 착장 선택")
            # 모든 JSON 파일을 점수순으로 정렬하여 가장 높은 것 선택
            all_outfits = []
            for file_info in matching_result.get('all_files', []):
                try:
                    json_content = s3_service.get_json_content(file_info['filename'])
                    match_score = calculate_match_score(request.user_input, json_content, request.expert_type.value)
                    all_outfits.append({
                        'filename': file_info['filename'],
                        'content': json_content,
                        'score': match_score,
                        's3_url': file_info['s3_url']
                    })
                except Exception as e:
                    continue
            
            if all_outfits:
                # 점수순으로 정렬하여 가장 높은 것 선택
                all_outfits.sort(key=lambda x: x['score'], reverse=True)
                selected_match = all_outfits[0]
                print(f"✅ 최고 점수 착장 선택: {selected_match['filename']} (점수: {selected_match['score']:.2f})")
            else:
                print("❌ 매칭할 수 있는 착장이 없어 fallback으로 전환")
                return await fallback_expert_analysis(request)
        else:
            # 기존 로직: 상위 3개 중에서 랜덤 선택
            import random
            top_matches = matching_result['matches']
            
            # 상위 3개 중에서 랜덤 선택
            if len(top_matches) >= 3:
                selected_match = random.choice(top_matches[:3])
            else:
                selected_match = random.choice(top_matches)
            
            print(f"✅ 선택된 착장: {selected_match['filename']} (점수: {selected_match['score']:.2f})")
        
        # 선택된 착장 정보 추출
        content = selected_match['content']
        extracted_items = content.get('extracted_items', {})
        situations = content.get('situations', [])
        
        # 간결한 응답 생성
        response = generate_concise_response(extracted_items, situations, request.expert_type.value, selected_match['s3_url'])
        
        # Redis에 분석 결과 추가
        analysis_content = f"[{request.expert_type.value}] S3 매칭 결과: {selected_match['filename']}"
        redis_service.append_prompt(request.room_id, analysis_content)
        
        return ResponseModel(
            success=True,
            message="S3 기반 착장 매칭 완료",
            data={
                "analysis": response,
                "matched_outfit": {
                    "filename": selected_match['filename'],
                    "score": selected_match['score'],
                    "s3_url": selected_match['s3_url'],
                    "situations": situations
                },
                "total_matches": matching_result['matching_count'],
                "source": "s3_json"
            }
        )
        
    except Exception as e:
        print(f"❌ S3 기반 분석 실패: {e}")
        logger.error(f"S3 기반 분석 실패: {e}")
        # 실패 시 기존 방식으로 폴백
        return await fallback_expert_analysis(request)

async def fallback_expert_analysis(request: ExpertAnalysisRequest):
    """기존 방식의 전문가 분석 (폴백)"""
    try:
        # Redis에서 기존 프롬프트 히스토리 가져오기
        existing_prompt = redis_service.get_prompt(request.room_id)
        
        # 기존 프롬프트와 새로운 user_input 합치기
        if existing_prompt:
            combined_input = existing_prompt + "\n\n[새로운 질문] " + request.user_input
            logger.info(f"기존 프롬프트와 새로운 입력 합침: room_id={request.room_id}")
        else:
            combined_input = request.user_input
            logger.info(f"새로운 입력만 사용: room_id={request.room_id}")
        
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
            message="기존 방식 전문가 분석 완료",
            data={
                **result,
                "source": "fallback"
            }
        )
    except Exception as e:
        logger.error(f"기존 방식 전문가 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_concise_response(extracted_items: dict, situations: list, expert_type: str, s3_url: str) -> str:
    """간결한 응답 생성"""
    try:
        response_parts = []
        
        # 상황 태그
        if situations:
            response_parts.append(f"🎯 **적합한 상황**: {', '.join(situations)}")
        
        # 아이템 정보
        items_info = []
        for category, item_info in extracted_items.items():
            if isinstance(item_info, dict) and item_info.get('item'):
                item_name = item_info.get('item', '')
                item_color = item_info.get('color', '')
                item_fit = item_info.get('fit', '')
                
                item_desc = item_name
                if item_color:
                    item_desc += f" ({item_color})"
                if item_fit:
                    item_desc += f" - {item_fit}"
                
                items_info.append(f"• {category.title()}: {item_desc}")
        
        if items_info:
            response_parts.append(f"👕 **착장 구성**:\n" + "\n".join(items_info))
        
        # 스타일링 방법 (스타일리스트인 경우 강조)
        styling_methods = extracted_items.get('styling_methods', {})
        if styling_methods and isinstance(styling_methods, dict):
            styling_info = []
            for key, value in styling_methods.items():
                if isinstance(value, str) and value:
                    styling_info.append(f"• {value}")
            
            if styling_info:
                if expert_type == "stylist":
                    response_parts.append(f"💡 **스타일링 포인트**:\n" + "\n".join(styling_info))
                else:
                    response_parts.append(f"✨ **스타일링**:\n" + "\n".join(styling_info))
        
        # 전문가별 추가 조언
        if expert_type == "stylist":
            response_parts.append("🎨 **스타일리스트 조언**: 이 조합은 균형감 있는 실루엣을 만들어내며, 상황에 맞는 세련된 룩을 완성합니다.")
        elif expert_type == "colorist":
            response_parts.append("🎨 **컬러리스트 조언**: 색상 조합이 조화롭게 어우러져 자연스러운 그라데이션을 만들어냅니다.")
        elif expert_type == "fit_expert":
            response_parts.append("📏 **핏 전문가 조언**: 각 아이템의 핏이 체형을 보완하며 편안하면서도 스타일리시한 실루엣을 연출합니다.")
        
        return "\n\n".join(response_parts)
        
    except Exception as e:
        print(f"❌ 응답 생성 실패: {e}")
        return "착장 정보를 분석하는 중 오류가 발생했습니다."

@router.post("/expert/chain")
async def expert_chain_analysis(request: ExpertChainRequest):
    """전문가 체인 분석 - 모든 전문가가 순차적으로 분석"""
    try:
        # Redis에서 기존 프롬프트 히스토리 가져오기
        existing_prompt = redis_service.get_prompt(request.room_id)
        
        # 기존 프롬프트와 새로운 user_input 합치기
        if existing_prompt:
            # 새로운 질문을 명확하게 구분하여 추가
            combined_input = existing_prompt + "\n\n[새로운 질문] " + request.user_input
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
            "claude_vision_service": {
                "initialized": claude_vision_service is not None,
                "service_type": str(type(claude_vision_service)) if claude_vision_service else "None",
                "status": "정상" if claude_vision_service else "서비스가 초기화되지 않았습니다"
            },
            "s3_service": {
                "initialized": s3_service is not None,
                "service_type": str(type(s3_service)) if s3_service else "None",
                "status": "정상" if s3_service else "서비스가 초기화되지 않았습니다",
                "bucket_name": s3_service.bucket_name if s3_service else "None",
                "bucket_prefix": s3_service.bucket_prefix if s3_service else "None"
            }
        }
    )

# ✅ 이미지 분석 API (S3 링크 기반)
@router.post("/vision/analyze-outfit")
async def analyze_outfit(request: ImageAnalysisRequest):
    """S3 이미지 링크 기반 착장 분석 API (패션 데이터 매칭 포함)"""
    
    print(f"🔍 analyze_outfit 호출됨 (S3 링크)")
    print(f"🔍 claude_vision_service 상태: {claude_vision_service is not None}")
    print(f"🔍 이미지 URL: {request.image_url}")
    
    # 서비스 초기화 확인
    if claude_vision_service is None:
        print("❌ claude_vision_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="Claude Vision 서비스가 초기화되지 않았습니다."
        )
    
    try:
        # S3 이미지 링크 분석
        image_analysis = claude_vision_service.analyze_outfit_from_url(
            image_url=request.image_url,
            prompt=request.prompt
        )
        print("✅ Claude API 호출 완료")
        
        # 패션 데이터와 매칭
        fashion_expert_service = get_fashion_expert_service()
        if fashion_expert_service:
            matched_result = await fashion_expert_service.analyze_image_with_fashion_data(image_analysis)
            extracted_items = matched_result["extracted_items"]
        else:
            # 패션 데이터 매칭 없이 기본 분석만 반환
            extracted_items = image_analysis
        
        # JSON 파일로 저장 (로컬)
        saved_filepath = save_outfit_analysis_to_json(extracted_items, room_id=request.room_id if hasattr(request, 'room_id') else None)
        
        # S3에 JSON 업로드 (이미지 파일명 기반)
        s3_json_url = None
        if s3_service:
            try:
                # 이미지 URL에서 파일명 추출
                image_filename = request.image_url.split('/')[-1].split('.')[0]  # 확장자 제거
                
                # JSON 파일이 이미 존재하는지 확인
                if not s3_service.check_json_exists(image_filename):
                    # JSON 데이터 준비
                    json_data = {
                        "extracted_items": extracted_items,
                        "situations": analyze_situations_from_outfit(extracted_items),
                        "analysis_timestamp": datetime.now().isoformat(),
                        "room_id": request.room_id if hasattr(request, 'room_id') else None,
                        "source_image_url": request.image_url
                    }
                    
                    # S3에 JSON 업로드
                    s3_json_url = s3_service.upload_json(json_data, image_filename)
                    print(f"✅ S3 JSON 업로드 완료: {s3_json_url}")
                else:
                    print(f"ℹ️ JSON 파일이 이미 존재합니다: {image_filename}")
                    
            except Exception as e:
                print(f"❌ S3 JSON 업로드 실패: {e}")
        
        return ResponseModel(
            success=True,
            message="이미지 분석 및 패션 데이터 매칭이 성공적으로 완료되었습니다",
            data={
                "extracted_items": extracted_items,
                "s3_json_url": s3_json_url
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        logger.error(f"이미지 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")

# ✅ S3 이미지 업로드 API (단일 파일)
@router.post("/vision/upload-image")
async def upload_image_to_s3(file: UploadFile = File(...)):
    """이미지를 S3에 업로드하는 API (단일 파일)"""
    
    print(f"🔍 upload_image_to_s3 호출됨")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    print(f"🔍 파일명: {file.filename}")
    
    # S3 서비스 초기화 확인
    if s3_service is None:
        print("❌ s3_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
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
        
        # S3에 업로드
        s3_url = s3_service.upload_image(image_bytes, file.filename)
        print("✅ S3 업로드 완료")
        
        return ResponseModel(
            success=True,
            message="이미지가 S3에 성공적으로 업로드되었습니다",
            data={
                "s3_url": s3_url,
                "filename": file.filename,
                "file_size": len(image_bytes)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        logger.error(f"S3 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")

# ✅ S3 이미지 업로드 API (다중 파일)
@router.post("/vision/upload-images")
async def upload_images_to_s3(files: list[UploadFile] = File(...)):
    """여러 이미지를 S3에 업로드하는 API"""
    
    print(f"🔍 upload_images_to_s3 호출됨")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    print(f"🔍 파일 개수: {len(files)}")
    
    # S3 서비스 초기화 확인
    if s3_service is None:
        print("❌ s3_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
        )
    
    try:
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                print(f"🔍 파일 처리 중: {file.filename}")
                
                # 파일 유효성 검증
                if not file.content_type or not file.content_type.startswith('image/'):
                    failed_files.append({
                        "filename": file.filename,
                        "error": "이미지 파일이 아닙니다."
                    })
                    continue
                
                image_bytes = await file.read()
                print(f"✅ 이미지 읽기 완료: {len(image_bytes)} bytes")
                
                if len(image_bytes) == 0:
                    failed_files.append({
                        "filename": file.filename,
                        "error": "빈 파일입니다."
                    })
                    continue
                
                # S3에 업로드
                s3_url = s3_service.upload_image(image_bytes, file.filename)
                print(f"✅ S3 업로드 완료: {file.filename}")
                
                uploaded_files.append({
                    "s3_url": s3_url,
                    "filename": file.filename,
                    "file_size": len(image_bytes)
                })
                
            except Exception as e:
                print(f"❌ 파일 업로드 실패: {file.filename} - {str(e)}")
                failed_files.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return ResponseModel(
            success=True,
            message=f"업로드 완료: {len(uploaded_files)}개 성공, {len(failed_files)}개 실패",
            data={
                "uploaded_files": uploaded_files,
                "failed_files": failed_files,
                "total_files": len(files),
                "success_count": len(uploaded_files),
                "failure_count": len(failed_files)
            }
        )
        
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        logger.error(f"S3 다중 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")

# ✅ 배치 이미지 분석 API
@router.post("/vision/batch-analyze")
async def batch_analyze_images():
    """S3의 /image 디렉토리에서 JSON이 없는 이미지들을 일괄 분석"""
    
    print(f"🔍 batch_analyze_images 호출됨")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    
    # S3 서비스 초기화 확인
    if s3_service is None:
        print("❌ s3_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
        )
    
    try:
        # JSON이 없는 이미지 파일들 조회
        files_to_analyze = s3_service.get_files_without_json()
        
        if not files_to_analyze:
            return ResponseModel(
                success=True,
                message="분석할 이미지가 없습니다. 모든 이미지에 대한 JSON이 이미 존재합니다.",
                data={
                    "total_files": 0,
                    "analyzed_files": [],
                    "failed_files": []
                }
            )
        
        print(f"🔍 분석 대상 파일 수: {len(files_to_analyze)}")
        
        analyzed_files = []
        failed_files = []
        
        # 각 파일에 대해 분석 수행
        for file_info in files_to_analyze:
            try:
                print(f"🔍 파일 분석 중: {file_info['filename']}")
                
                # ContentType 문제가 있는 경우 수정 시도
                if s3_service:
                    try:
                        # S3에서 파일의 ContentType 확인
                        response = s3_service.s3_client.head_object(
                            Bucket=s3_service.bucket_name,
                            Key=file_info['s3_key']
                        )
                        content_type = response.get('ContentType', '')
                        
                        # ContentType이 잘못된 경우 수정
                        if content_type == 'binary/octet-stream' or not content_type.startswith('image/'):
                            print(f"⚠️ ContentType 수정 중: {content_type} -> image/jpeg")
                            s3_service.fix_image_content_type(file_info['s3_key'])
                    except Exception as e:
                        print(f"⚠️ ContentType 확인 실패: {e}")
                
                # ImageAnalysisRequest 객체 생성
                request_data = ImageAnalysisRequest(
                    image_url=file_info['s3_url'],
                    room_id=None,  # 배치 처리시 room_id는 None
                    prompt=None
                )
                
                # 내부적으로 analyze_outfit 함수 호출
                result = await analyze_outfit(request_data)
                
                if result.success:
                    analyzed_files.append({
                        "filename": file_info['filename'],
                        "s3_url": file_info['s3_url'],
                        "analysis_result": result.data
                    })
                    print(f"✅ 파일 분석 완료: {file_info['filename']}")
                else:
                    failed_files.append({
                        "filename": file_info['filename'],
                        "s3_url": file_info['s3_url'],
                        "error": result.message
                    })
                    print(f"❌ 파일 분석 실패: {file_info['filename']} - {result.message}")
                
            except Exception as e:
                print(f"❌ 파일 분석 중 에러 발생: {file_info['filename']} - {str(e)}")
                failed_files.append({
                    "filename": file_info['filename'],
                    "s3_url": file_info['s3_url'],
                    "error": str(e)
                })
        
        return ResponseModel(
            success=True,
            message=f"배치 분석 완료: {len(analyzed_files)}개 성공, {len(failed_files)}개 실패",
            data={
                "total_files": len(files_to_analyze),
                "analyzed_files": analyzed_files,
                "failed_files": failed_files,
                "success_count": len(analyzed_files),
                "failure_count": len(failed_files)
            }
        )
        
    except Exception as e:
        print(f"❌ 배치 분석 에러 발생: {str(e)}")
        logger.error(f"배치 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 분석 실패: {str(e)}")

# ✅ 관리자 API - JSON 파일 관리
@router.get("/admin/json-files")
async def get_json_files():
    """S3의 모든 JSON 파일 목록 조회"""
    
    print(f"🔍 get_json_files 호출됨")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    
    # S3 서비스 초기화 확인
    if s3_service is None:
        print("❌ s3_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
        )
    
    try:
        json_files = s3_service.list_json_files()
        
        return ResponseModel(
            success=True,
            message=f"JSON 파일 목록 조회 완료: {len(json_files)}개 파일",
            data={
                "json_files": json_files,
                "total_count": len(json_files)
            }
        )
        
    except Exception as e:
        print(f"❌ JSON 파일 목록 조회 실패: {str(e)}")
        logger.error(f"JSON 파일 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"JSON 파일 목록 조회 실패: {str(e)}")

@router.get("/admin/json-content/{filename}")
async def get_json_content(filename: str):
    """특정 JSON 파일의 내용 조회"""
    
    print(f"🔍 get_json_content 호출됨: {filename}")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    
    # S3 서비스 초기화 확인
    if s3_service is None:
        print("❌ s3_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
        )
    
    try:
        json_content = s3_service.get_json_content(filename)
        
        return ResponseModel(
            success=True,
            message="JSON 파일 내용 조회 완료",
            data={
                "filename": filename,
                "content": json_content
            }
        )
        
    except Exception as e:
        print(f"❌ JSON 파일 내용 조회 실패: {str(e)}")
        logger.error(f"JSON 파일 내용 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"JSON 파일 내용 조회 실패: {str(e)}")

class SituationsUpdateRequest(BaseModel):
    situations: list

@router.put("/admin/update-situations/{filename}")
async def update_situations(filename: str, request: SituationsUpdateRequest):
    """JSON 파일의 situations 태그 업데이트"""
    
    print(f"🔍 update_situations 호출됨: {filename}")
    print(f"🔍 새로운 situations: {request.situations}")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    
    # S3 서비스 초기화 확인
    if s3_service is None:
        print("❌ s3_service가 None입니다!")
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
        )
    
    try:
        s3_url = s3_service.update_json_situations(filename, request.situations)
        
        return ResponseModel(
            success=True,
            message="Situations 태그 업데이트 완료",
            data={
                "filename": filename,
                "updated_situations": request.situations,
                "s3_url": s3_url
            }
        )
        
    except Exception as e:
        print(f"❌ Situations 업데이트 실패: {str(e)}")
        logger.error(f"Situations 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Situations 업데이트 실패: {str(e)}")

# ✅ 이미지 분석 API (파일 업로드 기반 - 기존 방식 유지)
@router.post("/vision/analyze-outfit-upload")
async def analyze_outfit_upload(file: UploadFile = File(...)):
    """파일 업로드 기반 착장 분석 API (패션 데이터 매칭 포함)"""
    
    print(f"🔍 analyze_outfit_upload 호출됨")
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
        image_analysis = claude_vision_service.analyze_outfit(image_bytes)
        print("✅ Claude API 호출 완료")
        
        # 패션 데이터와 매칭
        fashion_expert_service = get_fashion_expert_service()
        if fashion_expert_service:
            matched_result = await fashion_expert_service.analyze_image_with_fashion_data(image_analysis)
            extracted_items = matched_result["extracted_items"]
        else:
            # 패션 데이터 매칭 없이 기본 분석만 반환
            extracted_items = image_analysis
        
        # JSON 파일로 저장
        saved_filepath = save_outfit_analysis_to_json(extracted_items)
        
        return ResponseModel(
            success=True,
            message="이미지 분석 및 패션 데이터 매칭이 성공적으로 완료되었습니다",
            data={"extracted_items": extracted_items}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        logger.error(f"이미지 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")
