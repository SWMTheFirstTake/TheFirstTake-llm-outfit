import os
import json
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)

def analyze_situations_from_outfit(extracted_items: dict) -> list:
    """착장 분석을 통해 적합한 상황 태그 추출 (여름 시즌 고려)"""
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
    
    # 여름 시즌 체크 (현재 여름이므로 여름에 적합한 착장만 고려)
    summer_appropriate = True
    summer_inappropriate_items = ["긴팔", "롱슬리브", "긴바지", "롱팬츠", "코트", "패딩", "니트", "스웨터", "블레이저", "블레이져", "자켓", "재킷"]
    
    if any(item in top_item for item in summer_inappropriate_items) or \
       any(item in bottom_item for item in summer_inappropriate_items):
        summer_appropriate = False
    
    # 상황별 판단 로직
    # 소개팅/데이트 (자켓+반바지 조합 완전 제외)
    jacket_keywords = ["셔츠", "블레이저", "자켓", "재킷", "블레이져"]
    pants_keywords = ["슬랙스", "팬츠", "바지"]
    formal_shoes = ["로퍼", "옥스포드", "구두"]
    shorts_keywords = ["반바지", "쇼츠", "하프팬츠", "숏팬츠", "숏츠", "쇼트팬츠"]
    
    has_jacket = any(keyword in top_item for keyword in jacket_keywords)
    has_pants = any(keyword in bottom_item for keyword in pants_keywords)
    has_formal_shoes = any(keyword in shoes_item for keyword in formal_shoes)
    has_shorts = any(keyword in bottom_item for keyword in shorts_keywords)
    
    # 자켓+반바지 조합은 소개팅에 완전히 부적절 - 제외
    if has_jacket and has_pants and has_formal_shoes and not has_shorts:
        situations.append("소개팅")
        situations.append("데이트")
    # 자켓+반바지 조합이면 소개팅 상황에서 제외
    elif has_jacket and has_shorts:
        # 소개팅 상황에 추가하지 않음
        pass
    
    # 면접/비즈니스
    if any(keyword in top_item for keyword in ["셔츠", "블레이저"]) and \
       any(keyword in bottom_item for keyword in ["슬랙스"]) and \
       any(keyword in shoes_item for keyword in ["로퍼", "옥스포드"]) and \
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
    if any(keyword in top_item for keyword in ["셔츠", "블레이저"]) and \
       any(keyword in bottom_item for keyword in ["슬랙스", "팬츠"]) and \
       any(keyword in shoes_item for keyword in ["로퍼", "옥스포드", "샌들"]):
        situations.append("파티")
        situations.append("이벤트")
    
    # 여름 시즌에 적합하지 않은 착장은 제외
    if not summer_appropriate:
        situations = ["여름에 부적합"]
    
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