import requests
import time
import json

def debug_index():
    """인덱스 디버깅"""
    
    base_url = "http://localhost:6020/api"
    
    print("🔍 인덱스 디버깅 시작")
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
    print("🔍 상황별 검색 테스트")
    print("=" * 50)
    
    # 2. 상황별 검색 테스트
    test_situations = ["소개팅", "일상", "캐주얼"]
    
    for situation in test_situations:
        print(f"\n🔍 상황 검색: {situation}")
        try:
            response = requests.post(f"{base_url}/admin/search-by-situation", json={"situation": situation})
            if response.status_code == 200:
                result = response.json()
                files = result.get('data', {}).get('files', [])
                print(f"   - 찾은 파일 수: {len(files)}")
                if files:
                    print(f"   - 첫 번째 파일: {files[0]}")
            else:
                print(f"   - 검색 실패: {response.status_code}")
        except Exception as e:
            print(f"   - 검색 오류: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 아이템별 검색 테스트")
    print("=" * 50)
    
    # 3. 아이템별 검색 테스트
    test_items = ["셔츠", "티셔츠", "팬츠"]
    
    for item in test_items:
        print(f"\n🔍 아이템 검색: {item}")
        try:
            response = requests.post(f"{base_url}/admin/search-by-item", json={"item": item})
            if response.status_code == 200:
                result = response.json()
                files = result.get('data', {}).get('files', [])
                print(f"   - 찾은 파일 수: {len(files)}")
                if files:
                    print(f"   - 첫 번째 파일: {files[0]}")
            else:
                print(f"   - 검색 실패: {response.status_code}")
        except Exception as e:
            print(f"   - 검색 오류: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 실제 API 호출 테스트")
    print("=" * 50)
    
    # 4. 실제 API 호출 테스트
    test_request = {
        "user_input": "소개팅을 가야 하는 상황이야",
        "room_id": 59,
        "expert_type": "color_expert"
    }
    
    print(f"🔍 API 호출: {test_request['user_input']}")
    start_time = time.time()
    
    try:
        response = requests.post(f"{base_url}/expert/single", json=test_request)
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
                
            # 전체 응답 확인
            print(f"   - 전체 응답: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 요청 실패: {response.status_code}")
            print(f"   - 응답: {response.text}")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

if __name__ == "__main__":
    debug_index() 