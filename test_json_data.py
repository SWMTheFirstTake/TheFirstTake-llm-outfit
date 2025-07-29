from services.fashion_expert_service import SimpleFashionExpertService
import os

def test_json_data_loading():
    print("🔍 JSON 데이터 로드 테스트 시작")
    
    try:
        # 서비스 초기화
        service = SimpleFashionExpertService('test')
        
        print("\n📊 JSON 데이터 로드 결과:")
        print(f"   - 패션 아이템: {len(service.fashion_reference_data['fashion_items'])}개")
        print(f"   - 아웃핏 조합: {len(service.fashion_reference_data['outfit_combinations'])}개")
        print(f"   - 스타일링 팁: {len(service.fashion_reference_data['styling_tips'])}개")
        print(f"   - 컬러 추천: {len(service.fashion_reference_data['color_recommendations'])}개")
        print(f"   - 계절별 조언: {len(service.fashion_reference_data['seasonal_advice'])}개")
        
        # 실제 데이터 샘플 출력
        if service.fashion_reference_data['outfit_combinations']:
            print(f"\n🎯 첫 번째 아웃핏 조합:")
            print(f"   {service.fashion_reference_data['outfit_combinations'][0]}")
        
        if service.fashion_reference_data['fashion_items']:
            print(f"\n👕 첫 번째 패션 아이템:")
            print(f"   {service.fashion_reference_data['fashion_items'][0]}")
        
        if service.fashion_reference_data['color_recommendations']:
            print(f"\n🎨 첫 번째 컬러 추천:")
            print(f"   {service.fashion_reference_data['color_recommendations'][0]}")
        
        # 응답 생성 테스트
        print(f"\n🧪 응답 생성 테스트:")
        from models.fashion_models import FashionExpertType, ExpertAnalysisRequest
        
        request = ExpertAnalysisRequest(
            user_input="데이트룩 추천해줘",
            room_id="test",
            expert_type=FashionExpertType.STYLE_ANALYST
        )
        
        import asyncio
        result = asyncio.run(service.get_single_expert_analysis(request))
        print(f"   응답: {result['analysis']}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_json_data_loading() 