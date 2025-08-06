import requests
import time
import json

def test_index_status():
    """인덱스 상태 확인 및 성능 테스트"""
    
    base_url = "http://localhost:6020/api"
    
    print("🔍 인덱스 상태 확인")
    print("=" * 50)
    
    # 1. 인덱스 통계 확인
    try:
        response = requests.get(f"{base_url}/admin/index-stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 인덱스 통계: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 인덱스 통계 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 인덱스 통계 조회 오류: {e}")
    
    print("\n" + "=" * 50)
    print("🚀 성능 테스트")
    print("=" * 50)
    
    # 2. 성능 테스트
    test_requests = [
        {
            "user_input": "소개팅을 가야 하는 상황이야",
            "room_id": 59,
            "expert_type": "color_expert"
        },
        {
            "user_input": "다른거는?",
            "room_id": 59,
            "expert_type": "color_expert"
        }
    ]
    
    for i, request_data in enumerate(test_requests, 1):
        print(f"\n🔍 테스트 {i}: {request_data['user_input']}")
        
        start_time = time.time()
        try:
            response = requests.post(f"{base_url}/expert/single", json=request_data)
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                search_method = result.get('data', {}).get('search_method', 'N/A')
                matches_count = len(result.get('data', {}).get('matches', []))
                
                print(f"✅ 응답 시간: {end_time - start_time:.2f}초")
                print(f"   - 검색 방법: {search_method}")
                print(f"   - 매칭된 착장 수: {matches_count}")
                
                if search_method == 'index':
                    print("   - 🎉 인덱스 활용 성공!")
                else:
                    print("   - ⚠️ 전체 스캔으로 폴백됨")
            else:
                print(f"❌ 요청 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    test_index_status() 