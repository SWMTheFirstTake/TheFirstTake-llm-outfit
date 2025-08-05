import asyncio
import json
from services.fashion_expert_service import get_fashion_expert_service, FashionExpertType
from models.fashion_models import ExpertAnalysisRequest

async def test_improved_prompt():
    """개선된 프롬프트가 구체적인 옷 정보를 포함하는지 테스트"""
    
    # 서비스 초기화
    expert_service = get_fashion_expert_service()
    
    # 테스트용 JSON 데이터 (소개팅 상황)
    test_json_data = {
        "top": {"item": "반팔 셔츠", "color": "브라운", "fit": "레귤러핏", "material": "면"},
        "bottom": {"item": "슬랙스", "color": "블랙", "fit": "와이드핏", "material": "면"},
        "shoes": {"item": "로퍼", "color": "브라운", "style": "캐주얼"},
        "styling_methods": {
            "top_wearing_method": "부분적으로 넣기",
            "tuck_degree": "앞부분만 넣기",
            "fit_details": "깔끔하고 정돈된 핏",
            "silhouette_balance": "비즈니스에 적합한 실루엣",
            "styling_points": "앞부분만 살짝 넣어 캐주얼한 무드 연출"
        }
    }
    
    # 테스트 요청 생성
    request = ExpertAnalysisRequest(
        user_input="소개팅에 갈 건데 어떤 옷을 입을까요?",
        room_id="test_room",
        expert_type=FashionExpertType.STYLE_ANALYST,
        json_data=test_json_data
    )
    
    print("🧪 개선된 프롬프트 테스트 시작")
    print(f"📝 테스트 JSON 데이터:")
    print(json.dumps(test_json_data, ensure_ascii=False, indent=2))
    print("\n" + "="*50)
    
    try:
        # 전문가 분석 실행
        result = await expert_service.get_single_expert_analysis(request)
        
        print(f"✅ 분석 결과:")
        print(f"전문가: {result['expert_role']}")
        print(f"응답 소스: {result['response_source']}")
        print(f"\n📋 분석 내용:")
        print(result['analysis'])
        
        # 구체적인 옷 정보가 포함되었는지 확인
        analysis_text = result['analysis'].lower()
        required_items = ['브라운', '반팔 셔츠', '블랙', '슬랙스', '브라운', '로퍼']
        
        missing_items = []
        for item in required_items:
            if item.lower() not in analysis_text:
                missing_items.append(item)
        
        if missing_items:
            print(f"\n❌ 누락된 옷 정보: {missing_items}")
        else:
            print(f"\n✅ 모든 구체적인 옷 정보가 포함됨!")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_improved_prompt()) 