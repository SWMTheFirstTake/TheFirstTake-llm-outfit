import requests
import json

def test_context_search():
    """대화 컨텍스트를 활용한 검색 테스트"""
    
    base_url = "http://localhost:8000/api"
    
    # 첫 번째 요청: 구체적인 검색 조건
    print("🔍 첫 번째 요청: 구체적인 검색 조건")
    request1 = {
        "user_input": "소개팅을 가야 하는 상황이야",
        "room_id": 59,
        "expert_type": "color_expert"
    }
    
    response1 = requests.post(f"{base_url}/expert/single", json=request1)
    print(f"✅ 첫 번째 응답: {response1.status_code}")
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   - 검색 방법: {result1.get('data', {}).get('search_method', 'N/A')}")
        print(f"   - 매칭된 착장 수: {len(result1.get('data', {}).get('matches', []))}")
    
    print("\n" + "="*50 + "\n")
    
    # 두 번째 요청: 모호한 입력
    print("🔍 두 번째 요청: 모호한 입력")
    request2 = {
        "user_input": "다른거는?",
        "room_id": 59,  # 같은 room_id 사용
        "expert_type": "color_expert"
    }
    
    response2 = requests.post(f"{base_url}/expert/single", json=request2)
    print(f"✅ 두 번째 응답: {response2.status_code}")
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   - 검색 방법: {result2.get('data', {}).get('search_method', 'N/A')}")
        print(f"   - 매칭된 착장 수: {len(result2.get('data', {}).get('matches', []))}")
        
        # 컨텍스트 활용 여부 확인
        if result2.get('data', {}).get('search_method') == 'index':
            print("   - 🎉 인덱스 활용 성공! (대화 컨텍스트 활용)")
        else:
            print("   - ⚠️ 전체 스캔으로 폴백됨")
    
    print("\n" + "="*50 + "\n")
    
    # 세 번째 요청: 다른 모호한 입력
    print("🔍 세 번째 요청: 다른 모호한 입력")
    request3 = {
        "user_input": "더 보여줘",
        "room_id": 59,  # 같은 room_id 사용
        "expert_type": "color_expert"
    }
    
    response3 = requests.post(f"{base_url}/expert/single", json=request3)
    print(f"✅ 세 번째 응답: {response3.status_code}")
    
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"   - 검색 방법: {result3.get('data', {}).get('search_method', 'N/A')}")
        print(f"   - 매칭된 착장 수: {len(result3.get('data', {}).get('matches', []))}")
        
        if result3.get('data', {}).get('search_method') == 'index':
            print("   - 🎉 인덱스 활용 성공! (대화 컨텍스트 활용)")
        else:
            print("   - ⚠️ 전체 스캔으로 폴백됨")

if __name__ == "__main__":
    test_context_search() 