import json
import os
from services.fashion_expert_service import SimpleFashionExpertService

def debug_service():
    print("🔍 서비스 디버깅 시작")
    
    try:
        # 서비스 초기화
        service = SimpleFashionExpertService('test')
        
        print(f"\n📊 로드된 데이터:")
        print(f"   - 패션 아이템: {len(service.fashion_reference_data['fashion_items'])}개")
        print(f"   - 아웃핏 조합: {len(service.fashion_reference_data['outfit_combinations'])}개")
        print(f"   - 컬러 추천: {len(service.fashion_reference_data['color_recommendations'])}개")
        print(f"   - 스타일링 팁: {len(service.fashion_reference_data['styling_tips'])}개")
        
        # 실제 데이터 샘플 확인
        if service.fashion_reference_data['outfit_combinations']:
            print(f"\n🎯 첫 번째 아웃핏 조합:")
            print(f"   {service.fashion_reference_data['outfit_combinations'][0]}")
        
        if service.fashion_reference_data['fashion_items']:
            print(f"\n👕 첫 번째 패션 아이템:")
            print(f"   {service.fashion_reference_data['fashion_items'][0]}")
        
        # 응답 생성 테스트
        print(f"\n🧪 응답 생성 테스트:")
        test_inputs = ["데이트룩 추천해줘", "출근복 추천해줘", "여름 옷 추천해줘"]
        
        for test_input in test_inputs:
            print(f"\n📝 테스트 입력: {test_input}")
            
            # 직접 함수 호출
            from models.fashion_models import FashionExpertType
            response = service._generate_response_from_reference_data(test_input, FashionExpertType.STYLE_ANALYST)
            print(f"   응답: {response}")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_service() 