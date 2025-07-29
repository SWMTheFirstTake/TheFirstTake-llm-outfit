#!/usr/bin/env python3
"""
JSON 데이터 기반 응답 생성 테스트
"""

import asyncio
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fashion_expert_service import SimpleFashionExpertService
from models.fashion_models import FashionExpertType, ExpertAnalysisRequest

def test_json_data_loading():
    """JSON 데이터 로딩 상태 테스트"""
    print("🔍 JSON 데이터 로딩 상태 확인")
    
    # 서비스 초기화
    service = SimpleFashionExpertService("dummy_key")
    
    # JSON 데이터 상태 출력
    print(f"\n📊 JSON 데이터 상태:")
    print(f"아웃핏 조합: {len(service.fashion_reference_data['outfit_combinations'])}개")
    print(f"컬러 추천: {len(service.fashion_reference_data['color_recommendations'])}개")
    print(f"패션 아이템: {len(service.fashion_reference_data['fashion_items'])}개")
    print(f"스타일링 팁: {len(service.fashion_reference_data['styling_tips'])}개")
    print(f"계절 조언: {len(service.fashion_reference_data['seasonal_advice'])}개")
    
    # 실제 데이터 샘플 출력
    if service.fashion_reference_data['outfit_combinations']:
        print(f"\n🎯 첫 번째 아웃핏 조합:")
        combo = service.fashion_reference_data['outfit_combinations'][0]
        print(f"   조합명: {combo['combination']}")
        print(f"   아이템들: {', '.join(combo['items'])}")
        print(f"   상황: {combo['occasion']}")
    else:
        print("❌ 아웃핏 조합 데이터가 없습니다!")
    
    if service.fashion_reference_data['color_recommendations']:
        print(f"\n🎨 첫 번째 컬러 추천:")
        color = service.fashion_reference_data['color_recommendations'][0]
        print(f"   컬러: {color['color']}")
        print(f"   설명: {color['description']}")
    else:
        print("❌ 컬러 추천 데이터가 없습니다!")
    
    if service.fashion_reference_data['fashion_items']:
        print(f"\n👕 첫 번째 패션 아이템:")
        item = service.fashion_reference_data['fashion_items'][0]
        print(f"   아이템: {item['item']}")
        print(f"   설명: {item['description']}")
        print(f"   스타일링 팁: {item['styling_tips']}")
    else:
        print("❌ 패션 아이템 데이터가 없습니다!")
    
    if service.fashion_reference_data['styling_tips']:
        print(f"\n💡 첫 번째 스타일링 팁:")
        print(f"   {service.fashion_reference_data['styling_tips'][0]}")
    else:
        print("❌ 스타일링 팁 데이터가 없습니다!")
    
    return service

def test_specific_keywords(service):
    """특정 키워드로 테스트"""
    print(f"\n🔍 특정 키워드 테스트")
    
    test_cases = [
        "데이트룩 추천해줘",
        "여름 휴가 옷 추천해줘", 
        "스트라이프 셔츠 추천해줘",
        "스카이블루 컬러 추천해줘"
    ]
    
    for test_input in test_cases:
        print(f"\n--- 테스트: {test_input} ---")
        response = service._generate_response_from_reference_data(test_input, FashionExpertType.STYLE_ANALYST)
        print(f"응답: {response}")

if __name__ == "__main__":
    print("🧪 JSON 데이터 로딩 및 키워드 테스트")
    
    # JSON 데이터 로딩 테스트
    service = test_json_data_loading()
    
    # 특정 키워드 테스트
    test_specific_keywords(service) 