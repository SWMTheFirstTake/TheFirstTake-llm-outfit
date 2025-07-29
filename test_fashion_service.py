#!/usr/bin/env python3
"""
패션 전문가 서비스 테스트 스크립트
참고 데이터 로드 및 관련 데이터 추출 기능을 테스트합니다.
"""

import asyncio
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.fashion_expert_service import SimpleFashionExpertService
from models.fashion_models import FashionExpertType, ExpertAnalysisRequest

async def test_fashion_service():
    """패션 서비스 테스트"""
    
    # API 키 설정 (실제 키가 필요합니다)
    api_key = "your-claude-api-key-here"  # 실제 API 키로 교체 필요
    
    try:
        # 서비스 초기화
        print("🚀 패션 전문가 서비스 초기화 중...")
        service = SimpleFashionExpertService(api_key)
        
        # 테스트 케이스들
        test_cases = [
            {
                "input": "데이트용 옷 추천해줘",
                "description": "데이트 상황에 맞는 추천"
            },
            {
                "input": "출근용 셔츠 추천해줘",
                "description": "출근용 셔츠 추천"
            },
            {
                "input": "여름에 입을 옷 추천해줘",
                "description": "계절별 추천"
            },
            {
                "input": "블랙 컬러로 코디 추천해줘",
                "description": "특정 컬러 추천"
            },
            {
                "input": "청바지와 어울리는 상의 추천해줘",
                "description": "특정 아이템 조합 추천"
            }
        ]
        
        print("\n" + "="*50)
        print("📋 테스트 시작")
        print("="*50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 테스트 {i}: {test_case['description']}")
            print(f"입력: {test_case['input']}")
            
            # 관련 데이터 추출 테스트
            relevant_data = service._get_relevant_reference_data(test_case['input'])
            
            if relevant_data:
                print(f"📚 관련 참고 데이터:")
                print(relevant_data)
            else:
                print("📚 관련 참고 데이터: 없음")
            
            print("-" * 30)
        
        # 실제 API 호출 테스트 (API 키가 있을 때만)
        if api_key != "your-claude-api-key-here":
            print("\n🤖 실제 API 호출 테스트")
            
            request = ExpertAnalysisRequest(
                user_input="데이트용 옷 추천해줘",
                room_id="test-room",
                expert_type=FashionExpertType.STYLE_ANALYST,
                user_profile="20대 남성, 175cm, 70kg",
                context_info={"occasion": "데이트", "season": "여름"}
            )
            
            result = await service.get_single_expert_analysis(request)
            print(f"결과: {result['analysis']}")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

def test_reference_data_loading():
    """참고 데이터 로드 테스트 (API 키 없이)"""
    print("📚 참고 데이터 로드 테스트")
    
    try:
        # 임시 API 키로 서비스 초기화 (데이터 로드만 테스트)
        service = SimpleFashionExpertService("temp-key")
        
        print("✅ 참고 데이터 로드 성공!")
        print(f"   - 패션 아이템: {len(service.fashion_reference_data['fashion_items'])}개")
        print(f"   - 아웃핏 조합: {len(service.fashion_reference_data['outfit_combinations'])}개")
        print(f"   - 스타일링 팁: {len(service.fashion_reference_data['styling_tips'])}개")
        print(f"   - 컬러 추천: {len(service.fashion_reference_data['color_recommendations'])}개")
        print(f"   - 계절별 조언: {len(service.fashion_reference_data['seasonal_advice'])}개")
        
        # 샘플 데이터 출력
        if service.fashion_reference_data['fashion_items']:
            print(f"\n📦 샘플 패션 아이템:")
            for item in service.fashion_reference_data['fashion_items'][:2]:
                print(f"   - {item['item']}: {item['description']}")
        
        if service.fashion_reference_data['outfit_combinations']:
            print(f"\n👔 샘플 아웃핏 조합:")
            for combo in service.fashion_reference_data['outfit_combinations'][:2]:
                print(f"   - {combo['combination']}: {', '.join(combo['items'])}")
        
        # 참고 데이터 기반 응답 생성 테스트
        print(f"\n🤖 참고 데이터 기반 응답 생성 테스트")
        test_inputs = [
            "데이트용 옷 추천해줘",
            "출근용 셔츠 추천해줘", 
            "여름에 입을 옷 추천해줘",
            "블랙 컬러로 코디 추천해줘",
            "청바지와 어울리는 상의 추천해줘"
        ]
        
        expert_types = [
            FashionExpertType.STYLE_ANALYST,
            FashionExpertType.TREND_EXPERT,
            FashionExpertType.COLOR_EXPERT,
            FashionExpertType.FITTING_COORDINATOR
        ]
        
        for test_input in test_inputs:
            print(f"\n🔍 입력: {test_input}")
            
            # 관련 데이터 추출 테스트
            relevant_data = service._get_relevant_reference_data(test_input)
            if relevant_data:
                print(f"📚 관련 데이터: {len(relevant_data.split('\\n'))}개 항목")
            
            # 각 전문가별 응답 생성 테스트
            for expert_type in expert_types:
                response = service._generate_response_from_reference_data(test_input, expert_type)
                if response:
                    print(f"   {expert_type.value}: {response}")
                else:
                    print(f"   {expert_type.value}: LLM 사용 필요")
        
    except Exception as e:
        print(f"❌ 참고 데이터 로드 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 패션 전문가 서비스 테스트")
    print("="*50)
    
    # 참고 데이터 로드 테스트
    test_reference_data_loading()
    
    # 전체 테스트 (API 키가 있을 때만 실행)
    # asyncio.run(test_fashion_service())
    
    print("\n✅ 테스트 완료!") 