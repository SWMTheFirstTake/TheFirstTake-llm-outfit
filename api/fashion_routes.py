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
from services.fashion_expert_service import SimpleFashionExpertService, get_fashion_expert_service
from services.redis_service import redis_service
from config import settings
from services.claude_vision_service import ClaudeVisionService
from services.s3_service import s3_service
from services.score_calculator_service import ScoreCalculator
from services.batch_analyzer_service import BatchAnalyzerService
from services.outfit_analyzer_service import OutfitAnalyzerService
from services.outfit_matcher_service import outfit_matcher_service
from services.utils import save_outfit_analysis_to_json, analyze_situations_from_outfit

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

@router.get("/health")
def health_check():
    return ResponseModel(
        success=True,
        message="패션 전문가 시스템 정상 작동 중",
        data={"service": "fashion_expert_system"}
    )

@router.post("/expert/single")
async def single_expert_analysis(request: ExpertAnalysisRequest):
    """단일 전문가 분석 - S3 JSON 파일 기반 매칭"""
    print(f"🔍 single_expert_analysis 호출됨: {request.expert_type.value}")
    
    try:
        # S3에서 매칭되는 착장 찾기
        print(f"🔍 S3 매칭 시도: '{request.user_input}' (전문가: {request.expert_type.value})")
        matching_result = outfit_matcher_service.find_matching_outfits_from_s3(request.user_input, request.expert_type.value)
        
        if not matching_result:
            # S3 연결 실패 등의 경우 기존 방식 사용
            print("❌ S3 매칭 실패로 fallback 로직 사용")
            print(f"   - s3_service 상태: {s3_service is not None}")
            if s3_service:
                print(f"   - s3_client 상태: {s3_service.s3_client is not None}")
                print(f"   - bucket_name: {s3_service.bucket_name}")
                print(f"   - bucket_json_prefix: {s3_service.bucket_json_prefix}")
            else:
                print("   - s3_service가 None입니다!")
            return await fallback_expert_analysis(request)
        
        if not matching_result['matches']:
            # 매칭 점수가 낮은 경우에도 가장 높은 점수의 착장 선택
            print("ℹ️ 매칭 점수가 낮지만 가장 높은 점수의 착장 선택")
            # 모든 JSON 파일을 점수순으로 정렬하여 가장 높은 것 선택
            all_outfits = []
            for file_info in matching_result.get('all_files', []):
                try:
                    json_content = s3_service.get_json_content(file_info['filename'])
                    match_score = outfit_matcher_service.score_calculator.calculate_match_score(request.user_input, json_content, request.expert_type.value)
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
            print(f"✅ S3 매칭 성공: {len(matching_result['matches'])}개 착장 발견")
            # 더욱 개선된 로직: 강제 다양성 보장
            import random
            top_matches = matching_result['matches']
            
            # 상위 20개까지 확장 (더 많은 선택지)
            selection_pool = top_matches[:min(20, len(top_matches))]
            
            # Redis에서 최근 사용된 아이템들 확인 (같은 세션에서 중복 방지)
            recent_used = redis_service.get_recent_used_outfits(request.room_id, limit=20)
            
            # Redis 연결 실패 시에도 기본 중복 방지를 위한 로컬 캐시 사용
            if not recent_used:
                print("⚠️ Redis 연결 실패 또는 최근 사용 데이터 없음, 로컬 중복 방지 사용")
                # 최소한의 중복 방지를 위해 빈 리스트로 시작
                recent_used = []
            
            print(f"🔄 Redis에서 가져온 최근 사용 아이템: {len(recent_used)}개")
            if recent_used:
                print(f"   - 최근 사용된 파일들: {recent_used[:5]}...")
            
            # 최근 사용된 아이템 제외 (더 강력한 중복 방지)
            available_matches = [match for match in selection_pool 
                               if match['filename'] not in recent_used]
            
            print(f"🔄 중복 제거 후 사용 가능한 아이템: {len(available_matches)}개 (전체: {len(selection_pool)}개)")
            
            # 사용 가능한 아이템이 부족하면 전체 데이터베이스에서 랜덤 선택
            if len(available_matches) < 3:
                print(f"⚠️ 선택 풀 부족 ({len(available_matches)}개), 전체 DB에서 랜덤 선택")
                # 전체 JSON 파일에서 최근 사용되지 않은 것들 찾기
                all_files = matching_result.get('all_files', [])
                unused_files = [f for f in all_files if f['filename'] not in recent_used]
                
                if unused_files:
                    # 랜덤하게 10개 선택하여 풀에 추가
                    random_additional = random.sample(unused_files, min(10, len(unused_files)))
                    for file_info in random_additional:
                        try:
                            json_content = s3_service.get_json_content(file_info['filename'])
                            match_score = outfit_matcher_service.score_calculator.calculate_match_score(request.user_input, json_content, request.expert_type.value)
                            available_matches.append({
                                'filename': file_info['filename'],
                                'content': json_content,
                                'score': match_score,
                                's3_url': file_info['s3_url']
                            })
                        except Exception as e:
                            continue
            
            # 여전히 부족하면 전체에서 선택하되, 최근 사용된 것들은 가중치를 낮춤
            if not available_matches:
                print("⚠️ 사용 가능한 아이템이 없어 전체에서 선택하되 가중치 조정")
                available_matches = selection_pool
                # 최근 사용된 아이템들은 선택 확률을 낮춤
                for match in available_matches:
                    if match['filename'] in recent_used:
                        match['score'] *= 0.1  # 점수를 10%로 낮춤 (더 강력한 중복 방지)
            
            # 강제 다양성: 같은 파일이 연속으로 선택되지 않도록
            if len(available_matches) > 1:
                # 최근 5개 요청에서 사용된 파일들을 더 강력하게 제외
                recent_5_used = recent_used[:5]
                if recent_5_used:
                    available_matches = [match for match in available_matches 
                                       if match['filename'] not in recent_5_used]
                    print(f"🔄 최근 5개 사용 파일 제외 후: {len(available_matches)}개")
                    
                    # 여전히 부족하면 가중치만 낮춤
                    if len(available_matches) < 2:
                        available_matches = [match for match in selection_pool]
                        for match in available_matches:
                            if match['filename'] in recent_5_used:
                                match['score'] *= 0.05  # 점수를 5%로 낮춤
                
                # 전문가 타입별 + 강제 다양성 선택 로직
                if len(available_matches) >= 3:
                    # 가중치 기반 선택을 위한 점수 정규화
                    total_score = sum(match['score'] for match in available_matches)
                    if total_score > 0:
                        for match in available_matches:
                            match['weight'] = match['score'] / total_score
                    else:
                        # 모든 점수가 0인 경우 균등 가중치
                        weight = 1.0 / len(available_matches)
                        for match in available_matches:
                            match['weight'] = weight
                    
                    # 점수대별 그룹화
                    high_score = [m for m in available_matches if m['score'] >= 0.6]
                    mid_score = [m for m in available_matches if 0.3 <= m['score'] < 0.6]
                    low_score = [m for m in available_matches if m['score'] < 0.3]
                    
                    print(f"📊 점수대별 분포: 고득점({len(high_score)}개), 중간({len(mid_score)}개), 저득점({len(low_score)}개)")
                    
                    # 점수대별 선택 확률 (고득점 40%, 중간 40%, 저득점 20%)
                    import random
                    score_choice = random.choices(
                        ['high', 'mid', 'low'], 
                        weights=[0.4, 0.4, 0.2], 
                        k=1
                    )[0]
                    
                    print(f"🎲 선택된 점수대: {score_choice}")
                    
                    # 선택된 점수대에서 후보 선택
                    if score_choice == 'high' and high_score:
                        candidates = high_score
                        print(f"✅ 고득점 그룹에서 선택 (점수: 0.6+)")
                    elif score_choice == 'mid' and mid_score:
                        candidates = mid_score
                        print(f"✅ 중간 점수 그룹에서 선택 (점수: 0.3-0.6)")
                    elif score_choice == 'low' and low_score:
                        candidates = low_score
                        print(f"✅ 저득점 그룹에서 선택 (점수: 0.3 미만)")
                    else:
                        # 선택된 점수대에 후보가 없으면 다른 점수대에서 선택
                        if high_score:
                            candidates = high_score
                            print(f"⚠️ 고득점 그룹으로 대체 선택")
                        elif mid_score:
                            candidates = mid_score
                            print(f"⚠️ 중간 점수 그룹으로 대체 선택")
                        elif low_score:
                            candidates = low_score
                            print(f"⚠️ 저득점 그룹으로 대체 선택")
                        else:
                            candidates = available_matches
                            print(f"⚠️ 전체에서 선택")
                    
                    # 전문가 타입별 필터링
                    candidates = outfit_matcher_service.score_calculator.apply_expert_filter(candidates, request.expert_type.value)
                    
                    # 최종 선택 (균등 확률)
                    if candidates:
                        selected_match = random.choice(candidates)
                        print(f"🎲 최종 선택: {selected_match['filename']} (점수: {selected_match['score']:.3f})")
                    else:
                        # 필터링 후 후보가 없으면 전체에서 선택
                        selected_match = random.choice(available_matches)
                        print(f"⚠️ 필터링 후 후보 없음, 전체에서 선택: {selected_match['filename']}")
                else:
                    # 후보가 적으면 완전 랜덤 선택
                    selected_match = random.choice(available_matches)
                    print(f"🎲 후보 부족으로 랜덤 선택: {selected_match['filename']}")
                
                # 선택된 아이템을 최근 사용 목록에 추가
                redis_service.add_recent_used_outfit(request.room_id, selected_match['filename'])
                
                print(f"✅ 선택된 착장: {selected_match['filename']} (점수: {selected_match['score']:.2f})")
                print(f"📊 선택 풀 크기: {len(available_matches)}개, 전체 매칭: {len(top_matches)}개")
                print(f"🎯 전문가 타입: {request.expert_type.value}, 점수: {selected_match['score']:.2f}")
                print(f"🔄 최근 사용 제외: {len(recent_used)}개")
                
                # 가중치 정보 출력
                if 'weight' in selected_match:
                    print(f"⚖️ 선택 가중치: {selected_match['weight']:.3f}")
                
                # 선택된 아이템의 주요 정보 출력
                content = selected_match['content']
                items = content.get('extracted_items', {})
                situations = content.get('situations', [])
                
                print(f"👕 아이템: {items.get('top', {}).get('item', 'N/A')} / {items.get('bottom', {}).get('item', 'N/A')}")
                print(f"🏷️ 상황: {', '.join(situations[:3])}")
                print(f"🔄 최근 사용 제외: {len(recent_used)}개")
                
                # 중복 방지 강화: 선택된 아이템을 즉시 로컬 캐시에도 추가
                recent_used.append(selected_match['filename'])
                if len(recent_used) > 20:
                    recent_used.pop(0)  # 가장 오래된 것 제거
            
            print(f"✅ 선택된 아이템을 Redis와 로컬 캐시에 추가: {selected_match['filename']}")
        
        # 선택된 착장 정보 추출
        content = selected_match['content']
        extracted_items = content.get('extracted_items', {})
        situations = content.get('situations', [])
        
        # JSON 데이터를 전문가 서비스로 전달하여 자연스러운 답변 생성
        expert_service = get_fashion_expert_service()
        if expert_service:
            # JSON 데이터를 request에 추가
            request.json_data = extracted_items
            expert_result = await expert_service.get_single_expert_analysis(request)
            response = expert_result['analysis']
            print(f"✅ JSON 기반 전문가 분석 완료: {expert_result['expert_type']}")
        else:
            # 전문가 서비스가 없으면 기존 방식 사용
            response = generate_concise_response(extracted_items, situations, request.expert_type.value, selected_match['s3_url'])
            print("⚠️ 전문가 서비스 없음, 기존 방식 사용")
        
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
        
        # 상의
        top = extracted_items.get('top', {})
        if isinstance(top, dict) and top.get('item'):
            item_name = top.get('item', '')
            item_color = top.get('color', '')
            item_fit = top.get('fit', '')
            
            item_desc = item_name
            if item_color:
                item_desc += f" ({item_color})"
            if item_fit:
                item_desc += f" - {item_fit}"
            
            items_info.append(f"• 상의: {item_desc}")
        
        # 하의
        bottom = extracted_items.get('bottom', {})
        if isinstance(bottom, dict) and bottom.get('item'):
            item_name = bottom.get('item', '')
            item_color = bottom.get('color', '')
            item_fit = bottom.get('fit', '')
            
            item_desc = item_name
            if item_color:
                item_desc += f" ({item_color})"
            if item_fit:
                item_desc += f" - {item_fit}"
            
            items_info.append(f"• 하의: {item_desc}")
        
        # 신발
        shoes = extracted_items.get('shoes', {})
        if isinstance(shoes, dict) and shoes.get('item'):
            item_name = shoes.get('item', '')
            item_color = shoes.get('color', '')
            
            item_desc = item_name
            if item_color:
                item_desc += f" ({item_color})"
            
            items_info.append(f"• 신발: {item_desc}")
        
        if items_info:
            response_parts.append(f"👕 **착장 구성**:\n" + "\n".join(items_info))
        

        
        # 스타일링 방법 (스타일리스트인 경우 강조)
        styling_methods = extracted_items.get('styling_methods', {})
        if styling_methods and isinstance(styling_methods, dict):
            styling_info = []
            
            # 주요 스타일링 포인트들을 카테고리별로 정리
            main_styling = []
            detail_styling = []
            
            for key, value in styling_methods.items():
                if isinstance(value, str) and value:
                    # 전문 용어를 쉬운 말로 변환
                    easy_value = value
                    
                    # 프렌치턱, 하프턱 등의 전문 용어를 쉬운 말로 변경
                    easy_value = easy_value.replace("프렌치턱", "앞부분만 살짝 넣기")
                    easy_value = easy_value.replace("하프턱", "앞부분만 넣기")
                    easy_value = easy_value.replace("오버핏", "여유있게")
                    easy_value = easy_value.replace("레귤러핏", "딱 맞게")
                    easy_value = easy_value.replace("슬림핏", "타이트하게")
                    easy_value = easy_value.replace("크로스 스타일", "단추 교차 스타일")
                    
                    # 주요 스타일링 (상의 착용법, 핏감, 실루엣)
                    if key in ['top_wearing_method', 'tuck_degree', 'fit_details', 'silhouette_balance']:
                        main_styling.append(f"• {easy_value}")
                    # 세부 스타일링 (소매, 단추, 액세서리 등)
                    elif key in ['cuff_style', 'button_style', 'accessory_placement', 'pocket_usage', 'belt_style']:
                        detail_styling.append(f"• {easy_value}")
                    # 기타 스타일링 포인트
                    else:
                        detail_styling.append(f"• {easy_value}")
            
            # 주요 스타일링 표시
            if main_styling:
                if expert_type == "stylist":
                    response_parts.append(f"💡 **주요 스타일링**:\n" + "\n".join(main_styling))
                else:
                    response_parts.append(f"✨ **스타일링**:\n" + "\n".join(main_styling))
            
            # 세부 스타일링 표시 (스타일리스트인 경우에만)
            if detail_styling and expert_type == "stylist":
                response_parts.append(f"🎯 **세부 포인트**:\n" + "\n".join(detail_styling))
        
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
    
    # OutfitAnalyzerService 인스턴스 생성
    outfit_analyzer = OutfitAnalyzerService()
    
    try:
        # 새로운 서비스를 사용하여 분석 수행
        result = await outfit_analyzer.analyze_outfit_from_url(
            image_url=request.image_url,
            room_id=request.room_id if hasattr(request, 'room_id') else None,
            prompt=request.prompt
        )
        
        return ResponseModel(
            success=result["success"],
            message=result["message"],
            data=result["data"]
        )
        
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
    
    # BatchAnalyzerService 인스턴스 생성
    batch_analyzer = BatchAnalyzerService()
    
    try:
        # 배치 분석 수행
        result = await batch_analyzer.analyze_batch()
        
        if result["total_files"] == 0:
            return ResponseModel(
                success=True,
                message="분석할 이미지가 없습니다. 모든 이미지에 대한 JSON이 이미 존재합니다.",
                data=result
            )
        
        return ResponseModel(
            success=True,
            message=f"배치 분석 완료: {result['success_count']}개 성공, {result['failure_count']}개 실패",
            data=result
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

@router.delete("/admin/delete-outfit/{filename}")
async def delete_outfit(filename: str):
    """특정 아웃핏의 이미지와 JSON 파일을 S3에서 삭제"""
    
    print(f"🔍 delete_outfit 호출됨: {filename}")
    print(f"🔍 s3_service 상태: {s3_service is not None}")
    
    if s3_service is None:
        raise HTTPException(
            status_code=500, 
            detail="S3 서비스가 초기화되지 않았습니다."
        )
    
    try:
        # JSON 파일 내용 가져오기 (이미지 URL 확인용)
        json_content = s3_service.get_json_content(filename)
        image_url = json_content.get('source_image_url', '')
        
        deleted_files = []
        
        # 1. JSON 파일 삭제
        json_key = f"{s3_service.bucket_json_prefix}/{filename}.json"
        try:
            s3_service.s3_client.delete_object(
                Bucket=s3_service.bucket_name,
                Key=json_key
            )
            deleted_files.append(f"JSON: {json_key}")
            print(f"✅ JSON 파일 삭제 완료: {json_key}")
        except Exception as e:
            print(f"⚠️ JSON 파일 삭제 실패: {e}")
        
        # 2. 이미지 파일 삭제 (URL에서 키 추출)
        if image_url:
            try:
                # URL에서 S3 키 추출
                image_key = image_url.replace(f"https://{s3_service.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/", "")
                s3_service.s3_client.delete_object(
                    Bucket=s3_service.bucket_name,
                    Key=image_key
                )
                deleted_files.append(f"Image: {image_key}")
                print(f"✅ 이미지 파일 삭제 완료: {image_key}")
            except Exception as e:
                print(f"⚠️ 이미지 파일 삭제 실패: {e}")
        
        return ResponseModel(
            success=True,
            message=f"아웃핏 파일들이 삭제되었습니다.",
            data={
                "filename": filename,
                "deleted_files": deleted_files,
                "image_url": image_url
            }
        )
        
    except Exception as e:
        print(f"❌ 아웃핏 삭제 실패: {str(e)}")
        logger.error(f"아웃핏 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"삭제 실패: {str(e)}")

# ✅ 이미지 분석 API (파일 업로드 기반 - 기존 방식 유지)
@router.post("/vision/analyze-outfit-upload")
async def analyze_outfit_upload(file: UploadFile = File(...)):
    """파일 업로드 기반 착장 분석 API (패션 데이터 매칭 포함)"""
    
    # OutfitAnalyzerService 인스턴스 생성
    outfit_analyzer = OutfitAnalyzerService()
    
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
        
        # 새로운 서비스를 사용하여 분석 수행
        result = await outfit_analyzer.analyze_outfit_from_bytes(
            image_bytes=image_bytes,
            filename=file.filename
        )
        
        return ResponseModel(
            success=result["success"],
            message=result["message"],
            data=result["data"]
        )
        
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")
        logger.error(f"이미지 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 실패: {str(e)}")
