import asyncio
import json
from services.claude_vision_service import ClaudeVisionService
from services.fashion_expert_service import SimpleFashionExpertService
from config import settings

async def test_vision_styling_analysis():
    """비전 API 스타일링 방법 분석 테스트"""
    
    print("🔍 비전 API 스타일링 방법 분석 테스트 시작")
    
    try:
        # 서비스 초기화
        vision_service = ClaudeVisionService(api_key=settings.CLAUDE_API_KEY)
        fashion_service = SimpleFashionExpertService(api_key=settings.CLAUDE_API_KEY)
        
        print("✅ 서비스 초기화 완료")
        
        # 테스트용 이미지 URL (실제 이미지 URL로 교체 필요)
        test_image_url = "https://example.com/test-outfit.jpg"
        
        print(f"🔍 테스트 이미지 분석 시작: {test_image_url}")
        
        # 이미지 분석 (실제 URL이 없으므로 시뮬레이션)
        # 실제 테스트시에는 아래 주석을 해제하고 사용
        # image_analysis = vision_service.analyze_outfit_from_url(test_image_url)
        
        # 시뮬레이션용 분석 결과 (새로운 JSON 형식 - 간소화된 색상명)
        image_analysis = {
            "top": {
                "item": "밀리터리 스타일 긴팔 셔츠",
                "color": "브라운",
                "fit": "오버핏",
                "material": "면 혼방",
                "length": "엉덩이 중간까지 내려오는 길이"
            },
            "bottom": {
                "item": "와이드 슬랙스",
                "color": "블랙",
                "fit": "와이드핏",
                "material": "울 혼방 팬츠",
                "length": "발등을 살짝 덮는 기장"
            },
            "shoes": {
                "item": "캔버스 스니커즈",
                "color": "화이트",
                "style": "캐주얼"
            },
            "accessories": [
                {
                    "item": "비즈 목걸이",
                    "color": "골드"
                }
            ],
            "styling_methods": {
                "top_wearing_method": "상의를 하의에 일부만 넣었음",
                "tuck_degree": "앞부분만 넣기",
                "fit_details": "어깨와 가슴은 여유롭고, 허리는 적당히 타이트함",
                "silhouette_balance": "상하의 길이 비율이 잘 맞아 균형감이 좋음",
                "styling_points": "소매 롤업, 버튼 2개만 단추"
            }
        }
        
        print("✅ 이미지 분석 완료")
        print("\n📋 분석 결과:")
        print(image_analysis)
        
        # 패션 데이터 매칭
        print("\n🔍 패션 데이터 매칭 시작...")
        matched_result = await fashion_service.analyze_image_with_fashion_data(image_analysis)
        
        print("\n✅ 매칭 결과:")
        print(json.dumps(matched_result, ensure_ascii=False, indent=2))
        
        # 스타일링 방법 정보 확인
        if "extracted_items" in matched_result:
            styling_methods = matched_result["extracted_items"].get("styling_methods", {})
            print("\n🎯 스타일링 방법 분석:")
            for key, value in styling_methods.items():
                if value:
                    print(f"   {key}: {value}")
        
        # 추천 확인
        if "recommendations" in matched_result:
            print("\n💡 스타일링 기반 추천:")
            for rec in matched_result["recommendations"]:
                print(f"   {rec}")
        
        # JSON 파일 저장 테스트
        print("\n💾 JSON 파일 저장 테스트...")
        from api.fashion_routes import save_outfit_analysis_to_json
        
        saved_filepath = save_outfit_analysis_to_json(image_analysis, room_id="test_room_123")
        if saved_filepath:
            print(f"✅ JSON 파일 저장 성공: {saved_filepath}")
            
            # 저장된 파일 내용 확인
            with open(saved_filepath, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
                print(f"\n📄 저장된 JSON 내용:")
                print(f"   상황 태그: {saved_data.get('situations', [])}")
                print(f"   분석 시간: {saved_data.get('analysis_timestamp', 'N/A')}")
                print(f"   룸 ID: {saved_data.get('room_id', 'N/A')}")
        else:
            print("❌ JSON 파일 저장 실패")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_vision_styling_analysis()) 